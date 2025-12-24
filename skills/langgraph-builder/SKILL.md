---
name: langgraph-builder
description: >
  Build LLM agents with LangGraph. Use for: ReAct agents, multi-agent (supervisor/swarm),
  stateful workflows, human-in-the-loop. Always fetch latest docs via URLs provided.
---

# LangGraph Builder

## Official Documentation (Always Fetch Latest)

- **Docs**: https://langchain-ai.github.io/langgraph/
- **API Reference**: https://reference.langchain.com/python/langgraph/agents/
- **PyPI**: https://pypi.org/project/langgraph/ (v1.0.5)

## Quick Start

```python
from langchain.agents import create_agent

def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

agent = create_agent(
    model="gpt-4o",
    tools=[search],
    system_prompt="You are a helpful assistant.",
)

result = agent.invoke({"messages": [{"role": "user", "content": "Search for Python tutorials"}]})
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: invoke() without compile()
graph = StateGraph(State)
graph.invoke(input)  # Error!

# ❌ WRONG: Mutating state directly
def node(state):
    state["items"].append(item)  # Never mutate!
    return state

# ❌ WRONG: interrupt without checkpointer
app = graph.compile(interrupt_before=["review"])  # Needs checkpointer!

# ❌ WRONG: List without reducer
class State(TypedDict):
    messages: list  # Will overwrite, not append!

# ❌ WRONG: Tool without docstring
def bad_tool(x): return x  # LLM can't understand!

# ✅ CORRECT patterns
app = graph.compile()
result = app.invoke(input)

def node(state):
    return {"items": [*state["items"], item]}  # Return new state

app = graph.compile(checkpointer=InMemorySaver(), interrupt_before=["review"])

class State(TypedDict):
    messages: Annotated[list, add_messages]  # Use reducer

def good_tool(x: str) -> str:
    """Process the input string."""
    return x
```

## Reference Guides

- [Create Agent](references/create-agent.md) - prebuilt agent, model shorthand
- [Middleware](references/middleware.md) - PII, summarization, guardrails
- [Multi-Agent](references/multi-agent.md) - supervisor, swarm patterns
- [Persistence](references/persistence.md) - checkpointer, memory
- [Decision Tree](references/decision-tree.md) - pattern selection

## Version Info

- **langgraph**: 1.0.5 (Dec 2025)
- **langgraph-supervisor**: 0.0.31
- **langgraph-swarm**: 0.1.0
- **Python**: >=3.10
