# Deep Agents API 레퍼런스

## create_deep_agent()

Deep Agent를 생성하는 메인 함수입니다.

### 시그니처

```python
def create_deep_agent(
    model: str | BaseChatModel = "claude-sonnet-4-5-20250929",
    tools: list[BaseTool | Callable] = [],
    system_prompt: str = "",
    middleware: list[AgentMiddleware] = [],
    subagents: list[SubAgent | CompiledSubAgent] = [],
    backend: Backend | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None
) -> CompiledGraph
```

### 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `model` | `str \| BaseChatModel` | `"claude-sonnet-4-5-20250929"` | 사용할 LLM 모델 |
| `tools` | `list[BaseTool \| Callable]` | `[]` | 커스텀 도구 목록 |
| `system_prompt` | `str` | `""` | 도메인별 지침 |
| `middleware` | `list[AgentMiddleware]` | `[]` | 미들웨어 목록 |
| `subagents` | `list[SubAgent \| CompiledSubAgent]` | `[]` | 서브에이전트 목록 |
| `backend` | `Backend \| None` | `None` | 파일시스템 백엔드 |
| `interrupt_on` | `dict` | `None` | 인터럽트 설정 |

### 모델 지정 방식

```python
# 문자열 형식 (권장)
agent = create_deep_agent(model="anthropic:claude-sonnet-4-20250514")
agent = create_deep_agent(model="openai:gpt-4o")

# LangChain 모델 객체
from langchain.chat_models import init_chat_model
model = init_chat_model("anthropic:claude-sonnet-4-20250514", temperature=0.0)
agent = create_deep_agent(model=model)
```

### 반환값

```python
CompiledGraph  # LangGraph 컴파일된 그래프
```

### 기본 사용 예시

```python
from deepagents import create_deep_agent
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """My custom tool."""
    return f"Result for: {query}"

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[my_tool],
    system_prompt="You are a helpful assistant."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Hello!"}]
})
```

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
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]  # 인터럽트 설정
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

### stream()

스트리밍 실행 메서드입니다.

```python
for event in agent.stream({
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
