# 테스팅 규칙

> 구현 코드/pytest 설정/conftest: Skills `testing.md` 참조.

## 테스트 피라미드

**목표 비율**: 단위 70% | 통합 20% | E2E 10%

## 네이밍 규칙

| 요소 | 규칙 | 예시 |
|------|------|------|
| 파일 | `test_{module}.py` | `test_mcp_tools.py` |
| 클래스 | `Test{Feature}` | `TestQueryTool` |
| 함수 | `test_{scenario}` | `test_query_returns_results()` |

## Pytest 마커

- `@pytest.mark.unit` — 빠름, 외부 의존성 없음
- `@pytest.mark.integration` — DB, 외부 서비스 필요
- `@pytest.mark.e2e` — 전체 시스템 테스트
- `@pytest.mark.asyncio` — 비동기 테스트

## AAA 패턴 (필수)

모든 테스트는 **Arrange → Act → Assert** 구조 준수.

## 테스트 독립성

- 테스트 간 전역 상태 공유 금지
- 의존성 주입에 fixture 사용
- 각 테스트는 어떤 순서로든 독립 실행 가능

## 모킹

- `unittest.mock` 대신 `pytest-mock` (`mocker` fixture) 사용
- 외부 API/DB: 단위 테스트에서 항상 모킹
- 내부 로직: 실제 코드 사용
- 통합 테스트: 실제 연결 검증

## 명확한 Assertion

자명하지 않은 검사에 assertion 메시지 필수: `assert result.status == "success", f"Expected success, got {result.status}"`

## 절대 하지 말 것

- 테스트 함수 간 가변 상태 공유
- 실행 순서에 의존하는 테스트 작성
- 단위 테스트에서 내부 로직 모킹 (경계만 모킹)
- 자명하지 않은 검사에서 assertion 메시지 생략
- 프로덕션 DB 직접 접근 (mock 사용)
