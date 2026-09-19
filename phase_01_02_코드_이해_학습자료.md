# 6-2 미션 Phase 01~02 코드 이해 학습자료

## 먼저 결론

현재 구현은 AI API를 만든 단계가 아니다. AI에게 전달할 **로컬 Git 변경 정보 수집기**를 만든 단계다.

~~~text
터미널 명령
  ↓
main.py
  ↓
cli.py의 parser가 명령 해석
  ↓
git_service.py가 로컬 git 실행
  ↓
GitChanges 객체에 결과 저장
~~~

현재 GitHub에서 정보를 가져오지 않는다. Python이 내 컴퓨터의 git 프로그램을 실행하고, git이 프로젝트의 .git 정보와 현재 파일을 비교한다.

## 1. 기초 용어

### Python 모듈

Python 파일 하나를 모듈이라고 부른다. 예를 들어 cli.py는 cli 모듈이다.

### import

다른 모듈의 기능을 현재 파일에서 사용할 수 있게 가져오는 문법이다.

~~~python
from ai_git_helper.cli import main
~~~

이 문장은 ai_git_helper 폴더 안 cli.py에서 main 함수를 가져온다는 뜻이다.

### 패키지

Python 파일을 기능별 폴더로 묶은 것이다. ai_git_helper 폴더에는 __init__.py가 있어 Python 패키지로 사용할 수 있다.

### 함수

특정 작업을 묶어 이름을 붙인 코드다.

~~~python
def get_current_branch(working_directory: Path) -> str:
~~~

get_current_branch는 함수 이름이고, working_directory는 입력값이며, -> str은 문자열을 반환할 것으로 표시한 타입 힌트다.

### 클래스와 객체

클래스는 데이터와 기능의 설계도이고 객체는 그 설계도로 만든 실제 값이다.

GitChanges는 Git 결과를 담는 설계도이고, collect_git_changes가 반환하는 GitChanges(...)가 실제 객체다.

### dataclass

데이터를 담는 클래스를 간결하게 만드는 Python 기능이다.

### property

함수처럼 작성하지만 객체의 값처럼 사용할 수 있게 하는 장식 기능이다.

~~~python
changes.has_changes
~~~

실제로는 has_changes 함수의 결과를 읽는다.

### 예외

정상 흐름을 계속할 수 없는 문제가 발생했을 때 전달되는 오류 객체다. 이 프로젝트에서는 GitCommandError처럼 오류 종류를 구분한다.

### CLI와 parser

CLI는 터미널에서 프로그램을 사용하는 방식이다. parser는 사용자가 입력한 명령과 옵션을 해석하는 코드다.

~~~bash
python main.py commit
~~~

parser는 command 값이 commit인지 pr인지 확인한다. parser 자체가 Git이나 GitHub를 읽는 것은 아니다.

### subprocess

subprocess는 Python 표준 모듈이다. Git 전용 모듈이 아니다. 운영체제에 설치된 외부 프로그램을 실행하고 그 결과를 Python으로 가져온다.

~~~text
Python
  ↓ subprocess.run()
운영체제의 git 프로그램
  ↓
Git이 .git과 현재 파일 비교
  ↓
명령 결과
  ↓
Python의 result.stdout
~~~

### Git repository와 GitHub

Git repository는 내 컴퓨터에 있는 Git 프로젝트다. GitHub는 Git repository를 인터넷에 저장하는 서비스다.

현재 코드는 GitHub API나 로그인 기능을 사용하지 않는다.

### working tree, staged, unstaged

working tree는 현재 파일 상태다. unstaged는 수정했지만 git add하지 않은 변경이고, staged는 git add한 변경이다.

~~~bash
git diff
git diff --cached
~~~

git diff는 unstaged, git diff --cached는 staged 변경을 보여 준다.

## 2. 파일별 역할

| 파일 | 역할 |
|---|---|
| main.py | 프로그램 실행 시작점 |
| cli.py | 터미널 명령 구조와 parser |
| models.py | Git 결과와 초안 데이터를 담는 구조 |
| errors.py | 오류 종류 정의 |
| git_service.py | 로컬 Git 실행과 결과 수집 |
| safety.py | 다음 단계에서 민감정보 보호 |
| prompts.py | 다음 단계에서 AI 프롬프트 작성 |
| api_client.py | 다음 단계에서 AI API 호출 |
| validation.py | 다음 단계에서 AI 결과 검증 |
| output.py | 검증된 Commit·PR 초안을 터미널 출력 문자열로 변환 |
| tests/test_scaffold.py | Phase 01~02 자동 테스트 |

## 3. 파일 간 호출 흐름

