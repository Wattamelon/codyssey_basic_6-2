# Phase 07 - 전체 CLI 흐름 통합

## 역할

너는 Python CLI 애플리케이션을 통합하는 시니어 개발자다.

## 목표

앞선 모듈을 `python main.py commit`과 `python main.py pr`로 연결한다.

## 작업 순서

1. `commit`, `pr` 하위 명령을 만든다.
2. `--model`, `--temperature`, `--max-tokens` 옵션과 기본값을 제공한다.
3. `--safe-mode`와 `--no-safe-mode`를 제공한다.
4. `--max-diff-lines`, `--max-diff-chars`를 제공한다.
5. `--show-prompt`는 학습용으로 제공하되 민감정보 보호 주의를 표시한다.
6. Git 변경 사항이 없으면 API Key 확인과 API 호출 전에 종료한다.
7. safe-mode를 적용한다.
8. 명령에 따라 prompt와 schema를 선택한다.
9. API를 1회 호출한다.
10. 응답을 파싱하고 검증하고 출력한다.
11. 예상 가능한 오류는 traceback 없이 `[ERROR]` 메시지와 종료 코드 1로 처리한다.
12. Ctrl+C는 종료 코드 130으로 처리한다.

## 실행 예시

```bash
python main.py --help
python main.py commit
python main.py pr
python main.py commit --model <MODEL> --temperature 0.2 --max-tokens 1500
```

## 금지사항

- API Key 출력 금지
- 자동 commit·push·GitHub PR 생성 금지
- API 무한 재시도 금지
- 앞선 모듈을 무시한 중복 구현 금지

## 검증

Git 변경 없음, Key 없음, Git 저장소 아님, safe-mode 경고, API mock 성공·실패를 각각 확인한다.

