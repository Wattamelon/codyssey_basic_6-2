# Phase 03~07 코드 추적 학습자료

> 대상: AI Git Helper의 Phase 03(safe-mode)부터 Phase 07(CLI 통합)까지
>
> 이 문서는 **현재 구현된 코드**를 설명한다. 실제 Gemini API 호출 결과는 포함하지 않는다. API Key 없이도 `--show-prompt`와 자동 테스트로 대부분의 흐름을 학습할 수 있다.

## 0. 먼저 보는 전체 구조

### 프로젝트 파일 지도

| 파일 | 왜 존재하는가 | Phase |
| --- | --- | --- |
| `main.py` | 운영체제가 Python 프로그램을 시작하는 입구 | 01, 07 |
| `ai_git_helper/cli.py` | 사용자가 입력한 옵션을 해석하고 전체 순서를 지휘 | 07 |
| `ai_git_helper/git_service.py` | 로컬 Git 프로그램을 실행해 변경 정보를 수집 | 02 |
| `ai_git_helper/models.py` | 파일 사이를 안전하게 오가는 데이터 상자 | 01~06 |
| `ai_git_helper/safety.py` | diff의 민감정보를 가리고 크기를 제한 | 03 |
| `ai_git_helper/prompts.py` | Git 정보를 AI가 이해할 프롬프트·JSON 규칙으로 변환 | 04 |
| `ai_git_helper/api_client.py` | Gemini API에 HTTP 요청을 한 번 보내고 JSON을 받음 | 05 |
| `ai_git_helper/errors.py` | 예상 가능한 오류의 이름을 모아 둠 | 02~06 |
| `ai_git_helper/validation.py` | AI 응답이 Commit/PR 규칙을 지키는지 검사 | 06 |
| `ai_git_helper/output.py` | 검증된 초안을 복사하기 좋은 터미널 문자열로 만듦 | 06 |
| `tests/` | 실제 API 없이 각 기능과 연결 순서를 검증 | 03~07 |

### 실행 구조도

```text
사용자 입력: python main.py commit
    ↓
main.py
    ↓ main()
ai_git_helper/cli.py
    ↓ build_parser() / parser.parse_args()
    ↓ _run_command(args)
    ↓ collect_git_changes(Path.cwd())
ai_git_helper/git_service.py
    ↓ _run_git([...])
운영체제의 git 프로그램
    ↓ GitChanges 객체 반환
cli.py
    ↓ apply_safe_mode(changes.diff_text)
ai_git_helper/safety.py
    ↓ SafetyResult 객체 반환
cli.py
    ↓ build_commit_prompt(...) 또는 build_pr_prompt(...)
ai_git_helper/prompts.py
    ↓ 프롬프트 문자열 + JSON Schema 선택
cli.py
    ↓ GeminiClient().generate_json(...)
ai_git_helper/api_client.py
    ↓ requests.post()로 HTTP 요청 1회
    ↓ dict(JSON 객체) 반환
cli.py
    ↓ validate_commit_draft(...) 또는 validate_pr_draft(...)
ai_git_helper/validation.py
    ↓ CommitDraft 또는 PRDraft 반환
cli.py
    ↓ format_commit_draft(...) 또는 format_pr_draft(...)
ai_git_helper/output.py
    ↓ print(...)
터미널 출력
```

### 파일 사이의 호출 관계

| 호출하는 파일 | 호출받는 파일·함수 | 입력 | 반환 | 다음 사용처 |
| --- | --- | --- | --- | --- |
| `main.py` | `cli.main()` | 터미널 인자 | 종료 코드 | 운영체제 |
| `cli.py` | `git_service.collect_git_changes()` | 현재 폴더 `Path` | `GitChanges` | 변경 없음 확인, 프롬프트 |
| `cli.py` | `safety.apply_safe_mode()` | `diff_text`, 제한값 | `SafetyResult` | 프롬프트 |
| `cli.py` | `prompts.build_*_prompt()` | `GitChanges`, `SafetyResult` | 문자열 | API의 `user_input` |
| `cli.py` | `GeminiClient.generate_json()` | 프롬프트·스키마·옵션 | `dict` | 검증 함수 |
| `cli.py` | `validation.validate_*_draft()` | AI JSON 객체 | Draft 객체 | 출력 함수 |
| `cli.py` | `output.format_*_draft()` | Draft 객체 | 출력 문자열 | `print()` |

## 1. 먼저 알아둘 기초 용어

