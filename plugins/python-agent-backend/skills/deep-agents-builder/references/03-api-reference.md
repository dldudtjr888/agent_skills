# Deep Agents API 레퍼런스

> **최종 업데이트**: 2026-01-23 (deepagents 0.3.8)

## create_deep_agent()

Deep Agent를 생성하는 메인 함수입니다.

### 시그니처

```python
def create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: list[SubAgent | CompiledSubAgent] | None = None,
    response_format: ResponseFormat | None = None,
    context_schema: type[Any] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```

### 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `model` | `str \| BaseChatModel \| None` | `None` → Claude Sonnet 4.5 | 사용할 LLM 모델 |
| `tools` | `Sequence[BaseTool \| Callable \| dict]` | `None` | 커스텀 도구 목록 |
| `system_prompt` | `str \| None` | `None` | 기본 프롬프트에 **추가**되는 도메인별 지침 |
| `middleware` | `Sequence[AgentMiddleware]` | `()` | 기본 미들웨어에 **추가**되는 커스텀 미들웨어 |
| `subagents` | `list[SubAgent \| CompiledSubAgent]` | `None` | 서브에이전트 목록 |
| `response_format` | `ResponseFormat \| None` | `None` | 구조화된 출력 포맷 |
| `context_schema` | `type[Any] \| None` | `None` | 커스텀 상태 스키마 |
| `checkpointer` | `Checkpointer \| None` | `None` | 상태 영속화 (HITL 필수) |
| `store` | `BaseStore \| None` | `None` | LangGraph Store (장기 메모리) |
| `backend` | `BackendProtocol \| BackendFactory` | `None` | 파일시스템 백엔드 |
| `interrupt_on` | `dict[str, bool \| InterruptOnConfig]` | `None` | Human-in-the-loop 설정 |
| `debug` | `bool` | `False` | 디버그 모드 |
| `name` | `str \| None` | `None` | 에이전트 이름 (트레이스용) |
| `cache` | `BaseCache \| None` | `None` | 응답 캐시 |

### SystemMessage 지원 (0.3.7+)

LangChain `SystemMessage`를 직접 사용할 수 있습니다:

```python
from langchain_core.messages import SystemMessage

# 기존 방식 (system_prompt 파라미터)
agent = create_deep_agent(system_prompt="You are a helpful assistant.")

# 새로운 방식 (SystemMessage 직접 사용)
from deepagents import create_deep_agent

agent = create_deep_agent()
result = agent.invoke({
    "messages": [
        SystemMessage(content="You are a helpful assistant."),
        {"role": "user", "content": "Hello!"}
    ]
})
```

### 모델 지정 방식

```python
# 문자열 형식 (권장)
agent = create_deep_agent(model="anthropic:claude-sonnet-4-5-20250929")
agent = create_deep_agent(model="openai:gpt-4o")

# LangChain 모델 객체
from langchain.chat_models import init_chat_model
model = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0.0)
agent = create_deep_agent(model=model)
```

### 반환값

```python
CompiledStateGraph  # LangGraph 컴파일된 그래프 (recursion_limit=1000)
```

---

## 기본 미들웨어 스택 (7개)

`create_deep_agent()`는 자동으로 다음 미들웨어를 순서대로 적용합니다:

| 순서 | 미들웨어 | 역할 |
|------|---------|------|
| 1 | **TodoListMiddleware** | `write_todos`, `read_todos` 도구 제공 |
| 2 | **FilesystemMiddleware** | `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` |
| 3 | **SubAgentMiddleware** | `task` 도구로 서브에이전트 위임 |
| 4 | **SummarizationMiddleware** | 170k 토큰 또는 모델 최대의 85%에서 자동 압축 |
| 5 | **AnthropicPromptCachingMiddleware** | Anthropic 모델 프롬프트 캐싱 |
| 6 | **PatchToolCallsMiddleware** | 체크포인트 중단된 도구 호출 복구 |
| 7 | **HumanInTheLoopMiddleware** | `interrupt_on` 설정 시에만 활성화 |

---

## TypedDict 스키마

### SubAgent

서브에이전트 설정을 위한 TypedDict입니다.

