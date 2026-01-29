# Multi-Agent Patterns

Two patterns: **Supervisor** (tools-based orchestration) and **Swarm** (peer-to-peer handoffs).

## Supervisor Pattern (Recommended: Tools-based)

Sub-agents wrapped as tools, orchestrated by supervisor.

```python
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o")

# 1. Create specialized sub-agents
calendar_agent = create_agent(
    model,
    tools=[create_event, check_availability],
    system_prompt="You are a calendar assistant.",
)

email_agent = create_agent(
    model,
    tools=[send_email],
    system_prompt="You are an email assistant.",
)

# 2. Wrap sub-agents as tools
@tool
def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language."""
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def manage_email(request: str) -> str:
    """Send emails using natural language."""
    result = email_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

# 3. Create supervisor with wrapped tools
supervisor = create_agent(
    model,
    tools=[schedule_event, manage_email],
    system_prompt="You coordinate calendar and email tasks.",
)

# 4. Use
result = supervisor.invoke({
    "messages": [{"role": "user", "content": "Schedule meeting and send reminder"}]
})
```

### Why Tools-based?

- **Recommended by LangChain** (langgraph-supervisor library is deprecated for new use)
- Cleaner context (sub-agents don't see supervisor's routing logic)
- Easier testing of individual sub-agents

---

## Swarm Pattern

Agents hand off to each other dynamically.

```bash
pip install langgraph-swarm
```

```python
from langgraph_swarm import create_swarm, create_handoff_tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

alice = create_agent(
    model="gpt-4o",
    tools=[
        math_tool,
        create_handoff_tool(agent_name="Bob", description="Transfer for general questions"),
    ],
    system_prompt="You are Alice, a math expert.",
    name="Alice",
)

bob = create_agent(
    model="gpt-4o",
    tools=[
        search_tool,
        create_handoff_tool(agent_name="Alice", description="Transfer for math"),
    ],
    system_prompt="You are Bob, a general assistant.",
    name="Bob",
)

workflow = create_swarm(
    agents=[alice, bob],
    default_active_agent="Bob",
)

app = workflow.compile(checkpointer=InMemorySaver())
result = app.invoke(
    {"messages": [{"role": "user", "content": "What's 2+2?"}]},
    {"configurable": {"thread_id": "user-123"}}
)
```

---

## When to Use Which

| Scenario | Pattern |
|----------|---------|
| Distinct domains (calendar, email, CRM) | Supervisor |
| Dynamic peer collaboration | Swarm |
| Centralized workflow control | Supervisor |
| Customer service routing | Swarm |

## Common Mistakes

```python
# ❌ WRONG: Sub-agent tool without docstring
@tool
def calendar(req: str) -> str:
    return calendar_agent.invoke(...)  # Supervisor can't understand!

# ❌ WRONG: Swarm agent without name
agent = create_agent(model, tools)  # Missing name!

# ✅ CORRECT
@tool
def calendar(req: str) -> str:
    """Schedule calendar events using natural language."""
    return calendar_agent.invoke(...)

agent = create_agent(model, tools, name="my_agent")
```

## Docs

- Supervisor: https://docs.langchain.com/oss/python/langchain/supervisor
- Swarm: https://github.com/langchain-ai/langgraph-swarm-py
