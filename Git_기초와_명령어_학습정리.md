# Git 기초와 명령어 학습 정리

이 문서는 Git을 처음 배우는 사람을 위한 학습 자료다. 6-2 미션에서 필요한 Git 변경 사항 수집과 커밋 메시지 생성 흐름을 이해하는 데 초점을 둔다.

## 1. 핵심 결론

Git은 내 컴퓨터 안에서 파일 변경 이력을 기록하고 관리하는 프로그램이다.

GitHub는 Git 저장소를 인터넷에 올려 두고 공유하고 협업하게 해 주는 서비스다.

~~~text
Git      = 내 컴퓨터의 변경 이력 관리 도구
GitHub   = 인터넷에 있는 Git 저장소 서비스
~~~

## 2. Git을 쓰는 이유

파일을 수정하다 보면 이전 상태로 돌아가고 싶거나, 어떤 변경을 했는지 기록하고 싶거나, 다른 사람의 변경과 합치고 싶을 때가 있다.

Git은 변경 내용을 commit이라는 단위로 저장한다.

~~~text
처음 코드
  ↓ 수정
commit 1: 로그인 화면 추가
  ↓ 수정
commit 2: 로그인 오류 처리
  ↓ 수정
commit 3: README 보완
~~~

### 쉬운 비유

Git은 게임 저장 슬롯과 비슷하다.

- 파일 수정: 게임 진행 중
- git add: 이번 저장에 넣을 내용을 고르기
- git commit: 고른 내용을 저장하기
- git log: 저장 기록 보기
- git restore: 저장하지 않은 변경 되돌리기
- git switch: 다른 작업 흐름으로 이동하기

## 3. Git과 GitHub 차이

| 구분 | Git | GitHub |
|---|---|---|
| 위치 | 내 컴퓨터 | 인터넷 서버 |
| 역할 | 변경 이력 관리 | 보관, 공유, 협업 |
| 인터넷 필요 | 기본 작업은 불필요 | push, pull에 필요 |
| 대표 명령 | status, add, commit, diff | push, pull, clone |
| 계정 필요 | 필요 없음 | 보통 필요 |

현재 6-2 미션 도구가 읽는 것은 GitHub 정보가 아니라 로컬 Git 정보다.

~~~text
Python 프로그램
  ↓
내 컴퓨터의 git status, git diff 실행
  ↓
로컬 프로젝트의 Git 관리 정보와 현재 파일 비교
  ↓
변경 결과를 Python으로 전달
~~~

이 미션 도구는 GitHub에 자동으로 push하거나 PR을 만들지 않는다. 커밋 메시지와 PR 본문 초안을 출력하는 것이 목표다.

## 4. Git 저장소란?

Git 저장소 또는 repository는 Git이 이력 관리를 하는 프로젝트 폴더다.

~~~text
my-project/
├── Git 관리 폴더
├── main.py
├── README.md
└── requirements.txt
~~~

Git 관리 폴더에는 커밋 이력, 브랜치 정보, 설정 등이 저장된다. 이 폴더는 직접 삭제하거나 수정하지 않는 것이 좋다.

### 새 저장소 만들기

~~~bash
git init
~~~

### 기존 저장소 복제하기

~~~bash
git clone <REPOSITORY_URL>
~~~

## 5. Git이 파일을 보는 네 가지 상태

~~~text
작업 폴더
  ↓ git add
Staging Area
  ↓ git commit
Local Repository
  ↓ git push
Remote Repository, 예: GitHub
~~~

### Working Tree 또는 작업 폴더

현재 내가 파일을 열고 수정하는 실제 프로젝트 폴더다.

### Untracked

새 파일을 만들었지만 Git이 아직 추적하지 않는 상태다.

~~~text
?? new_file.py
~~~

### Modified 또는 Unstaged

Git이 이미 알고 있는 파일을 수정했지만, 다음 commit에 넣겠다고 아직 선택하지 않은 상태다.

~~~text
 M main.py
~~~

이 상태의 변경은 다음 명령으로 확인한다.

~~~bash
git diff
~~~

### Staged

다음 commit에 넣겠다고 선택한 변경이다.

~~~bash
git add main.py
~~~

이 상태의 변경은 다음 명령으로 확인한다.

~~~bash
git diff --cached
~~~

### Committed

staging area에 있는 변경을 하나의 이력으로 저장한 상태다.

~~~bash
git commit -m "feat: Git 변경 사항 수집 추가"
~~~

## 6. 상태 흐름 한 장으로 보기

~~~text
새 파일 생성
  ↓
