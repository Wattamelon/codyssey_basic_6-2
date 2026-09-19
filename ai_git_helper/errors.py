"""프로그램에서 사용하는 사용자 정의 예외."""


class AIGitHelperError(Exception):  # 이 프로그램에서 예상하고 처리할 오류의 공통 부모다.
    """예상 가능한 프로그램 오류의 기본 예외."""


class GitCommandError(AIGitHelperError):  # git_service가 Git 실행·저장소 확인 실패를 CLI에 알릴 때 쓴다.
    """Git 명령 실행 오류."""


class APIRequestError(AIGitHelperError):  # api_client가 HTTP 요청·응답 형식 문제를 CLI에 알릴 때 쓴다.
    """AI API 요청 또는 응답 처리 오류."""


class ConfigurationError(AIGitHelperError):  # API 키처럼 실행 전 필요한 설정이 빠졌음을 표현한다.
    """필수 환경변수 등 설정 오류."""


class ValidationError(AIGitHelperError):  # validation이 AI JSON이 기대한 초안 규칙을 어길 때 쓴다.
    """AI 응답이 Commit/PR 초안 규칙을 만족하지 않을 때의 오류."""
