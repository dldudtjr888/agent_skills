# 코딩 표준

> Protocol/DI 패턴: `core-infrastructure.md` | 에러 처리: `error-handling.md`

## 코드 재사용 (절대 규칙)

새 코드를 작성하기 전에, 항상 기존 구현을 검색하고 확립된 패턴을 따를 것.

- 새 함수를 만들기 전에 `Grep`, `Glob`으로 유사 구현 검색
- 새로 만들지 말고 기존 유틸리티 (로깅, 설정, HTTP 클라이언트) 재사용
- 횡단 관심사에 대해 프로젝트의 확립된 패턴을 따를 것

## SOLID 원칙

- **SRP**: 각 클래스/함수/모듈은 하나의 책임만
- **OCP**: 확장에 열려 있고, 수정에 닫혀 있음. 추상 인터페이스 사용.
- **LSP**: 파생 클래스는 기본 클래스를 대체할 수 있어야 함
- **ISP**: 클라이언트는 사용하지 않는 인터페이스에 의존하지 말 것
- **DIP**: 구체 구현이 아닌 추상화에 의존. DI 사용.

## 추가 원칙

- **DRY**: 같은 로직이 여러 곳에 있으면 → 통합
- **KISS**: 단순한 해결책 선호. 불필요한 추상화 제거.
- **YAGNI**: 지금 필요한 것만 구현. 추측성 기능 금지.

## 네이밍 (PEP 8)

- **패키지/모듈**: `snake_case` (예: `mysql_agent.py`)
- **클래스**: `PascalCase` (예: `MySQLAgent`)
- **함수/변수**: `snake_case`, 함수는 동사 (예: `fetch_user`)
- **상수**: `UPPER_SNAKE_CASE` (예: `MAX_RETRIES`)
- **비공개**: `_single_underscore` (protected), `__double` (private)
- **불리언**: `is_`/`has_` 접두사 (예: `is_valid`, `has_permission`)
- 단일 문자 변수 금지 (루프 인덱스 제외)

## 타입 힌팅

- 모든 함수 파라미터와 반환값에 타입 힌트 필수
- nullable 타입에 `Optional[T]` 사용
- 비동기 반환 타입 명시 필수
- 레이어 경계에서 덕 타이핑에 `Protocol` 사용

## 비동기 프로그래밍

- 모든 I/O 작업은 반드시 async
- 순차: 직접 `await`
- 병렬: `asyncio.gather()` 또는 `asyncio.create_task()`
- 리소스 관리: 연결, 풀, 세션에 `async with`
- 타임아웃: 장시간 작업에 `asyncio.wait_for()`

## 로깅

- 프로젝트 표준 로거만 사용 (새 로거 유틸리티 생성 금지)
- **구조화된 로깅**: JSON 또는 key=value 형식으로 파싱 가능한 로그 출력
- 요청 추적을 위해 `trace_id`, `session_id` 등 컨텍스트 필드 포함
- **로그 레벨**: DEBUG (개발 디버깅) | INFO (정상 흐름) | WARNING (복구 가능한 문제) | ERROR (실패, 조치 필요)
- 에러 로그에는 `exc_info=True`로 스택 트레이스 포함 (상세: `error-handling.md`)
- 외부 서비스 호출에 소요 시간, 상태 코드, 에러 로깅

## 보안

- 시크릿은 `.env` 파일에만, `os.getenv()`로 로드
- SQL: 파라미터화된 쿼리만. 문자열 포맷팅 금지.
- 비밀번호, API 키, 토큰 로깅 절대 금지
- 에러 메시지에서 민감한 정보 마스킹

## 절대 하지 말 것

- 새 로거 유틸리티 생성 (프로젝트 표준 로거 사용)
- Python 코드에 프롬프트 하드코딩 (YAML 프롬프트 파일 사용)
- async 함수에서 동기 I/O 작성
- 기존 코드 검색 없이 새 함수 생성
