# AI 프로바이더 패턴

> 구현 코드/디렉토리 구조: Skills 파일 참조. 이 문서는 원칙과 제약조건만 다룸.

## 핵심 추상화 원칙

1. **타입 경계**: 프로바이더 비의존 코드는 통합 타입만 사용 (`AIRequest`, `AIResponse`, `EnvelopeDTO`, `AgentSpec`, Protocol). SDK 타입은 `core/ai/providers/{provider}/` 내부에만.
2. **패턴 기반 라우팅**: 모델 이름 정규식으로 프로바이더 선택. 프로바이더 변경 = 모델 이름 변경.
3. **단일 변환 지점**: 메시지 포맷팅은 MessageFormatter 한 곳에서만. 프로바이더별 하드코딩 금지.
4. **Protocol 기반 DI**: 빌더와 서비스는 Protocol에 의존. 구체 클래스 의존 금지.
5. **무상태 서비스**: 핸들러/오케스트레이터는 세션 상태 미보유. 상태는 저장소 레이어.

## 타입 경계 다이어그램

```
상위 레이어 (router, services, handlers)
    │  사용 가능: AIRequest, AIResponse, EnvelopeDTO, AgentSpec, Protocols만
    ▼
  EnvelopeDTO ↔ AIRequest → provider.call() → AIResponse
    ▼
프로바이더 SDK 타입 → core/ai/providers/{provider}/ 내부에만
```

## BaseProvider 프로토콜

```python
class BaseProvider(ABC):
    """Provider 추상 인터페이스

    모든 Provider는 통합 AIRequest를 받아 적절한 API 형식으로 변환,
    응답을 다시 AIResponse로 변환.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """프로바이더 식별자 (예: "openai", "anthropic", "openrouter")"""
        pass

    @abstractmethod
    async def call(self, request: AIRequest) -> AIResponse:
        """API 호출 실행 - 전체 요청/응답 사이클 처리"""
        pass

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """이 프로바이더가 해당 모델을 지원하는지 확인"""
        pass

    @abstractmethod
    def transform_request(self, request: AIRequest) -> Dict[str, Any]:
        """AIRequest를 프로바이더별 API 형식으로 변환"""
        pass

    @abstractmethod
    def transform_response(self, raw_response: Any) -> AIResponse:
        """프로바이더별 응답을 AIResponse로 변환"""
        pass

    @abstractmethod
    async def aclose(self) -> None:
        """비동기 클라이언트 종료 및 리소스 정리"""
        pass
```

## 프로바이더 디렉토리 구조

```
core/ai/providers/{provider_name}/
├── __init__.py        # 모듈 exports
├── provider.py        # BaseProvider 구현
├── builder.py         # 에이전트 빌더
├── executor.py        # 에이전트 실행기
├── settings.py        # 모델 설정 해석기
├── param_policy.py    # 파라미터 검증 정책
└── *_client.py        # API 클라이언트
```

## ProviderRegistry (자동 라우팅)

```python
class ProviderRegistry:
    """모델 이름 패턴으로 자동 라우팅"""

    MODEL_PATTERNS: List[Tuple[str, str]] = PROVIDER_REGISTRY_MODEL_PATTERNS

    def __init__(self, config_loader=None):
        self._providers: Dict[str, BaseProvider] = {}
        self._custom_patterns: List[Tuple[str, str]] = []

    def register(self, provider: BaseProvider) -> None:
        """프로바이더를 이름으로 등록"""
        self._providers[provider.name] = provider

    def add_custom_pattern(self, pattern: str, provider_name: str) -> None:
        """커스텀 라우팅 패턴 추가 (우선 적용)"""
        self._custom_patterns.append((pattern, provider_name))

    def get_provider(self, model: str) -> BaseProvider:
        """모델 이름 기반으로 적절한 프로바이더 자동 라우팅"""
        # 1. 커스텀 패턴 먼저 확인 (FIFO)
        # 2. 기본 패턴 확인
        # 3. 매칭 없으면 ValueError raise

    async def call(self, request: AIRequest) -> AIResponse:
        """자동 라우팅 + 호출"""
        provider = self.get_provider(request.model)
        return await provider.call(request)

    async def aclose_all(self) -> None:
        """등록된 모든 프로바이더 종료"""
```

### 라우팅 패턴 (순서 중요 - 첫 매칭 우선)

```python
PROVIDER_REGISTRY_MODEL_PATTERNS = [
    (r"^gpt-.*", "openai"),
    (r"^o[1-3]-.*", "openai"),
    (r"^claude-.*", "anthropic"),
    (r"^langchain/.*", "langchain"),
    (r"^gemini-.*", "google"),
    (r"^mistral-.*", "mistral"),
]

AGENT_FACTORY_MODEL_PATTERNS = [
    (r"^openai/", "openai"),           # OpenRouter 벤더 프리픽스
    (r"^anthropic/", "anthropic"),
    (r"^(gpt-|o1-|o3-)", "openai"),    # 직접 모델 이름
    (r"^claude-", "anthropic"),
    (r"^langgraph://", "langgraph"),
]
```