| 용어 | 한글 의미·비유 | 정확한 의미 | 이번 프로젝트에서 필요한 이유 |
| --- | --- | --- | --- |
| Python 모듈 | `.py` 파일 한 장 | Python 코드가 들어 있는 파일 | `safety.py`처럼 역할을 나눈다. |
| 패키지 | 모듈을 담은 폴더 | `__init__.py`를 가진 모듈 묶음 | `ai_git_helper`가 패키지다. |
| `import` | 다른 상자에서 도구를 빌려오기 | 다른 모듈의 이름을 현재 파일에서 사용 가능하게 함 | `cli.py`가 다른 기능을 연결한다. |
| 함수 | 버튼이 달린 작은 기계 | 입력을 받아 처리하고 `return`으로 결과를 돌려주는 코드 묶음 | `apply_safe_mode()` 등이 이에 해당한다. |
| 클래스/객체 | 설계도/그 설계도로 만든 실제 상자 | 데이터와 동작을 묶는 문법/그 결과 | `GeminiClient()`는 API 요청 상자다. |
| dataclass | 항목 칸이 미리 그려진 택배 상자 | 필드 저장용 `__init__` 등을 자동 생성하는 클래스 | `GitChanges`가 여러 Git 결과를 함께 운반한다. |
| 예외(Exception) | 정상 길에서 벗어났다는 경고 카드 | 실행 중 오류를 알리고 호출자에게 전달하는 객체 | API·Git 오류를 traceback 대신 `[ERROR]`로 보여 준다. |
| CLI/parser | 터미널 명령 번역기 | 명령행 문자열을 `args.command` 같은 값으로 변환 | `commit`, `--max-tokens`를 읽는다. |
| 환경변수 | 프로그램 밖에 붙인 비밀 메모 | 셸 프로세스에 저장된 이름=값 | API Key를 코드에 쓰지 않는다. |
| subprocess | Python이 터미널 직원에게 부탁하는 도구 | 운영체제의 외부 프로그램을 실행하는 표준 라이브러리 | `git` 실행 파일을 실행한다. Python이 Git을 직접 읽는 것이 아니다. |
| staged/unstaged | 포장 완료/아직 작업대 위 | `git add`된 변경/아직 add하지 않은 변경 | 둘 다 커밋 초안의 근거가 된다. |
| diff | 두 버전의 차이 목록 | 파일의 추가·삭제 줄을 표현한 텍스트 | AI가 무엇이 바뀌었는지 판단할 재료다. |
| API/HTTP 요청 | 다른 서비스 창구에 양식 제출 | 네트워크로 서버에 요청하고 응답을 받는 규약 | Gemini에 프롬프트를 보낸다. |
| JSON | 컴퓨터용 이름표 달린 메모 | 객체·배열 등을 텍스트로 표현하는 데이터 형식 | AI 응답을 `title`, `body` 등으로 읽는다. |
| mock | 진짜 대신 쓰는 연습용 인형 | 테스트에서 외부 기능을 가짜 객체로 바꾸는 기법 | API 비용·네트워크 없이 테스트한다. |

## 2. 데이터 상자와 오류 이름표

### `models.py`: 파일 사이를 이동하는 데이터

```python
@dataclass(frozen=True)
class GitChanges:
    branch: str
    status_text: str
    changed_files: list[str]
    diff_text: str
    diff_line_count: int

    @property
    def has_changes(self) -> bool:
        return bool(self.changed_files)
```

| 줄 | 코드 | 의미와 다음 사용처 |
| --- | --- | --- |
| 1 | `@dataclass(frozen=True)` | `GitChanges(...)`를 쉽게 만들고, 만든 뒤 필드를 바꾸지 못하게 한다. 수집 결과가 중간에 실수로 변하지 않게 한다. |
| 2 | `class GitChanges` | Git 결과를 한 덩어리로 묶는 설계도다. |
| 3~7 | `branch` 등 필드 | 실제 예: `branch="main"`, `changed_files=["README.md"]`, `diff_text="..."`. `cli.py`와 `prompts.py`가 읽는다. |
| 9 | `@property` | 함수 호출 괄호 없이 `changes.has_changes`처럼 읽게 한다. |
| 10~11 | `bool(self.changed_files)` | 목록이 비어 있으면 `False`, 하나라도 있으면 `True`. API 호출 전 분기에 쓴다. |

`SafetyResult`, `CommitDraft`, `PRDraft`도 같은 방식의 데이터 상자다. 각각 안전 처리 결과, 검증된 커밋 초안, 검증된 PR 초안을 전달한다.

### `errors.py`: 오류를 종류별로 구분하는 이유

```python
class AIGitHelperError(Exception):
    """예상 가능한 프로그램 오류의 기본 예외."""

class GitCommandError(AIGitHelperError):
    """Git 명령 실행 오류."""
```

| 줄 | 의미 |
| --- | --- |
| `class AIGitHelperError(Exception)` | Python 기본 오류 `Exception`을 물려받은, 이 프로젝트 전용 오류의 부모 이름표다. |
| `class GitCommandError(AIGitHelperError)` | Git 실행 실패를 표시한다. |
| `APIRequestError`, `ConfigurationError`, `ValidationError` | API 통신, Key 설정, AI 결과 검증 실패를 각각 표시한다. |

클래스 몸통이 비어 보이는 것은 정상이다. 여기서는 “오류의 행동”보다 “오류의 종류”가 중요하다. `cli.py`는 `except AIGitHelperError` 한 줄로 네 종류를 모두 잡아 `[ERROR]`로 출력한다.

## 3. Phase 03 — safe-mode: 보내기 전 검문소

### 역할과 흐름

쉬운 비유로, `safety.py`는 택배를 외부 AI에 보내기 전 비밀번호가 적힌 부분을 검은 펜으로 가리고, 상자가 너무 크면 앞부분만 보내는 검문소다.

```text
changes.diff_text
  "password=abc...\n+   +새 기능..."
       ↓ apply_safe_mode(...)
SafetyResult(
  text="password=[MASKED_SECRET]...",
  masked_count=1,
  truncated=False
)
       ↓
prompts.py
```

### import와 상수 (1~16행)

```python
import re
from .models import SafetyResult

DEFAULT_MAX_DIFF_LINES = 200
DEFAULT_MAX_DIFF_CHARS = 20_000
TRUNCATION_NOTICE = "\n[SAFE MODE: diff 일부 생략]"
```

| 줄 | 의미 |
| --- | --- |
| `import re` | Python **표준 라이브러리**다. 정규표현식이라는 “문자열 패턴 찾기” 도구를 가져온다. 외부 패키지가 아니다. |
| `from .models ...` | 현재 패키지의 `models.py`에서 결과 상자 설계도를 가져온다. `.`은 같은 `ai_git_helper` 폴더라는 뜻이다. |
| 두 `DEFAULT_...` | 옵션을 생략했을 때의 안전한 기본 제한이다. `cli.py` 도움말과 기본값에도 사용된다. |
| `TRUNCATION_NOTICE` | 내용이 생략됐다는 사실을 AI와 사용자 모두 알 수 있게 하는 표식이다. |

