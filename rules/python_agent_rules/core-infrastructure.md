# 공통 인프라 패턴

> 프로바이더 통신: `ai-provider-patterns.md` | 에이전트 실행: `ai-agent-patterns.md`

## 핵심 원칙

1. **타입 경계**: 프로바이더 비의존 코드는 통합 타입만 사용 (`AIRequest`, `AIResponse`, `EnvelopeDTO`, `AgentSpec`, Protocol). SDK 타입은 `core/ai/providers/{provider}/` 내부에만 존재.
2. **Protocol 기반 DI**: 의존성 주입에 `@runtime_checkable Protocol` 사용. 구체 클래스 의존 금지. Protocol을 만족하는 모든 객체가 동작.
3. **무상태 서비스**: 핸들러와 오케스트레이터는 세션 상태를 보유하지 않음. 상태는 저장소 레이어에 존재. 수평 확장 가능.
4. **네임스페이스 격리**: `ContextVar`로 컨텍스트-로컬 상태 관리 (로깅, 추적, 컨테이너). 멀티테넌트 간 상태 누출 방지.

## 통합 타입 시스템

```
상위 레이어 (router, services, handlers)
    │  사용 가능: AIRequest, AIResponse, EnvelopeDTO, AgentSpec, Protocols만
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  EnvelopeDTO (system_prompt, user_input, context, vars)     │
│       ↕ to_envelope() / to_*_api()                         │
│  AIRequest  ──── provider.call() ────→  AIResponse          │
│  (model, instructions, input, metadata)  (content, usage)   │
└─────────────────────────────────────────────────────────────┘
    │  transform_request() / transform_response()
    ▼
프로바이더 SDK 타입 → core/ai/providers/{provider}/ 내부에만 존재
```

### AIRequest

```python
@dataclass
class AIRequest:
    model: str                              # "gpt-4o", "claude-3-5-sonnet"
    instructions: str                       # 시스템 프롬프트
    input: str                              # 사용자 입력
    context: Optional[str] = None           # 대화 히스토리
    max_output_tokens: int = 2000
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    reasoning_effort: Optional[str] = None  # "low", "medium", "high"
    json_schema: Optional[Dict] = None
    enable_web_search: bool = False
    tools: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

- 기본 Python 타입만 사용. SDK import 금지.
- `metadata` dict: 추상화를 깨지 않으면서 프로바이더별 파라미터 전달.
- `to_envelope()`: MessageEnvelope 변환 메서드.

### AIResponse

```python
@dataclass
class AIResponse:
    content: str
    model_used: str
    raw_response: Optional[Any] = None
    usage: Optional[Dict[str, int]] = None   # prompt_tokens, completion_tokens
    tool_calls: List[Dict] = field(default_factory=list)
    fallback_used: bool = False
    latency_ms: Optional[float] = None
```

- 정규화된 응답. 프로바이더 고유 필드 없음.

## 메시지 파이프라인

### 조립 흐름

```
MessageBuilder       → 프롬프트 로드, 변수 치환
    ↓
ContextAssembler     → 대화 히스토리 + 메모리 연결
    ↓
EnvelopeDTO          → API 비의존 데이터 전송 객체
    ↓
MessageFormatter     → 프로바이더별 형식 (to_agents_api, to_anthropic_api 등)
```

**원칙**: Envelope를 먼저 구성 → 프로바이더 포맷은 마지막에.

### EnvelopeDTO

```python
@dataclass
class EnvelopeDTO:
    system_prompt: str
    user_input: str
    context: Optional[str] = None       # 히스토리 + 메모리
    variables: Dict[str, str] = ...     # 템플릿 변수
    metadata: Dict[str, Any] = ...      # 추적 정보 등
```

### MessageBuilder

```python
class MessageBuilder:
    def build(self, prompt_key: str, user_input: str,
              context: Optional[str] = None,
              variables: Optional[Dict] = None,
              prompt_version: Optional[str] = None) -> EnvelopeDTO: ...

    def build_from_template(self, system_prompt: str,
                            user_input: str, **kwargs) -> EnvelopeDTO: ...
```

- `build()`: ConfigLoader로 프롬프트 로드 + 변수 치환 + Envelope 구성
- `build_from_template()`: 직접 프롬프트 전달 (ConfigLoader 불필요)

### MessageFormatter

프로바이더별 변환 정적 메서드:

```python
class MessageFormatter:
    @staticmethod
    def to_agents_api(envelope: EnvelopeDTO) -> Dict: ...     # OpenAI Agents SDK
    @staticmethod
    def to_anthropic_api(envelope: EnvelopeDTO) -> Dict: ...  # Anthropic
    @staticmethod
    def to_langgraph_api(envelope: EnvelopeDTO) -> List: ...  # LangGraph
    @staticmethod
    def to_chat_api(envelope: EnvelopeDTO) -> List: ...       # 범용 Chat API
