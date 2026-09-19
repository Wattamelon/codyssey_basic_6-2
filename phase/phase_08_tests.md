# Phase 08 - 테스트 보강과 통합 검증

## 역할

너는 테스트 전략을 세우는 Python QA 엔지니어다.

## 목표

미션 평가에 필요한 핵심 기능을 실제 API 호출 없이 반복 검증할 수 있는 테스트를 완성한다.

## 테스트 범위

1. Git status 파싱
2. staged·unstaged diff 수집
3. Git 저장소 오류
4. 변경 없음 분기
5. safe-mode 마스킹
6. 줄 수·문자 수 제한
7. prompt 컨텍스트
8. API Key 누락
9. API 성공 응답
10. API timeout·인증·429·5xx
11. JSON 파싱 실패
12. Commit 제목·본문 검증
13. PR 필수 섹션 검증
14. 터미널 출력 formatter
15. CLI 호출 횟수 1회 보장

## 테스트 원칙

- 실제 API Key를 사용하지 않는다.
- 실제 외부 네트워크에 의존하지 않는다.
- 테스트끼리 작업 디렉터리와 환경변수를 오염시키지 않는다.
- 실패 메시지가 사용자가 이해할 수 있는지도 확인한다.
- 미션 PDF에 없는 동작을 공식 요구사항으로 과장하지 않는다.

## 실행

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

테스트 수와 결과, 아직 수동 확인이 필요한 항목을 보고한다.
