# Create Agent

LangChain 1.0 unified agent creation API (built on LangGraph).

## Basic Usage

```python
from langchain.agents import create_agent

def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

agent = create_agent(
    model="gpt-4o",
    tools=[calculator],
    system_prompt="You are a helpful assistant.",
)

result = agent.invoke({"messages": [{"role": "user", "content": "What's 2+2?"}]})
print(result["messages"][-1]["content"])
```

## Model Options

```python
# String identifier (recommended)
agent = create_agent("gpt-4o", tools)
agent = create_agent("gpt-4o-mini", tools)
agent = create_agent("claude-sonnet-4-20250514", tools)

# Or explicit ChatModel instance
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o", temperature=0)
agent = create_agent(model, tools)
```

## With Persistence

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="gpt-4o",
    tools=[calculator],
    system_prompt="You are helpful.",
    checkpointer=InMemorySaver(),
)

config = {"configurable": {"thread_id": "user-123"}}
result = agent.invoke({"messages": [{"role": "user", "content": "Hi"}]}, config)
```

## Streaming

```python
for chunk in agent.stream({"messages": [{"role": "user", "content": "Hello"}]}):
    print(chunk)

# Messages only
for chunk in agent.stream(input, stream_mode="messages"):
    print(chunk["content"], end="")
```

## Key Parameters

| Parameter | Purpose |
|-----------|---------|
| `model` | LLM (string or ChatModel) |
| `tools` | List of tool functions |
| `system_prompt` | System instructions |
| `checkpointer` | State persistence |
| `interrupt_before` | Human-in-the-loop nodes |
| `middleware` | Custom middleware list |
| `response_format` | Structured output config |

## Structured Output

```python
from pydantic import BaseModel
from langchain.agents.structured_output import ToolStrategy

class ContactInfo(BaseModel):
    name: str
    email: str

agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_tool],
    response_format=ToolStrategy(ContactInfo),
)
```

## Migration Note

```python
# ❌ OLD (deprecated)
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model, tools, prompt="...")

# ✅ NEW (LangChain 1.0)
from langchain.agents import create_agent
agent = create_agent(model, tools, system_prompt="...")
```

## Docs

- https://docs.langchain.com/oss/python/langchain/agents
- https://reference.langchain.com/python/langgraph/agents/
