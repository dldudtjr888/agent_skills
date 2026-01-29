# AI 에이전트 시스템 패턴

> 구현 코드/디렉토리 구조: Skills 파일 참조. 이 문서는 원칙과 제약조건만 다룸.

## 에이전트 빌더 & 팩토리

### AgentBuilderProtocol

```python
@runtime_checkable
class AgentBuilderProtocol(Protocol):
    """에이전트 빌더 인터페이스"""

    def build_agent(
        self,
        agent_key: str,
        *,
        overrides: Optional[Any] = None,
        extra_tools: Optional[Sequence[Any]] = None,
        mcp_servers: Optional[Sequence[Any]] = None,
    ) -> Any:
        """에이전트 생성"""

    def get_spec(self, agent_key: str, overrides: Optional[Any] = None) -> Any:
        """SDK 인스턴스 없이 에이전트 스펙 조회"""
```

### AgentSpec

```python
@dataclass
class AgentSpec:
    """정규화된 에이전트 사양 (순수 Python 타입, SDK 객체 없음)"""
    name: str
    instructions: str
    model: str
    tools: List[str]                    # 도구 이름 목록
    model_settings: Dict[str, Any]      # temperature, max_tokens 등
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### AgentFactory

```python
class AgentFactory:
    """모델 프로바이더 기반 에이전트 생성 팩토리

    예시:
        factory = AgentFactory()

        # OpenAI 모델 → OpenAIAgentBuilder
        agent = factory.create_agent("supervisor", model="gpt-4o")

        # LangGraph 모델 → LangGraphAgentBuilder
        agent = factory.create_agent("research", model="langgraph://research-graph")
    """

    def __init__(self, config_loader: Optional[Any] = None):
        self._builders: dict[str, AgentBuilderProtocol] = {}
        self._config_loader = config_loader

    def _detect_provider(self, model: str) -> str:
        """AGENT_FACTORY_MODEL_PATTERNS로 모델명에서 프로바이더 감지"""
        for pattern, provider in MODEL_PATTERNS:
            if re.match(pattern, model, re.IGNORECASE):
                return provider
        return "openai"  # 기본값

    def _get_builder(self, provider: str) -> AgentBuilderProtocol:
        """프로바이더용 빌더 조회/생성 (캐시됨)"""
        if provider not in self._builders:
            self._builders[provider] = self._create_builder(provider)
        return self._builders[provider]

    def _create_builder(self, provider: str) -> AgentBuilderProtocol:
        """프로바이더 기반으로 적절한 빌더 생성"""
        if provider == "openai":
            from core.ai.providers.openai import OpenAIAgentBuilder
            return OpenAIAgentBuilder(config_loader=self._config_loader)
        elif provider == "langgraph":
            raise NotImplementedError("LangGraph builder not yet implemented")
        # ... 추가 프로바이더

    def create_agent(
        self,
        agent_key: str,
        *,
        model: Optional[str] = None,
        overrides: Optional[Any] = None,
        extra_tools: Optional[Sequence[Any]] = None,
        mcp_servers: Optional[Sequence[Any]] = None,
    ) -> Any:
        """프로바이더 자동 감지로 에이전트 생성"""
        if model is None:
            config_loader = self._get_config_loader()
            agents_config = config_loader.load_agents_config()
            model = agents_config.get("agents", {}).get(agent_key, {}).get("model", "gpt-4o")

        provider = self._detect_provider(model)
        builder = self._get_builder(provider)

        return builder.build_agent(
            agent_key,
            overrides=overrides,
            extra_tools=extra_tools,
            mcp_servers=mcp_servers,
        )


def get_agent_factory(config_loader: Optional[Any] = None) -> AgentFactory:
    """AgentFactory 싱글턴 조회"""
```

- 빌더는 프로바이더별 싱글턴 캐시
- 싱글턴: `get_agent_factory()`로 접근

## 에이전트 레지스트리

```python
@dataclass
class AgentBuilder:
    """에이전트 빌더 등록 정보"""
    name: str
    sync_factory: Optional[Callable] = None    # 동기 팩토리
    async_factory: Optional[Callable] = None   # 비동기 팩토리
    requires_mcp: bool = False                 # MCP 서버 필요 여부
    description: str = ""