현재 실제로 연결된 호출은 다음과 같다.

~~~text
python main.py --help
  ↓
main.py의 main import
  ↓
cli.py의 main()
  ↓
build_parser()
  ↓
parser.parse_args()
  ↓
도움말 출력
~~~

Git 수집 함수는 현재 CLI에 연결하기 전 단계이므로 직접 호출하면 다음 흐름이 된다.

~~~text
collect_git_changes()
  ↓
ensure_git_repository()
  ↓
_run_git(["rev-parse", ...])
  ↓
운영체제의 git 실행 파일
  ↓
get_current_branch()
  ↓
_run_git(["branch", "--show-current"])
  ↓
_run_git(["status", "--short"])
  ↓
parse_changed_files()
  ↓
_run_git(["diff", ...])
  ↓
_run_git(["diff", "--cached", ...])
  ↓
GitChanges 객체 반환
~~~

## 4. main.py 한 줄씩

~~~python
from ai_git_helper.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
~~~

| 코드 | 의미 |
|---|---|
| from | 다른 모듈에서 이름을 가져온다 |
| ai_git_helper.cli | ai_git_helper 폴더의 cli.py |
| import main | cli.py의 main 함수를 가져온다 |
| if __name__ | 이 파일을 직접 실행했는지 확인한다 |
| main() | CLI 실행을 시작한다 |
| SystemExit | 반환한 숫자를 프로그램 종료 코드로 전달한다 |

입력과 결과:

~~~text
python main.py
  ↓
main.py 실행
  ↓
cli.main() 호출
  ↓
도움말 출력
~~~

## 5. cli.py 한 줄씩

### import 부분

~~~python
from __future__ import annotations
import argparse
from typing import Sequence
~~~

- future import: 타입 힌트 해석을 늦추는 Python 설정이다.
- argparse: Python 표준 모듈이며 터미널 명령을 해석한다.
- Sequence: 여러 문자열 입력을 표현하는 타입 힌트다.

argparse는 Git이나 GitHub를 읽지 않는다. 오직 사용자가 입력한 command와 option을 Python 값으로 바꾼다.

### build_parser 함수

~~~python
def build_parser() -> argparse.ArgumentParser:
~~~

parser를 만드는 함수다. 반환값은 argparse의 ArgumentParser 객체다.

~~~python
parser = argparse.ArgumentParser(
    prog="ai-git-helper",
    description="Git 변경 사항을 분석해 AI 기반 커밋 메시지와 Pull Request 초안을 생성하는 CLI입니다.",
)
~~~

프로그램 이름과 도움말 설명을 등록한다.

~~~python
parser.add_argument(
    "command",
    nargs="?",
    choices=("commit", "pr"),
    help="commit: 커밋 메시지 생성, pr: Pull Request 초안 생성",
)
~~~

- command: 사용자가 입력할 위치 인자 이름
- nargs="?": 현재 단계에서는 command를 생략할 수 있음
- choices: commit 또는 pr만 허용
- help: 도움말에 표시할 설명

### main 함수

~~~python
def main(arguments: Sequence[str] | None = None) -> int:
~~~

arguments가 없으면 실제 터미널 입력을 argparse가 읽는다. 테스트에서는 arguments에 목록을 직접 넣어 parser만 시험할 수 있다.

~~~python
parser = build_parser()
args = parser.parse_args(arguments)
~~~

parser를 만들고 입력을 해석한다.

예를 들어:

~~~python
args = parser.parse_args(["commit"])
~~~

결과는 개념적으로 다음과 같다.

~~~python
args.command == "commit"
~~~

~~~python
if args.command is None:
    parser.print_help()
    return 0
~~~

명령이 없으면 도움말을 출력하고 정상 종료한다.

~~~python
parser.error("아직 Git 수집과 AI API 기능이 구현되지 않았습니다.")
~~~

commit이나 pr을 인식하기는 하지만, 아직 실제 기능이 연결되지 않았으므로 오류를 보여 준다.

## 6. models.py 한 줄씩

~~~python
from dataclasses import dataclass
~~~

Python 표준 모듈 dataclasses에서 dataclass 기능을 가져온다.

~~~python
@dataclass(frozen=True)
class GitChanges:
~~~

Git 결과를 담는 클래스를 만든다. frozen=True이므로 만든 뒤 필드 변경을 제한한다.

~~~python
branch: str
status_text: str
changed_files: list[str]
diff_text: str
diff_line_count: int
~~~

GitChanges가 가질 데이터의 이름과 예상 타입이다.

~~~python
@property
def has_changes(self) -> bool:
    return bool(self.changed_files)
