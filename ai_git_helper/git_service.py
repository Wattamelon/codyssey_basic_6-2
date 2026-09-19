"""Git 저장소에서 변경 상태와 diff를 수집한다."""

from __future__ import annotations  # 타입 표기의 즉시 평가를 미뤄 모듈 로딩을 단순하게 한다.

import subprocess  # 외부 git 실행 파일을 자식 프로세스로 실행한다.
from pathlib import Path  # 운영체제별 경로를 문자열 대신 객체로 다룬다.

from .errors import GitCommandError  # Git 관련 실패를 CLI가 공통 방식으로 처리하게 한다.
from .models import GitChanges  # 수집한 값의 모듈 간 전달 형식이다.


def _run_git(arguments: list[str], working_directory: Path) -> str:
    """Git 명령을 실행하고 표준 출력을 반환한다."""

    try:  # 실행 파일 자체가 없거나 OS가 실행을 막는 오류를 별도로 번역한다.
        result = subprocess.run(  # Git 명령이 끝날 때까지 실행하고 결과를 받는다.
            ["git", *arguments],  # 예: ["git", "status", "--short"] 형태의 안전한 인자 목록이다.
            cwd=working_directory,  # 호출 위치가 아닌 지정된 저장소에서 Git을 실행한다.
            capture_output=True,  # 표준 출력과 오류 출력을 모두 결과 객체에 보관한다.
            text=True,  # 바이트가 아닌 문자열로 출력을 받는다.
            encoding="utf-8",  # Git 출력 해석에 사용할 문자 인코딩이다.
            errors="replace",  # 해석 불가 문자는 예외 대신 대체 문자로 바꾼다.
            check=False,  # 반환 코드는 직접 읽어 더 친절한 오류로 바꾼다.
        )
    except FileNotFoundError as error:
        raise GitCommandError(
            "Git 실행 파일을 찾을 수 없습니다. Git 설치를 확인하세요."
        ) from error
    except OSError as error:
        raise GitCommandError(
            f"Git 명령을 실행할 수 없습니다: {error}"
        ) from error

    if result.returncode != 0:  # Git이 0 이외의 실패 코드를 반환했는지 확인한다.
        detail = result.stderr.strip() or result.stdout.strip() or "알 수 없는 Git 오류"  # 오류 출력, 보조 출력, 기본 문구 순으로 상세 이유를 고른다.
        command = " ".join(["git", *arguments])  # 사용자에게 보여 줄 명령 모양을 만든다.
        raise GitCommandError(f"{command} 명령 실행에 실패했습니다: {detail}")  # 저수준 결과를 도메인 오류로 변환한다.

    return result.stdout  # 성공했을 때만 표준 출력 원문을 호출자에게 준다.


def ensure_git_repository(working_directory: Path) -> None:
    """작업 위치가 Git work tree 안인지 확인한다."""

    output = _run_git(  # Git의 저장소 내부 여부 확인 명령을 실행한다.
        ["rev-parse", "--is-inside-work-tree"],
        working_directory,
    ).strip()
    if output != "true":  # Git이 work tree 내부라고 명확히 답하지 않은 경우다.
        raise GitCommandError(
            "현재 디렉터리는 Git 리포지토리가 아닙니다."
        )


def get_current_branch(working_directory: Path) -> str:
    """현재 브랜치 이름을 반환하고 detached HEAD를 표시한다."""

    branch = _run_git(  # detached HEAD에서는 빈 문자열을 내는 현재 브랜치 조회 명령을 실행한다.
        ["branch", "--show-current"],
        working_directory,
    ).strip()
    return branch or "(detached HEAD)"  # 빈 브랜치명 대신 사용자가 이해할 수 있는 상태명을 반환한다.


def parse_changed_files(status_text: str) -> list[str]:
    """porcelain short status에서 변경 파일 경로를 추출한다."""

    changed_files: list[str] = []  # 발견 순서를 유지하면서 중복을 제거할 결과 목록이다.
    for raw_line in status_text.splitlines():  # porcelain 출력의 각 파일 상태 행을 순회한다.
        if len(raw_line) < 4:  # XY 상태 두 글자와 공백·경로가 없는 비정상 행은 건너뛴다.
            continue

        file_path = raw_line[3:].strip()  # 앞의 두 상태 문자와 공백을 제외해 경로 부분만 얻는다.
        if " -> " in file_path:  # Git이 이름 변경을 'old -> new' 형식으로 표현했는지 확인한다.
            file_path = file_path.rsplit(" -> ", maxsplit=1)[1].strip()  # AI에는 최종 새 경로만 전달한다.

        # Git이 따옴표로 감싼 경로는 바깥 따옴표만 제거한다.
        if len(file_path) >= 2 and file_path[0] == file_path[-1] == '"':  # 공백·특수문자 때문에 Git이 경로를 인용했는지 확인한다.
            file_path = file_path[1:-1]  # 바깥 큰따옴표만 제거한다.

        if file_path and file_path not in changed_files:  # 빈 경로와 이미 추가한 경로는 제외한다.
            changed_files.append(file_path)  # 최초 등장 순서를 보존해 결과에 추가한다.

    return changed_files  # prompts가 파일 목록을 만들 때 사용할 경로 목록을 반환한다.


def collect_git_changes(working_directory: Path) -> GitChanges:
    """현재 브랜치와 status, staged·unstaged diff를 수집한다."""

    ensure_git_repository(working_directory)  # 이후 명령 전에 현재 위치가 유효한 Git 저장소인지 보장한다.

    branch = get_current_branch(working_directory)  # 프롬프트에 포함할 현재 브랜치를 수집한다.
    status_text = _run_git(  # 변경 파일을 가장 안정적인 porcelain 짧은 형식으로 가져온다.
        ["status", "--short"],
        working_directory,
    ).rstrip("\r\n")
    changed_files = parse_changed_files(status_text)  # 상태 원문에서 사람·AI가 읽기 좋은 경로 목록을 추출한다.

    unstaged_diff = _run_git(  # 아직 staging 하지 않은 작업 트리 변경을 수집한다.
        ["diff", "--no-ext-diff", "--unified=3"],
        working_directory,
    ).strip()
    staged_diff = _run_git(  # 이미 staging 된 인덱스 변경을 수집한다.
        ["diff", "--cached", "--no-ext-diff", "--unified=3"],
        working_directory,
    ).strip()

    sections: list[str] = []  # 두 종류의 diff를 구분 표식과 함께 모을 리스트다.
    if staged_diff:  # staged 변경이 있을 때만 빈 섹션을 만들지 않는다.
        sections.append(f"=== STAGED DIFF ===\n{staged_diff}")  # AI가 변경 상태를 구별하도록 표제를 붙인다.
    if unstaged_diff:  # unstaged 변경이 있을 때만 빈 섹션을 만들지 않는다.
        sections.append(f"=== UNSTAGED DIFF ===\n{unstaged_diff}")  # AI가 변경 상태를 구별하도록 표제를 붙인다.

    diff_text = "\n\n".join(sections)  # 섹션 사이에 빈 줄을 둔 단일 diff 텍스트를 만든다.
    return GitChanges(  # cli·safety·prompts가 공유할 불변 수집 결과를 생성한다.
        branch=branch,
        status_text=status_text,
        changed_files=changed_files,
        diff_text=diff_text,
        diff_line_count=len(diff_text.splitlines()) if diff_text else 0,  # 빈 diff는 0으로, 그 외에는 실제 줄 수를 저장한다.
    )