### 민감정보 패턴과 마스킹 (19~63행)

```python
SENSITIVE_PATTERNS = [
    (re.compile(r"..."), "[MASKED_API_KEY]"),
    # 다른 token/password/email 패턴들
]

def mask_sensitive_text(text: str) -> tuple[str, int]:
    masked_text = text
    masked_count = 0
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked_text, count = pattern.subn(replacement, masked_text)
        masked_count += count
    return masked_text, masked_count
```

| 줄 | 코드 | 의미 |
| --- | --- | --- |
| 19~50 | `SENSITIVE_PATTERNS` | `(찾을 규칙, 바꿀 글자)` 쌍의 리스트다. API Key, Bearer token, `password=...`, 이메일 등을 찾는다. |
| 53 | `def ... -> tuple[str, int]` | 입력 문자열을 받고 `(가려진 문자열, 가린 횟수)` 두 값을 돌려준다는 타입 힌트다. |
| 56~57 | 초기값 | 원문을 복사하고 가린 횟수를 0에서 시작한다. 원본 변수 `text`는 바꾸지 않는다. |
| 59 | `for` | 패턴 목록을 하나씩 반복한다. |
| 60 | `subn(...)` | `re`가 제공한다. 문자열을 바꾼 결과와 바꾼 횟수를 동시에 돌려준다. |
| 61 | `+=` | 기존 횟수에 이번 횟수를 더한다. |
| 63 | `return` | `apply_safe_mode()`와 `prompts.py`가 이 두 값을 받는다. |

**한계:** 패턴과 다른 모양의 비밀값은 놓칠 수 있다. 그래서 `--show-prompt`로 사람이 확인하는 단계가 있다.

### 줄 수·문자 수 제한 (66~91행)

```python
def _limit_text_by_chars(text, max_chars, truncated):
    needs_truncation = truncated or len(text) > max_chars
    if not needs_truncation:
        return text, False
    notice = _truncation_notice(max_chars)
    content_limit = max(0, max_chars - len(notice))
    return text[:content_limit] + notice, True
```

| 줄 | 의미 |
| --- | --- |
| `_limit...` | 이름 앞 `_`는 “이 파일 안에서만 쓰는 보조 함수”라는 관례다. Python이 강제로 막지는 않는다. |
| `len(text)` | 문자열의 문자 수를 센다. |
| `truncated or ...` | 줄 수 제한에서 이미 잘렸거나 문자 수가 넘을 때 생략한다. `or`는 둘 중 하나만 참이어도 참이다. |
| `text[:content_limit]` | 앞에서부터 제한 길이만큼 잘라낸다. |
| `+ notice` | 생략 표식을 붙여도 전체 길이가 `max_chars`를 넘지 않게 한다. |

### 중심 함수 `apply_safe_mode()` (94~149행)

```python
def apply_safe_mode(text, *, enabled, max_lines=200, max_chars=20_000):
    original_lines = len(text.splitlines()) if text else 0
    if not enabled:
        return SafetyResult(...)

    masked_text, masked_count = mask_sensitive_text(text)
    all_lines = masked_text.splitlines()
    limited_lines = all_lines[:max_lines]
    final_text, truncated = _limit_text_by_chars(...)
    return SafetyResult(...)
```

| 줄 | 코드 | 실행 전 → 실행 후 |
| --- | --- | --- |
| 94~100 | 함수 선언의 `*` | `enabled=True`처럼 이름을 반드시 써서 전달해야 한다. 인자 순서를 헷갈리지 않게 한다. |
| 108~111 | `ValueError` | 0 이하 제한값은 의미가 없으므로 즉시 오류를 낸다. `cli.py`가 `[ERROR]`로 처리한다. |
| 113 | `splitlines()` | diff를 줄 목록으로 바꾸고 원래 줄 수를 센다. |
| 115~122 | `if not enabled` | `--no-safe-mode`일 때다. 마스킹·제한 없이 원문을 담은 `SafetyResult`를 반환한다. |
| 124 | 마스킹 호출 | 예: `secret=abcd` → `secret=[MASKED_SECRET]`, 횟수 1. |
| 125~128 | 줄 제한 | 모든 줄을 리스트로 만든 뒤 앞 `max_lines`개만 남긴다. |
| 130~134 | 문자 제한 | 줄 제한 결과를 다시 문자 수 기준으로 줄인다. |
| 136~141 | `diff_part` | 안내 문구는 실제 diff 줄이 아니므로 `transmitted_lines` 계산에서 뺀다. |
| 143~149 | `SafetyResult(...)` | 다음 파일이 쓸 최종 데이터 상자를 만든다. |

**삭제하면?** API로 비밀값이나 매우 큰 diff가 그대로 나갈 위험이 커지고, 미션의 안전 처리 요구를 충족하지 못한다.

### Phase 03 테스트

`tests/test_safety.py`는 가짜 API Key·password·email만 사용한다. `test_masks_fake_credentials...`는 원문 비밀값이 결과에서 사라졌는지 검사하고, 제한 테스트는 생략 표식과 길이를 검사한다. 실제 비밀값·외부 API는 사용하지 않는다.

**이번 단계 핵심:** `SafetyResult`, 정규표현식, `splitlines()`, `return`, 기본값

## 4. Phase 04 — 프롬프트와 JSON Schema: AI에게 주는 작업 지시서

### import 관계

```python
from .models import GitChanges
from .models import SafetyResult
from .safety import mask_sensitive_text
```

