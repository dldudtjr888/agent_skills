---
name: openrouter-langgraph-builder
description: "Build production multi-agent systems with OpenRouter + LangChain/LangGraph v1.0. Use for: (1) OpenRouter API integration with LangChain v1 create_agent (2) Multi-agent orchestration with supervisor/swarm patterns (3) Migration from OpenAI Agents SDK (4) Model routing strategies for cost/quality/speed optimization (5) Middleware for guardrails, HITL, context management (6) Streaming and structured outputs (7) Production deployment with FastAPI (8) Debugging and observability. Includes maintenance workflows for tracking OpenRouter updates."
---

# OpenRouter + LangGraph Builder

Build scalable, cost-optimized multi-agent systems using OpenRouter with LangChain/LangGraph v1.0.

## Quick Start

```bash
# Install (LangChain v1.0+)
pip install langchain langchain-openai langgraph
pip install langgraph-supervisor  # For multi-agent

# Set API key
export OPENROUTER_API_KEY="your-key"
```

## Core Pattern: OpenRouter + LangChain v1

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# OpenRouter client via ChatOpenAI
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "Your App Name",
    },
)

# Create agent (LangChain v1.0)
agent = create_agent(
    model=llm,
    tools=[my_tool],
    system_prompt="You are a helpful assistant.",
)

# Run
result = agent.invoke({"messages": [{"role": "user", "content": "Hello!"}]})
```

## OpenRouter Model Variants

Use variants for routing optimization:

```python
# Speed optimized
llm_fast = ChatOpenAI(model="anthropic/claude-sonnet-4:nitro", ...)

# Cost optimized  
llm_cheap = ChatOpenAI(model="anthropic/claude-sonnet-4:floor", ...)

# Tool calling accuracy
llm_tools = ChatOpenAI(model="anthropic/claude-sonnet-4:exacto", ...)

# Web search enabled
llm_search = ChatOpenAI(model="anthropic/claude-sonnet-4:online", ...)
```

## Multi-Agent with Supervisor

```python
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver

# Specialized agents
research_agent = create_agent(
    model=ChatOpenAI(model="anthropic/claude-sonnet-4", ...),
    tools=[web_search],
    name="researcher",
)

coding_agent = create_agent(
    model=ChatOpenAI(model="openai/gpt-4o", ...),
    tools=[code_executor],
    name="coder",
)

# Supervisor orchestration
workflow = create_supervisor(
    agents=[research_agent, coding_agent],
    model=ChatOpenAI(model="anthropic/claude-sonnet-4", ...),
    prompt="Route research to researcher, coding to coder.",
)

# Compile with memory
app = workflow.compile(checkpointer=InMemorySaver())
```

## Middleware (LangChain v1.0)

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ToolRetryMiddleware,
    PIIMiddleware,
)

agent = create_agent(
    model=llm,
    tools=[...],
    middleware=[
        ToolRetryMiddleware(max_retries=3),
        PIIMiddleware("email", strategy="redact"),
    ],
)
```

### Custom Middleware

```python
from langchain.agents.middleware import AgentMiddleware

class CostTrackerMiddleware(AgentMiddleware):
    def after_model(self, state, response):
        # Track token usage
        usage = response.usage_metadata
        print(f"Tokens: {usage.total_tokens}")
        return state
```

## Streaming

```python
async for event in agent.astream_events(
    {"messages": [{"role": "user", "content": "Hello"}]},
    version="v2",
):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
```

## Structured Output

```python
from pydantic import BaseModel

class ExtractedInfo(BaseModel):
    name: str
    date: str

agent = create_agent(
    model=llm.with_structured_output(ExtractedInfo),
    tools=[],
)
```

## Provider Routing

```python
# Custom provider order
response = llm.invoke(
    messages,
    extra_body={
        "provider": {
            "order": ["Anthropic", "Azure"],
            "allow_fallbacks": True,
        }
    }
)

# Zero Data Retention
response = llm.invoke(
    messages,
    extra_body={
        "provider": {"data_collection": "deny"}
    }
)
```

## Reference Guides

For comprehensive guides, see references:

### 📡 [OpenRouter API](references/openrouter-api.md)
Complete OpenRouter features: variants, provider routing, exacto, web search, pricing.

### 🤖 [LangChain v1 Agents](references/langchain-v1-agents.md)
create_agent, middleware hooks, state management, checkpointing.

### 🔄 [Multi-Agent Patterns](references/multi-agent-patterns.md)
Supervisor, swarm, handoffs, hierarchical architectures, **context engineering**, **conditional handoffs**.

