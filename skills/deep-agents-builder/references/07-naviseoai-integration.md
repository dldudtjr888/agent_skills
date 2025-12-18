# naviseoAI 프로젝트 통합 가이드

Deep Agents를 naviseoAI 프로젝트 아키텍처에 통합하는 방법입니다.

---

## naviseoAI 아키텍처 개요

```
naviseoAI/
├── core/                    # 범용 AI 프레임워크 (재사용 가능)
│   ├── ai/providers/        # Provider 추상화 (OpenAI, Anthropic, LangChain)
│   ├── runtime/             # AgentRuntime, Protocols
│   ├── config/              # ConfigLoader
│   └── ...
├── navis/                   # 프로젝트 특화 구현
│   ├── specialists/         # 에이전트 빌드 (supervisor, mysql, plan, research)
│   └── ...
├── services/                # 비즈니스 로직
├── config/                  # YAML 설정 파일
│   ├── agents.yaml          # 에이전트 설정
│   └── ...
└── prompts/                 # 프롬프트 관리
    └── orchestrator/        # 에이전트별 프롬프트
```

---

## 1. Provider 정의 (core/ai/providers/)

### BaseProvider 인터페이스

모든 Provider는 `core/ai/providers/base.py`의 `BaseProvider`를 구현합니다.

```python
# core/ai/providers/base.py
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Provider abstract interface"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., "openai", "langchain", "deepagents")"""
        pass

    @abstractmethod
    async def call(self, request: AIRequest) -> AIResponse:
        """Execute API call"""
        pass

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """Check if this provider supports the given model"""
        pass

    @abstractmethod
    def transform_request(self, request: AIRequest) -> Dict[str, Any]:
        """Transform AIRequest to provider-specific format"""
        pass

    @abstractmethod
    def transform_response(self, raw_response: Any) -> AIResponse:
        """Transform provider response to AIResponse"""
        pass

    @abstractmethod
    async def aclose(self) -> None:
        """Close async client and cleanup resources"""
        pass
```

### Deep Agents Provider 구현

```python
# core/ai/providers/deepagents/__init__.py
from .provider import DeepAgentsProvider

__all__ = ["DeepAgentsProvider"]
```

```python
# core/ai/providers/deepagents/provider.py
from typing import Any, Dict
from deepagents import create_deep_agent
from ..base import BaseProvider
from ...ai_types import AIRequest, AIResponse


class DeepAgentsProvider(BaseProvider):
    """Deep Agents Provider for naviseoAI"""

    def __init__(
        self,
        model: str = "anthropic:claude-sonnet-4-20250514",
        tools: list = None,
        system_prompt: str = "",
        subagents: list = None,
        middleware: list = None,
    ):
        self._model = model
        self._tools = tools or []
        self._system_prompt = system_prompt
        self._subagents = subagents or []
        self._middleware = middleware or []
        self._agent = None

    @property
    def name(self) -> str:
        return "deepagents"

    def _ensure_agent(self):
        """Lazy initialization of agent"""
        if self._agent is None:
            self._agent = create_deep_agent(
                model=self._model,
                tools=self._tools,
                system_prompt=self._system_prompt,
                subagents=self._subagents,
                middleware=self._middleware,
            )
        return self._agent

    async def call(self, request: AIRequest) -> AIResponse:
        agent = self._ensure_agent()
        params = self.transform_request(request)
        result = agent.invoke(params)
        return self.transform_response(result)

    def supports_model(self, model: str) -> bool:
        # Deep Agents는 다양한 모델 지원
        supported_prefixes = ["anthropic:", "openai:", "google:"]
        return any(model.startswith(p) for p in supported_prefixes)

    def transform_request(self, request: AIRequest) -> Dict[str, Any]:
        return {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]
        }

    def transform_response(self, raw_response: Any) -> AIResponse:
        last_message = raw_response["messages"][-1]
        return AIResponse(
            content=last_message.content,
            model=self._model,
            usage=raw_response.get("usage", {}),
        )

    async def aclose(self) -> None:
        self._agent = None
```

### Provider Registry 등록

```python
# core/ai/providers/registry.py
from .deepagents import DeepAgentsProvider

# Provider 등록
PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "langchain": LangChainProvider,
    "deepagents": DeepAgentsProvider,  # Deep Agents 추가
}
```

---

## 2. 에이전트 빌드 (navis/specialists/)

### Deep Agents 기반 Specialist 구현

```python
# navis/specialists/deep_research.py
"""Deep Agents 기반 Research Specialist"""

from typing import Any
from langchain_core.tools import tool
from deepagents import create_deep_agent
from core import ConfigLoader, get_logger

logger = get_logger(__name__)


@tool
def tavily_search(query: str, max_results: int = 5) -> str:
    """Run web search using Tavily"""
    from tavily import TavilyClient
    import os

    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return client.search(query, max_results=max_results)


class DeepResearchSpecialist:
    """Deep Agents 기반 Research Specialist"""

    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader.get("agents.deep_research", {})
        self.agent = self._build_agent()

    def _build_agent(self):
        """에이전트 빌드"""
        return create_deep_agent(
            model=self.config.get("model", "anthropic:claude-sonnet-4-20250514"),
            tools=[tavily_search],
            system_prompt=self._load_prompt(),
            subagents=self._build_subagents(),
        )

    def _load_prompt(self) -> str:
        """prompts/에서 프롬프트 로드"""
        from pathlib import Path
        import yaml

        prompt_path = Path("prompts/orchestrator/deep_research.yaml")
        if prompt_path.exists():
            with open(prompt_path) as f:
                data = yaml.safe_load(f)
                return data.get("system", "")
        return ""

    def _build_subagents(self) -> list:
        """서브에이전트 구성"""
        return [
            {
                "name": "fact-checker",
                "description": "Verify facts and claims",
                "system_prompt": "You verify facts using web search.",
                "tools": [tavily_search],
            },
            {
                "name": "summarizer",
                "description": "Summarize research findings",
                "system_prompt": "You summarize findings concisely.",
                "tools": [],
            },
        ]

    async def run(self, query: str) -> dict:
        """에이전트 실행"""
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        return {
            "content": result["messages"][-1].content,
            "metadata": {"agent": "deep_research"}
        }
```

