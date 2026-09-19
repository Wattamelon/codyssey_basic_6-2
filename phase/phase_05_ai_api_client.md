# Phase 05 - AI API 클라이언트 구현

## 역할

너는 REST API와 외부 서비스 오류 처리를 담당하는 Python 개발자다.

## 목표

선택한 AI 서비스의 공식 문서에 맞춰 REST API를 1회 호출하고, 구조화된 JSON 응답을 안전하게 추출하는 클라이언트를 구현한다.

## 기본 선택

참고 프로젝트와의 일관성을 위해 Gemini Developer API를 기본 provider로 사용한다. 단, Endpoint·모델명·요청 body·응답 구조는 현재 공식 문서를 확인하고 추측하지 않는다.

## 작업

1. API Key를 `GEMINI_API_KEY` 환경변수에서 읽는다.
2. API Key 누락 시 호출하지 않고 설정 방법을 안내한다.
3. `requests`를 사용해 POST 요청을 구성한다.
4. 인증 헤더, system instruction, user input, model, temperature, max output tokens를 전달한다.
5. Commit·PR JSON Schema를 structured output 설정에 전달한다.
6. timeout, 연결 실패, HTTP 400, 401·403, 429, 5xx를 구분해 사용자 메시지를 만든다.
7. 응답 JSON에서 최종 model output 텍스트만 추출한다.
8. Markdown 코드 블록으로 감싼 JSON도 방어적으로 처리한다.
9. 최상위 JSON이 객체인지 확인한다.
10. API Key나 전체 인증 헤더를 오류 메시지에 출력하지 않는다.

## 요청 횟수 조건

- 한 번의 commit 또는 pr 실행에서 API 호출은 최대 1회로 한다.
- 검증 실패 시 자동 무한 재시도하지 않는다.
- 제목 길이 보정은 로컬 후처리 또는 명확한 오류로 처리한다.

## 테스트

실제 API를 호출하지 말고 HTTP client를 mock한다.

- 성공 응답
- timeout
- ConnectionError
- 401·403
- 429
- JSON 파싱 실패
- 예상 필드 누락
- API Key 누락

```bash
python -m unittest discover -s tests -v
```

실제 API 실행이 필요한 경우에는 Key를 요청하거나 저장하지 말고, 사용자가 직접 실행할 수 있는 검증 명령만 안내한다.

