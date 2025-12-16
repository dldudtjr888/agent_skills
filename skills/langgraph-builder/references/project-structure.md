# Recommended Project Structure

## Basic Agent Project

```
project/
├── pyproject.toml
├── .env
├── langgraph.json          # For LangGraph Platform
│
├── src/
│   ├── __init__.py
│   ├── state.py            # State definitions
│   ├── nodes.py            # Node functions
│   ├── tools.py            # Tool definitions
│   ├── graph.py            # Graph assembly + compile
│   └── prompts.py          # System prompts
│
└── tests/
    └── test_graph.py
```

## Multi-Agent Project

```
project/
├── pyproject.toml
├── .env
├── langgraph.json
│
├── src/
│   ├── __init__.py
│   ├── state.py            # Shared state
│   │
│   ├── agents/             # Each agent as subgraph
│   │   ├── __init__.py
│   │   ├── researcher.py
│   │   ├── coder.py
│   │   └── reviewer.py
│   │
│   ├── supervisor/
│   │   ├── __init__.py
│   │   └── graph.py        # Supervisor logic
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py
│   │   └── code_exec.py
│   │
│   └── main.py             # Entry point, compiles full graph
│
└── tests/
    ├── test_agents.py
    └── test_integration.py
```

## Key Files

### pyproject.toml
```toml
[project]
name = "my-agent"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "langgraph>=1.0.0",
    "langchain>=1.0.0",           # For create_agent (v1.0+)
    "langchain-openai>=0.2.0",    # or langchain-anthropic
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

### .env
```bash
# LLM Provider
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# LangSmith (recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=my-agent

# LangGraph Platform (if deploying)
LANGGRAPH_API_KEY=...
```

### langgraph.json (for Platform deployment)
```json
{
  "dependencies": ["./"],
  "graphs": {
    "agent": "./src/graph.py:app"
  },
  "env": ".env"
}
```

### src/state.py
```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    # Add other state fields as needed
```

### src/graph.py
```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from .state import AgentState
from .nodes import agent_node

def create_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    return graph

# Compiled app for export
graph = create_graph()
app = graph.compile(checkpointer=InMemorySaver())
```

## Environment Setup

```bash
# Create project
mkdir my-agent && cd my-agent

# Initialize with uv (recommended)
uv init
uv add langgraph langchain-openai python-dotenv

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install langgraph langchain-openai python-dotenv

# Create .env
cp .env.example .env
# Edit .env with your API keys

# Run locally
python -m src.main

# Or with LangGraph Platform
langgraph dev
```