| 가져오는 이름 | 출처 | 왜 필요한가 | import가 없으면 |
| --- | --- | --- | --- |
| `GitChanges` | `models.py` | 브랜치·status·파일·diff를 읽는다. | 함수 정의의 타입 이름을 찾지 못한다. |
| `SafetyResult` | `models.py` | 안전 처리된 diff와 메타정보를 읽는다. | 같은 문제 발생 |
| `mask_sensitive_text` | `safety.py` | 프롬프트를 만들기 직전 한 번 더 마스킹한다. | 방어막 한 겹이 사라진다. |

### 시스템 지시와 Schema (10~63행)

```python
SYSTEM_PROMPT = """... JSON만 반환합니다. ...""".strip()

COMMIT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "body": {...}},
    "required": ["title", "body"],
    "additionalProperties": False,
}
```

| 코드 | 의미 |
| --- | --- |
| `"""..."""` | 여러 줄 문자열이다. AI가 지켜야 할 공통 원칙을 담는다. |
| `.strip()` | 문자열 맨 앞·끝의 불필요한 줄바꿈·공백을 제거한다. |
| `"type": "object"` | JSON의 최상위 형태가 `{...}`인 객체여야 한다는 뜻이다. |
| `properties` | 허용하는 이름표와 값 종류다. Commit은 `title`, `body`다. |
| `required` | 반드시 있어야 하는 키 목록이다. |
| `additionalProperties: False` | 여기 적지 않은 뜻밖의 키를 줄이려는 규칙이다. |

PR schema는 `title`, `why`, `what`, `how_to_test` 네 항목을 요구한다. Schema는 AI에게 형식을 요청하는 1차 방어이고, Phase 06의 `validation.py`가 실제 응답을 다시 검사하는 2차 방어다.

### `build_git_context()` (66~102행)

```python
changed_files_text = "\n".join(
    f"- {file_name}" for file_name in changes.changed_files
) or "- 변경 파일 없음"

safe_diff, extra_masked_count = mask_sensitive_text(safety_result.text)
return f"""
현재 브랜치:
{changes.branch}
...
안전 처리된 git diff:
{safe_diff}
""".strip()
```

| 줄 | 의미 |
| --- | --- |
| 73~75 | `for file_name in ...` | 변경 파일 목록을 `- README.md`처럼 한 줄씩 만든다. 목록이 비면 `or` 오른쪽 문구를 쓴다. |
| 77 | 재마스킹 | Phase 03 결과라도 실수로 원문이 넘어온 경우를 대비한 방어다. |
| 78~79 | 빈 diff 처리 | untracked 파일은 status에는 있어도 일반 `git diff`에는 없을 수 있다. 이 경우 AI에게 파일 목록과 status만 사용하라고 알린다. |
| 81~82 | 메타정보 | diff가 생략됐는지와 총 마스킹 수를 프롬프트에 기록한다. |
| 84~102 | f-string | `{changes.branch}`처럼 중괄호 안 값을 문자열에 끼워 넣어 최종 프롬프트 재료를 만든다. |

### Commit/PR 프롬프트 함수 (105~160행)

```python
def build_commit_prompt(changes, safety_result):
    git_context = build_git_context(changes, safety_result)
    return f"""... title은 최대 72자 ...
    {git_context}
    """.strip()
```

| 함수 | 입력 | 반환 | 왜 둘로 나뉘는가 |
| --- | --- | --- | --- |
| `build_commit_prompt` | 같은 Git·안전 결과 | `title`, `body`를 요구하는 문자열 | 커밋은 제목·본문만 필요하다. 제목 최대 72자다. |
| `build_pr_prompt` | 같은 Git·안전 결과 | Why/What/How to Test를 요구하는 문자열 | PR은 변경 배경·내용·확인법을 구분해야 한다. 제목 최대 80자다. |

`{{`와 `}}`는 f-string 안에서 실제 `{`, `}`를 출력하려는 이스케이프다. 한 개만 쓰면 Python은 변수 자리로 오해한다.

### Phase 04 테스트

`tests/test_prompts.py`는 Git 컨텍스트에 브랜치·status·파일·가려진 diff가 들어가는지, 가짜 비밀값은 없는지, Commit/PR Schema가 필요한 키를 가지는지 검사한다.

**이번 단계 핵심:** f-string, dict, list, Schema, 2중 마스킹

## 5. Phase 05 — API Client: 인터넷 창구 담당자

### 중요 구분

```text
Python 표준 모듈: json, os, re
외부 패키지: requests (requirements.txt로 설치)
우리 코드: errors.py
외부 서비스: Gemini API 서버
```

`requests`가 Gemini 정보를 직접 “읽는” 것이 아니다. `requests.post()`는 인터넷을 통해 HTTP 요청을 보내고, Gemini 서버가 답한 HTTP 응답을 Python으로 가져온다.

### import와 API Key 함수 (10~37행)

```python
import json
import os
import re
from typing import Any, Mapping
import requests
from .errors import APIRequestError, ConfigurationError

def get_api_key() -> str:
    api_key = os.environ.get(GEMINI_API_KEY_ENV, "").strip()
    if not api_key:
        raise ConfigurationError(...)
    return api_key
```

| 코드 | 의미 |
| --- | --- |
| `os.environ.get(...)` | 현재 터미널이 Python에 전달한 환경변수에서 Key를 읽는다. 파일을 읽는 코드가 아니다. |
| 두 번째 인자 `""` | 변수가 없을 때 빈 문자열을 기본으로 준다. |
| `.strip()` | Key 양끝에 실수로 넣은 공백·줄바꿈을 제거한다. |
| `raise ConfigurationError` | Key가 없을 때 API 요청을 보내지 않고 오류를 호출자에게 전달한다. |
| `return api_key` | Key 자체는 요청 헤더에만 쓰고, print하지 않는다. |