```

새 프로바이더 추가 시 `to_{provider}_api()` 메서드만 추가.

## 응답 파싱 (2단계)

```
프로바이더 원시 응답
    → Core Parser      → ProviderMessage (role, content, provider, metadata)
    → Domain Parser    → ParsedResult (tokens, tool_calls, handoffs, costs)
    → 저장소 (프로바이더 비의존)
```

- **Core Parser**: 경량, 프로젝트 간 재사용 가능
- **Domain Parser**: 프로젝트별 확장 (비용 계산, 핸드오프 파싱 등)

## DI 컨테이너

```python
class BaseContainer(DeclarativeContainer):
    config = Object({})               # 설정 로더 (서브클래스에서 오버라이드)
    agent_registry = Object({})       # 에이전트 레지스트리
    tracing = Callable(get_tracing)   # 추적 구현

    async def init_async_resources(self) -> None: ...
    async def shutdown_async_resources(self) -> None: ...
```

프로젝트별 확장:

```python
class ApplicationContainer(BaseContainer):
    config = Singleton(MyConfigLoader)
    agent_registry = Object(AGENT_REGISTRY)
    memory_manager = Singleton(MemoryManager, ...)
    orchestrator = Singleton(Orchestrator, ...)
```

**규칙**: `BaseContainer`는 `core/`에 위치 (범용). `ApplicationContainer`는 `domain/`에 위치 (프로젝트별).

## 로깅 & 추적

### 네임스페이스 인식 로깅

```python
# 네임스페이스 설정 (멀티테넌트 격리)
set_logging_namespace("my_project")
logger = get_logger("module_name")     # 현재 네임스페이스의 로거 반환

# 초기화
setup_logging(config, namespace="my_project")
```

- `ContextVar` 기반 → 스레드/태스크별 격리
- 네임스페이스별 독립 로거 팩토리
- `SensitiveDataFilter`: 자동 시크릿 마스킹
- `JSONFormatter`: 구조화된 JSON 로그 출력

### TracingProtocol

```python
@runtime_checkable
class TracingProtocol(Protocol):
    def trace_context(self, name: str, metadata: Optional[Dict] = None): ...
    def record_outcome(self, result: Any, success: bool, error: Optional[str] = None) -> None: ...
    def run_evaluation(self, name: str, **kwargs) -> Any: ...
```

- 기본값: `NoOpTracing` (아무것도 하지 않음)
- 교체: `set_tracing(OpikTracing(), namespace="my_project")`
- 프로젝트별 구현 제공 (Opik, OpenTelemetry 등)

## SSE & 스트리밍

### 통합 스트림 이벤트

모든 스트림 어댑터가 생성하는 프로바이더 비의존 이벤트:

| 카테고리 | 이벤트 |
|----------|--------|
| 텍스트 | `TEXT_DELTA`, `TEXT_DONE` |
| 추론 | `REASONING_DELTA`, `REASONING_DONE` |
| 도구 | `TOOL_CALL_START`, `TOOL_CALL_ARGS_DELTA`, `TOOL_CALL_DONE`, `TOOL_RESULT` |
| 에이전트 | `AGENT_START`, `AGENT_CHANGE` (핸드오프), `AGENT_END` |
| 메타데이터 | `USAGE`, `ERROR`, `DONE` |

### 스트림 어댑터 패턴

```
OpenAI SDK 이벤트    → OpenAIStreamAdapter    → UnifiedStreamEvent
Anthropic 이벤트     → AnthropicStreamAdapter → UnifiedStreamEvent
LangChain 콜백      → LangChainStreamAdapter → UnifiedStreamEvent
```

### StreamResult 래퍼

콘텐츠 스트리밍과 메타데이터 접근을 분리:

```python
result = await execute_stream(task, user_id, session_id)

# 1. 클라이언트에 콘텐츠 스트리밍
async for chunk, chunk_type in result.stream():
    if chunk_type == "delta":
        yield format_chunk(content=chunk)

