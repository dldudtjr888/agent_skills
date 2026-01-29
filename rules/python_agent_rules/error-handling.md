# 에러 처리 규칙

> 프로바이더 복원력: `ai-provider-patterns.md` | 예외 계층: `core-infrastructure.md` | 로깅: `coding-standards.md`

## 4가지 표준 패턴

### 1. 공개 API 메서드 → 에러 Dict 캐치 & 반환

**대상**: 사용자 대면 메서드
**반환**: `Dict[str, Any]` - `{"success": bool, "error": str, "error_type": str}`

- `ValidationError` → warning 로그 + `error_type="validation"`
- 기타 예외 → error 로그 + `exc_info=True` + `error_type="internal"`

### 2. 내부 헬퍼 메서드 → 즉시 발생

**대상**: 내부 전용 헬퍼 메서드
- 빠른 실패: 예외를 상위로 전파
- 호출자가 처리 결정
- 스택 트레이스 보존
- docstring에 `Raises:` 섹션 반드시 문서화

### 3. 초기화 메서드 → 명확한 메시지와 함께 발생

**대상**: `__init__`, `__aenter__`, 팩토리 메서드
- 초기화 실패 시 즉시 중단
- 명확한 에러 메시지 + 해결 가이드
- 설정 문서 참조 (`.env.example`, README)
- `RuntimeError` 또는 `ValueError` 사용

### 4. 선택적 기능 → None 반환 & Warning 로그

**대상**: 실패해도 괜찮은 기능 (캐시, 추적, 메트릭)
- 우아한 성능 저하
- `None` 반환 + 영향 설명과 함께 warning 로그
- 호출자가 분기를 위해 `None` 검사

## 에러 유형

| 유형 | 발생 시점 | 재시도 | 조치 |
|------|----------|--------|------|
| `ValidationError` | 사용자 입력 실패 | 아니오 | warning 로그 + 에러 dict |
| `ConfigurationError` | 설정/환경변수 누락 | 아니오 | error 로그 + raise + 해결 가이드 |
| `ResourceError` | 외부 리소스 실패 | 예 (3회 지수 백오프) | 재시도 후 raise |
| `InternalError` | 예상치 못한 내부 에러 | 아니오 | error 로그 (`exc_info=True`) + raise |

## 규칙

- 명확한 계층 구조의 도메인 예외 클래스 정의
- 구체적이고 실행 가능한 에러 메시지 제공
- 다시 발생시키기 전에 로그 기록 (예외를 조용히 삼키지 말 것)

## 절대 하지 말 것

- 다시 발생시키거나 로깅하지 않는 `except Exception` 포괄 캐치
- 예외를 조용히 삼킴 (`except: pass`)
- 내부 메서드에서 raise 대신 에러 코드 반환
- 에러 메시지에 민감한 데이터 (자격 증명, 토큰) 로깅
