"""AI Git Helper의 명령줄 흐름을 앞선 기능 모듈에 연결한다."""

from __future__ import annotations  # 타입 표기의 즉시 평가를 미룬다.

import argparse  # 명령줄 인자 파싱과 도움말 출력을 제공한다.
from pathlib import Path  # 현재 작업 디렉터리를 Git 수집 함수에 경로 객체로 전달한다.
from typing import Sequence  # 테스트에서 전달할 선택적 인자 시퀀스의 타입이다.

from .api_client import DEFAULT_MAX_OUTPUT_TOKENS, DEFAULT_MODEL, GeminiClient
from .errors import AIGitHelperError
from .git_service import collect_git_changes
from .output import format_commit_draft, format_pr_draft
from .prompts import (
    COMMIT_RESPONSE_SCHEMA,
    PR_RESPONSE_SCHEMA,
    SYSTEM_PROMPT,
    build_commit_prompt,
    build_pr_prompt,
)
from .safety import DEFAULT_MAX_DIFF_CHARS, DEFAULT_MAX_DIFF_LINES, apply_safe_mode
from .validation import validate_commit_draft, validate_pr_draft


DEFAULT_TEMPERATURE = 1.0  # 모델 응답 다양성의 기본값이다.
DEFAULT_MAX_TOKENS = DEFAULT_MAX_OUTPUT_TOKENS  # API 모듈의 기본 출력 한도를 CLI 기본값으로 재사용한다.


def _positive_integer(value: str) -> int:
    parsed = int(value)  # argparse가 받은 문자열을 정수로 변환한다.
    if parsed <= 0:  # 토큰·diff 제한은 0 이하일 수 없다.
        raise argparse.ArgumentTypeError("0보다 큰 정수여야 합니다.")
    return parsed  # argparse가 args 속성에 저장할 검증된 양의 정수다.


def build_parser() -> argparse.ArgumentParser:
    """commit/pr 명령과 공통 실행 옵션을 구성한다."""

    parser = argparse.ArgumentParser(  # 프로그램 이름·설명·오류 형식을 관리할 파서를 만든다.
        prog="ai-git-helper",
        description="Git 변경 사항을 분석해 AI 기반 커밋 메시지와 PR 초안을 생성합니다.",
    )
    parser.add_argument(  # 첫 위치 인자로 commit 또는 pr 하위 작업을 받는다.
        "command",
        nargs="?",
        choices=("commit", "pr"),
        help="commit: 커밋 메시지 생성, pr: Pull Request 초안 생성",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini 모델명")  # 기본 모델을 사용하되 사용자가 바꿀 수 있게 한다.
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"응답 다양성 (기본값: {DEFAULT_TEMPERATURE})",
    )
    parser.add_argument(
        "--max-tokens",
        type=_positive_integer,
        default=DEFAULT_MAX_TOKENS,
        help=f"최대 출력 토큰 수 (기본값: {DEFAULT_MAX_TOKENS})",
    )

    safe_mode_group = parser.add_mutually_exclusive_group()  # 켜기와 끄기 플래그를 동시에 받지 않게 한다.
    safe_mode_group.add_argument(
        "--safe-mode",
        dest="safe_mode",
        action="store_true",
        default=True,
        help="민감정보 마스킹과 diff 크기 제한을 적용합니다. (기본값)",
    )
    safe_mode_group.add_argument(
        "--no-safe-mode",
        dest="safe_mode",
        action="store_false",
        help="안전 처리를 끕니다. 민감정보가 포함될 수 있으므로 주의하세요.",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=_positive_integer,
        default=DEFAULT_MAX_DIFF_LINES,
        help=f"safe-mode에서 전송할 최대 diff 줄 수 (기본값: {DEFAULT_MAX_DIFF_LINES})",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=_positive_integer,
        default=DEFAULT_MAX_DIFF_CHARS,
        help=f"safe-mode에서 전송할 최대 diff 문자 수 (기본값: {DEFAULT_MAX_DIFF_CHARS})",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="API 호출 없이, 학습용으로 실제 전송 프롬프트를 표시합니다.",
    )
    parser.add_argument(
        "--debug-response",
        action="store_true",
        help="JSON 파싱 실패 때만 마스킹된 AI 응답 미리보기를 표시합니다.",
    )
    return parser  # main과 테스트가 사용할 완성된 파서를 반환한다.