def register_agent(name: str, builder: AgentBuilder) -> None:
    """core.AGENT_REGISTRY에 에이전트 등록"""

def register_navis_agents() -> None:
    """벌크 등록 (프로젝트 시작 시 호출)"""
```

- 네임스페이스 격리로 에이전트 그룹 분리
- sync/async 팩토리 모두 지원, MCP 서버 필요 여부 플래그
- `register_agent()`, `list_available_agents()`로 동적 등록/탐색

## 컨텍스트 프로바이더 원칙

### BaseContextProvider

```python
class BaseContextProvider(ABC):
    """요청 전 검증 + 컨텍스트 준비 (템플릿 메서드)"""

    @property
    @abstractmethod
    def context_type(self) -> str:
        """컨텍스트 타입 식별자 (예: "chat", "document", "research")"""
        ...

    async def validate_and_authorize(
        self,
        user_id: str,
        params: dict
    ) -> ValidationResult:
        """검증 + 인가 (템플릿 메서드)"""
        # 1. _validate_params() 호출
        # 2. _authorize() 호출
        # 3. 결과 통합 반환

    async def prepare_context(
        self,
        user_id: str,
        params: dict
    ) -> ChatContext:
        """컨텍스트 준비 (템플릿 메서드)"""
        # 1. validate_and_authorize() 호출
        # 2. _prepare_context_data() 호출
        # 3. ChatContext 반환

    @abstractmethod
    async def _validate_params(self, params: dict) -> ValidationResult:
        """파라미터 검증 (서브클래스 구현)"""
        ...

    @abstractmethod
    async def _authorize(self, user_id: str, params: dict) -> AuthResult:
        """권한 검증 (서브클래스 구현)"""
        ...

    @abstractmethod
    async def _prepare_context_data(self, user_id: str, params: dict) -> dict:
        """컨텍스트 데이터 준비 (서브클래스 구현)"""
        ...
