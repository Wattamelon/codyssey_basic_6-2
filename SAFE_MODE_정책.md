# Safe Mode 정책

## 목적

Git diff를 외부 AI API에 보내기 전에 민감정보 노출 가능성과 과도한 입력 전송을 줄인다.

## 기본값

- 최대 diff 줄 수: 200줄
- 최대 diff 문자 수: 20,000자
- 기본 적용 순서: 민감정보 마스킹 → 줄 수 제한 → 문자 수 제한

## 마스킹 대상

- API Key, secret, token, password 계열 변수 값
- Bearer token
- 일반적인 OpenAI, Google, GitHub Key 형태
- 이메일 주소

## 생략 처리

줄 수 또는 문자 수 제한으로 diff 일부가 빠지면, 최종 전송 문자열에 다음 안내를 포함한다.

```text
[SAFE MODE: diff 일부 생략]
```

안내 문구까지 포함한 최종 문자열은 설정한 최대 문자 수를 넘지 않는다.

## 한계와 사용자 책임

정규표현식 마스킹은 모든 비밀값, 개인정보, 회사 내부 정보를 완벽하게 탐지하지 못한다. 특히 형식이 알려지지 않은 토큰, 문맥상 민감한 코드, 짧은 비밀값은 남을 수 있다.

따라서 API 호출 전에는 다음을 확인한다.

```bash
git status --short
git diff
git diff --cached
```

safe-mode를 끄면 원본 diff가 그대로 반환된다. 이후 CLI 단계에서는 safe-mode 비활성화 시 명확한 경고를 출력해야 한다.