## ModelRouter (폴백 시퀀스)

```python
class ModelRouter:
    """중앙 모델 선택, 폴백, 정책 관리"""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        self._cooldowns: Dict[str, datetime] = {}      # model → cooldown 만료 시점
        self._failure_counts: Dict[str, int] = {}      # model → 실패 횟수

    def resolve_sequence(
        self,
        service_type: str,
        primary_model: Optional[str] = None,
        override_sequence: Optional[List[str]] = None,
    ) -> List[str]:
        """폴백 시퀀스 해석

        예시:
            router.resolve_sequence("completion", "gpt-5.2")
            # Returns: ["gpt-5.2", "gpt-5", "gpt-4o", "gpt-4o-mini"]
        """

    def apply_param_policy(self, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """모델 능력에 맞게 파라미터 필터링"""

    def record_failure(self, model: str, cooldown_minutes: Optional[int] = None) -> None:
        """모델 실패 기록 및 cooldown 적용"""

    def is_available(self, model: str) -> bool:
        """모델 사용 가능 여부 확인 (cooldown 중 아닌지)"""
```

### 기본 폴백 시퀀스

```python
def _default_fallback_sequence(self, primary_model: Optional[str]) -> List[str]:
    if normalized == "gpt-5.2":
        return ["gpt-5.2", "gpt-5", "gpt-4o", "gpt-4o-mini"]
    if normalized == "claude-3.5":
        return [normalized, "claude-3-sonnet", "claude-3-haiku"]
    if normalized == "gemini-1.5-pro":
        return [normalized, "gemini-1.5-flash"]
```

## OpenAI Agents SDK vs LangChain

| 항목 | OpenAI Agents SDK | LangChain/OpenRouter |
|------|-------------------|----------------------|
| LLM 파라미터 | 에이전트 생성 시 설정 | 요청 시 설정 |
| 요청 형식 | `input: "..."` | `messages: [...]` |
| 모델 변경 | 에이전트 재생성 필요 | 요청에 전달 |
| 세션 관리 | `Runner.run(session=...)` | 외부 메모리 |

**중요**: OpenAI Agents SDK는 런타임에 `temperature`/`max_tokens` 미지원. 에이전트 생성 시 `ModelSettings`로 설정.

```python
# 올바름 - 에이전트 생성 시 설정
agent = Agent(name="assistant", model_settings={"temperature": 0.7})

# 틀림 - 런타임 파라미터 미지원
runner.run(input="...", temperature=0.7)
```

## 파라미터 지원 매트릭스

| 파라미터 | OpenAI | Anthropic | Google | OpenRouter |
|----------|--------|-----------|--------|------------|
| temperature | O | O | O | O |
| top_p | O | O | O | O |
| max_tokens | O | O | max_output_tokens | O |
| reasoning_effort | O (o1/o3/gpt-5) | X | X | O (패스스루) |
| presence_penalty | O | X | X | O |

### 모델별 지원 파라미터

```python
_MODEL_SUPPORTED_OPTIONAL_KEYS: Mapping[str, set[str]] = {
    "gpt-5.2": {
        "max_output_tokens", "metadata", "reasoning",
        "response_format", "tools", "modalities", "store", "text",
    },
    "gpt-5": {
        "max_output_tokens", "metadata", "reasoning",
        "response_format", "tools", "modalities", "store", "text",
    },
    "gpt-4o": {
        "max_output_tokens", "temperature", "top_p", "metadata",
        "response_format", "tools", "modalities", "store",
    },
    "gpt-4o-mini": {
        "max_output_tokens", "temperature", "top_p", "metadata", "store",
    },
    "o3-mini": {
        "max_output_tokens", "temperature", "top_p", "store", "metadata",
    },
}

_MODEL_DEFAULT_OPTIONAL_VALUES: Mapping[str, Dict[str, Any]] = {
    "gpt-4o": {"top_p": 0.9},
    "gpt-4o-mini": {"top_p": 0.9},
    "o3-mini": {"top_p": 0.9, "store": True},
}
```

**추론 모델 (o1/o3)**: `reasoning_effort`, `max_output_tokens`만 허용. `temperature`, `top_p` 등 금지.

```python
O1_MODEL_PARAMS = {"reasoning_effort", "max_output_tokens"}
O1_UNSUPPORTED_PARAMS = {"temperature", "top_p", "presence_penalty", "frequency_penalty"}
```

