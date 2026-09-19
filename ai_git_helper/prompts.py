"""Git 변경 맥락을 Commit·PR용 AI 프롬프트로 구성한다."""

from __future__ import annotations  # 타입 표기의 런타임 평가를 미룬다.

from .models import GitChanges  # Git 수집 단계가 만든 변경 컨텍스트 타입이다.
from .models import SafetyResult  # safe-mode가 만든 전송용 diff 타입이다.
from .safety import mask_sensitive_text  # 안전 처리 결과도 마지막으로 한 번 더 마스킹한다.


SYSTEM_PROMPT = """  # 모든 API 요청에 공통으로 전달할 역할·안전 규칙이다.
당신은 Git 변경 사항을 근거로 정확한 커밋 메시지와 Pull Request 초안을
작성하는 개발 보조 AI입니다.

반드시 다음 원칙을 지키세요.
- 모든 결과는 한국어로 작성합니다.
- 제공된 Git 변경 정보에 없는 기능, 원인, 테스트 결과를 지어내지 않습니다.
- 민감정보 또는 마스킹 표식을 원래 값으로 복원하려 하지 않습니다.
- 간결하고 구체적으로 작성합니다.
- Markdown 코드 블록을 사용하지 않고, 요청한 JSON만 반환합니다.
- JSON 문자열 안에서도 Markdown용 역슬래시 표기(예: \\_)를 사용하지 않습니다.
""".strip()  # 들여쓰기로 생긴 앞뒤 빈 줄을 제거해 정확한 시스템 지시문을 만든다.


# 이 딕셔너리는 Gemini API의 ``response_format.schema``에 전달되는 JSON Schema다.
# 즉, 프롬프트의 'JSON으로 답해라'라는 자연어 요청을 넘어 API가 기대하는 응답의
# 모양을 기계적으로 알려 준다. 그래도 모델 응답은 완전히 신뢰할 수 없으므로,
# 실제 반환값은 validation.py의 validate_commit_draft()에서 한 번 더 검증한다.
#
# 미션에서 커밋 본문은 선택 사항이다. 다만 이 프로젝트는 변경 근거를 남기기 위해
# body를 최소 1개, 최대 3개 항목으로 요구한다.
COMMIT_RESPONSE_SCHEMA = {  # Gemini에 요청할 커밋 JSON의 허용 구조다.
    "type": "object",  # 최상위 값은 [] 배열이나 단일 문자열이 아닌 { ... } 객체여야 한다.
    "properties": {  # 객체 안에 둘 수 있는 필드 이름과 각 필드의 타입 규칙을 정의한다.
        "title": {"type": "string"},  # 커밋 제목: JSON 문자열 한 개를 요구한다. 길이는 validation.py가 72자로 검사한다.
        "body": {  # 커밋 본문: 변경 근거를 항목별로 전달하기 위한 필드다.
            "type": "array",  # body 자체는 "문장" 하나가 아니라 ["문장 1", "문장 2"] 배열이어야 한다.
            "items": {"type": "string"},  # 배열의 모든 원소는 숫자·객체가 아닌 문자열이어야 한다.
            "minItems": 1,  # 빈 배열 []은 허용하지 않아 최소 한 가지 변경 근거를 요구한다.
            "maxItems": 3,  # 과도하게 긴 초안을 막고 핵심 변경 사항 세 개까지만 받는다.
        },
    },
    "required": ["title", "body"],  # 두 필드는 모두 반드시 있어야 하며 하나라도 누락되면 형식 위반이다.
    "additionalProperties": False,  # summary·emoji 같은 약속되지 않은 최상위 필드는 받지 않는다.
}


