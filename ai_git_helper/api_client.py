"""Gemini Interactions API를 한 번 호출하고 JSON 결과를 추출한다.

이 모듈은 ``requests``가 HTTP 요청을 보내는 역할만 맡는다. Git 변경 사항을
프롬프트로 만드는 일과 결과를 Commit/PR 형식으로 검증하는 일은 각각 다른
모듈에서 처리한다.
"""

from __future__ import annotations  # 타입 표기의 평가를 나중으로 미룬다.

import json  # 모델이 반환한 JSON 문자열을 Python 객체로 해석한다.
import os  # 환경변수에서 비밀 API 키를 읽는다.
import re  # 코드 블록·잘못된 이스케이프를 복구할 정규표현식에 사용한다.
from typing import Any, Mapping  # 외부 JSON과 schema의 유연한 타입을 나타낸다.

import requests  # Gemini REST API에 HTTP POST 요청을 보낸다.

from .errors import APIRequestError, ConfigurationError  # API·설정 실패를 CLI가 처리할 도메인 오류로 표현한다.
from .safety import mask_sensitive_text  # 진단 출력에서도 민감값이 새지 않도록 한다.


GEMINI_API_KEY_ENV = "GEMINI_API_KEY"  # 키를 코드에 두지 않고 찾을 환경변수 이름이다.
GEMINI_INTERACTIONS_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/interactions"
)
DEFAULT_MODEL = "gemini-3.6-flash"  # 별도 옵션이 없을 때 요청할 Gemini 모델이다.
# Git diff와 구조화된 응답을 처리하는 모델 요청은 30초를 넘길 수 있다.
# 자동 재시도는 하지 않되, 정상 처리 중인 요청을 너무 일찍 끊지 않도록 120초를 준다.
DEFAULT_TIMEOUT_SECONDS = 120  # 네트워크 요청 하나가 허용되는 최대 대기 시간이다.
DEFAULT_MAX_OUTPUT_TOKENS = 2048  # 응답 JSON이 잘리지 않도록 둔 기본 생성 한도다.


def get_api_key() -> str:
    """환경변수에서 API Key를 읽고, 없으면 안전한 안내 오류를 낸다."""

    api_key = os.environ.get(GEMINI_API_KEY_ENV, "").strip()  # 누락 시 빈 문자열로 받고 공백도 제거한다.
    if not api_key:  # 빈 키로 API를 호출하지 않고 즉시 이해하기 쉬운 오류를 낸다.
        raise ConfigurationError(
            "GEMINI_API_KEY 환경변수가 설정되지 않았습니다. "
            '예: export GEMINI_API_KEY="YOUR_API_KEY"'
        )
    return api_key  # 유효한 비어 있지 않은 키를 요청 생성 단계에 넘긴다.


def parse_json_object(text: str) -> dict[str, Any]:
    """모델 텍스트에서 JSON 객체를 읽는다.

    Structured output을 요청하지만, 모델이 Markdown 코드 블록이나 짧은 안내
    문구를 덧붙일 수 있다. 이 경우에도 안쪽 JSON 객체만 읽는다. 배열 등 객체가
    아닌 최상위 JSON은 이 프로그램이 기대하는 Commit/PR 데이터가 아니므로 거절한다.
    """

    cleaned = text.strip()  # 응답 앞뒤의 공백·줄바꿈을 제거한다.
    try:  # 먼저 전체 응답이 순수 JSON이라고 가정하고 빠르게 해석한다.
        parsed = json.loads(cleaned)  # JSON 문자열을 Python 값으로 변환한다.
    except json.JSONDecodeError as error:
        parsed = _find_embedded_json_object(cleaned)  # 설명문·코드 블록 안의 JSON 객체를 찾아 복구한다.
        if parsed is None:
            # 일부 모델은 Markdown 강조를 피하려고 JSON 안에 \_처럼 허용되지 않는
            # 이스케이프를 넣는다. JSON에서 허용되지 않는 이스케이프만 제거해 복구한다.
            repaired = re.sub(r'\\([^"\\/bfnrtu])', r"\1", cleaned)  # JSON에서 허용하지 않는 역슬래시 이스케이프만 제거한다.
            if repaired != cleaned:
                try:
                    parsed = json.loads(repaired)
                except json.JSONDecodeError:
                    parsed = _find_embedded_json_object(repaired)
        if parsed is None:  # 어느 복구 경로도 객체를 찾지 못한 경우다.
            if _looks_like_incomplete_json(cleaned):
                raise APIRequestError(
                    "AI 응답 JSON이 중간에 끝났습니다. "
                    "--max-tokens 값을 늘려 다시 실행하세요."
                ) from error
            raise APIRequestError("AI 응답이 올바른 JSON 형식이 아닙니다.") from error

    if not isinstance(parsed, dict):  # 이 도구가 기대하는 최상위 JSON은 객체여야 한다.
        raise APIRequestError("AI 응답의 최상위 JSON은 객체여야 합니다.")
    return parsed  # 검증된 JSON 객체를 validation 모듈로 넘긴다.