Untracked
  ↓ git add <FILE_NAME>
Staged
  ↓ git commit
Committed

기존 파일 수정
  ↓
Modified, Unstaged
  ↓ git add <FILE_NAME>
Staged
  ↓ git commit
Committed
~~~

같은 파일도 일부 변경은 staged이고, 그 뒤에 추가한 수정은 unstaged일 수 있다.

## 7. git status

~~~bash
git status
~~~

현재 저장소 상태를 사람이 읽기 쉬운 긴 형식으로 보여 준다.

짧은 목록 확인과 자동화에는 다음을 자주 쓴다.

~~~bash
git status --short
~~~

예시:

~~~text
 M main.py
M  README.md
MM config.py
?? new_file.py
A  docs/guide.md
D  old_file.py
R  old_name.py -> new_name.py
~~~

short status의 앞 두 칸은 다음 뜻이다.

~~~text
XY 파일명
X: Staging Area 상태
Y: Working Tree 상태
~~~

| 예시 | 의미 |
|---|---|
| 공백 M main.py | main.py 수정, 아직 add하지 않음 |
| M 공백 README.md | README 수정 내용을 add함 |
| MM config.py | 이전 수정은 add했고, 그 뒤 또 수정함 |
| ?? new_file.py | Git이 아직 추적하지 않는 새 파일 |
| A 공백 guide.md | 새 파일을 add함 |
| D 공백 old_file.py | 삭제를 add함 |
| R 공백 old.py -> new.py | 이름 변경을 add함 |

### 6-2 미션에서 필요한 이유

AI에게 변경 내용을 설명하려면 먼저 어떤 파일이 바뀌었는지 알아야 한다.

~~~text
git status --short
  ↓
변경 파일 목록
  ↓
AI 프롬프트에 파일 맥락으로 전달
~~~

## 8. git diff

### 아직 add하지 않은 변경 보기

~~~bash
git diff
~~~

현재 작업 폴더와 staging area를 비교한다. 즉, unstaged 변경을 보여 준다.

~~~diff
- print("old message")
+ print("new message")
~~~

- 기호는 삭제된 줄이다.
- 더하기 기호는 추가된 줄이다.
- diff의 더하기와 빼기는 Python 코드 연산자가 아니다.

### add한 변경 보기

~~~bash
git diff --cached
~~~

또는 아래 명령도 같은 의미다.

~~~bash
git diff --staged
~~~

staging area와 마지막 commit을 비교한다.

### 변경량만 보기

~~~bash
git diff --stat
git diff --cached --stat
~~~

파일별 추가와 삭제 줄 수를 요약한다.

### 주변 문맥 줄 수 지정

~~~bash
git diff --unified=3
~~~

변경된 줄 주변의 문맥을 3줄 보여 준다. 6-2 미션 코드에서는 AI가 변경 맥락을 이해하도록 이 옵션을 사용한다.

### 외부 diff 도구 사용 안 하기

~~~bash
git diff --no-ext-diff
~~~

개인 설정의 외부 diff 도구 대신 Git 기본 결과를 사용한다. 자동화 프로그램이 일정한 형식의 출력을 받기 위해 유용하다.

## 9. git add

~~~bash
git add main.py
~~~

main.py의 현재 변경을 staging area에 올린다.

여러 파일을 선택할 수 있다.

~~~bash
git add main.py README.md
~~~

현재 폴더 아래 변경을 넓게 선택할 수도 있다.

~~~bash
git add .
~~~

주의: git add .은 의도하지 않은 파일도 포함할 수 있다. 특히 환경변수 파일이나 임시 파일이 포함되지 않았는지 status와 diff로 먼저 확인한다.

### 추천 순서

~~~bash
git status --short
git diff
git add <FILE_NAME>
git diff --cached
~~~

## 10. git commit

~~~bash
git commit -m "feat: Git 변경 사항 수집 기능 추가"
~~~

git commit은 staging area에 있는 변경만 저장한다.

일반적인 순서:

~~~text
파일 수정
  ↓
git diff로 변경 확인
  ↓
git add로 선택
  ↓
git diff --cached로 최종 확인
  ↓
git commit으로 저장
~~~

### 좋은 커밋 제목

~~~text
좋은 예:
feat: Git 변경 사항 수집 기능 추가
fix: API Key 누락 오류 메시지 개선
docs: README 실행 방법 보완

피할 예:
수정
변경함
작업 완료
~~~

6-2 미션은 이런 커밋 제목과 본문 초안을 AI로 생성하는 도구를 만드는 과제다.

## 11. git log

~~~bash
git log
~~~