## Thinking/Reasoning 파라미터

| 프로바이더 | 파라미터 | 값 |
|-----------|----------|--------|
| OpenAI (o1/o3/gpt-5) | `reasoning_effort` | `low`, `medium`, `high` |
| Anthropic (Claude 3.7+) | `thinking.budget_tokens` | 최소 1024 |
| Google (Gemini 3) | `thinking_level` | `minimal`, `low`, `medium`, `high` |
| OpenRouter | 통합 `reasoning` | 하위 모델에 패스스루 |

## OpenRouter 설정

```python
@dataclass
class OpenRouterConfig:
    """OpenRouter 전용 설정"""

    # 라우팅 & 폴백
    models: Optional[List[str]] = None           # 폴백 모델
    route: Optional[str] = None                  # 'fallback'
    suffix: Optional[str] = None                 # ':nitro', ':floor', ':online', ':free'
    fallback_enabled: bool = True

    # 프로바이더 제어
    provider_order: Optional[List[str]] = None   # 프로바이더 우선순위
    provider_sort: Optional[str] = None          # 'throughput' | 'price'
    provider_require_parameters: bool = False

    # Reasoning (GPT-5, o1, o3, Grok-3)
    reasoning_effort: Optional[str] = None       # none~xhigh
    reasoning_max_tokens: Optional[int] = None

    # Thinking (Gemini 3)
    thinking_level: Optional[str] = None         # minimal~high

    # Headers
    app_name: Optional[str] = None               # X-Title
    site_url: Optional[str] = None               # HTTP-Referer
```

### OpenRouter 티어

| 티어 | 용도 | 특징 |
|------|------|------|
| FAST | 높은 처리량 | 저비용, 고속 |
| BALANCED | 범용 | 중간 품질/속도 |
| POWERFUL | 복잡한 추론 | 최고 품질 |
| CODING | 코드 생성 | 코드 최적화 |

고급: 폴백 배열, 프로바이더 순서, 접미사 라우팅 (`:nitro`, `:floor`, `:free`, `:online`)

## FallbackProvider (폴백 + 서킷 브레이커)

```python
@dataclass(frozen=True)
class FallbackConfig:
    """폴백 프로바이더 설정"""
    provider_order: List[str] = field(default_factory=lambda: ["openrouter", "openai"])
    use_circuit_breaker: bool = True
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    max_fallback_attempts: int = -1           # -1 = 전부 시도
    fail_fast_on_all_open: bool = False


@dataclass
class FallbackResult:
    """폴백 프로바이더 호출 결과"""
    response: Optional[AIResponse]
    provider_used: Optional[str]
    providers_tried: List[str]
    fallback_used: bool
    errors: Dict[str, str]
    total_latency_ms: float


class FallbackProvider:
    """다중 프로바이더 페일오버 + 서킷 브레이커 통합"""

    def __init__(
        self,
        providers: Sequence[BaseProvider],
        config: Optional[FallbackConfig] = None,
        circuit_registry: Optional[CircuitBreakerRegistry] = None,
    ):
        self.config = config or DEFAULT_FALLBACK_CONFIG
        self._providers: Dict[str, BaseProvider] = {}
        self._circuit_registry = circuit_registry or CircuitBreakerRegistry()
        self._circuits: Dict[str, AsyncCircuitBreaker] = {}

        # 프로바이더 등록 및 서킷 브레이커 생성
        for provider in providers:
            self._providers[provider.name] = provider

    async def call(self, request: AIRequest) -> AIResponse:
        """자동 폴백으로 요청 실행"""
        result = await self.call_with_details(request)
        if result.response is None:
            raise AllProvidersFailedError(...)
        return result.response

    async def call_with_details(self, request: AIRequest) -> FallbackResult:
        """상세 폴백 정보와 함께 실행"""
        # 1. 모든 서킷이 OPEN인지 확인
        # 2. 우선순위 순으로 프로바이더 시도
        # 3. OPEN 서킷 프로바이더 건너뛰기
        # 4. 에러 및 지연시간 추적

    def get_circuit_states(self) -> Dict[str, str]:
        """모든 프로바이더의 현재 서킷 브레이커 상태 조회"""
```

## ResilientProvider (래퍼 패턴)

