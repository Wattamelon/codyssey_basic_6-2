# AI Git Helper CLI

현재 Git 저장소의 변경 사항을 읽어 AI에게 전달하고, 사람이 검토할 **커밋 메시지** 또는 **Pull Request 초안**을 만드는 터미널 프로그램입니다.

이 프로그램은 Git 변경을 자동으로 적용하지 않습니다. AI가 만든 문구는 초안이므로, 사용자가 변경 사실과 테스트 방법을 확인한 뒤 직접 사용합니다.

## 실행 환경

- Python 3.10 이상
- Git이 설치된 터미널 환경
- Gemini API를 사용할 경우 Gemini API Key

## 프로젝트 구조

| 경로 | 역할 |
| --- | --- |
| `main.py` | `python main.py ...` 실행 진입점 |
| `ai_git_helper/cli.py` | 명령 옵션과 전체 실행 순서 연결 |
| `ai_git_helper/git_service.py` | `git status`, staged/unstaged `git diff` 수집 |
| `ai_git_helper/safety.py` | 민감정보 패턴 마스킹과 diff 크기 제한 |
| `ai_git_helper/prompts.py` | Git 정보를 Commit/PR 프롬프트·JSON Schema로 구성 |
| `ai_git_helper/api_client.py` | Gemini REST API 요청 한 번 및 JSON 응답 추출 |
| `ai_git_helper/validation.py` | AI 응답의 제목·배열·필수 PR 섹션 검증 |
| `ai_git_helper/output.py` | 검증된 초안을 터미널 형식으로 출력 |
| `tests/` | 실제 API 없이 동작을 검증하는 자동 테스트 |

## 설치

프로젝트 폴더에서 가상환경을 만들고 활성화합니다. 가상환경은 이 프로젝트의 라이브러리를 시스템 Python과 분리하는 전용 공간입니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

가상환경을 활성화한 터미널에서는 아래처럼 실행합니다.

```bash
python main.py --help
```

종료할 때는 `deactivate`를 실행합니다.

## API Key 설정

API Key는 코드나 Git에 저장하지 않고 현재 터미널의 환경변수로만 설정합니다.

```bash
export GEMINI_API_KEY="발급받은_키"
```

`.env.example`은 변수 이름을 보여 주는 예시 파일일 뿐, 프로그램이 `.env` 파일을 자동으로 읽지는 않습니다. `.env`와 실제 값을 담는 `.env.*` 파일은 `.gitignore`로 제외되며, `.env.example`만 안내용 추적 예외입니다. 실제 Key를 작성해 커밋하면 안 됩니다.

Key가 없거나 잘못된 경우에는 `[ERROR]` 안내가 표시되며 Key 자체는 출력하지 않습니다.

## 실행 방법

반드시 **변경 사항이 있는 Git 저장소 안에서** 실행합니다.

```bash
# 커밋 메시지 초안
python main.py commit

# Pull Request 초안
python main.py pr
```

모델과 생성 옵션은 필요할 때만 바꿉니다.

```bash
python main.py commit --model gemini-3.6-flash --temperature 0.2 --max-tokens 1500
```

| 옵션 | 기본값 | 의미 |
| --- | --- | --- |
| `--model` | `gemini-3.6-flash` | 사용할 Gemini 모델명 |
| `--temperature` | `1.0` | 응답의 다양성 값 |
| `--max-tokens` | `2048` | API가 생성할 최대 출력 토큰 수 |
| `--safe-mode` | 켜짐 | 마스킹과 diff 제한 적용 |
| `--no-safe-mode` | 꺼짐 | 안전 처리를 비활성화. 민감정보 전송 위험이 있어 권장하지 않음 |
| `--max-diff-lines` | `200` | safe-mode에서 전송하는 최대 diff 줄 수 |
| `--max-diff-chars` | `20000` | safe-mode에서 전송하는 최대 diff 문자 수 |
| `--show-prompt` | 꺼짐 | API 호출 없이 실제 전송 프롬프트를 표시 |

