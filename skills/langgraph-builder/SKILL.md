---
name: langgraph-builder
description: >
  Build production-grade LLM agents and workflows using LangGraph SDK.
  Use for: (1) Creating ReAct agents with tools, (2) Multi-agent supervisor/swarm systems,
  (3) Stateful workflows with memory and persistence, (4) Human-in-the-loop patterns,
  (5) Streaming and deployment to LangGraph Platform.
  Triggers: "langgraph", "agent workflow", "multi-agent", "react agent", "stateful agent",
  "tool calling agent", "agent supervisor", "langgraph platform"
---

# LangGraph Builder

## Core Principles (Stable)

1. **State**: Define with `TypedDict` or Pydantic. Use `Annotated` with reducers for list merging.
2. **Node**: Pure functions `(state) -> partial_state`. Never mutate state directly.
3. **Edge**: Normal (fixed) or Conditional (dynamic routing). Keep routing functions deterministic.
4. **Compile**: Always call `.compile()` before `invoke()`/`stream()`. Add checkpointer here.

## Workflow

1. **Before coding**: `web_fetch` the relevant official docs from `references/url-index.md`
2. **Pattern selection**: Follow decision tree in `references/decision-tree.md`
3. **Implementation**: Reference anti-patterns in `references/anti-patterns.md`
4. **Testing**: Use patterns from `references/testing.md`
5. **Deployment**: Follow `references/production-checklist.md`

## Quick Reference

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph = StateGraph(State)
graph.add_node("agent", agent_fn)
graph.add_edge(START, "agent")
graph.add_edge("agent", END)
app = graph.compile(checkpointer=checkpointer)  # optional
```

## Important

**LangGraph 1.0 (Oct 2025)**: `langgraph.prebuilt` deprecated → use `langchain.agents` instead.
New docs at `docs.langchain.com`. Always `web_fetch` official documentation before implementing.
Check `references/url-index.md` for categorized documentation links.