# PR은 제목 외에도 '왜 바꿨는가', '무엇을 바꿨는가', '어떻게 확인할 수 있는가'를
# 분리해 출력해야 한다. 이 schema의 필드 이름은 output.py의 PR 섹션과 1:1로 대응한다.
#
# JSON Schema는 각 배열에 maxItems를 두지 않는다. PR의 각 섹션은 변경 규모에 따라
# 여러 항목이 필요할 수 있기 때문이다. 대신 빈 섹션은 minItems=1로 금지하고,
# 항목의 문자열 여부와 내용 정리는 validation.py가 최종 보장한다.
PR_RESPONSE_SCHEMA = {  # Gemini에 요청할 PR JSON의 허용 구조다.
    "type": "object",  # 최상위 값은 네 개의 이름 있는 필드를 가진 JSON 객체여야 한다.
    "properties": {  # AI가 반환할 수 있는 필드와 각 필드의 세부 규칙이다.
        "title": {"type": "string"},  # PR 제목: 한 개의 문자열이다. validation.py가 최대 80자로 별도 검사한다.
        "why": {  # 변경의 배경·문제·필요성을 적는 'Why' 섹션이다.
            "type": "array",  # 배경이 여러 개일 수 있어 문자열 배열로 받는다.
            "items": {"type": "string"},  # 각 배경 설명은 문자열이어야 한다.
            "minItems": 1,  # Why 섹션을 빈 배열로 반환하는 것은 허용하지 않는다.
        },
        "what": {  # 실제로 추가·수정·삭제한 내용을 적는 'What' 섹션이다.
            "type": "array",  # 여러 변경 사항을 독립된 불릿으로 출력할 수 있게 배열로 받는다.
            "items": {"type": "string"},  # 각 변경 설명은 문자열이어야 한다.
            "minItems": 1,  # What 섹션에는 최소 한 항목이 필요하다.
        },
        "how_to_test": {  # 사용자가 수행할 수 있는 확인 절차를 적는 'How to Test' 섹션이다.
            "type": "array",  # 여러 테스트 절차를 순서 또는 항목별로 담을 수 있게 배열로 받는다.
            "items": {"type": "string"},  # 각 확인 방법은 문자열이어야 한다.
            "minItems": 1,  # 테스트 방법을 전혀 제공하지 않는 PR 초안은 허용하지 않는다.
        },
    },
    "required": ["title", "why", "what", "how_to_test"],  # 네 섹션이 모두 있어야 output.py가 빠짐없이 렌더링할 수 있다.
    "additionalProperties": False,  # 정의하지 않은 최상위 필드를 막아 출력·검증 계약을 단순하게 유지한다.
}


def build_git_context(changes: GitChanges, safety_result: SafetyResult) -> str:
    """브랜치·status·파일·안전 처리된 diff를 AI 입력으로 묶는다.

    호출자는 apply_safe_mode 결과를 전달해야 한다. 혹시 원문이 잘못
    전달되더라도 한 번 더 마스킹해 프롬프트에 비밀값이 남지 않게 한다.
    """

    changed_files_text = "\n".join(  # 파일명마다 불릿을 붙여 사람이 읽기 쉬운 목록을 만든다.
        f"- {file_name}" for file_name in changes.changed_files
    ) or "- 변경 파일 없음"  # 빈 목록일 때도 AI가 컨텍스트 누락으로 오해하지 않게 한다.

    safe_diff, extra_masked_count = mask_sensitive_text(safety_result.text)  # 방어적으로 재마스킹해 모듈 경계를 안전하게 만든다.
    if not safe_diff.strip():  # diff가 비었거나 공백뿐이면 설명문으로 대체한다.
        safe_diff = "(diff 텍스트 없음: 파일 목록과 status만 사용하세요.)"

    truncation_status = "예" if safety_result.truncated else "아니오"  # 불리언을 프롬프트의 한국어 표기로 바꾼다.
    total_masked_count = safety_result.masked_count + extra_masked_count  # 첫 마스킹과 방어적 재마스킹 횟수를 합친다.

    return f"""  # 수집 데이터와 안전 메타데이터를 하나의 AI 입력 문자열로 만든다.
현재 브랜치:
{changes.branch}

git status --short:
{changes.status_text or "(결과 없음)"}

변경 파일:
{changed_files_text}

safe-mode 정보:
- 마스킹 수: {total_masked_count}
- 원본 diff 줄 수: {safety_result.original_lines}
- 전송 diff 줄 수: {safety_result.transmitted_lines}
- diff 일부 생략 여부: {truncation_status}

안전 처리된 git diff:
{safe_diff}
""".strip()  # 템플릿 앞뒤의 불필요한 빈 줄을 제거한다.