```

### ContextProviderRegistry

```python
class ContextProviderRegistry:
    """스레드 안전한 싱글턴 레지스트리"""

    _instance: Optional["ContextProviderRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ContextProviderRegistry":
        """이중 잠금 패턴으로 싱글턴 조회"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, provider_cls: Type[BaseContextProvider]) -> None:
        """클래스 등록 (팩토리 메서드 패턴)"""

    def get(self, context_type: str) -> BaseContextProvider:
        """요청당 새 인스턴스 생성 반환"""
```

**2단계 검증**: `_validate_params()` → `_authorize()` → `_prepare_context_data()`

**추가 3단계**: 서브클래스 구현 → 레지스트리 등록 → 핸들러 확인/구현

## 핸들러 템플릿 메서드 원칙

### BaseHandler

```python
class BaseHandler(ABC):
    """핸들러 기본 클래스 (템플릿 메서드 패턴)"""

    async def handle(
        self,
        message: str,
        context: ChatContext,
        session_id: str,
        user_id: str,
        *,
        metadata: Optional[Dict] = None,
    ) -> AsyncIterator[SSEEvent]:
        """템플릿 메서드 - 오버라이드 금지"""
        # 1. 입력 가드레일 체크 (기본 클래스)
        guardrail_result = await self._check_input_guardrails(message, context)
        if guardrail_result.blocked:
            yield self._create_error_event(guardrail_result.blocking_reason)
            return

        # 2. 토큰 제한 체크 (기본 클래스)
        token_check = await self._check_token_limit(message, context)
        if not token_check.passed:
            yield self._create_error_event(token_check.reason)
            return

        # 3. start 이벤트 (기본 클래스)
        yield self._create_start_event(session_id, metadata)

        # 4. 서브클래스에 위임
        try:
            async for event in self._do_handle(
                message, context, session_id, user_id, metadata=metadata
            ):
                yield event
        except Exception as e:
            yield self._create_error_event(str(e))
            return

        # 5. done 이벤트 (기본 클래스)
        yield self._create_done_event(session_id)

    @abstractmethod
    async def _do_handle(
        self,
        message: str,
        context: ChatContext,
        session_id: str,
        user_id: str,
        *,
        metadata: Optional[Dict] = None,
    ) -> AsyncIterator[SSEEvent]:
        """서브클래스가 이것만 구현"""
        ...

    async def _check_input_guardrails(
        self,
        message: str,
        context: ChatContext
    ) -> AggregatedGuardrailResult:
        """입력 가드레일 체크 (fail-open)"""

    async def _check_token_limit(
        self,
        message: str,
        context: ChatContext
    ) -> TokenCheckResult:
        """토큰 제한 체크"""

    def _create_start_event(self, session_id: str, metadata: Optional[Dict]) -> SSEEvent:
        """start SSE 이벤트 생성"""

    def _create_done_event(self, session_id: str) -> SSEEvent:
        """done SSE 이벤트 생성"""

    def _create_error_event(self, reason: str, code: str = "error") -> SSEEvent:
        """error SSE 이벤트 생성"""
```

**메서드 네이밍 규칙**:
- `handle()` — 공개 API (템플릿 메서드, **오버라이드 금지**)
- `_do_handle()` — protected (서브클래스가 구현)
- `__parse_metadata()` — private (내부 헬퍼)

### HandlerRegistry

```python
class HandlerRegistry:
    """핸들러 레지스트리 (팩토리 패턴)"""

    def register(self, handler_type: str, handler_cls: Type[BaseHandler]) -> None:
        """핸들러 클래스 등록"""

    def get(self, handler_type: str, **kwargs) -> BaseHandler:
        """핸들러 인스턴스 생성 반환"""

    def list_handlers(self) -> List[str]:
        """등록된 핸들러 타입 목록"""
```

**추가 3단계**: `BaseHandler` 서브클래스 → `HandlerRegistry` 등록 → `config/handlers.yaml` 설정

## 에이전트 런타임

### ExecutorProtocol

```python
@runtime_checkable
class ExecutorProtocol(Protocol):
    """에이전트 실행기 프로토콜"""

    async def run(
        self,
        agent: AgentProtocol,
        input: str,
        *,
        session: Optional[Any] = None
    ) -> Any:
        """에이전트 실행"""
        ...
```

### ExecutorFactory

```python
class ExecutorFactory:
    """레지스트리 기반 실행기 팩토리"""

    _registry: Dict[str, Type[ExecutorProtocol]] = {}

    @classmethod
    def register(cls, name: str, executor_cls: Type[ExecutorProtocol]) -> None:
        """실행기 클래스 등록"""
        cls._registry[name] = executor_cls

    @classmethod
    def create(
        cls,
        name: str = "openai",
        config: Optional[ExecutorConfig] = None
    ) -> ExecutorProtocol:
        """이름으로 실행기 생성"""
        if name not in cls._registry:
            raise ValueError(f"Unknown executor: {name}")
        return cls._registry[name](config)

    @classmethod
    def list_available(cls) -> List[str]:
        """사용 가능한 실행기 목록"""
        return list(cls._registry.keys())
```

### AgentRuntime

```python
class AgentRuntime:
    """실행 + 메모리 + 추적 통합"""

    def __init__(
        self,
        agent_id: str,
        *,
        session_id: str = "default",
        memory_adapter: Optional[MemoryAdapterProtocol] = None,
        executor: Optional[ExecutorProtocol] = None,
        executor_name: str = "openai",
        executor_config: Optional[ExecutorConfig] = None,
    ):
        self.agent_id = agent_id
        self.session_id = session_id
        self._memory = memory_adapter
        self._executor = executor
        self._executor_name = executor_name
        self._executor_config = executor_config

    @property
    def executor(self) -> ExecutorProtocol:
        """지연 초기화된 실행기"""
        if self._executor is None:
            self._executor = ExecutorFactory.create(
                self._executor_name,
                self._executor_config
            )
        return self._executor

    async def _execute_turn(
        self,
        agent: AgentProtocol,
        user_input: str
    ) -> Any:
        """단일 턴 실행 + 추적 + 메모리 통합"""
        # 1. 메모리 컨텍스트로 입력 준비
        prepared_input = await self._memory.prepare_input(
            user_input,
            include_recent=5,
            include_relevant=3
        ) if self._memory else user_input

        # 2. 추적 컨텍스트와 함께 실행
        with trace_context(name=f"agent_{self.agent_id}_turn"):
            result = await self.executor.run(
                agent,
                prepared_input,
                session=self._get_session()
            )

        # 3. LLM 메트릭 로깅
        # 4. 추적 결과 기록
        # 5. 메모리에 저장
        if self._memory:
            await self._memory.save_output(
                user_input,
                result.content,
                priority=MemoryPriority.MEDIUM
            )

        return result
```

- 실행기 우선순위: 명시적 주입 > 팩토리(이름 기반)

## 메모리 시스템 원칙

### 3계층 아키텍처

```
MemoryAdapter (권장 API 진입점)
    ↓
MemoryManager (오케스트레이터)
    ├── Cache (TTL 기반)
    ├── Session Store (SQLite/MySQL)
    ├── Long-term Store (벡터 DB)
    └── Middleware (보안)
```

### MemoryAdapterProtocol

```python
@runtime_checkable
class MemoryAdapterProtocol(Protocol):
    """메모리 어댑터 프로토콜"""

    def get_session(self) -> Optional[Any]:
        """현재 세션 조회"""
        ...

    async def prepare_input(
        self,
        user_input: str,
        include_recent: int = 5,
        include_relevant: int = 3
    ) -> str:
        """최근/관련 컨텍스트와 함께 입력 준비"""
        ...

    async def prepare_envelope(
        self,
        prompt_key: str,
        user_input: str,
        variables: Optional[dict] = None,
        **kwargs
    ) -> MessageEnvelope:
        """메모리 컨텍스트 포함 MessageEnvelope 준비"""
        ...

    async def save_output(
        self,
        user_input: str,
        agent_output: str,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        metadata: Optional[dict] = None
    ) -> None:
        """에이전트 출력 저장"""
        ...

    async def save_important(
        self,
        content: str,
        memory_type: MemoryType,
        priority: MemoryPriority,
        **kwargs
    ) -> str:
        """중요 정보 저장 (장기 메모리)"""
        ...

    async def get_relevant_context(
        self,
        query: str,
        limit: int = 5
    ) -> GetContextResult:
        """관련 컨텍스트 조회"""
        ...
```

### 미들웨어 체인

```
SecurityMiddleware → ReliabilityMiddleware → 실제 저장소
```

### 메모리 우선순위 & 승격

| 우선순위 | 동작 | 저장소 |
|---------|------|--------|
| `LOW` | 임시 | 세션만 |
| `MEDIUM` | 일반 | 세션, 임계값 초과 시 자동 승격 |
| `HIGH` | 중요 | 세션 + 장기 즉시 |
| `CRITICAL` | 컴플라이언스 | 세션 + 장기 + 백업 |

```python
class MemoryPriority(str, Enum):
    LOW = "low"           # 인사말 등 임시
    MEDIUM = "medium"     # 일반 쿼리
    HIGH = "high"         # 중요 결정
    CRITICAL = "critical" # 컴플라이언스 데이터
```

### 교차 에이전트 메모리 공유

**메모리 공유**: 동일 `user_id`로 공유, 고유 `agent_id`로 격리

```python
# 모든 에이전트가 user_id 공유, agent_id는 고유
supervisor = MemoryManager(user_id="project_x", agent_id="supervisor")
researcher = MemoryManager(user_id="project_x", agent_id="research")
```

**추가 3단계**: Backend protocol 구현 → SessionFactory 등록 → `config/memory.yaml` 설정

## 라우팅 전략 원칙

### RouteDecision

```python
@dataclass
class RouteDecision:
    """라우팅 결정"""
    route_type: str              # "direct", "fast_path", "supervisor"
    confidence: float            # 0.0 ~ 1.0
    complexity: str              # "simple", "medium", "complex"
    reasoning: str               # 결정 이유
    target: Optional[str] = None # fast_path 대상 에이전트
    metadata: dict = field(default_factory=dict)

    @property
    def is_fast_path(self) -> bool:
        return self.route_type == "fast_path"

    @property
    def requires_supervisor(self) -> bool:
        return self.route_type == "supervisor"
```

### BaseRoutingStrategy

```python
class BaseRoutingStrategy(ABC):
    """라우팅 전략 기본 클래스"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def route(
        self,
        query: str,
        context: dict
    ) -> RouteDecision:
        """라우팅 결정 (서브클래스 구현)"""
        ...

    def configure(self, config: dict) -> None:
        """설정 적용"""

    async def route_with_metrics(
        self,
        query: str,
        context: dict
    ) -> RouteDecision:
        """메트릭 수집과 함께 라우팅"""
        start = time.perf_counter()
        decision = await self.route(query, context)
        latency_ms = (time.perf_counter() - start) * 1000

        self._log_decision(query, decision, latency_ms)
        self._record_metrics(decision, latency_ms)

        return decision

    def _log_decision(
        self,
        query: str,
        decision: RouteDecision,
        latency_ms: float
    ) -> None:
        """라우팅 결정 로깅"""

    def _record_metrics(
        self,
        decision: RouteDecision,
        latency_ms: float
    ) -> None:
        """프로메테우스 등 메트릭 기록"""
