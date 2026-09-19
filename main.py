"""AI Git Helper CLI의 실행 진입점."""

from ai_git_helper.cli import main  # 실제 명령줄 처리 함수는 패키지의 cli 모듈에서 가져온다.


if __name__ == "__main__":  # 이 파일을 직접 실행했을 때만 아래 진입점을 실행한다.
    raise SystemExit(main())  # main의 반환 코드를 운영체제가 이해하는 프로세스 종료 코드로 전달한다.
