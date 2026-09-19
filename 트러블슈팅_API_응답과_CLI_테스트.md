# 트러블슈팅: API 응답과 CLI 테스트

이 문서는 `python main.py commit`, `python main.py pr`를 실제로 시험하면서 발생한 오류와 해결 과정을 정리한 기록이다. API Key, 실제 Git diff, 실제 API 원문 응답은 보안상 기록하지 않는다.

## 실행 환경

```bash
source .venv/bin/activate
python main.py commit
python main.py pr
```

프로그램은 다음 순서로 움직인다.

```text
Git 변경 수집
→ safe-mode
→ Commit 또는 PR 프롬프트 생성
→ Gemini REST API 요청
→ API 응답에서 텍스트 추출
→ JSON 파싱
→ Commit/PR 규칙 검증
→ 터미널 출력
```

오류 메시지는 이 흐름에서 어느 단계가 실패했는지 알려 주는 표지판이다.

---

## 1. `[ERROR] AI API 응답에서 최종 텍스트 결과를 찾지 못했습니다.`

### 발생 상황

`python main.py commit` 실행 뒤 API 요청은 성공했지만, 프로그램이 모델의 최종 텍스트를 찾지 못했다.

### 처음 코드가 기대한 모습

처음에는 REST 응답이 아래처럼 최상위 `output_text`를 바로 가진다고 가정했다.

```json
{
  "output_text": "{\"title\": \"docs: 안내 추가\"}"
}
```

### 실제 REST API 응답의 핵심 구조

Gemini Interactions API의 raw REST 응답은 보통 모델 결과를 `steps` 안에 넣는다.

```json
{
  "status": "completed",
  "steps": [
    {
      "type": "model_output",
      "content": [
        {
          "type": "text",
          "text": "{\"title\": \"docs: 안내 추가\"}"
        }
      ]
    }
  ]
}
```

`output_text`는 SDK가 제공하는 편의 필드일 수 있지만, raw REST 응답에서는 항상 존재하지 않는다. 그래서 REST API를 `requests`로 직접 호출하는 이 프로젝트에서는 `steps`를 읽어야 한다.

### 해결

`ai_git_helper/api_client.py`의 `_extract_output_text()`를 수정했다.

```text
1. output_text가 있으면 호환용으로 먼저 사용한다.
2. 없으면 steps 목록을 뒤에서부터 확인한다.
3. type이 model_output인 step을 찾는다.
4. 그 안의 content 목록에서 type이 text인 항목을 찾는다.
5. text들을 이어 붙여 JSON parser로 전달한다.
```

```python
steps = response_data.get("steps")
for step in reversed(steps):
    if step.get("type") != "model_output":
        continue
    content = step.get("content")
    text_parts = [part.get("text") for part in content if part.get("type") == "text"]
    return "".join(text_parts)
```

### 왜 `reversed()`를 쓰는가?

한 번의 API 실행에는 생각 과정, 도구 호출, 모델 출력 등 여러 step이 있을 수 있다. 사용자에게 보여 줄 답은 마지막 `model_output`인 경우가 자연스러워서 뒤에서부터 찾는다.

### 확인 방법

실제 API 호출 없이 아래 테스트로 raw REST 응답 모양을 재현한다.

```bash
python -m unittest tests.test_api_client.GeminiClientTests.test_rest_success_reads_model_output_step_and_sends_request_once -v
```

---

## 2. `[ERROR] AI 응답이 올바른 JSON 형식이 아닙니다.`

### 발생 상황

`python main.py pr` 실행 뒤 모델 텍스트를 찾는 데는 성공했지만, 그 텍스트 전체를 `json.loads()`로 읽을 수 없었다.

### 원인

프로그램은 AI에게 JSON만 반환하라고 요청하고 JSON Schema도 보낸다. 하지만 생성형 AI는 드물게 아래처럼 JSON 외의 설명이나 Markdown 코드 블록을 덧붙일 수 있다.

````text
요청한 PR 초안입니다.

```json
{"title": "docs: 안내 추가", "why": ["..."], "what": ["..."], "how_to_test": ["..."]}
```

검토해 주세요.
````

이 문자열 전체는 JSON이 아니다. JSON parser는 첫 글자가 `{` 또는 `[`처럼 JSON 시작 문법이기를 기대하므로 실패한다.

### 해결

`parse_json_object()`에 복구 단계를 추가했다.

```text
1. 우선 텍스트 전체를 JSON으로 파싱한다. 가장 정상적인 경우다.
2. 실패하면 ```json ... ``` 코드 블록 안을 찾는다.
3. 그래도 실패하면 텍스트 안에서 {로 시작하는 JSON 객체를 찾는다.
4. 찾은 값이 Python dict인지 확인한다.
5. 그래도 실패하면 원문을 노출하지 않고 JSON 형식 오류를 출력한다.
```

```python
try:
    parsed = json.loads(cleaned)
except json.JSONDecodeError:
    parsed = _find_embedded_json_object(cleaned)
    if parsed is None:
        raise APIRequestError("AI 응답이 올바른 JSON 형식이 아닙니다.")
```