```

### 라우팅 전략 종류

설정 기반 전략 선택 (`config/routing.yaml`). `StrategyRouter`가 라우팅 실행 + 메트릭 수집.

| 전략 | 용도 | 속도 |
|------|------|------|
| `rule_based` | 정규식 패턴 | 가장 빠름 |
| `hybrid` | 전략 체이닝 + 폴백 | 보통 |
| `embedding` | 벡터 유사도 | 느림 |
| `llm` | LLM 분류 | 가장 느림 |

**추가 3단계**: `RoutingStrategy` 구현 → `RouterFactory` 등록 → `config/routing.yaml` 설정

## 가드레일 체인 원칙

### GuardrailResult

```python
@dataclass
class GuardrailResult:
    """단일 가드레일 결과"""
    passed: bool
    blocked: bool
    guardrail_name: str
    execution_time_ms: float
    modified_content: Optional[str] = None
    reason: Optional[str] = None
    details: dict = field(default_factory=dict)


@dataclass
class AggregatedGuardrailResult:
    """집계된 가드레일 결과"""
    passed: bool
    blocked: bool
    final_content: str
    results: list[GuardrailResult] = field(default_factory=list)
    total_execution_time_ms: float = 0.0
    blocking_reason: Optional[str] = None
```

### BaseGuardrail

```python
class BaseGuardrail(ABC):
    """가드레일 기본 클래스 (템플릿 메서드)"""

    def __init__(self, name: str, blocking: bool = True):
        self.name = name
        self.blocking = blocking

    async def check(
        self,
        content: str,
        context: dict
    ) -> GuardrailResult:
        """템플릿 메서드 - 시간 측정/로깅 포함"""
        start = time.perf_counter()

        try:
            result = await self._do_check(content, context)
        except Exception as e:
            # 가드레일 실패는 통과로 처리 (fail-open)
            result = GuardrailResult(
                passed=True,
                blocked=False,
                guardrail_name=self.name,
                execution_time_ms=0,
                reason=f"Guardrail error: {e}"
            )

        result.execution_time_ms = (time.perf_counter() - start) * 1000
        self._log_result(result)

        return result

    @abstractmethod
    async def _do_check(
        self,
        content: str,
        context: dict
    ) -> GuardrailResult:
        """서브클래스가 구현"""
        ...

    def _log_result(self, result: GuardrailResult) -> None:
        """결과 로깅"""