def _find_embedded_json_object(text: str) -> dict[str, Any] | None:
    """코드 블록 또는 설명문 안에 포함된 첫 JSON 객체를 찾는다.

    이 함수는 API 응답을 화면에 출력하지 않는다. 민감할 수 있는 Git 변경 내용이
    오류 메시지로 새지 않으면서, 모델의 형식 실수를 복구하기 위함이다.
    """

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.I)  # Markdown 코드 블록이 있으면 내용만 찾는다.
    candidates = [fenced.group(1).strip()] if fenced else []  # 코드 블록 내부를 첫 후보로 추가한다.
    candidates.extend(text[start:] for start, char in enumerate(text) if char == "{")  # 모든 '{' 위치부터의 문자열도 후보로 추가한다.

    decoder = json.JSONDecoder()  # 문자열 일부를 해석할 raw_decode 기능을 준비한다.
    for candidate in candidates:  # 가장 가능성 높은 후보부터 차례로 시도한다.
        try:
            parsed, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):  # 배열 등은 이 프로그램의 응답 형식이 아니므로 객체만 받는다.
            return parsed
    return None  # 올바른 내장 객체를 찾지 못했음을 호출자에게 알린다.


def _looks_like_incomplete_json(text: str) -> bool:
    """응답이 JSON 값의 시작 부분에서 끊긴 흔적이 있는지 확인한다."""

    return text.rstrip().endswith(("{", "[", ",", ":"))  # JSON 값이 이어져야 하는 기호에서 끝났는지 검사한다.