### 왜 원문 응답을 오류 메시지에 출력하지 않는가?

AI에게 Git diff가 전달됐으므로, 오류 메시지에 응답 전체를 출력하면 코드·경로·민감한 내용이 터미널 로그에 불필요하게 남을 수 있다. 이 프로젝트는 오류의 **종류**만 알려 주고 원문은 출력하지 않는다.

### 확인 방법

```bash
python -m unittest tests.test_api_client.GeminiClientTests.test_json_object_with_markdown_explanation_is_accepted -v
python -m unittest tests.test_api_client.GeminiClientTests.test_json_object_with_plain_text_prefix_is_accepted -v
```

---

## 3. 테스트 파일을 만들었는데 diff 내용이 비어 보인 경우

### 증상

새 파일을 만든 뒤 `python main.py commit --show-prompt`를 실행했지만 다음처럼 보일 수 있다.

```text
git status --short:
?? demo_workspace/

안전 처리된 git diff:
(diff 텍스트 없음: 파일 목록과 status만 사용하세요.)
```

### 원인

`git status`는 아직 Git이 추적하지 않는 새 파일(untracked)도 보여 준다. 반면 일반 `git diff`와 `git diff --cached`는 보통 Git이 추적 중이거나 staging area에 올린 변경을 비교한다. 따라서 untracked 파일의 내용은 diff에 바로 나타나지 않을 수 있다.

### 해결

커밋하지 않고 staging area에만 올린다.

```bash
git add demo_workspace
python main.py commit --show-prompt
```

그러면 프로그램이 다음 명령으로 staged 파일의 내용 차이를 수집한다.

```bash
git diff --cached --no-ext-diff --unified=3
```

### 중요한 구분

| 명령 | 일어나는 일 |
| --- | --- |
| `git add demo_workspace` | 파일을 staging area에 올림. **커밋은 만들지 않음** |
| `python main.py commit` | AI 초안만 생성. **Git 커밋은 만들지 않음** |
| `git commit -m "..."` | 실제 Git 커밋 생성 |

---

## 4. 재발 시 점검 순서

### JSON 미리보기가 `:` 또는 `,`에서 끝난 경우

예를 들어 아래처럼 `"why":`에서 끝나면 JSON parser 자체의 문제가 아니라 모델 출력이 중간에 끊긴 것이다.

```text
{"title": "...", "why":
```

기본 최대 출력 토큰은 2,048이며, 그래도 같은 문제가 나면 더 큰 값으로 한 번 재실행한다.

```bash
python main.py pr --temperature 0.2 --max-tokens 4096
```

이 실행도 API 요청 1회이므로, 반복 실행 전에는 비용·쿼터를 확인한다.

### API 요청 시간이 초과된 경우

기본 HTTP timeout은 120초다. 모델이 큰 Git 변경 맥락과 구조화된 응답을 처리하는 동안에는 이만큼 기다릴 수 있다. 이 프로그램은 같은 요청을 자동 재시도하지 않는다.

- 네트워크 연결을 확인한다.
- `--show-prompt`로 실제 전송 diff가 지나치게 크지 않은지 확인한다.
- 잠시 뒤 한 번만 다시 실행한다. 반복 실행은 API 비용과 쿼터를 사용할 수 있다.

### 1단계: Git 변경이 보이는지 확인

```bash
git status --short
```

- 아무것도 안 나오면 변경 사항이 없다.
- `?? 파일명`은 untracked 파일이다.
- `A  파일명`, `M  파일명` 등은 staged 변경일 수 있다.
- ` M 파일명`은 unstaged 변경이다.

### 2단계: API 없이 전송 내용을 확인

```bash
python main.py commit --show-prompt
python main.py pr --show-prompt
```

이 명령은 API 비용 없이 Git 수집·safe-mode·프롬프트 생성까지 확인한다.

### 3단계: Key 설정 여부 확인

Key 값 자체는 출력하지 말고, 설정 여부만 확인한다.

```bash
if [ -n "$GEMINI_API_KEY" ]; then echo "Key is set"; else echo "Key is not set"; fi
```

### 4단계: 실제 요청 실행

```bash
python main.py commit
python main.py pr
```

### 5단계: 자동 테스트 실행

```bash
python -m unittest discover -s tests -v
```

## 5. 현재 확인 결과

- raw REST API의 `steps → model_output → content → text` 응답 구조 처리 추가
- Markdown/설명문이 섞인 JSON 객체 복구 처리 추가
- 실제 HTTP를 호출하지 않는 mock 테스트 추가
- 전체 자동 테스트 **51개 통과**

## 6. 남아 있는 한계

- JSON Schema를 보내도 AI 출력이 항상 완벽한 JSON이라는 보장은 없다. 그래서 local parser와 `validation.py`가 한 번 더 검사한다.
- safe-mode는 정규표현식 기반 보조 장치다. 모든 비밀값을 찾아낸다고 보장하지 않는다.
- 실제 API 호출은 모델 상태, 네트워크, 쿼터, 비용 정책의 영향을 받는다.
- 출력된 Commit/PR 내용은 AI 초안이므로 사람이 변경 사실과 테스트 방법을 검토해야 한다.
