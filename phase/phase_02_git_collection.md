# Phase 02 - Git 변경 사항 수집 구현

## 역할

너는 Python subprocess와 Git 자동화를 잘 아는 개발자다.

## 목표

Git 저장소에서 현재 브랜치, `git status`, staged·unstaged `git diff`를 안전하게 수집하는 기능을 구현한다.

## 작업

1. Git 저장소 내부인지 확인한다.
2. 현재 브랜치를 수집한다. detached HEAD도 오류 없이 표시한다.
3. `git status --short`를 수집한다.
4. 변경 파일 목록을 파싱한다.
5. `git diff --no-ext-diff --unified=3`와 `git diff --cached --no-ext-diff --unified=3`를 수집한다.
6. staged와 unstaged 결과를 구분해 하나의 모델로 반환한다.
7. 변경 파일이 없으면 `has_changes`가 false가 되도록 한다.
8. Git 실행 파일 없음, Git 저장소 아님, Git 명령 실패를 사용자 정의 예외로 처리한다.
9. `shell=True`를 사용하지 않는다.

## 주의사항

- untracked 파일은 status에는 나타나지만 일반 diff에는 내용이 없을 수 있다. 파일명만으로도 컨텍스트를 만들 수 있게 한다.
- 공백·특수문자·rename 파일명을 고려한다.
- 실제 commit·push는 절대 수행하지 않는다.

## 테스트

다음 단위 테스트를 작성한다.

- 수정·신규·rename 파일 파싱
- 빈 status 처리
- Git 명령 실패 처리
- staged와 unstaged diff 결합
- detached HEAD 표시

## 완료 조건

- 실제 Git 저장소에서 변경 상태를 읽을 수 있다.
- 변경 사항이 없을 때 정확히 판별한다.
- 테스트가 통과한다.

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

마지막에 변경 파일, 테스트 결과, 알려진 제한을 보고한다.

