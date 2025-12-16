# LangGraph Documentation Index

Always `web_fetch` relevant URLs before implementing. LangGraph updates frequently.

## ⚠️ Important: v1.0 Changes (October 2025)

- **New unified docs site**: `docs.langchain.com` (Python + JS)
- **`langgraph.prebuilt` deprecated** → Use `langchain.agents` instead
- **New `create_agent`** in `langchain` package (replaces `create_react_agent` from prebuilt)
- Old docs at `langchain-ai.github.io/langgraph/` may be outdated

## Official Documentation (Primary)

| Category | URL | Notes |
|----------|-----|-------|
| **New Unified Docs** | https://docs.langchain.com/ | Python + JS combined |
| LangGraph Concepts | https://docs.langchain.com/langgraph/concepts | Core concepts |
| LangGraph Tutorials | https://docs.langchain.com/langgraph/tutorials | Step-by-step guides |
| LangGraph How-tos | https://docs.langchain.com/langgraph/how-tos | Specific features |
| LangGraph API Ref | https://docs.langchain.com/langgraph/reference | Class/function signatures |
| LangChain Agents | https://docs.langchain.com/langchain/agents | create_agent (new) |

## Legacy Docs (Still Available)

| Category | URL |
|----------|-----|
| Old LangGraph Docs | https://langchain-ai.github.io/langgraph/ |
| Old Reference | https://langchain-ai.github.io/langgraph/reference/ |

## Pattern-Specific Docs

| Pattern | URL |
|---------|-----|
| Quick Start | https://docs.langchain.com/langgraph/tutorials/introduction |
| Agents (new) | https://docs.langchain.com/langchain/agents |
| ReAct from Scratch | https://docs.langchain.com/langgraph/how-tos/react-agent-from-scratch |
| Tool Calling | https://docs.langchain.com/langgraph/how-tos/tool-calling |
| Streaming | https://docs.langchain.com/langgraph/how-tos/streaming |
| Persistence | https://docs.langchain.com/langgraph/how-tos/persistence |
| Memory | https://docs.langchain.com/langgraph/how-tos/memory |
| Human-in-the-loop | https://docs.langchain.com/langgraph/how-tos/human-in-the-loop |
| Subgraphs | https://docs.langchain.com/langgraph/how-tos/subgraph |
| Multi-agent | https://docs.langchain.com/langgraph/concepts/multi-agent |

## SDK & Platform

| Item | URL |
|------|-----|
| langgraph (PyPI) | https://pypi.org/project/langgraph/ |
| langgraph-sdk (PyPI) | https://pypi.org/project/langgraph-sdk/ |
| LangGraph Platform | https://docs.langchain.com/langgraph/cloud |

## Prebuilt → LangChain Agents Migration

```python
# OLD (deprecated)
from langgraph.prebuilt import create_react_agent

# NEW (v1.0+)
from langchain.agents import create_agent
```

## GitHub Repositories

| Item | URL |
|------|-----|
| LangGraph Main | https://github.com/langchain-ai/langgraph |
| Examples | https://github.com/langchain-ai/langgraph/tree/main/examples |
| langgraph-supervisor | https://github.com/langchain-ai/langgraph-supervisor-py |
| langgraph-swarm | https://github.com/langchain-ai/langgraph-swarm-py |

## Version Check

```bash
pip index versions langgraph
pip index versions langgraph-sdk
pip index versions langchain
```

Check releases: https://github.com/langchain-ai/langgraph/releases
Changelog: https://changelog.langchain.com/