~~~

changed_files가 비어 있지 않으면 True, 비어 있으면 False를 반환한다.

이 값은 앞으로 다음 판단에 사용된다.

~~~text
변경 파일 없음
  ↓
has_changes = False
  ↓
AI API 호출하지 않고 종료
~~~

CommitDraft와 PRDraft는 다음 단계에서 AI가 만든 결과를 담기 위한 준비 모델이다.

## 7. errors.py

~~~python
class AIGitHelperError(Exception):
~~~

프로젝트 오류의 가장 기본이 되는 부모 클래스다.

~~~python
class GitCommandError(AIGitHelperError):
~~~

Git 명령 오류를 표현한다.

~~~python
class APIRequestError(AIGitHelperError):
~~~

AI API 요청이나 응답 오류를 표현한다.

~~~python
class ConfigurationError(AIGitHelperError):
~~~

환경변수 누락 같은 설정 오류를 표현한다.

오류를 종류별로 나누면 최종 CLI에서 다음처럼 사용자에게 알릴 수 있다.

~~~text
Git 오류 → GitCommandError
API 오류 → APIRequestError
설정 오류 → ConfigurationError
~~~

## 8. git_service.py 핵심

### import

~~~python
import subprocess
from pathlib import Path

from .errors import GitCommandError
from .models import GitChanges
~~~

- subprocess: Python 표준 모듈. 외부 git 실행 파일을 실행한다.
- Path: Python 표준 모듈. 폴더·파일 경로를 다룬다.
- .errors: 같은 패키지의 errors.py
- .models: 같은 패키지의 models.py

subprocess가 Git 정보를 직접 분석하는 것은 아니다. subprocess는 git을 실행하고 git의 출력을 가져온다. Git이 .git 정보와 파일을 비교한다.

### _run_git

~~~python
def _run_git(arguments: list[str], working_directory: Path) -> str:
~~~

Git 인자 목록과 실행 폴더를 받아 문자열을 반환한다.

~~~python
result = subprocess.run(
    ["git", *arguments],
    cwd=working_directory,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    check=False,
)
~~~

예를 들어 arguments가 ["status", "--short"]라면 실제 실행은 다음과 같다.

~~~bash
git status --short
~~~

- cwd: 어느 폴더에서 실행할지
- capture_output: stdout과 stderr를 Python으로 가져오기
- text: 결과를 문자열로 받기
- encoding: UTF-8 사용
- errors: 깨진 문자를 대체
- check=False: 종료 코드를 직접 확인

result.stdout에는 Git이 출력한 문자열이 들어간다.

~~~text
git status --short
  ↓
Git 출력
  ↓
result.stdout
~~~

return result.stdout는 그 문자열을 호출한 함수에 돌려준다.

### 오류 처리

Git이 설치되지 않으면 FileNotFoundError가 발생한다. 이를 GitCommandError로 바꿔 사용자가 이해할 수 있는 오류로 만든다.

Git 명령이 실패하면 result.returncode가 0이 아니다. 이때 stderr나 stdout에 있는 원인을 읽어 GitCommandError 메시지에 포함한다.

### ensure_git_repository

~~~bash
git rev-parse --is-inside-work-tree
~~~

결과가 true인지 검사한다. true가 아니면 현재 폴더가 Git repository가 아니라고 판단한다.

### get_current_branch

~~~bash
git branch --show-current
~~~

현재 브랜치 이름을 가져온다. detached HEAD에서는 빈 값이 나올 수 있으므로 (detached HEAD)라고 표시한다.

### parse_changed_files

~~~text
 M README.md
?? new file.py
R  old.py -> new.py
~~~

raw_line[3:]은 앞의 상태 문자 2개와 구분 공백을 제외한 부분이다. rename에는 화살표가 있으므로 오른쪽의 새 파일명을 사용한다.

### collect_git_changes

이 함수의 실행 순서는 다음과 같다.

~~~text
Git repository 확인
  ↓
브랜치 확인
  ↓
git status --short
  ↓
변경 파일 목록 추출
  ↓
git diff
  ↓
git diff --cached
  ↓
STAGED·UNSTAGED 헤더로 결합
  ↓
GitChanges 객체 반환
~~~

입력은 Path 객체다.

~~~python
collect_git_changes(Path("/project"))
~~~

반환값은 branch, status_text, changed_files, diff_text, diff_line_count를 가진 GitChanges 객체다.

## 9. 실제 실행 상황

### 상황 A: 도움말

입력:

~~~bash
python main.py --help
~~~

흐름:

