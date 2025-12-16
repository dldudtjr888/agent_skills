# Pattern Selection Decision Tree

## Q1: How many agents?

**Single agent** → Go to Q2  
**Multiple agents** → Go to Q4

---

## Q2: Does the agent need tools?

**No** → Simple chain (single-node StateGraph)  
**Yes** → Go to Q3

---

## Q3: Is basic ReAct sufficient?

**Yes** → Use `create_agent()` (langchain v1.0+)
```python
# NEW (v1.0+)
from langchain.agents import create_agent
agent = create_agent(model, tools, prompt="...")

# OLD (deprecated, still works)
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model, tools, prompt="...")
```

**No** (need custom logic, state, routing) → Build ReAct from scratch
- Fetch: `react-agent-from-scratch` how-to guide
- Use: Custom StateGraph with agent + tools nodes

---

## Q4: What's the agent relationship?

**Central coordination needed** → Supervisor pattern
- One supervisor routes to specialized agents
- Fetch: `langgraph-supervisor` docs

**Peer-to-peer collaboration** → Swarm pattern  
- Agents hand off to each other directly
- Fetch: `langgraph-swarm` docs

**Fixed sequential pipeline** → Sequential graph
- Explicit edges between agent nodes

**Dynamic branching** → Conditional edges + subgraphs
- Use `add_conditional_edges()` for routing

---

## Q5: Human intervention needed?

**Yes** → Add `interrupt_before` or `interrupt_after`
```python
app = graph.compile(
    checkpointer=checkpointer,  # Required!
    interrupt_before=["sensitive_node"]
)
```

**No** → Standard execution

---

## Q6: Conversation persistence needed?

**Within session only** → Checkpointer with `thread_id`
```python
from langgraph.checkpoint.memory import InMemorySaver
app = graph.compile(checkpointer=InMemorySaver())
app.invoke(input, config={"configurable": {"thread_id": "user-123"}})
```

**Across sessions (long-term memory)** → Store
```python
from langgraph.store.memory import InMemoryStore
app = graph.compile(store=InMemoryStore())
```

**Both** → Use both checkpointer and store

---

## Quick Pattern Summary

| Scenario | Pattern | Key Components |
|----------|---------|----------------|
| Simple tool-calling bot | Prebuilt Agent | `create_agent` (langchain) |
| Custom agent logic | Custom ReAct | StateGraph + ToolNode + tools_condition |
| Team of specialists | Supervisor | `create_supervisor` or custom |
| Collaborative agents | Swarm | Handoff tools |
| Approval workflows | HITL | interrupt_before + checkpointer |
| Chatbot with memory | Persistence | Checkpointer + thread_id |
| Parallel processing | Map-Reduce | Send API |
