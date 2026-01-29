# Pattern Selection

## Quick Decision

```
Single agent + tools? → create_agent
Multiple agents + central control? → Supervisor (tools-based)
Multiple agents + peer handoffs? → Swarm
Need conversation memory? → Add checkpointer
Need human approval? → Add interrupt_before
```

## Pattern Summary

| Scenario | Pattern | Install |
|----------|---------|---------|
| Simple tool-calling | `create_agent` | `langchain` |
| Team with coordinator | Supervisor (tools-based) | `langchain` |
| Peer-to-peer agents | Swarm | `langgraph-swarm` |
| Conversation memory | Checkpointer | `langgraph` |
| Human approval | interrupt_before | `langgraph` |

## Code Snippets

### Single Agent
```python
from langchain.agents import create_agent

agent = create_agent("gpt-4o", tools, system_prompt="...")
```

### Supervisor (Tools-based)
```python
from langchain.tools import tool
from langchain.agents import create_agent

# Wrap sub-agents as tools
@tool
def research(request: str) -> str:
    """Research using natural language."""
    return research_agent.invoke({"messages": [{"role": "user", "content": request}]})

supervisor = create_agent("gpt-4o", tools=[research, code], system_prompt="...")
```

### Swarm
```python
from langgraph_swarm import create_swarm, create_handoff_tool

workflow = create_swarm([agent1, agent2], default_active_agent="agent1")
app = workflow.compile()
```

### With Memory
```python
from langgraph.checkpoint.memory import InMemorySaver

app = graph.compile(checkpointer=InMemorySaver())
app.invoke(input, {"configurable": {"thread_id": "user-123"}})
```

### With Human Approval
```python
app = graph.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["review_node"]
)
```

## Installation

```bash
pip install langchain              # Core (includes create_agent)
pip install langgraph              # State graphs, checkpointing
pip install langgraph-swarm        # Peer-to-peer multi-agent
```