# 2. 스트리밍 완료 후 메타데이터 접근
usage = result.metadata  # prompt_tokens, completion_tokens, model 등
```

### SSE 이벤트 라이프사이클

```
start → chunk* → done  (또는 error)
```

- 메타데이터 (trace_id, session_id, model)는 HTTP 헤더에
- SSE 페이로드는 콘텐츠만 포함 (최소화)

## DB 추상화

```python
@dataclass
class PoolConfig:
    host: str
    port: int
    user: str
    password: str       # ${VAR}로 .env에서 로드
    database: str
    pool_size: int = 10
    pool_min_size: int = 2
    connect_timeout: int = 10

class AsyncConnectionPool(ABC):
    async def initialize(self) -> None: ...      # 스레드 안전 초기화
    async def close(self) -> None: ...           # 스레드 안전 종료
    async def acquire(self) -> Connection: ...   # 자동 초기화 포함
    async def health_check(self) -> Dict: ...    # 풀 상태 확인
```

- `PoolStatus` enum: `UNINITIALIZED → INITIALIZING → READY → CLOSING → CLOSED`
- 서브클래스가 `_create_pool()`, `_close_pool()`, `_acquire_connection()`, `_ping()` 구현

## 인프라 유틸리티

| 유틸리티 | 위치 | 용도 |
|---------|------|------|
| `ResponseCache` | `core/infra/cache.py` | LLM 응답 해시 기반 캐시 |
| `UnifiedRateLimiter` | `core/infra/rate_limiter.py` | 토큰 버킷 레이트 리미터 |
| `CircuitBreaker` | `core/infra/circuit_breaker.py` | 장애 차단 패턴 |
| 재시도 유틸리티 | `core/infra/retry.py` | 지수 백오프 + 지터 |
| `sanitize_for_bson()` | `core/infra/serialization.py` | MongoDB용 데이터 정제 |
| `SSEResponse` | `core/infra/sse.py` | SSE 이벤트 스트림 |

## 예외 계층

4가지 표준 예외 타입: `ValidationError`, `ConfigurationError`, `ResourceError`, `InternalError`

각 타입별 재시도 정책과 대응 패턴은 `error-handling.md` 참조.

## core/ 확장 패턴

`domain/`은 `core/`의 Protocol과 기본 클래스를 확장:

| core/ (범용) | domain/ (프로젝트별) |
|-------------|---------------------|
| `BaseContainer` | `ApplicationContainer` (DI 구성) |
| `ConfigLoader` | 프로젝트별 설정 접근자 |
| `TracingProtocol` | 구체적인 추적 구현 (Opik 등) |
| `BaseProvider` | 프로바이더별 구현 |
| `RoutingStrategy` | 프로젝트별 라우팅 전략 |
| `BaseGuardrail` | 프로젝트별 가드레일 |
| `BaseHandler` | 프로젝트별 핸들러 |
| `MemoryStore` | 프로젝트별 메모리 백엔드 |
| `AsyncConnectionPool` | 프로젝트별 DB 풀 |

**SDK Import 격리**:

```python
# 타입 체크 전용 (런타임 비용 없음)
if TYPE_CHECKING:
    from agents import Agent, ModelSettings

# 런타임: 필요한 곳에서 지연 import
def build_agent(self, ...):
    from agents import Agent  # 실제 빌드 시에만
```

## 규칙

- 프로바이더 비의존 코드는 통합 타입만 사용 (AIRequest, AIResponse, EnvelopeDTO)
- 의존성 주입에 `@runtime_checkable Protocol` 사용
- SDK 타입 import에 `TYPE_CHECKING` 사용, 런타임에는 지연 import
- 메시지 포맷팅은 MessageFormatter 한 곳에서만
- 로거는 프로젝트 표준 `get_logger()` 사용 (새 로거 생성 금지)
- 로그에 `trace_id`, `session_id` 등 컨텍스트 필드 포함
- DB 풀은 `AsyncConnectionPool` 추상 클래스 확장
- 인프라 유틸리티는 `core/infra/`에 배치 (도메인 의존성 없음)

## 절대 하지 말 것

- `core/` 외부에서 인프라 유틸리티 재생성 (기존 모듈 재사용)
- `core/`에서 `domain/` import (범용성 파괴)
- SDK 고유 객체를 레이어 경계를 넘어 전달 (Protocol/DTO 사용)
- 핸들러나 오케스트레이터에서 세션 상태 보유 (무상태 원칙)
- `ContextVar` 없이 글로벌 상태 공유 (네임스페이스 격리 필수)
- SSE 이벤트 페이로드에 usage/metadata 전송 (HTTP 헤더 사용)
- `start` 또는 `done` SSE 이벤트 생략 (클라이언트가 라이프사이클에 의존)
- 스트리밍 중 이벤트 루프 차단 (async generator 사용)
