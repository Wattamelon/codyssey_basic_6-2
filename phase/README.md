# 6-2 미션 단계별 Codex 프롬프트

이 디렉터리의 프롬프트를 순서대로 Codex에 입력해 프로젝트를 단계적으로 구현한다.

## 사용 순서

1. `phase_01_project_scaffold.md`
2. `phase_02_git_collection.md`
3. `phase_03_safe_mode.md`
4. `phase_04_prompt_and_schema.md`
5. `phase_05_ai_api_client.md`
6. `phase_06_validation_and_output.md`
7. `phase_07_cli_integration.md`
8. `phase_08_tests.md`
9. `phase_09_readme_and_evidence.md`
10. `phase_10_final_qa.md`

각 단계가 끝난 뒤 Codex가 보고한 테스트 결과를 확인하고 다음 프롬프트를 실행한다. 테스트가 실패하면 다음 단계로 넘어가지 말고 해당 단계에서 수정한다.

## 공통 원칙

- 작업 디렉터리의 기존 파일과 사용자 변경을 먼저 확인한다.
- API Key와 실제 민감정보를 파일·로그·README·테스트에 기록하지 않는다.
- 실제 `git commit`, `git push`, GitHub PR 생성은 자동화하지 않는다.
- 각 단계는 해당 단계의 범위만 수정하고, 기존 동작을 불필요하게 재작성하지 않는다.
- 구현 후 관련 테스트와 문법 검사를 실행하고 결과를 요약한다.
- 미션 PDF의 요구사항과 이 프로젝트의 `기초과정_6주차_2단계_study.md`를 우선 근거로 사용한다.
- API Endpoint, 모델명, 요청·응답 형식은 사용하는 AI 서비스의 공식 문서를 확인한 뒤 구현한다.

## 목표 구조

```text
main.py
ai_git_helper/
  __init__.py
  cli.py
  errors.py
  models.py
  git_service.py
  safety.py
  prompts.py
  api_client.py
  validation.py
  output.py
tests/
README.md
requirements.txt
.env.example
.gitignore
```
