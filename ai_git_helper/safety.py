"""AI API 전송 전 민감정보를 마스킹하고 diff 크기를 제한한다.

정규표현식 기반 마스킹은 보조 안전장치다. 모든 비밀값을 탐지한다고
보장하지 않으므로, 사용자는 전송 전 diff를 직접 확인해야 한다.
"""

from __future__ import annotations  # 타입 표기의 평가를 미뤄 호환성과 순환 참조 안전성을 높인다.

import re  # 비밀값 형태를 찾고 바꾸는 정규표현식 기능을 제공한다.

from .models import SafetyResult  # 안전 처리 결과를 다른 모듈과 약속된 데이터 형태로 반환한다.


DEFAULT_MAX_DIFF_LINES = 200  # 기본 safe-mode가 API에 보낼 최대 diff 줄 수다.
DEFAULT_MAX_DIFF_CHARS = 20_000  # 기본 safe-mode가 API에 보낼 최대 문자 수다.
TRUNCATION_NOTICE = "\n[SAFE MODE: diff 일부 생략]"  # 잘린 결과 끝에 붙여 생략 사실을 AI와 사용자에게 알린다.


# 각 원소는 ``(pattern, replacement)`` 튜플이다.
# - pattern: diff 문자열에서 비밀값처럼 보이는 부분을 찾는 컴파일된 정규표현식이다.
# - replacement: 찾은 부분 전체를 대신할 안전한 문자열이다. ``r"\1 ..."``의 ``\1``은
#   첫 번째 괄호 그룹(예: bearer, api_key)을 그대로 재사용한다는 뜻이다.
#
# 이 목록의 순서도 동작에 영향을 준다. mask_sensitive_text()는 위에서 아래 순서로
# 치환하므로, 더 구체적인 토큰 형식을 먼저 처리하고 일반적인 ``key=value`` 형식은
# 그 다음에 처리한다. 다만 정규식 기반 탐지는 모든 비밀값을 발견한다고 보장하지
# 않으므로, 이 목록은 '최종 보안 검토'가 아니라 실수로 전송하는 일을 줄이는 보조 장치다.
SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [  # (탐지 정규식, 치환 문자열) 쌍을 우선순위대로 모은다.
    (
        # \b는 단어 경계, {16,}은 뒤에 허용 문자 16개 이상이 이어져야 함을 뜻한다.
        re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),  # OpenAI 계열 ``sk-`` 키 형태를 찾는다.
        "[MASKED_API_KEY]",  # 실제 키를 알아볼 수 없는 공통 표식으로 바꾼다.
    ),
    (
        # ``AIza`` 접두어 뒤의 20자 이상만 대상으로 해 짧은 일반 문자열 오탐을 줄인다.
        re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),  # Google API 키의 흔한 접두어와 길이를 찾는다.
        "[MASKED_API_KEY]",  # API 키 원문을 숨긴다.
    ),
    (
        # (?:...)은 캡처하지 않는 선택 그룹이다. ghp_ 또는 github_pat_ 접두어를 허용한다.
        re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),  # GitHub 개인 액세스 토큰 형태를 찾는다.
        "[MASKED_API_KEY]",  # GitHub 토큰 원문을 숨긴다.
    ),
    (
        # (?i)는 대소문자를 구분하지 않는다. (bearer)는 인증 방식만 캡처하고,
        # \s+ 뒤의 10자 이상 토큰 값을 찾는다.
        re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{10,}"),  # 대소문자와 무관하게 Bearer 토큰을 찾는다.
        r"\1 [MASKED_TOKEN]",  # \1으로 Bearer 표시는 유지하고 실제 토큰 값만 숨긴다.
    ),
    (
        # 첫 그룹은 비밀값을 담을 법한 변수명, 두 번째 줄은 구분자와 실제 값이다.
        # 따옴표가 있는 값과 따옴표 없는 값을 모두 처리한다.
        re.compile(  # key=value 또는 key: value 형태의 흔한 설정 비밀값을 찾는다.
            r"(?i)\b(api[_-]?key|secret|password|passwd|token)"
            r"\s*[:=]\s*"
            r"(?:['\"][^'\"\r\n]+['\"]|[A-Za-z0-9._~+/=-]{4,})"
        ),
        r"\1=[MASKED_SECRET]",  # \1으로 필드 이름은 남기고 구분자를 '='와 안전한 표식으로 통일한다.
    ),
    (
        # 로컬 파트@도메인.최상위도메인 형태를 넓게 찾아 개인정보 노출을 줄인다.
        re.compile(  # 이메일 주소 형태의 개인정보를 찾는다.
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "[MASKED_EMAIL]",  # 이메일 원문을 숨긴다.
    ),
]