### 모델 텍스트를 JSON 객체로 바꾸기 (40~60행)

```python
cleaned = text.strip()
fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.I)
if fenced:
    cleaned = fenced.group(1).strip()

parsed = json.loads(cleaned)
if not isinstance(parsed, dict):
    raise APIRequestError(...)
```

| 줄 | 의미 |
| --- | --- |
| 48 | AI 텍스트 양끝 공백을 제거한다. |
| 49~51 | AI가 실수로 `````json ... ````` 코드 블록을 붙인 경우 내부 내용만 꺼낸다. |
| 53~56 | `json.loads`는 JSON **문자열**을 Python dict/list로 바꾼다. JSON 문법이 틀리면 `JSONDecodeError`를 잡아 프로젝트 오류로 바꾼다. |
| 58~60 | `["항목"]` 같은 배열이 아니라 `{ "title": ... }` 객체인지 확인한다. 다음 검증 함수가 키를 읽을 수 있게 하기 위함이다. |

### `GeminiClient`와 HTTP 요청 (63~138행)

```python
class GeminiClient:
    def __init__(self, api_key=None, *, endpoint=..., timeout_seconds=30):
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    def generate_json(...):
        api_key = self._api_key or get_api_key()
        payload = {...}
        response = requests.post(self._endpoint, headers=headers, json=payload, timeout=...)
```

| 줄 | 코드 | 의미 |
| --- | --- | --- |
| 63 | `class GeminiClient` | API 요청에 필요한 주소·시간 제한을 보관하는 객체 설계도다. |
| 70~79 | `__init__` | `GeminiClient()`가 만들어질 때 실행된다. `self`는 새로 만든 그 객체 자신이다. 테스트에서는 가짜 Key·주소를 넣을 수 있다. |
| 72 | `str | None` | Key가 문자열이거나 아직 없을 수 있다는 타입 힌트다. |
| 73의 `*` | 이후 인자는 이름을 써서만 전달한다. |
| 81~90 | `generate_json` | 한 번의 API 요청에 필요한 입력을 모두 받는다. `Mapping`은 dict처럼 키로 값을 찾는 자료형을 뜻한다. |
| 93 | `or` | 생성자에 Key가 있으면 그것을 쓰고, 없으면 환경변수에서 읽는다. |
| 94~109 | `payload` | Gemini 서버로 보낼 JSON 객체다. model, user input, system instruction, 생성 옵션, Schema를 담는다. `store: False`는 이 단발 CLI가 서버 대화 상태를 저장하지 않겠다는 뜻이다. |
| 110~113 | `headers` | HTTP 요청의 부가 정보다. Key는 `x-goog-api-key` 헤더에 넣는다. 오류 메시지에는 이 dict를 출력하지 않는다. |
| 115~121 | `requests.post` | 서버에 POST 요청을 **한 번** 보낸다. `json=payload`는 requests가 dict를 JSON으로 바꾸어 전송하게 한다. `timeout=30`은 영원히 기다리지 않게 한다. |
| 122~127 | `except` | 시간 초과·연결 실패·그 외 requests 오류를 각각 사용자가 이해할 `APIRequestError`로 바꾼다. `from error`는 원래 원인을 개발자가 추적할 연결을 남긴다. |
| 129~130 | `response.ok` | HTTP 성공 상태인지 확인한다. 실패면 상태 코드별 안내를 만든다. |
| 132~135 | `response.json()` | HTTP 본문의 JSON을 Python 자료형으로 바꾼다. API가 JSON을 안 주면 오류다. |
| 137~138 | 최종 변환 | `output_text`만 꺼내고 `parse_json_object`에 넘겨 dict를 반환한다. |

### 상태 코드와 응답 추출 (141~164행)

`_http_error_message()`는 400(요청 형식), 401/403(인증·권한), 429(한도), 5xx(서버)를 서로 다른 한국어 안내로 바꾼다. `_extract_output_text()`는 응답 dict의 `output_text`가 비어 있지 않은 문자열인지 확인한다.

### Phase 05 테스트와 mock

`tests/test_api_client.py`의 `@patch("ai_git_helper.api_client.requests.post")`는 테스트하는 동안만 진짜 `requests.post`를 가짜 함수로 교체한다.

| 테스트 | 만든 상황 | 확인하는 것 |
| --- | --- | --- |
| `test_success...` | 가짜 `output_text` 응답 | 요청 payload·헤더·호출 횟수 1회·dict 변환 |
| `test_timeout...` | 가짜 Timeout 발생 | 사용자용 시간 초과 메시지 |
| `test_auth_errors...` | 401, 403 응답 | Key가 오류 메시지에 새지 않음 |
| `test_rate_limit...` | 429 응답 | 한도 안내 |
| `test_bad_request...` | 400, 503 응답 | 요청 오류와 서버 오류 구분 |
| `test_missing_api_key...` | 환경변수 비움 | HTTP 요청 전에 `ConfigurationError` 발생 |

**이번 단계 핵심:** 환경변수, HTTP header/body, `requests`, `try/except`, mock

## 6. Phase 06 — AI 답변 검증과 출력

### `validation.py`: AI 답변을 그대로 믿지 않는 이유

AI가 `{ "title": "..." }`처럼 JSON을 줘도 제목이 너무 길거나 `how_to_test`가 비어 있을 수 있다. 따라서 API Client의 dict와 사용자 출력 사이에 검증 문을 둔다.