~~~text
운영체제
  ↓ main.py
  ↓ cli.main()
  ↓ build_parser()
  ↓ parse_args()
  ↓ argparse가 도움말 출력
~~~

이 경우 Git을 실행하지 않는다.

### 상황 B: 변경 없는 Git 저장소에서 commit

입력:

~~~bash
python main.py commit
~~~

현재 Phase 02의 실제 흐름은 parser가 commit을 인식한 뒤 “아직 기능이 구현되지 않았다”는 오류를 출력하는 것이다.

아직 collect_git_changes가 cli.main에 연결되지 않았기 때문이다.

### 상황 C: Git 수집 함수 직접 실행

~~~python
changes = collect_git_changes(Path.cwd())
~~~

흐름:

~~~text
현재 폴더가 Git repository인지 확인
  ↓
브랜치 이름 확인
  ↓
status 실행
  ↓
파일 목록 파싱
  ↓
unstaged·staged diff 실행
  ↓
GitChanges 반환
~~~

### 상황 D: staged와 unstaged가 함께 있을 때

~~~bash
git add <FILE_NAME>
~~~

이후 다른 파일도 수정하면 git diff --cached에는 첫 파일이, git diff에는 두 번째 파일이 나타난다. 프로그램은 둘을 각각 수집해 헤더로 구분한다.

### 상황 E: Git repository가 아닌 폴더

Git 확인 명령이 true를 반환하지 않는다. GitCommandError가 발생한다.

## 10. 테스트 설명

tests/test_scaffold.py는 unittest를 사용한다.

- assertEqual: 두 값이 같은지 확인
- assertTrue: 값이 참인지 확인
- assertFalse: 값이 거짓인지 확인
- assertIn: 어떤 값이 목록·문자열 안에 있는지 확인
- assertRaises: 특정 오류가 발생하는지 확인

tempfile.TemporaryDirectory는 테스트 전용 임시 폴더를 만들고 테스트 후 삭제한다.

테스트에서 임시 Git repository를 만드는 이유는 현재 프로젝트의 실제 Git 상태를 망가뜨리지 않기 위해서다.

현재 테스트는 다음을 검증한다.

1. commit과 pr 명령을 parser가 인식
2. 수정·신규·rename 파일 파싱
3. Git repository가 아닌 폴더 오류
4. staged·unstaged diff 수집
5. 변경 없음 판별
6. detached HEAD 표시

테스트가 없는 영역도 있다.

- 실제 AI API 호출
- 실제 HTTP 응답
- safe-mode
- 최종 CLI와 Git 수집의 연결
- JSON 응답 검증
- 최종 터미널 출력

## 11. 구현됨과 예정 기능

| 상태 | 기능 | 관련 파일 |
|---|---|---|
| 구현됨 | CLI 명령 구조 | cli.py |
| 구현됨 | Git 저장소 확인 | git_service.py |
| 구현됨 | status·diff 수집 | git_service.py |
| 구현됨 | 오류 종류 골격 | errors.py |
| 구현됨 | 데이터 모델 골격 | models.py |
| 예정 | 민감정보 마스킹 | safety.py |
| 예정 | AI 프롬프트 | prompts.py |
| 예정 | AI API 호출 | api_client.py |
| 예정 | 결과 검증 | validation.py |
| 구현됨 | 최종 출력 | output.py |
| 예정 | 전체 CLI 연결 | cli.py |

## 12. 이번 단계에서 기억할 것

1. parser는 터미널 입력을 해석한다.
2. subprocess는 Git 전용 기능이 아니라 외부 프로그램 실행 기능이다.
3. Git이 .git과 현재 파일을 비교한다.
4. Python은 Git의 결과를 result.stdout로 받는다.
5. git status는 무엇이 변경됐는지 알려 준다.
6. git diff는 어떻게 변경됐는지 알려 준다.
7. GitChanges는 수집한 정보를 하나로 묶은 객체다.
8. 현재는 GitHub 정보를 읽지 않는다.

## 이해 확인 질문

1. parser와 subprocess의 역할은 어떻게 다른가?
2. subprocess가 Git 정보를 직접 분석하지 않는다는 말은 무슨 뜻인가?
3. git diff와 git diff --cached의 차이는 무엇인가?
4. GitChanges 객체가 필요한 이유는 무엇인가?
5. Python이 Git 명령의 결과를 어느 값에서 읽는가?

## 직접 실행해 볼 명령

~~~bash
python main.py --help
python -m unittest discover -s tests -v
python -m compileall -q .
git --version
git status --short
~~~

다음 단계는 safety.py에 민감정보 마스킹과 diff 크기 제한을 추가하는 Phase 03이다.
