# temperature와 max-tokens 실행 예제

이 파일은 `ai-git-helper`가 분석할 Git 변경 사항을 만들고, `--temperature`와
`--max-tokens` 값을 바꿔 실행하는 연습용 안내다.

## 먼저 알아둘 점

- 이 도구는 **Git 저장소 안에서만** 실행할 수 있다.
- API를 실제로 호출하려면 `GEMINI_API_KEY` 환경변수가 필요하다.
- 처음에는 `--show-prompt`를 사용하면 API 호출·비용 발생 없이 프롬프트만 확인할 수 있다.
- `temperature`는 응답의 다양성 정도이고, `max-tokens`는 AI 응답의 최대 길이다.

## 1. 예제 변경 만들기

`examples/sample_feature.py`의 인사말을 아래처럼 바꾼다.

```python
return f"반갑습니다, {name}! AI Git Helper 연습을 시작합니다."
```

또는 파일 끝에 다음 함수를 추가해도 된다.

```python

def farewell(name: str) -> str:
    """전달받은 이름을 포함한 작별 인사를 반환한다."""

    return f"다음에 만나요, {name}!"
```

저장한 뒤 Git이 변경을 인식했는지 확인한다.

```bash
git status --short
```

## 2. API 없이 프롬프트만 확인하기

`6-2` 디렉터리에서 실행한다.

```bash
python3 main.py commit --temperature 0.2 --max-tokens 300 --show-prompt
```

이 명령은 Git diff와 함께 만들어진 프롬프트를 출력하지만 Gemini API는 호출하지 않는다.
`--show-prompt`는 모델 설정값 자체를 화면에 표시하지는 않으며, API 호출 전 변경
내용과 safe-mode 처리 결과를 점검하는 용도다.

## 3. 실제 Commit 초안 생성하기

API 키를 현재 터미널 세션에 설정한 뒤 실행한다.

```bash
export GEMINI_API_KEY="발급받은_키"
python3 main.py commit --temperature 0.2 --max-tokens 300
```

낮은 `temperature`(예: `0.2`)는 비교적 일관되고 보수적인 문구를 유도한다.
`max-tokens 300`은 짧은 Commit 제목·본문에는 대체로 충분한 상한이다.

## 4. 실제 PR 초안 생성하기

```bash
python3 main.py pr --temperature 0.8 --max-tokens 800
```

PR은 Why, What, How to Test 세 섹션을 생성하므로 Commit보다 큰 `max-tokens` 값을
주어도 좋다. `temperature 0.8`은 문장 표현의 다양성을 조금 더 허용한다.

## 값 비교용 명령

같은 Git 변경 사항에서 아래 명령들을 각각 실행해 결과를 비교한다.

```bash
# 가장 안정적인 표현을 우선하는 Commit 초안
python3 main.py commit --temperature 0.1 --max-tokens 200

# 기본 설정의 Commit 초안
python3 main.py commit --temperature 1.0 --max-tokens 2048

# 길이가 넉넉한 PR 초안
python3 main.py pr --temperature 0.7 --max-tokens 1000
```

## 주의할 점

- `max-tokens`는 반드시 0보다 큰 정수여야 한다.
- `temperature`에는 현재 코드상 범위 검사가 없으므로, 사용하는 모델 API가 지원하는 값을 선택해야 한다.
- 같은 입력이어도 AI 응답은 완전히 동일하다고 보장되지 않는다.
- 생성된 Commit/PR 초안은 사실 여부와 테스트 방법을 반드시 직접 검토한다.