```text
API가 반환한 dict
  ↓ validate_commit_draft(...)
CommitDraft(title="docs: ...", body_lines=[...])
  ↓ format_commit_draft(...)
출력 문자열
```

```python
def _require_text(value, field_name):
    if not isinstance(value, str):
        raise ValidationError(...)
    normalized = " ".join(value.split())
    if not normalized:
        raise ValidationError(...)
    return normalized
```

| 줄 | 의미 |
| --- | --- |
| `isinstance(value, str)` | 값이 정말 문자열인지 확인한다. 숫자·list·None이면 거절한다. |
| `value.split()` | 공백·탭·줄바꿈 기준으로 조각낸다. 예: `"docs:\n 안내"` → `["docs:", "안내"]`. |
| `" ".join(...)` | 조각을 한 칸으로 다시 이어 제목을 한 줄로 만든다. |
| `raise ValidationError` | 비어 있거나 형식이 틀리면 출력 단계로 보내지 않는다. |

```python
def _validate_title(value, *, field_name, max_length):
    title = _require_text(value, field_name)
    if len(title) > max_length:
        raise ValidationError("... 자동으로 자르지 않았습니다.")
    return title
```

자동으로 제목을 자르지 않는 이유는 “feat: 결제...”처럼 의미의 핵심이 잘릴 수 있기 때문이다. Commit은 최대 72자, PR은 최대 80자로 명확히 오류를 낸다.

```python
def _validate_bullet_lines(value, field_name):
    if not isinstance(value, list):
        raise ValidationError(...)
    for index, item in enumerate(value, start=1):
        ...
        line = _BULLET_PREFIX.sub("", " ".join(item.split())).strip()
        if line:
            normalized_lines.append(line)
```

| 문법 | 의미 |
| --- | --- |
| `enumerate(..., start=1)` | 배열 항목 번호를 사람이 읽는 1번부터 만든다. 오류 메시지에 “2번째 항목”을 넣기 좋다. |
| `_BULLET_PREFIX.sub(...)` | AI가 이미 `- 항목`이라고 답해도 앞 불릿을 지운다. `output.py`가 불릿을 한 번만 붙인다. |
| `if line` | 빈 문자열은 목록에 넣지 않는다. |

`validate_commit_draft()`는 `title`, `body`를 검사해 `CommitDraft`를 만든다. `validate_pr_draft()`는 title과 Why/What/How to Test 세 배열을 모두 검사해 `PRDraft`를 만든다.

### `output.py`: 사람이 읽는 최종 모양

```python
def _format_bullets(lines: list[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)

def format_commit_draft(draft: CommitDraft) -> str:
    return "\n".join((
        "[AI Git Helper] Commit Message Draft",
        SEPARATOR,
        draft.title,
        "",
        _format_bullets(draft.body_lines),
        SEPARATOR,
        FINAL_REVIEW_MESSAGE,
    ))
```

| 코드 | 의미 |
| --- | --- |
| `SEPARATOR = "-" * 56` | `-`를 56번 반복한 구분선 문자열이다. |
| `_format_bullets` | 검증되어 불릿이 제거된 문자열 목록 앞에 `- `를 한 번 붙인다. |
| `"\n".join(...)` | 목록의 각 항목을 줄바꿈으로 이어 하나의 출력 문자열을 만든다. 아직 출력하지는 않는다. |
| `format_pr_draft` | 같은 방식으로 `## Why`, `## What`, `## How to Test` 섹션을 추가한다. |
| `print(...)` | 실제 출력은 이 파일이 아니라 호출자인 `cli.py`가 한다. 함수가 문자열만 반환하므로 테스트하기 쉽다. |

### Phase 06 테스트

`tests/test_validation_and_output.py`는 제목 줄바꿈 정리, 길이 초과 오류, 빈 배열·잘못된 타입 오류, 불릿 중복 제거, Commit/PR 출력 모양을 검사한다. 실패하면 AI 응답이 그대로 사용자에게 잘못 출력될 가능성을 의심할 수 있다.

**이번 단계 핵심:** `isinstance`, `split/join`, 정규표현식, 검증, dataclass, 문자열 렌더링

## 7. Phase 07 — CLI 통합: 지휘자 `cli.py`

### import가 보여 주는 의존성 방향

```python
from .api_client import DEFAULT_MODEL, GeminiClient
from .errors import AIGitHelperError
from .git_service import collect_git_changes
from .output import format_commit_draft, format_pr_draft
from .prompts import ...
from .safety import ...
from .validation import ...
```

현재 파일은 `cli.py`다. 이 파일은 모든 전문 기능을 직접 다시 구현하지 않고, 각 파일에서 필요한 함수만 import해 **순서만 지휘**한다. 이것이 파일을 나눈 가장 큰 이유다. 예를 들어 Git 명령 코드는 `git_service.py`에만 있고, `cli.py`에는 `subprocess` import가 없다.

### parser 만들기 (28~93행)

```python
def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 정수여야 합니다.")
    return parsed

parser.add_argument("command", nargs="?", choices=("commit", "pr"))
```

| 줄 | 의미 |
| --- | --- |
| `argparse` | Python 표준 라이브러리 CLI 해석기다. |
| `_positive_integer` | `--max-tokens 0` 같은 잘못된 입력을 parser 단계에서 막는다. 문자열 `"1500"`을 정수 `1500`으로 바꾼다. |
| `nargs="?"` | command를 생략해도 된다는 뜻이다. 생략하면 `--help`를 보여 준다. |
| `choices=(...)` | command에 `commit`, `pr` 외 단어가 오면 parser가 오류를 낸다. |
| `mutually_exclusive_group()` | `--safe-mode`와 `--no-safe-mode`를 동시에 쓰지 못하게 하는 선택 그룹이다. |
| `dest="safe_mode"` | 둘 중 어느 옵션을 써도 최종값은 `args.safe_mode`에 저장된다. |
| `action="store_true/false"` | 옵션이 있으면 True 또는 False를 저장한다. |