최근 commit부터 이력을 보여 준다.

짧은 형식:

~~~bash
git log --oneline
~~~

예시:

~~~text
a1b2c3d feat: Git 변경 사항 수집 기능 추가
d4e5f6g docs: README 추가
~~~

왼쪽 문자열은 commit hash다. 특정 commit을 가리키는 고유 식별자다.

## 12. 브랜치

브랜치는 하나의 작업 흐름을 다른 작업과 분리하는 기능이다.

~~~text
main
  ├── feature/git-collector
  └── fix/readme-typo
~~~

main을 안정적인 기본 작업선이라고 생각하면 feature 브랜치는 새 기능을 안전하게 실험하는 별도 작업선이다.

### 현재 브랜치 확인

~~~bash
git branch --show-current
~~~

### 브랜치 목록

~~~bash
git branch
~~~

### 새 브랜치를 만들고 이동

~~~bash
git switch -c feature/git-collector
~~~

### 기존 브랜치로 이동

~~~bash
git switch main
~~~

### detached HEAD

브랜치가 아닌 특정 commit을 직접 가리키는 상태다. 브랜치 이름이 비어 있을 수 있다.

6-2 프로젝트의 Git 수집 코드는 이 경우 빈 값 대신 (detached HEAD)를 표시한다.

## 13. 되돌리기

되돌리기는 무엇을 되돌리는지 먼저 구분해야 한다.

### 작업 폴더의 수정 취소

아직 add하지 않은 특정 파일 변경을 마지막 commit 상태로 되돌린다.

~~~bash
git restore <FILE_NAME>
~~~

주의: 수정한 내용이 사라질 수 있다. 먼저 git diff를 확인한다.

### staging area에서 내리기

add한 파일을 다시 unstaged로 만든다.

~~~bash
git restore --staged <FILE_NAME>
~~~

파일의 수정 내용은 사라지지 않고 staging area에서만 내려간다.

### 마지막 commit 메시지 바꾸기

아직 push하지 않은 마지막 commit의 메시지를 고친다.

~~~bash
git commit --amend -m "새 커밋 메시지"
~~~

이미 공유한 commit을 amend하면 협업자에게 혼란을 줄 수 있다.

### 특히 조심할 명령

~~~bash
git reset --hard
~~~

현재 학습 단계에서는 실행하지 않는 것을 권장한다. 작업 내용을 잃을 수 있다.

## 14. .gitignore

.gitignore는 Git에게 특정 파일이나 폴더를 추적하지 말라고 알려 주는 파일이다.

예시:

~~~text
.venv/
__pycache__/
.env
.DS_Store
~~~

### 왜 필요한가?

- 가상환경은 다른 사람이 다시 만들 수 있다.
- Python 캐시는 자동 생성된다.
- 환경변수 파일에는 API Key가 들어갈 수 있다.
- 운영체제 임시 파일은 프로젝트 결과물이 아니다.

중요: 이미 Git이 추적 중인 파일은 .gitignore에 추가해도 자동으로 추적이 멈추지 않는다.

## 15. 원격 저장소와 GitHub

원격 저장소는 내 컴퓨터 밖에 있는 Git 저장소다. GitHub가 대표적이다.

### 원격 주소 확인

~~~bash
git remote -v
~~~

### 원격 저장소로 올리기

~~~bash
git push origin main
~~~

### 원격 변경 가져오기

~~~bash
git pull origin main
~~~

### 복제하기

~~~bash
git clone <REPOSITORY_URL>
~~~

6-2 미션에서는 결과물을 GitHub에 push해야 하지만, 프로그램 자체가 git push를 자동으로 실행할 필요는 없다. 사용자가 검토 후 직접 push하는 방식이 미션 범위에 맞다.

## 16. 6-2 미션과 Git 연결

| 미션에서 필요한 것 | Git 명령 또는 개념 | 프로그램에서 할 일 |
|---|---|---|
| Git 저장소 여부 | git rev-parse --is-inside-work-tree | 실행 위치 확인 |
| 현재 브랜치 | git branch --show-current | PR 초안 맥락 제공 |
| 변경 파일 목록 | git status --short | AI에 파일 목록 제공 |
| unstaged 변경 | git diff | 아직 add하지 않은 코드 수집 |
| staged 변경 | git diff --cached | add한 코드 수집 |
| 변경 없음 | status 결과가 비어 있음 | API 호출 없이 종료 |
| 안전한 적용 | add, diff --cached, commit | 사용자가 결과 검토 후 직접 적용 |

## 17. Python 프로젝트가 Git을 읽는 방식