class GeminiClient:
    """Gemini REST 요청 한 건을 구성하는 작은 클라이언트.

    API Key는 생성 시 인자로 받거나, 생략하면 실행 시 환경변수에서 읽는다.
    그래서 Key가 코드나 저장소에 들어가지 않는다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        endpoint: str = GEMINI_INTERACTIONS_ENDPOINT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key  # 주입된 키가 있으면 테스트·특수 실행에서 환경변수보다 우선한다.
        self._endpoint = endpoint  # 테스트에서 대체 가능한 API 주소를 보관한다.
        self._timeout_seconds = timeout_seconds  # requests 호출에 쓸 시간 제한을 보관한다.

    def generate_json(
        self,
        *,
        system_instruction: str,
        user_input: str,
        response_schema: Mapping[str, Any],
        model: str = DEFAULT_MODEL,
        temperature: float = 1.0,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        debug_response: bool = False,
    ) -> dict[str, Any]:
        """Gemini에 한 번 요청하고 최종 ``output_text``를 JSON 객체로 반환한다."""

        api_key = self._api_key or get_api_key()  # 주입 키 또는 환경변수 키를 하나 선택한다.
        payload = {  # Gemini Interactions API가 요구하는 요청 본문을 구성한다.
            "model": model,
            "input": user_input,
            "system_instruction": system_instruction,
            "generation_config": {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": dict(response_schema),
            },
            # Git diff는 민감할 수 있다. 이 단발성 CLI는 서버 대화 상태를 쓰지 않는다.
            "store": False,
        }
        headers = {  # HTTP 본문 형식과 Google 인증 키를 헤더에 넣는다.
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        try:  # 네트워크 라이브러리 예외를 프로그램 전용 오류로 번역한다.
            response = requests.post(
                self._endpoint,
                headers=headers,
                json=payload,
                timeout=self._timeout_seconds,
            )
        except requests.Timeout as error:
            raise APIRequestError("AI API 요청 시간이 초과되었습니다. 잠시 후 다시 시도하세요.") from error
        except requests.ConnectionError as error:
            raise APIRequestError("AI API에 연결하지 못했습니다. 네트워크 연결을 확인하세요.") from error
        except requests.RequestException as error:
            raise APIRequestError("AI API 요청 중 네트워크 오류가 발생했습니다.") from error

        if not response.ok:  # HTTP 2xx가 아닌 경우 본문을 노출하지 않고 상태 코드 기반 안내를 쓴다.
            raise APIRequestError(_http_error_message(response.status_code))

        try:  # HTTP 본문을 JSON으로 해석한다.
            response_data = response.json()
        except ValueError as error:
            raise APIRequestError("AI API 응답 본문이 JSON 형식이 아닙니다.") from error

        output_text = _extract_output_text(response_data)  # 여러 API 응답 경로에서 최종 모델 텍스트를 꺼낸다.
        try:
            return parse_json_object(output_text)  # 모델 텍스트를 다음 validation 단계용 JSON 객체로 변환한다.
        except APIRequestError as error:
            if debug_response:
                raise APIRequestError(
                    f"{error}\n{_masked_response_preview(output_text)}"
                ) from error
            raise


def _http_error_message(status_code: int) -> str:
    """상태 코드만 사용해 안전하고 사용하기 쉬운 오류를 만든다."""

    if status_code == 400:  # 잘못된 요청 형식은 옵션·모델 확인으로 안내한다.
        return "AI API 요청 형식이 올바르지 않습니다. 모델과 요청 옵션을 확인하세요."
    if status_code in (401, 403):
        return "AI API 인증 또는 권한 확인에 실패했습니다. GEMINI_API_KEY를 확인하세요."
    if status_code == 429:
        return "AI API 요청 한도에 도달했습니다. 잠시 후 다시 시도하세요."
    if 500 <= status_code <= 599:
        return "AI API 서버에 일시적인 오류가 발생했습니다. 잠시 후 다시 시도하세요."
    return f"AI API 요청이 실패했습니다. (HTTP {status_code})"  # 알려지지 않은 코드는 번호만 안전하게 보여 준다.


def _extract_output_text(response_data: Any) -> str:
    """Interactions REST 응답에서 마지막 model_output의 텍스트를 가져온다.

    ``output_text``는 SDK가 덧붙이는 편의 필드라 raw REST 응답에는 보통 없다.
    따라서 REST의 표준 ``steps -> model_output -> content -> text`` 경로를 먼저
    지원한다. output_text는 테스트나 SDK 형태 응답과의 호환을 위한 보조 경로다.
    """

    if not isinstance(response_data, dict):  # API 최상위 응답이 객체인지 확인한다.
        raise APIRequestError("AI API 응답 구조가 올바르지 않습니다.")

    output_text = response_data.get("output_text")  # SDK·테스트 호환용 편의 필드를 먼저 확인한다.
    if isinstance(output_text, str) and output_text.strip():  # 비어 있지 않은 문자열이면 즉시 사용한다.
        return output_text

    steps = response_data.get("steps")  # raw REST 표준 경로의 단계 목록을 가져온다.
    if isinstance(steps, list):  # 단계 목록일 때만 역순 탐색한다.
        for step in reversed(steps):
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue

            content = step.get("content")
            if not isinstance(content, list):
                continue

            text_parts = [
                part.get("text")
                for part in content
                if isinstance(part, dict)
                and part.get("type") == "text"
                and isinstance(part.get("text"), str)
            ]
            text = "".join(text_parts)
            if text.strip():
                return text

    raise APIRequestError("AI API 응답에서 최종 텍스트 결과를 찾지 못했습니다.")


def _masked_response_preview(text: str, limit: int = 1_500) -> str:
    """명시적 진단 모드에서만 쓸, 마스킹된 모델 출력 미리보기다."""

    masked, masked_count = mask_sensitive_text(text)  # 디버그에도 민감 패턴을 먼저 숨긴다.
    preview = masked[:limit].replace("\n", "\\n")  # 여러 줄 출력을 한 줄 미리보기로 바꾼다.
    suffix = "... (이후 생략)" if len(masked) > limit else ""  # 한도를 넘긴 경우에만 생략 표식을 붙인다.
    return (
        "[DEBUG] AI 응답 미리보기(민감정보 패턴 마스킹, 최대 "
        f"{limit}자, 마스킹 {masked_count}개): {preview}{suffix}"
    )
