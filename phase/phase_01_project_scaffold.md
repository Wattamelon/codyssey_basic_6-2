# Phase 01 - 프로젝트 기본 구조 만들기

## 역할

너는 Python CLI 프로젝트를 설계하는 시니어 개발자다.

## 목표

6-2 미션의 첫 단계로, Git 변경 사항을 분석해 AI 기반 커밋 메시지와 PR 초안을 생성하는 Python 프로젝트의 기본 구조를 만든다.

## 먼저 확인할 자료

- `기초과정_6주차_2단계_study.md`
- 미션 PDF
- 현재 작업 디렉터리의 파일과 사용자 변경 사항

## 작업

1. Python 3.10 이상을 전제로 프로젝트 디렉터리 구조를 만든다.
2. `main.py`, `ai_git_helper/`, `tests/`와 기본 모듈 파일을 생성한다.
3. 공통 예외 클래스와 dataclass 기반 모델의 최소 골격을 만든다.
4. `main.py --help`가 실행되도록 최소 CLI 진입점을 만든다.
5. `requirements.txt`, `.env.example`, `.gitignore`를 작성한다.
6. API Key는 `GEMINI_API_KEY` 환경변수로 관리한다. 실제 Key는 생성하거나 기록하지 않는다.
7. 아직 Git 수집, API 호출, 실제 생성 기능은 구현하지 않는다.

## 설계 조건

- 기능별 모듈을 분리한다.
- `git commit`, `git push`, GitHub PR 자동 생성은 넣지 않는다.
- 의존성은 필요한 것만 추가한다.
- 주석은 왜 필요한지 설명하는 곳에만 작성한다.

## 완료 조건

- `python main.py --help`가 정상 종료된다.
- 모든 Python 파일이 컴파일된다.
- import 오류가 없다.
- 실제 API Key가 저장소에 없다.
- 생성·수정한 파일 목록과 구조를 보고한다.

## 검증 명령

```bash
python --version
python main.py --help
python -m compileall -q .
```

작업이 끝나면 구현한 구조, 실행 결과, 다음 단계에서 사용할 확장 지점을 간단히 보고한다.