def build_commit_prompt(changes: GitChanges, safety_result: SafetyResult) -> str:
    """커밋 제목과 본문 생성용 프롬프트를 반환한다."""

    git_context = build_git_context(changes, safety_result)  # 커밋 지시문에 삽입할 공통 Git 컨텍스트를 만든다.

    return f"""  # 커밋용 JSON 예시·규칙·컨텍스트를 합친 사용자 프롬프트를 반환한다.
아래 Git 변경 사항을 분석해 커밋 메시지 초안을 작성하세요.

반드시 아래 JSON 구조만 반환하세요.
{{
  "title": "커밋 제목 한 줄",
  "body": ["핵심 변경 사항 1"]
}}

작성 규칙:
1. title은 한 줄이어야 하며 최대 72자, 가능하면 50자 이내로 작성합니다.
2. title에는 상황에 맞는 feat, fix, docs, refactor, test, chore prefix를 권장합니다.
3. body에는 1개 이상 3개 이하의 핵심 변경 사항을 작성합니다.
4. body 항목 앞에 하이픈을 넣지 않습니다.
5. 제공된 Git 변경 정보에 없는 기능, 원인, 테스트 결과를 지어내지 않습니다.
6. safe-mode로 일부 diff가 생략되었을 수 있으므로, 확인할 수 없는 내용을 단정하지 않습니다.
7. Markdown 코드 블록이나 JSON 밖의 설명을 추가하지 않습니다.

Git 변경 컨텍스트:
{git_context}
""".strip()  # API에 보내기 전 앞뒤 빈 줄을 제거한다.


def build_pr_prompt(changes: GitChanges, safety_result: SafetyResult) -> str:
    """PR 제목과 Why·What·How to Test 생성용 프롬프트를 반환한다."""

    git_context = build_git_context(changes, safety_result)  # PR 지시문에 삽입할 공통 Git 컨텍스트를 만든다.

    return f"""  # PR용 JSON 예시·규칙·컨텍스트를 합친 사용자 프롬프트를 반환한다.
아래 Git 변경 사항을 분석해 Pull Request 초안을 작성하세요.

반드시 아래 JSON 구조만 반환하세요.
{{
  "title": "PR 제목 한 줄",
  "why": ["변경 배경 1"],
  "what": ["핵심 변경 사항 1"],
  "how_to_test": ["사용자가 수행할 수 있는 확인 방법 1"]
}}

작성 규칙:
1. title은 한 줄이어야 하며 최대 80자로 작성합니다.
2. why, what, how_to_test에는 각각 최소 1개 항목을 작성합니다.
3. 각 배열 항목 앞에 하이픈을 넣지 않습니다.
4. how_to_test에는 실제로 실행했음을 주장하지 말고, 사용자가 수행할 수 있는 확인 방법만 작성합니다.
5. 제공된 Git 변경 정보에 없는 기능, 원인, 테스트 결과를 지어내지 않습니다.
6. safe-mode로 일부 diff가 생략되었을 수 있으므로, 확인할 수 없는 내용을 단정하지 않습니다.
7. Markdown 코드 블록이나 JSON 밖의 설명을 추가하지 않습니다.

Git 변경 컨텍스트:
{git_context}
""".strip()  # API에 보내기 전 앞뒤 빈 줄을 제거한다.