def mask_sensitive_text(text: str) -> tuple[str, int]:
    """민감정보 패턴을 마스킹하고 ``(안전한_텍스트, 치환_횟수)``를 반환한다.

    이 함수는 원본 ``text``를 수정하지 않는다. 대신 ``masked_text``라는 새 문자열에
    패턴을 하나씩 적용한다. ``re.Pattern.subn()``은 일반 ``sub()``와 달리
    ``(치환된 문자열, 실제 치환 횟수)``를 함께 반환한다. 따라서 호출자는 API에
    보낼 텍스트뿐 아니라 safe-mode가 실제로 몇 건을 숨겼는지도 알 수 있다.

    예를 들어 ``"token=abcd1234"``가 들어오면 일반 설정 패턴이 이를 찾아
    ``"token=[MASKED_SECRET]"``으로 바꾸고 횟수는 1이 된다.
    """

    masked_text = text  # 원문은 보존하고, 이 변수만 각 규칙의 결과로 갱신한다.
    masked_count = 0  # 모든 규칙이 실제로 바꾼 횟수를 더할 카운터다.

    for pattern, replacement in SENSITIVE_PATTERNS:  # 등록 순서대로 '현재까지 안전해진 텍스트'에 규칙을 적용한다.
        # subn은 매치가 없으면 원문과 0을 반환하므로 별도 if 없이 모든 규칙을 적용할 수 있다.
        masked_text, count = pattern.subn(replacement, masked_text)  # 치환된 텍스트와 이번 규칙의 치환 횟수를 함께 받는다.
        masked_count += count  # 이번 규칙이 숨긴 패턴 수를 전체 수에 더한다.

    return masked_text, masked_count  # 마스킹한 내용과 사용자 안내용 횟수를 함께 돌려준다.


def _truncation_notice(max_chars: int) -> str:
    """문자 수 제한 안에 들어가는 생략 안내 문구를 반환한다."""

    if max_chars <= 0:  # 제한값이 유효하지 않으면 잘못된 결과를 만들기 전에 중단한다.
        raise ValueError("max_chars는 0보다 커야 합니다.")

    if len(TRUNCATION_NOTICE) <= max_chars:  # 표준 안내 문구 전체가 제한 안에 들어가면 사용한다.
        return TRUNCATION_NOTICE  # 충분히 설명적인 생략 표식을 반환한다.

    # 아주 작은 제한값에서도 생략 사실은 남긴다.
    return "…"  # 표준 문구조차 긴 극단적 제한에서는 한 글자 표식을 반환한다.


def _limit_text_by_chars(text: str, max_chars: int, truncated: bool) -> tuple[str, bool]:
    """필요하면 생략 안내 문구를 포함해 문자열 길이를 제한한다."""

    if max_chars <= 0:  # 0 이하 제한은 유효하지 않다.
        raise ValueError("max_chars는 0보다 커야 합니다.")

    needs_truncation = truncated or len(text) > max_chars  # 앞선 줄 제한 또는 현재 문자 제한이 잘림을 요구하는지 계산한다.
    if not needs_truncation:  # 어느 제한에도 걸리지 않았으면 원문을 보존한다.
        return text, False  # 잘리지 않았다는 메타데이터와 함께 반환한다.

    notice = _truncation_notice(max_chars)  # 제한 안에 맞는 생략 문구를 고른다.
    content_limit = max(0, max_chars - len(notice))  # 문구 길이를 제외하고 원문에 할당할 문자 수를 계산한다.
    return text[:content_limit] + notice, True  # 앞부분과 생략 문구를 합쳐 제한을 지키는 결과를 반환한다.