def main(arguments: Sequence[str] | None = None) -> int:
    """CLI를 실행하고 예상 가능한 문제는 traceback 없이 처리한다."""

    parser = build_parser()  # 명령·옵션 정의를 생성한다.
    args = parser.parse_args(arguments)  # 실제 CLI 인자 또는 테스트용 인자 목록을 해석한다.
    if args.command is None:  # 명령 없이 실행한 경우다.
        parser.print_help()
        return 0

    try:  # 예상 가능한 도메인 오류를 traceback 대신 짧은 메시지로 바꾼다.
        return _run_command(args)
    except KeyboardInterrupt:
        print("\n[ERROR] 사용자가 실행을 취소했습니다.")
        return 130
    except AIGitHelperError as error:
        print(f"[ERROR] {error}")
        return 1
    except ValueError as error:
        print(f"[ERROR] 입력값이 올바르지 않습니다: {error}")
        return 1


def _run_command(args: argparse.Namespace) -> int:
    """Git 수집부터 출력까지의 단일 실행 흐름을 수행한다."""

    changes = collect_git_changes(Path.cwd())  # 현재 디렉터리의 Git 상태·diff를 한 번 수집한다.
    # 변경이 없으면 API Key 확인과 외부 API 호출을 모두 건너뛴다.
    if not changes.has_changes:
        print("[INFO] Git 변경 사항이 없습니다. API를 호출하지 않습니다.")
        return 0

    safety_result = apply_safe_mode(  # AI에 넘길 diff에서 민감정보와 과도한 길이를 처리한다.
        changes.diff_text,
        enabled=args.safe_mode,
        max_lines=args.max_diff_lines,
        max_chars=args.max_diff_chars,
    )
    _print_safe_mode_notice(args.safe_mode, safety_result.masked_count, safety_result.truncated)

    if args.command == "commit":  # 커밋 초안은 커밋 전용 지시문과 schema를 사용한다.
        prompt = build_commit_prompt(changes, safety_result)  # commit 프롬프트를 만든다.
        schema = COMMIT_RESPONSE_SCHEMA  # 모델의 JSON 응답 모양을 commit 구조로 제한한다.
    else:  # choices로 검증돼 남은 명령은 pr이다.
        prompt = build_pr_prompt(changes, safety_result)  # PR 프롬프트를 만든다.
        schema = PR_RESPONSE_SCHEMA  # 모델의 JSON 응답 모양을 PR 구조로 제한한다.

    if args.show_prompt:  # 학습·점검 목적이면 API 호출 전 프롬프트만 보여 준다.
        print("[WARNING] 아래 프롬프트는 외부 AI에 전송될 내용입니다.")
        print("[WARNING] safe-mode는 보조 장치이므로 민감정보가 없는지 직접 확인하세요.")
        print("-" * 56)
        print(prompt)
        print("-" * 56)
        print("[INFO] --show-prompt 모드에서는 API를 호출하지 않았습니다.")
        return 0

    # GeminiClient.generate_json 내부의 HTTP 요청은 한 번만 실행된다.
    response = GeminiClient().generate_json(  # 한 번의 HTTP 요청으로 schema에 맞는 JSON 응답을 받는다.
        system_instruction=SYSTEM_PROMPT,
        user_input=prompt,
        response_schema=schema,
        model=args.model,
        temperature=args.temperature,
        max_output_tokens=args.max_tokens,
        debug_response=args.debug_response,
    )

    if args.command == "commit":  # 응답을 명령에 맞는 초안 타입으로 검증·출력한다.
        print(format_commit_draft(validate_commit_draft(response)))
    else:
        print(format_pr_draft(validate_pr_draft(response)))
    return 0  # 정상 실행을 운영체제에 알린다.


def _print_safe_mode_notice(enabled: bool, masked_count: int, truncated: bool) -> None:
    """안전 처리가 실제로 내용을 바꾼 경우에만 짧은 안내를 출력한다."""

    if not enabled:
        print("[WARNING] safe-mode가 꺼져 있습니다. 민감정보가 외부 AI에 전송될 수 있습니다.")
        return
    if masked_count or truncated:
        details: list[str] = []
        if masked_count:
            details.append(f"민감정보 {masked_count}개 마스킹")
        if truncated:
            details.append("diff 일부 생략")
        print(f"[SAFE MODE] {', '.join(details)}되었습니다.")