```

### GuardrailChain

```python
class GuardrailChain:
    """가드레일 체인 실행기"""

    def __init__(
        self,
        guardrails: List[BaseGuardrail],
        parallel_execution: bool = True,
        timeout_ms: int = 5000
    ):
        self.guardrails = guardrails
        self.parallel_execution = parallel_execution
        self.timeout_ms = timeout_ms

    async def check_input(
        self,
        content: str,
        context: dict
    ) -> AggregatedGuardrailResult:
        """입력 가드레일 체크"""
        if self.parallel_execution:
            return await self._execute_guardrails_parallel(content, context)
        return await self._execute_guardrails_sequential(content, context)

    async def check_output(
        self,
        content: str,
        context: dict
    ) -> AggregatedGuardrailResult:
        """출력 가드레일 체크"""

    async def _execute_guardrails_parallel(
        self,
        content: str,
        context: dict
    ) -> tuple[list[GuardrailResult], str]:
        """병렬 실행 + blocking 가드레일 단축 평가"""
        # 1. blocking 가드레일 병렬 실행
        # 2. 첫 차단 시 단축 평가
        # 3. non-blocking은 백그라운드 실행
        # 4. 콘텐츠 수정 체이닝 처리

    async def _execute_guardrails_sequential(
        self,
        content: str,
        context: dict
    ) -> tuple[list[GuardrailResult], str]:
        """순차 실행 + 결정적 수정 체이닝"""