실제 예시:

```text
python main.py commit --temperature 0.2 --max-tokens 1500
    ↓ parser.parse_args()
args.command = "commit"
args.temperature = 0.2
args.max_tokens = 1500
args.safe_mode = True
```

### `main()`의 오류 처리 (96~115행)

```python
def main(arguments=None) -> int:
    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return _run_command(args)
    except KeyboardInterrupt:
        print("\n[ERROR] 사용자가 실행을 취소했습니다.")
        return 130
    except AIGitHelperError as error:
        print(f"[ERROR] {error}")
        return 1
```

| 줄 | 의미 |
| --- | --- |
| `arguments=None` | 실제 실행에서는 `None`이라서 parser가 터미널 인자를 읽는다. 테스트에서는 `main(["commit"])`처럼 직접 목록을 넣는다. |
| `return 0` | 운영체제에 “정상 종료”를 알리는 종료 코드다. |
| `try` | 아래 기능 실행 중 오류가 생길 수 있는 구간을 감싼다. |
| `KeyboardInterrupt` | 사용자가 Ctrl+C를 누르면 Python이 만드는 예외다. 종료 코드 130을 반환한다. |
| `AIGitHelperError` | Git/API/설정/검증 오류의 공통 부모다. traceback 대신 한 줄 `[ERROR]`로 바꾼다. |
| `ValueError` | safe-mode 제한값 같은 일반 값 오류도 사용자용 안내로 바꾼다. |

### 전체 연결의 핵심 `_run_command()` (118~165행)

```python
changes = collect_git_changes(Path.cwd())
if not changes.has_changes:
    print("[INFO] Git 변경 사항이 없습니다. API를 호출하지 않습니다.")
    return 0

safety_result = apply_safe_mode(changes.diff_text, ...)

if args.command == "commit":
    prompt = build_commit_prompt(changes, safety_result)
    schema = COMMIT_RESPONSE_SCHEMA
else:
    prompt = build_pr_prompt(changes, safety_result)
    schema = PR_RESPONSE_SCHEMA
```

| 줄 | 실행 전 → 실행 후 | 왜 이 순서인가 |
| --- | --- | --- |
| 121 | 현재 터미널 폴더 `Path.cwd()` → `GitChanges` | 프로그램은 “현재 폴더의 Git 저장소”를 분석한다. |
| 123~125 | `changed_files=[]` → 안내 출력·종료 | Key 확인과 API 호출보다 먼저 끝내 비용·불필요한 요청을 막는다. |
| 127~132 | raw `diff_text` → `SafetyResult` | AI에 전달하기 전에 반드시 안전 처리한다. |
| 133 | 마스킹/생략 여부 안내 | 사용자가 전송 내용의 제한 사실을 안다. |
| 135~140 | command 값 → 맞는 프롬프트와 Schema | Commit과 PR의 답 형식이 다르기 때문이다. |

```python
if args.show_prompt:
    print(prompt)
    return 0

response = GeminiClient().generate_json(...)
if args.command == "commit":
    print(format_commit_draft(validate_commit_draft(response)))
else:
    print(format_pr_draft(validate_pr_draft(response)))
```

| 줄 | 의미 |
| --- | --- |
| 142~149 | `--show-prompt`면 API 요청 전에 끝난다. 학습·보안 확인용이며 비용이 없다. |
| 152~159 | `GeminiClient()` 객체를 만들고 API 요청을 딱 한 번 보낸다. 반환값은 아직 검증 전 dict다. |
| 161~164 | 먼저 검증 함수가 Draft 객체로 바꾸고, 그 결과만 출력 함수에 넘긴다. 안쪽 함수가 먼저 실행된다. |
| 165 | 모든 단계가 성공했음을 뜻하는 0을 반환한다. |

### `_print_safe_mode_notice()` (168~180행)

safe-mode를 끈 경우에는 위험 경고를, 켠 뒤 실제로 가리거나 생략한 것이 있으면 `[SAFE MODE]` 안내를 출력한다. `details`는 문자열 리스트이고 `', '.join(details)`가 여러 안내를 쉼표로 잇는다.

### Phase 07 테스트

`tests/test_cli_integration.py`는 아래를 확인한다.

| 테스트 | 무엇을 확인하는가 | 실제 기능에서 실패하면 |
| --- | --- | --- |
| `test_no_changes...` | 변경 없음이면 API mock이 호출되지 않음 | 비용 없는 종료가 깨짐 |
| `test_commit_calls_api_once...` | Commit API 호출 1회와 옵션 전달 | 중복 API 요청 또는 옵션 무시 가능성 |
| `test_pr_calls_api_once...` | PR의 세 섹션 출력 | PR 형식 누락 가능성 |
| `test_show_prompt...` | 안전 프롬프트 확인 시 API 미호출 | 학습 모드가 비용을 발생시킬 수 있음 |
| `test_non_git_repository...` | Git 오류가 `[ERROR]`로 출력 | traceback이 사용자에게 노출될 수 있음 |
| `test_ctrl_c...` | Ctrl+C가 130으로 종료 | 취소 동작이 불명확해짐 |
| `test_real_temporary_git_repository...` | 임시 Git 저장소에서 실제 `git diff`부터 CLI까지 연결 | mock만 통과하고 실제 Git 연결이 깨질 수 있음 |

