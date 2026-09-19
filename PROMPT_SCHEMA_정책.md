# Commit·PR 프롬프트와 JSON Schema 정책

## 공통 원칙

- AI는 브랜치, Git status, 변경 파일, safe-mode 적용 diff를 근거로만 작성한다.
- 입력에 없는 기능, 원인, 테스트 결과를 지어내지 않는다.
- 결과는 한국어 JSON만 반환하고 Markdown 코드 블록이나 부가 설명을 넣지 않는다.
- safe-mode가 일부 diff를 생략했으면 확인할 수 없는 변경을 단정하지 않는다.

## Commit 정책

- 제목은 한 줄이며 최대 72자, 가능하면 50자 이내다.
- feat, fix, docs, refactor, test, chore prefix를 권장한다.
- 미션 PDF에서는 커밋 본문이 선택 사항이다.
- 이 구현에서는 최소 품질 증빙을 위해 body를 1개 이상 3개 이하의 항목으로 요구한다.

## PR 정책

- 제목은 한 줄이며 최대 80자다.
- why, what, how_to_test 배열은 각각 최소 1개 항목을 가진다.
- how_to_test는 이미 테스트를 완료했다고 주장하지 않고, 사용자가 실행할 수 있는 확인 방법을 작성한다.

## Schema 사용 이유

Commit과 PR의 JSON 구조를 분리하면 이후 API 호출 단계에서 응답 형식을 더 안정적으로 검증할 수 있다. additionalProperties를 false로 두어 미리 정하지 않은 필드가 들어오는 것을 막는다.