```

**설정 예시**:

```yaml
guardrails:
  parallel_execution: true
  timeout_ms: 5000
  input:
    checks:
      - name: moderation
        blocking: true       # 트리거 시 요청 중단
      - name: prompt_injection
        blocking: true
  output:
    checks:
      - name: pii_masking
        blocking: false      # 로그만 (중단 안 함)
```

- 병렬 실행: blocking 우선 → 첫 차단 시 단축 평가 → 비blocking은 백그라운드
- 여러 가드레일이 콘텐츠 수정 시, 결정성을 위해 순차 재실행

**추가 3단계**: `BaseGuardrail` 서브클래스 → `GuardrailChain` 추가 → `config/guardrails.yaml` 설정

## 요청 처리 파이프라인

```
HTTP → 입력 검증 → 컨텍스트 프로바이더 → 핸들러 선택 → BaseHandler.handle()
→ 가드레일 → 토큰 제한 → _do_handle() → 라우팅 → 메시지 빌드 → 프로바이더 호출
→ 스트리밍 → 결과 저장
```

### 상세 흐름

1. **HTTP 요청 수신** (router/)
2. **입력 검증** (Pydantic 모델)
3. **컨텍스트 프로바이더** (ContextProviderRegistry → prepare_context)
4. **핸들러 선택** (HandlerRegistry → get)
5. **BaseHandler.handle()** (템플릿 메서드)
   - 입력 가드레일 (GuardrailChain.check_input)
   - 토큰 제한 체크
   - start 이벤트
   - **_do_handle()** (서브클래스)
     - 라우팅 (RoutingStrategy.route)
     - 메시지 빌드 (MessageBuilder → EnvelopeDTO)
     - 프로바이더 호출 (ProviderRegistry.call)
   - 출력 가드레일 (GuardrailChain.check_output)
   - done 이벤트
6. **결과 저장** (MemoryAdapter.save_output)

## 규칙

- 서브클래스는 `_do_handle()` / `_do_check()` / `_validate_params()` 등 protected 메서드만 구현
- 모든 핸들러, 컨텍스트 프로바이더, 에이전트를 각 레지스트리에 등록
- 라우팅 전략은 설정 기반 (하드코딩 금지)
- 에이전트 간 메모리: 동일 `user_id` + 고유 `agent_id`
- 외부 레이어는 MemoryAdapter를 통해 접근 (MemoryManager 직접 사용 금지)
- 실행기는 ExecutorFactory를 통해 생성
- AgentFactory는 모델 이름 패턴으로 빌더 자동 라우팅

## 절대 하지 말 것

- `handle()` / `check()` 오버라이드 (protected 메서드만)
- 서브클래스에서 가드레일/토큰 검사 중복
- 관련 없는 워크플로우 간 `user_id` 혼용
- 다른 에이전트에 동일 `agent_id` 사용
- 장기 메모리 저장소 직접 접근 (MemoryAdapter 사용)
- 핸들러 코드에 라우팅 결정 하드코딩
- 체인 패턴 외부에 가드레일 로직 추가
- 레지스트리 외부에서 핸들러/컨텍스트 프로바이더 직접 생성
- AgentFactory 우회하여 프로바이더별 빌더 직접 호출