def apply_safe_mode(
    text: str,
    *,
    enabled: bool,
    max_lines: int = DEFAULT_MAX_DIFF_LINES,
    max_chars: int = DEFAULT_MAX_DIFF_CHARS,
) -> SafetyResult:
    """diff를 마스킹하고 줄 수·문자 수 제한을 적용한다.

    safe-mode가 꺼져 있으면 원문을 반환한다. 켜져 있으면 먼저
    마스킹하고, 줄 수 제한, 문자 수 제한 순서로 적용한다.
    최종 text는 생략 안내 문구를 포함해 max_chars를 넘지 않는다.

    처리 순서는 반드시 다음과 같다.

    1. ``enabled=False``면 사용자가 요청한 원문을 그대로 담아 반환한다.
    2. ``enabled=True``면 먼저 mask_sensitive_text()로 비밀값을 숨긴다.
    3. 마스킹된 결과에서 앞 ``max_lines``줄만 남긴다.
    4. 그 결과가 ``max_chars``를 넘거나 3단계에서 줄을 버렸다면, 끝에 생략 표식을
       붙인 뒤 문자열 전체가 문자 제한을 넘지 않도록 다시 자른다.

    즉 길이 제한보다 마스킹이 먼저다. 일부를 잘라 내더라도 남는 앞부분에 있는
    비밀값이 외부 API에 전달되지 않도록 하기 위해서다.
    """

    if max_lines <= 0:  # 0줄만 허용하면 의미 있는 diff를 보낼 수 없으므로 입력 오류로 처리한다.
        raise ValueError("max_lines는 0보다 커야 합니다.")
    if max_chars <= 0:  # 0자 이하면 생략 표식조차 표현할 수 없으므로 입력 오류로 처리한다.
        raise ValueError("max_chars는 0보다 커야 합니다.")

    original_lines = len(text.splitlines()) if text else 0  # 빈 문자열을 0줄로, 그 외에는 줄 분리 결과 수로 센다.

    if not enabled:  # 사용자가 명시적으로 safe-mode를 끈 경우 원문을 변경하지 않는다.
        # 호출자는 safe-mode 여부와 관계없이 SafetyResult만 다루므로 뒤 단계의 분기가 줄어든다.
        return SafetyResult(  # 그래도 후속 프롬프트 모듈이 같은 결과 형식을 쓰도록 감싼다.
            text=text,
            masked_count=0,
            original_lines=original_lines,
            transmitted_lines=original_lines,
            truncated=False,
        )

    masked_text, masked_count = mask_sensitive_text(text)  # 길이를 줄이기 전에 비밀값을 먼저 숨긴다.
    all_lines = masked_text.splitlines()  # 마스킹된 diff를 줄 단위로 나눈다.
    limited_lines = all_lines[:max_lines]  # Python 슬라이스는 max_lines번째 줄 직전까지만 남긴다.
    limited_text = "\n".join(limited_lines)  # 선택된 줄을 다시 API 전송용 문자열로 만든다.
    line_truncated = len(all_lines) > max_lines  # 줄 제한 때문에 버려진 내용이 있는지 기록한다.

    # line_truncated=True를 넘기면 문자 수가 충분해도 '일부 줄이 빠졌다'는 안내 문구를 붙인다.
    final_text, truncated = _limit_text_by_chars(  # 줄 제한 결과에 문자 수 제한을 추가로 적용한다.
        limited_text,
        max_chars,
        line_truncated,
    )

    # 안내 문구는 diff 자체가 아닌 메타데이터다. 따라서 AI에 전달한 실제 diff 줄 수를
    # 정확히 표시하려면 transmitted_lines를 계산하기 전에 이 문구를 제거해야 한다.
    diff_part = final_text  # 전송 줄 수 계산에서는 생략 안내 문구를 제외하기 위한 작업 변수다.
    if truncated and final_text.endswith(_truncation_notice(max_chars)):  # 표준 생략 문구가 붙은 경우를 처리한다.
        diff_part = final_text[: -len(_truncation_notice(max_chars))]  # 안내 문구를 뺀 실제 diff 부분만 남긴다.
    elif truncated and final_text.endswith("…"):  # 극단적 제한에서 한 글자 문구가 붙은 경우다.
        diff_part = final_text[:-1]  # 말줄임표 한 글자를 제거한다.

    return SafetyResult(  # 텍스트와 처리 사실을 함께 담아 prompts와 cli에 전달한다.
        text=final_text,
        masked_count=masked_count,
        original_lines=original_lines,
        transmitted_lines=len(diff_part.splitlines()) if diff_part else 0,
        truncated=truncated,
    )
