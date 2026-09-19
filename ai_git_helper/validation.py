"""AI의 JSON 응답을 신뢰할 수 있는 Commit/PR 초안으로 검증·정리한다."""

from __future__ import annotations  # 타입 표기의 평가를 나중으로 미룬다.

import re  # 모델이 붙인 불릿 기호를 제거하는 정규표현식에 사용한다.
from typing import Any, Mapping  # 외부 JSON 값과 키-값 매핑 타입을 명시한다.

from .errors import ValidationError  # 잘못된 AI 응답을 CLI가 사용자용 오류로 처리하게 한다.
from .models import CommitDraft, PRDraft  # 검증 후 출력 모듈에 전달할 타입이다.


COMMIT_TITLE_MAX_LENGTH = 72  # Git 커밋 제목의 일반적 권장 최대 길이다.
PR_TITLE_MAX_LENGTH = 80  # PR 제목에 적용할 최대 길이다.
_BULLET_PREFIX = re.compile(r"^(?:[-*+•◦])\s*")  # 문자열 시작의 여러 불릿 표기와 뒤 공백을 찾는다.


def _require_text(value: Any, field_name: str) -> str:
    """문자열인지 확인하고 줄바꿈을 공백으로 정리한다."""

    if not isinstance(value, str):  # JSON 필드가 문자열인지 먼저 엄격히 확인한다.
        raise ValidationError(f"'{field_name}' 필드는 문자열이어야 합니다.")

    normalized = " ".join(value.split())  # 줄바꿈·중복 공백을 한 칸으로 정리해 한 줄 텍스트로 만든다.
    if not normalized:  # 공백만 있던 값도 빈 값으로 거절한다.
        raise ValidationError(f"'{field_name}' 필드는 비어 있을 수 없습니다.")
    return normalized  # 비어 있지 않은 정규화 문자열을 반환한다.


def _validate_title(value: Any, *, field_name: str, max_length: int) -> str:
    """제목을 한 줄로 만들고, 의미 보존을 위해 긴 제목은 거절한다."""

    title = _require_text(value, field_name)  # 기본 문자열 검증과 한 줄 정리를 재사용한다.
    if len(title) > max_length:  # 임의 절단은 의미를 훼손할 수 있으므로 길면 오류로 돌린다.
        raise ValidationError(
            f"'{field_name}'은(는) 최대 {max_length}자여야 합니다. "
            "의미가 바뀔 수 있어 자동으로 자르지 않았습니다."
        )
    return title  # 길이 제한을 통과한 제목을 반환한다.


def _validate_bullet_lines(value: Any, field_name: str) -> list[str]:
    """배열의 빈 항목과 중복 불릿 표기를 제거한다."""

    if not isinstance(value, list):  # schema가 요구하는 배열 형식인지 확인한다.
        raise ValidationError(f"'{field_name}' 필드는 문자열 배열이어야 합니다.")

    normalized_lines: list[str] = []  # 비어 있지 않은 정리된 항목만 모은다.
    for index, item in enumerate(value, start=1):  # 오류 메시지에 사용자 친화적인 1부터의 순번을 사용한다.
        if not isinstance(item, str):  # 각 배열 원소도 문자열이어야 한다.
            raise ValidationError(
                f"'{field_name}'의 {index}번째 항목은 문자열이어야 합니다."
            )

        # 모델이 '- 항목'을 반환해도 출력 단계에서 '- - 항목'이 되지 않게 한다.
        line = _BULLET_PREFIX.sub("", " ".join(item.split())).strip()  # 공백을 정리하고 중복 불릿을 떼어 낸다.
        if line:  # 정리 뒤에도 내용이 남은 경우만 보존한다.
            normalized_lines.append(line)  # output이 불릿을 한 번만 붙일 수 있게 순수 텍스트를 저장한다.

    if not normalized_lines:  # 빈 항목만 받은 경우는 유효한 초안이 아니다.
        raise ValidationError(f"'{field_name}' 필드에는 비어 있지 않은 항목이 1개 이상 필요합니다.")
    return normalized_lines  # 검증·정리된 항목 목록을 반환한다.


def validate_commit_draft(response: Mapping[str, Any]) -> CommitDraft:
    """Commit 응답 JSON을 검증된 ``CommitDraft``로 바꾼다."""

    _require_mapping(response, "Commit 응답")  # 런타임에 실제 매핑인지 한 번 더 확인한다.
    return CommitDraft(  # 출력에 필요한 두 필드를 모두 검증한 불변 초안으로 조립한다.
        title=_validate_title(
            response.get("title"),
            field_name="title",
            max_length=COMMIT_TITLE_MAX_LENGTH,
        ),
        body_lines=_validate_bullet_lines(response.get("body"), "body"),
    )


def validate_pr_draft(response: Mapping[str, Any]) -> PRDraft:
    """PR 응답 JSON을 검증된 ``PRDraft``로 바꾼다."""

    _require_mapping(response, "PR 응답")  # 런타임에 실제 매핑인지 한 번 더 확인한다.
    return PRDraft(  # PR의 필수 네 섹션을 검증한 불변 초안으로 조립한다.
        title=_validate_title(
            response.get("title"), field_name="title", max_length=PR_TITLE_MAX_LENGTH
        ),
        why=_validate_bullet_lines(response.get("why"), "why"),
        what=_validate_bullet_lines(response.get("what"), "what"),
        how_to_test=_validate_bullet_lines(response.get("how_to_test"), "how_to_test"),
    )


def _require_mapping(value: Any, context: str) -> None:  # response가 JSON 객체처럼 키를 조회할 수 있는지 검사한다.
    if not isinstance(value, Mapping):  # dict뿐 아니라 일반 Mapping도 허용한다.
        raise ValidationError(f"{context}은(는) JSON 객체여야 합니다.")
