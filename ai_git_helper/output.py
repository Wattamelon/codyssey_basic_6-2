"""검증된 초안을 터미널에서 읽고 복사하기 쉬운 형식으로 렌더링한다."""

from __future__ import annotations  # 최신 타입 표기를 즉시 평가하지 않아 순환 참조를 피한다.

from .models import CommitDraft, PRDraft  # validation이 만든 안전한 초안 데이터 타입을 받는다.


SEPARATOR = "-" * 56  # 터미널 출력 영역을 구분하는 고정 길이 선이다.
FINAL_REVIEW_MESSAGE = "AI 초안입니다. 실제 변경 사항과 테스트 방법을 최종 검토하세요."  # AI 결과를 그대로 확정하지 말라는 마지막 안내다.


def _format_bullets(lines: list[str]) -> str:  # 문자열 항목 목록을 Markdown 불릿 목록으로 바꾼다.
    return "\n".join(f"- {line}" for line in lines)  # 각 항목 앞에 '- '를 붙이고 줄바꿈으로 연결한다.


def format_commit_draft(draft: CommitDraft) -> str:
    """Commit 제목·본문을 출력용 문자열로 만든다."""

    return "\n".join(  # 각 출력 조각을 줄바꿈 하나로 연결해 하나의 터미널 문자열로 만든다.
        (
            "[AI Git Helper] Commit Message Draft",  # 사람이 알아볼 수 있는 출력 제목이다.
            SEPARATOR,  # 제목과 초안 본문을 구분한다.
            draft.title,  # validation을 통과한 커밋 제목을 출력한다.
            "",  # 제목과 본문 불릿 사이에 빈 줄을 둔다.
            _format_bullets(draft.body_lines),  # 본문 항목을 불릿 목록으로 출력한다.
            SEPARATOR,  # 초안과 주의 문구를 구분한다.
            FINAL_REVIEW_MESSAGE,  # 최종 검토 책임을 사용자에게 알려 준다.
        )
    )


def format_pr_draft(draft: PRDraft) -> str:
    """PR 제목과 필수 Why·What·How to Test 섹션을 출력용 문자열로 만든다."""

    return "\n".join(  # PR의 여러 섹션을 하나의 출력 문자열로 조립한다.
        (
            "[AI Git Helper] Pull Request Draft",  # 사람이 알아볼 수 있는 출력 제목이다.
            SEPARATOR,  # 제목과 PR 초안 내용을 구분한다.
            draft.title,  # 검증된 PR 제목을 출력한다.
            "",  # 제목과 첫 섹션 사이에 빈 줄을 둔다.
            "## Why",  # 변경 배경 섹션의 Markdown 제목이다.
            _format_bullets(draft.why),  # 변경 배경 항목들을 출력한다.
            "",  # 섹션을 시각적으로 분리한다.
            "## What",  # 변경 내용 섹션의 Markdown 제목이다.
            _format_bullets(draft.what),  # 변경 내용 항목들을 출력한다.
            "",  # 섹션을 시각적으로 분리한다.
            "## How to Test",  # 검증 방법 섹션의 Markdown 제목이다.
            _format_bullets(draft.how_to_test),  # 사용자가 수행할 검증 방법을 출력한다.
            SEPARATOR,  # 초안과 주의 문구를 구분한다.
            FINAL_REVIEW_MESSAGE,  # AI 결과를 검토해야 한다는 안내다.
        )
    )