Gemini 모델명과 API 제공 상태는 바뀔 수 있으므로, 실제 사용 전에는 [Gemini API 공식 문서](https://ai.google.dev/gemini-api/docs)를 확인하세요.

## safe-mode와 민감정보

safe-mode는 기본으로 켜져 있으며 다음 순서로 동작합니다.

1. API Key, token, password, 이메일처럼 보이는 일부 패턴을 마스킹합니다.
2. diff 줄 수와 문자 수를 제한합니다.
3. 내용이 마스킹되거나 생략되면 터미널에 `[SAFE MODE]` 안내를 표시합니다.

정규표현식 기반 탐지는 모든 비밀값을 찾는 보안 기능이 아닙니다. 전송 전에 아래 명령으로 프롬프트를 직접 확인하고, 비밀값이 남아 있으면 실행하지 마세요.

```bash
python main.py commit --show-prompt
```

`--show-prompt`는 API를 호출하지 않으므로 비용이 들지 않습니다.

## 출력 예시

아래는 자동 테스트에서 사용하는 **가상의 AI 응답을 출력 모듈이 렌더링한 형태**입니다. 실제 API 실행 결과가 아닙니다.

```text
[AI Git Helper] Commit Message Draft
--------------------------------------------------------
docs: 안내 추가

- README 설명 추가
--------------------------------------------------------
AI 초안입니다. 실제 변경 사항과 테스트 방법을 최종 검토하세요.
```

PR 초안에는 `## Why`, `## What`, `## How to Test` 세 섹션이 반드시 포함됩니다. 제목이 너무 길거나, 필수 항목이 비어 있거나, 응답 형식이 맞지 않으면 출력 대신 오류를 알려 줍니다.

## API 호출과 비용 관리

- `commit` 또는 `pr` 한 번 실행할 때 API 호출은 최대 한 번입니다.
- Git 변경 사항이 없으면 API Key 확인과 API 호출 전에 종료합니다.
- `--show-prompt`는 API를 호출하지 않습니다.
- 자동 재시도는 하지 않습니다. timeout, 인증 실패, 429(요청 한도), 5xx 오류는 사용자가 이해할 수 있는 메시지로 종료합니다.
- 기본 HTTP timeout은 120초입니다. 큰 diff나 모델 처리 상황에서는 이 시간만큼 기다릴 수 있습니다.
- 모델별 비용과 사용량 제한은 API 제공자의 현재 정책을 확인해야 합니다.

## 사람이 검토해야 하는 이유

AI는 safe-mode로 전달된 Git 정보만 보고 초안을 만듭니다. diff가 생략되었을 수 있고, 코드의 의도·실제 테스트 결과·배포 영향까지 자동으로 확정할 수 없습니다. 특히 다음을 확인하세요.

- 제목이 변경 내용을 정확히 설명하는지
- Commit 본문 또는 PR의 Why/What이 사실인지
- How to Test가 실제로 가능한 절차인지
- 민감정보가 출력이나 전송 프롬프트에 남지 않았는지

## 테스트

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
python -m compileall -q .
```

현재 자동 테스트는 실제 HTTP 호출 없이 Git 수집, safe-mode, 프롬프트/스키마, API 오류 처리, 응답 검증, 터미널 출력, CLI 통합 흐름을 검증합니다. 상세 범위와 수동 점검 항목은 [테스트 통합검증 보고서](테스트_통합검증_보고서.md)를 참고하세요.

## 미션 요구사항 구현 체크리스트

- [x] Python 터미널 CLI에서 Git status와 staged·unstaged diff 수집
- [x] 변경이 없을 때 API 호출 없이 종료
- [x] 환경변수 기반 API Key 사용
- [x] Commit 제목 최대 72자 검증과 본문 출력
- [x] PR 제목 최대 80자 검증과 Why/What/How to Test 출력
- [x] 민감정보 마스킹·diff 제한을 위한 safe-mode
- [x] 모델, temperature, max tokens 옵션
- [x] API 오류와 JSON 형식 오류 안내
- [x] 실제 API 없이 반복 가능한 자동 테스트
- [x] 자동 `git commit`, `git push`, GitHub PR 생성 기능을 구현하지 않음

## 제출 증빙

미션 항목별 코드·테스트 근거는 [제출 증빙](제출_증빙.md)에 정리했습니다.