---

## 3. 비즈니스 로직 (services/)

### Orchestrator Service 통합

```python
# services/orchestrator_service.py
"""Deep Agents 통합 Orchestrator Service"""

from typing import AsyncIterator
from core import ConfigLoader, get_logger
from navis.specialists.deep_research import DeepResearchSpecialist

logger = get_logger(__name__)


class OrchestratorService:
    """에이전트 오케스트레이션 서비스"""

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self._agents = {}

    def _get_agent(self, agent_type: str):
        """에이전트 lazy initialization"""
        if agent_type not in self._agents:
            if agent_type == "deep_research":
                self._agents[agent_type] = DeepResearchSpecialist(self.config_loader)
            # 다른 에이전트 타입 추가...
        return self._agents[agent_type]

    async def route_and_execute(
        self,
        message: str,
        context_type: str = "general",
    ) -> AsyncIterator[str]:
        """메시지 라우팅 및 실행"""
        # 컨텍스트에 따라 적절한 에이전트 선택
        if context_type == "research":
            agent = self._get_agent("deep_research")
            result = await agent.run(message)
            yield result["content"]
        else:
            # 기존 로직...
            pass
```

---

## 4. Config 관리 (config/)

### agents.yaml 설정 추가

```yaml
# config/agents.yaml

agents:
  # 기존 에이전트들...
  supervisor:
    model: "gpt-5.2"
    # ...

  # Deep Agents 기반 에이전트
  deep_research:
    name: "Deep Research Specialist"
    model: "anthropic:claude-sonnet-4-20250514"  # Deep Agents 모델 형식
    prompt_version: "v1"  # prompts/orchestrator/deep_research.yaml

    # Deep Agents 특화 설정
    deepagents:
      subagents:
        - name: "fact-checker"
          model: "openai:gpt-4o"  # 서브에이전트 모델 오버라이드
        - name: "summarizer"
          model: "anthropic:claude-sonnet-4-20250514"

      # 백엔드 설정 (프로덕션용)
      backend:
        type: "runloop"  # virtual, runloop, daytona, modal
        api_key: "${RUNLOOP_API_KEY}"

      # 미들웨어 설정
      middleware:
        filesystem: true
        subagents: true

    # 도구 설정
    tools:
      tavily:
        enabled: true
        api_key: "${TAVILY_API_KEY}"
```

### ConfigLoader 사용

```python
# 설정 로드
from core import ConfigLoader

config_loader = ConfigLoader("config")
deep_research_config = config_loader.get("agents.deep_research")

# 환경변수 치환 자동 처리
# ${TAVILY_API_KEY} → 실제 환경변수 값
```

---

## 5. Prompts 관리 (prompts/)

### 프롬프트 파일 구조

```yaml
# prompts/orchestrator/deep_research.yaml
versions:
  v1:
    system: |
      You are a Deep Research Specialist powered by Deep Agents.

      ## Capabilities
      - Web search with Tavily
      - Task planning with todos
      - Subagent delegation for specialized tasks
      - File-based context management

      ## Workflow
      1. Analyze the research question
      2. Create a plan using write_todos
      3. Delegate to subagents for:
         - Fact checking
         - Summarization
      4. Synthesize findings into a report
      5. Save report to /final_report.md

      ## Guidelines
      - Always verify claims with fact-checker
      - Use summarizer for concise outputs
      - Save intermediate results to filesystem

current: v1
```

### 프롬프트 버전 관리

```python
# navis/specialists/deep_research.py
def _load_prompt(self) -> str:
    """버전 관리된 프롬프트 로드"""
    import yaml
    from pathlib import Path

    prompt_path = Path("prompts/orchestrator/deep_research.yaml")
    version = self.config.get("prompt_version", "v1")

    with open(prompt_path) as f:
        data = yaml.safe_load(f)
        current = data.get("current", version)
        versions = data.get("versions", {})
        return versions.get(current, {}).get("system", "")
```

---

## 6. 통합 체크리스트

### Provider 추가
- [ ] `core/ai/providers/deepagents/provider.py` 생성
- [ ] `core/ai/providers/deepagents/__init__.py` 생성
- [ ] `core/ai/providers/registry.py`에 등록

### Specialist 추가
- [ ] `navis/specialists/deep_research.py` 생성
- [ ] `navis/specialists/__init__.py`에 export 추가

### 설정 추가
- [ ] `config/agents.yaml`에 `deep_research` 섹션 추가
- [ ] 환경변수 추가 (`.env`)
  - `TAVILY_API_KEY`
  - `RUNLOOP_API_KEY` (프로덕션)

### 프롬프트 추가
- [ ] `prompts/orchestrator/deep_research.yaml` 생성

### Service 통합
- [ ] `services/orchestrator_service.py` 수정
- [ ] 라우팅 로직 추가

### 테스트
- [ ] `tests/unit/specialists/test_deep_research.py` 작성
- [ ] `tests/integration/test_deep_agents.py` 작성

---

## 참고

- [core/README.md](../../../../../core/README.md): Core 모듈 상세
- [docs/status/architecture.md](../../../../../docs/status/architecture.md): 전체 아키텍처
- [config/README.md](../../../../../config/README.md): 설정 관리
- [prompts/README.md](../../../../../prompts/README.md): 프롬프트 관리
