# Phase 04 - Commit·PR 프롬프트와 출력 스키마 설계

## 역할

너는 프롬프트 엔지니어링과 구조화된 AI 출력을 설계하는 개발자다.

## 목표

Git 컨텍스트를 바탕으로 Commit과 PR을 각각 생성할 수 있도록 프롬프트와 JSON Schema를 분리해 구현한다.

## 작업

1. 공통 system prompt를 만든다.
2. 현재 브랜치, status, 변경 파일, safe-mode 적용 diff를 컨텍스트로 묶는다.
3. Commit 전용 prompt를 만든다.
   - `title`: 한 줄
   - 최대 72자, 50자 이내 권장
   - `feat`, `fix`, `docs`, `refactor`, `test`, `chore` prefix 권장
   - `body`: 핵심 변경 내용 배열
4. PR 전용 prompt를 만든다.
   - `title`: 최대 80자
   - `why`, `what`, `how_to_test` 배열
   - 각 배열 최소 1개
5. 입력에 없는 기능·원인·테스트 결과를 지어내지 말라는 지시를 포함한다.
6. 테스트 완료를 확인할 수 없으면 완료했다고 쓰지 말라는 지시를 포함한다.
7. Markdown 코드 블록이 아닌 JSON만 반환하도록 지시한다.
8. Commit·PR JSON Schema를 분리하고 추가 속성을 허용하지 않는다.

## 주의사항

- 미션상 Commit 본문은 선택 사항이지만, 최소 품질 증빙을 위해 구현에서 요구할지 여부를 명확히 기록한다.
- safe-mode로 잘린 diff는 전체 변경이 아니라 일부라는 점을 컨텍스트에 표시한다.
- 프롬프트에 API Key나 실제 민감정보를 넣지 않는다.

## 테스트

- 컨텍스트에 브랜치·파일·status·diff가 포함되는지 확인
- Commit과 PR prompt가 서로 다른 규칙을 갖는지 확인
- 민감정보가 prompt에 들어가지 않는지 확인
- 필수 JSON Schema 필드 확인

```bash
python -m unittest discover -s tests -v
```