현재 구현한 git_service.py는 Python의 subprocess를 사용한다.

~~~python
result = subprocess.run(
    ["git", "status", "--short"],
    cwd=working_directory,
    capture_output=True,
    text=True,
)
~~~

이 코드는 터미널에서 다음 명령을 실행하는 것과 같다.

~~~bash
git status --short
~~~

역할 구분:

~~~text
subprocess
  = Python에서 외부 프로그램을 실행하는 도구

git
  = 실제로 Git 관리 정보와 현재 파일을 비교하는 프로그램

result.stdout
  = git이 출력한 결과를 Python 문자열로 받은 값
~~~

subprocess가 Git 정보를 직접 분석하는 것이 아니다. subprocess는 운영체제에게 git 프로그램 실행을 요청하고, Git이 출력한 결과를 가져온다.

## 18. 안전한 실습

별도의 연습 폴더에서 실행하는 것을 추천한다.

~~~bash
mkdir git-practice
cd git-practice
git init
~~~

파일을 하나 만든다.

~~~bash
echo "hello" > hello.txt
git status --short
~~~

?? hello.txt가 보이면 새 파일이지만 Git이 아직 추적하지 않는 상태다.

다음 순서로 진행한다.

~~~bash
git add hello.txt
git status --short
git commit -m "docs: hello 파일 추가"
git log --oneline
~~~

이후 파일을 수정한다.

~~~bash
echo "second line" >> hello.txt
git status --short
git diff
git add hello.txt
git diff --cached
git commit -m "docs: hello 내용 추가"
~~~

## 19. 자주 발생하는 상황

### Git 저장소가 아니라는 오류

증상:

~~~text
fatal: not a git repository
~~~

확인:

~~~bash
pwd
git rev-parse --is-inside-work-tree
~~~

해결: Git 프로젝트 폴더로 이동하거나, 새 프로젝트라면 git init을 실행한다.

### 변경했는데 git diff가 비어 있음

가능한 이유:

- 변경을 이미 git add했다.
- 파일이 .gitignore에 들어 있다.
- 파일을 저장하지 않았다.

확인:

~~~bash
git status --short
git diff --cached
~~~

### add한 내용을 취소하고 싶음

~~~bash
git restore --staged <FILE_NAME>
~~~

### API Key를 실수로 add한 것 같음

1. git diff --cached로 실제 포함 여부를 확인한다.
2. 아직 commit 전이면 git restore --staged로 staging area에서 제거한다.
3. .env를 .gitignore에 추가한다.
4. Key가 외부에 노출되었다면 해당 Key를 폐기하고 새 Key를 발급받는다.

## 20. 암기용 초압축 정리

~~~text
Git = 내 컴퓨터의 변경 이력 관리
GitHub = 인터넷상의 Git 저장소 서비스

status = 무엇이 바뀌었나
diff = 어떻게 바뀌었나
add = 다음 commit에 넣을 변경 선택
commit = 선택한 변경을 이력으로 저장
log = 저장 이력 확인

unstaged = 수정했지만 add하지 않음
staged = add했고 다음 commit에 포함될 예정

git diff = unstaged 변경
git diff --cached = staged 변경

branch = 분리된 작업 흐름
remote = 내 컴퓨터 밖의 저장소
push = 원격 저장소에 올리기
pull = 원격 변경 가져오기
~~~

## 21. 이해 확인 질문

1. Git과 GitHub의 역할 차이는 무엇인가?
2. git status와 git diff는 각각 무엇을 보여 주는가?
3. unstaged와 staged의 차이는 무엇인가?
4. git add는 파일을 저장하는 명령인가, 다음 commit에 넣을 변경을 선택하는 명령인가?
5. git diff와 git diff --cached는 무엇이 다른가?
6. commit 전에 git diff --cached를 확인하는 이유는 무엇인가?
7. subprocess와 git 프로그램은 어떤 역할이 다른가?
8. 6-2 미션 도구가 GitHub가 아니라 로컬 Git 정보를 읽는 이유는 무엇인가?
9. .gitignore에 .env를 넣는 이유는 무엇인가?
10. 변경 사항이 없을 때 AI API를 호출하지 않아야 하는 이유는 무엇인가?

## 22. 다음 공부 순서

1. 이 문서의 상태 흐름과 status, diff를 직접 실습한다.
2. 현재 프로젝트의 git_service.py를 다시 읽는다.
3. Phase 03의 safe-mode를 진행한다.
4. 이후 Python의 subprocess와 환경변수 개념을 더 깊게 공부한다.

