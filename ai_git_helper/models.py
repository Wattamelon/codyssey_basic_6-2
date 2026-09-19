"""모듈 사이에서 사용하는 기본 데이터 구조."""

from dataclasses import dataclass  # 반복적인 데이터 보관용 클래스의 생성자·표현식을 자동 생성한다.


@dataclass(frozen=True)  # 생성 후 필드를 바꾸지 못하게 해 수집한 Git 스냅샷을 안전하게 유지한다.
class GitChanges:
    """Git에서 수집한 변경 정보의 기본 모델."""

    branch: str  # 수집 시점의 현재 브랜치 이름이다.
    status_text: str  # `git status --short`의 원문이다.
    changed_files: list[str]  # status에서 추출한 중복 없는 변경 파일 경로 목록이다.
    diff_text: str  # staged와 unstaged diff를 합친 AI 입력 후보 텍스트다.
    diff_line_count: int  # diff_text의 줄 수로, 프롬프트·진단에서 크기를 파악할 때 쓴다.

    @property  # 호출 괄호 없이 계산형 속성처럼 읽도록 만든다.
    def has_changes(self) -> bool:
        """변경 파일이 하나 이상인지 반환한다."""

        return bool(self.changed_files)  # 빈 목록이면 False, 하나 이상이면 True를 반환한다.


@dataclass(frozen=True)  # safe-mode가 만든 전송용 결과도 변경 불가능한 값 객체로 유지한다.
class SafetyResult:
    """safe-mode 적용 뒤 AI API로 보낼 diff 정보."""

    text: str  # 마스킹·길이 제한까지 적용된 최종 전송 텍스트다.
    masked_count: int  # 정규식으로 치환한 민감정보 패턴 수다.
    original_lines: int  # 안전 처리 전 diff의 전체 줄 수다.
    transmitted_lines: int  # 실제 diff 부분으로 전송되는 줄 수다.
    truncated: bool  # 줄 수 또는 문자 수 때문에 일부를 생략했는지 나타낸다.


@dataclass(frozen=True)  # 검증을 통과한 커밋 초안을 불변 데이터로 전달한다.
class CommitDraft:
    """검증된 커밋 메시지 초안."""

    title: str  # 한 줄 커밋 제목이다.
    body_lines: list[str]  # 출력 시 불릿으로 렌더링할 핵심 변경 사항들이다.


@dataclass(frozen=True)  # 검증을 통과한 PR 초안을 불변 데이터로 전달한다.
class PRDraft:
    """검증된 Pull Request 초안."""

    title: str  # 한 줄 PR 제목이다.
    why: list[str]  # 변경 배경을 설명하는 항목들이다.
    what: list[str]  # 실제 변경 내용을 설명하는 항목들이다.
    how_to_test: list[str]  # 사용자가 따라 할 검증 방법 항목들이다.