```python
class ResilientProvider(BaseProvider):
    """모든 BaseProvider에 복원력을 추가하는 데코레이터

    데코레이터 패턴 구현:
    - 서킷 브레이커: 프로바이더가 불건전할 때 호출 방지
    - 재시도: 지수 백오프로 자동 재시도
    - 메트릭: 성공/실패율 기록
    """

    def __init__(
        self,
        provider: BaseProvider,
        config: Optional[ResilientConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        self._provider = provider
        self._config = config or DEFAULT_RESILIENT_CONFIG
        self._circuit_breaker: Optional[AsyncCircuitBreaker] = None

    async def call(self, request: AIRequest) -> AIResponse:
        """복원력 적용하여 실행 (서킷 브레이커 + 재시도 + 메트릭)"""

    async def _call_with_retry_and_circuit_breaker(self, request: AIRequest) -> AIResponse:
        """재시도와 서킷 브레이커 모두 적용

        순서 중요: 재시도는 서킷 브레이커 내부에서 적용
        """

    def get_circuit_state(self) -> Optional[str]:
        """현재 서킷 브레이커 상태 조회"""

    async def reset_circuit(self) -> None:
        """수동으로 서킷을 CLOSED 상태로 리셋"""
```

## 서킷 브레이커 패턴

```python
class CircuitState(str, Enum):
    CLOSED = "closed"       # 정상 상태, 모든 요청 허용
    OPEN = "open"           # 실패 상태, 모든 요청 거부
    HALF_OPEN = "half_open" # 복구 테스트 상태, 제한된 요청 허용


@dataclass(frozen=True)
class CircuitBreakerConfig:
    """서킷 브레이커 설정"""
    failure_threshold: int = 5           # OPEN 트리거 실패 횟수
    recovery_timeout: float = 30.0       # HALF_OPEN 전환까지 초
    half_open_max_calls: int = 3         # HALF_OPEN에서 최대 요청 수
    success_threshold: int = 2           # CLOSED 복귀 성공 횟수
```

### 상태 전이 다이어그램

```
CLOSED (정상)
  ↓ (failure_threshold 실패)
OPEN (즉시 실패)
  ↓ (recovery_timeout 경과)
HALF_OPEN (테스트 호출)
  ↓ (success_threshold 성공)
CLOSED (복구됨)
```

**재시도 대상**: `RATE_LIMIT`, `TIMEOUT`, `SERVER_ERROR`, `CONNECTION_ERROR`만 재시도

## 파라미터 정책 적용

```python
def apply_model_param_policy(
    model: str,
    base_params: Mapping[str, Any],
    optional_params: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """모델 능력에 맞게 파라미터 필터링

    예시 - GPT-5는 temperature 제외:
        apply_model_param_policy(
            "gpt-5",
            {"model": "gpt-5", "input": "test"},
            {"temperature": 0.7, "max_output_tokens": 1000}
        )
        # Returns: {'model': 'gpt-5', 'input': 'test', 'max_output_tokens': 1000}
    """


def retarget_params_for_model(
    params: Mapping[str, Any],
    model: str,
) -> Dict[str, Any]:
    """폴백 시 모델 전환할 때 파라미터 재조정

    예시 - gpt-5에서 gpt-4o로 폴백 시 reasoning 제외:
        retarget_params_for_model(
            {"model": "gpt-5", "input": "test", "reasoning": {...}},
            "gpt-4o"
        )
        # Returns: {'model': 'gpt-4o', 'input': 'test', 'top_p': 0.9}
    """
```

## 확장: 새 프로바이더 추가 (3단계)

1. `ProviderBase` 구현 → `core/ai/providers/{name}/provider.py`
2. 모델 패턴 추가 → `core/ai/providers/constants.py`
3. 포맷터 메서드 추가 → `MessageFormatter.to_{name}_api()`

변경 불필요: orchestrator, handlers, services, router.

## 규칙

- 프로바이더 비의존 코드는 통합 타입만 사용
- SDK 타입은 `core/ai/providers/{provider}/` 내부에만, 외부는 `TYPE_CHECKING` + 지연 import
- 모든 새 프로바이더를 중앙 레지스트리에 등록
- API 호출 전 지원 매트릭스에 따라 파라미터 필터링
- 추론 모델 파라미터 별도 검증 (o1/o3 제한)
- 리소스 정리를 위해 항상 `aclose()` 구현
- 외부 프로바이더 호출에 서킷 브레이커 적용
- 핸들러/오케스트레이터는 반드시 무상태

## 절대 하지 말 것

- `core/ai/providers/{provider}/` 외부에서 SDK 타입 import
- 프로바이더 선택 하드코딩 (패턴 기반 자동 라우팅 사용)
- API 메시지 형식 하드코딩 (MessageFormatter 사용)
- 미지원 파라미터를 프로바이더에 전송
- 여러 프로바이더에 동일 서킷 브레이커 인스턴스 사용
- 폴백 시 파라미터 재조정 생략 (`retarget_params_for_model` 사용)
- SSE 이벤트 페이로드에 usage/metadata 전송
- `start`/`done` SSE 이벤트 생략
- 스트리밍 중 이벤트 루프 차단