`unittest`는 Python 기본 테스트 도구다. `assertEqual(a, b)`는 두 값이 같은지, `assertTrue(x)`/`assertFalse(x)`는 참·거짓인지, `assertRaises(오류종류)`는 예상한 오류가 나는지 검사한다. `TemporaryDirectory`는 테스트 뒤 자동 삭제되는 임시 폴더여서 현재 프로젝트나 개인 Git 저장소를 오염시키지 않는다.

**이번 단계 핵심:** CLI parser, `Namespace`, try/except, 종료 코드, 의존성 연결, mock 통합 테스트

## 8. 명령을 머릿속으로 끝까지 따라가기

### 상황 A: 도움말

```text
사용자 입력: python main.py --help
운영체제 실행 파일: Python → main.py
처음 Python 호출: main.py의 main()
parser가 만든 값: --help는 argparse가 직접 처리
호출 순서: build_parser() → parser.parse_args() → 도움말 출력 → SystemExit(보통 0)
API/Git 호출: 없음
터미널 출력: 옵션 목록
```

### 상황 B: 변경 사항 없는 Git 저장소

```text
사용자 입력: python main.py commit
parser 값: args.command = "commit"
호출 순서:
  main() → _run_command()
  → collect_git_changes(Path.cwd())
  → GitChanges(changed_files=[])
  → changes.has_changes = False
터미널 출력: [INFO] Git 변경 사항이 없습니다. API를 호출하지 않습니다.
API Key 확인/API 호출: 없음
종료 코드: 0
```

### 상황 C: 파일을 수정한 Git 저장소

```text
사용자 입력: python main.py commit
중간 데이터 예:
  GitChanges(changed_files=["README.md"], diff_text="+설명 추가")
  SafetyResult(text="+설명 추가", masked_count=0, truncated=False)
  prompt = "... title/body JSON으로 반환 ..."
  (가상의 API 응답) {"title": "docs: 사용법 안내 추가", "body": ["README 설명 보강"]}
  CommitDraft(title="docs: 사용법 안내 추가", body_lines=["README 설명 보강"])
터미널 출력: 제목과 - 본문이 있는 Commit Draft
실제 API: Key가 있을 때만 호출된다. 위 API 응답은 설명용 가상값이다.
```

### 상황 D: staged와 unstaged가 함께 있음

```text
사용자 입력:
  git add staged.txt
  python main.py commit
git_service.py 내부:
  git diff --cached --no-ext-diff --unified=3  # staged 부분
  git diff --no-ext-diff --unified=3           # unstaged 부분
결과 diff_text:
  === STAGED DIFF ===
  ... staged.txt 차이 ...

  === UNSTAGED DIFF ===
  ... 아직 add하지 않은 차이 ...
다음 흐름: 두 부분을 합친 diff가 safe-mode → prompt로 전달된다.
```

### 상황 E: Git 저장소가 아닌 폴더

```text
사용자 입력: python /프로젝트경로/main.py commit
호출 순서:
  cli._run_command()
  → collect_git_changes(Path.cwd())
  → ensure_git_repository()
  → git rev-parse --is-inside-work-tree 실패
  → GitCommandError
  → cli.main()의 except AIGitHelperError
터미널 출력: [ERROR] ... Git 관련 오류 안내
종료 코드: 1
API 호출: 없음
```

## 9. 구현 상태와 다음에 수정할 때 알아야 할 것

| 상태 | 기능 | 관련 파일 | 수정할 때 주의할 점 |
| --- | --- | --- | --- |
| 구현됨 | safe-mode | `safety.py` | 새 패턴을 넣으면 과도한 마스킹/누락 여부를 테스트해야 한다. |
| 구현됨 | Commit/PR 프롬프트·Schema | `prompts.py` | prompt 요구와 `validation.py` 요구를 함께 바꿔야 한다. |
| 구현됨 | Gemini API 호출 | `api_client.py` | Key를 출력·저장하지 말고 HTTP mock 테스트를 추가해야 한다. |
| 구현됨 | 결과 검증·출력 | `validation.py`, `output.py` | Schema만 믿지 말고 로컬 검증을 유지한다. |
| 구현됨 | CLI 통합 | `cli.py` | API 호출 전 “변경 없음”·safe-mode 순서를 지켜야 한다. |
| 구현하지 않음 | 자동 commit/push/GitHub PR 생성 | 없음 | 미션 범위 밖이다. 초안만 출력한다. |

## 10. 직접 해 볼 안전한 명령

```bash
# 1. 옵션 목록만 보기: Git/API 호출 없음
.venv/bin/python main.py --help

# 2. 변경 사항이 있는 저장소에서 API 없이 프롬프트만 확인
.venv/bin/python main.py commit --show-prompt

# 3. 실제 API 없이 모든 자동 테스트 실행
.venv/bin/python -m unittest discover -s tests -v
```

## 11. 마지막 복습 질문

1. `subprocess`가 Git 정보를 직접 읽는 것이 아니라면, 실제로 `.git`과 working tree를 읽는 프로그램은 무엇인가?
2. `changes.has_changes` 검사가 API Key 확인보다 먼저 있는 이유는 무엇인가?
3. `SafetyResult`와 `GitChanges`를 따로 둔 이유는 무엇인가?
4. AI가 JSON Schema를 받았는데도 `validation.py`가 다시 검사하는 이유는 무엇인가?
5. `--show-prompt`가 API를 호출하지 않는다는 것은 어느 `if`와 `return`으로 보장되는가?

### 한 줄 요약

이 프로젝트는 “Git이 만든 변경 정보”를 Python이 수집하고, 안전하게 줄여 AI에게 한 번 전달한 뒤, AI 결과를 다시 검증해서 **초안만** 터미널에 보여 주는 프로그램이다.