```python
from typing import TypedDict, NotRequired, Sequence, Callable, Any
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain.agents.middleware import AgentMiddleware

class SubAgent(TypedDict):
    name: str                                          # 서브에이전트 이름
    description: str                                   # 서브에이전트 설명
    prompt: str                                        # 시스템 프롬프트 (또는 system_prompt)
    tools: Sequence[BaseTool | Callable | dict[str, Any]]  # 도구 목록
    model: NotRequired[str | BaseChatModel]            # 선택적 모델 오버라이드
    middleware: NotRequired[list[AgentMiddleware]]     # 선택적 미들웨어
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]
```

### CompiledSubAgent

사전 빌드된 서브에이전트를 위한 TypedDict입니다.

```python
from langchain_core.runnables import Runnable

class CompiledSubAgent(TypedDict):
    name: str                  # 서브에이전트 이름
    description: str           # 서브에이전트 설명
    runnable: Runnable         # 실행 가능한 LangGraph 그래프
```

### InterruptOnConfig

Human-in-the-loop 설정을 위한 TypedDict입니다.

```python
class InterruptOnConfig(TypedDict):
    allowed_decisions: list[Literal["approve", "edit", "reject"]]
```

---

## Agent 메서드

### invoke()

동기 실행 메서드입니다.

```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "Your query"}]
})

# 결과 접근
print(result["messages"][-1].content)
```

### ainvoke()

비동기 실행 메서드입니다.

```python
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Your query"}]
})
```

### stream()

스트리밍 실행 메서드입니다.

```python
for event in agent.stream({
    "messages": [{"role": "user", "content": "Your query"}]
}):
    print(event)
```

### astream()

비동기 스트리밍 메서드입니다.

```python
async for event in agent.astream({
    "messages": [{"role": "user", "content": "Your query"}]
}):
    print(event)
```

### get_graph()

에이전트 그래프를 반환합니다.

```python
graph = agent.get_graph()

# Mermaid 다이어그램으로 시각화
from IPython.display import display, Image
display(Image(graph.draw_mermaid_png()))
```

---

## 사용 예시

### 기본 에이전트

```python
from deepagents import create_deep_agent

agent = create_deep_agent()
result = agent.invoke({
    "messages": [{"role": "user", "content": "Hello!"}]
})
```

### 커스텀 도구

```python
from langchain_core.tools import tool
from deepagents import create_deep_agent

@tool
def my_tool(query: str) -> str:
    """My custom tool."""
    return f"Result for: {query}"

agent = create_deep_agent(
    tools=[my_tool],
    system_prompt="You are a helpful assistant."
)
```

### Human-in-the-Loop

```python
from langgraph.checkpoint.memory import MemorySaver
from deepagents import create_deep_agent

checkpointer = MemorySaver()

agent = create_deep_agent(
    checkpointer=checkpointer,  # 필수!
    interrupt_on={
        "execute": True,
        "write_file": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    }
)
```

### 장기 메모리

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_deep_agent(
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}
    )
)
```

### 구조화된 출력

```python
from pydantic import BaseModel
from deepagents import create_deep_agent

class ResearchReport(BaseModel):
    title: str
    summary: str
    findings: list[str]

agent = create_deep_agent(
    response_format=ResearchReport,
    system_prompt="Generate research reports in the specified format."
)
```

---

## 유틸리티 함수

### file_data_to_string()

파일 데이터를 문자열로 변환합니다.

```python
from deepagents.backends.utils import file_data_to_string

content = file_data_to_string(file_data)
```

### 메시지 포맷팅

```python
from utils import format_messages, format_message_content, show_prompt
from rich.console import Console

console = Console()

# 대화 메시지 포맷팅
format_messages(messages)

# 프롬프트 표시 (XML 하이라이팅)
show_prompt(
    prompt_text=INSTRUCTIONS,
    title="Instructions",
    border_style="blue"
)
```

---

## 다음 단계

- [04-middleware.md](04-middleware.md): 미들웨어 패턴
- [05-subagents.md](05-subagents.md): 서브에이전트 설계
- [08-hitl-memory.md](08-hitl-memory.md): Human-in-the-Loop 및 장기 메모리