### 🔀 [Migration Guide](references/migration-guide.md)
OpenAI Agents SDK → LangChain v1 + OpenRouter mapping, **complex handoffs**, **guardrail chains**.

### 💰 [Model Strategy](references/model-strategy.md)
Task-based model selection, cost/quality/speed optimization.

### 🚀 [Production Guide](references/production-guide.md) *(NEW)*
**FastAPI integration**, project structure, environment config, **error handling**, **checkpointing**.

### 🐛 [Debugging Guide](references/debugging-guide.md) *(NEW)*
**LangSmith tracing**, logging setup, **common errors and solutions**, debugging multi-agent.

### 🔧 [Maintenance Guide](references/maintenance-guide.md)
Track OpenRouter updates, version compatibility, web search patterns.

## Quick Reference

### Installation

```bash
pip install langchain langchain-openai langgraph
pip install langgraph-supervisor    # Supervisor pattern
pip install langgraph-swarm         # Swarm pattern
pip install deepagents              # Complex long-running agents
```

### ChatOpenRouter Helper

```python
# Use scripts/openrouter_client.py for reusable client
from openrouter_client import ChatOpenRouter

llm = ChatOpenRouter(model="anthropic/claude-sonnet-4")
llm_fast = ChatOpenRouter(model="anthropic/claude-sonnet-4", variant="nitro")
```

### Key Model Slugs

| Provider | Model | Use Case |
|----------|-------|----------|
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 | General, planning |
| `anthropic/claude-opus-4` | Claude Opus 4 | Complex reasoning |
| `openai/gpt-4o` | GPT-4o | Coding, multimodal |
| `openai/gpt-4o-mini` | GPT-4o Mini | Cost-efficient |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | Long context |
| `meta-llama/llama-4-maverick` | Llama 4 | Free tier |

### Variants

| Variant | Purpose |
|---------|---------|
| `:nitro` | Speed (throughput sorted) |
| `:floor` | Cost (price sorted) |
| `:exacto` | Tool calling accuracy |
| `:online` | Web search enabled |
| `:thinking` | Reasoning mode |
| `:free` | Free tier (rate limited) |

### Project Structure

```
my-agent-project/
├── src/
│   ├── main.py           # FastAPI entry
│   ├── config.py         # Environment config
│   ├── agents/           # Agent definitions
│   ├── tools/            # Tool implementations
│   └── middleware/       # Custom middleware
├── tests/
├── .env
└── pyproject.toml
```

### Error Handling

```python
from langchain_core.exceptions import OutputParserException
from langgraph.errors import GraphRecursionError

try:
    result = agent.invoke(input)
except OutputParserException as e:
    # Handle structured output failures
    pass
except GraphRecursionError:
    # Handle agent loops
    pass
```

## Resources

### OpenRouter
- **Docs**: https://openrouter.ai/docs
- **Models Catalog**: https://openrouter.ai/models
- **API Parameters**: https://openrouter.ai/docs/api/reference/parameters
- **Quickstart**: https://openrouter.ai/docs/quickstart
- **Announcements**: https://openrouter.ai/announcements
- **Status**: https://status.openrouter.ai

### LangChain / LangGraph
- **Docs Home**: https://docs.langchain.com
- **LangGraph**: https://docs.langchain.com/oss/python/langgraph
- **v1 Migration Guide**: https://docs.langchain.com/oss/python/migrate/langchain-v1
- **v1 Release Notes**: https://docs.langchain.com/oss/python/releases-v1
- **Quickstart**: https://docs.langchain.com/oss/python/langchain/quickstart
- **Persistence/Checkpointing**: https://docs.langchain.com/oss/python/langgraph/persistence
- **Memory Guide**: https://docs.langchain.com/oss/python/langchain/short-term-memory
- **API Reference**: https://docs.langchain.com/oss/python/reference/overview

### LangSmith
- **Dashboard**: https://smith.langchain.com
- **Docs**: https://docs.smith.langchain.com

### GitHub
- **langgraph-supervisor**: https://github.com/langchain-ai/langgraph-supervisor-py
- **langgraph-swarm**: https://github.com/langchain-ai/langgraph-swarm-py

## Version Info

This skill is current as of **December 2025** and covers:
- LangChain v1.0 / LangGraph v1.0
- OpenRouter API (500+ models)
- langgraph-supervisor, langgraph-swarm
- Middleware system (HITL, retry, PII, etc.)
- Production deployment patterns
- Debugging and observability

For latest updates, use the maintenance guide to search OpenRouter announcements.
