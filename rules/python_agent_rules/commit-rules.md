# 커밋 규칙

## 접두사

| 접두사 | 용도 |
|--------|------|
| `feat:` | 새 기능 |
| `fix:` | 버그 수정 |
| `chore:` | 빌드/설정 |
| `docs:` | 문서 |
| `refactor:` | 리팩토링 |
| `test:` | 테스트 |
| `style:` | 포맷팅 |

## 형식

- 명령형 (예: "add", "added" 아님)
- 소문자
- 끝에 마침표 없음
- 간결하게 유지

## 예시

```
feat: add postgresql mcp server integration
fix: resolve session timeout on idle connections
docs: update architecture diagram for v2 chat
refactor: extract rate limiter to core/infra
test: add unit tests for message parser
```
