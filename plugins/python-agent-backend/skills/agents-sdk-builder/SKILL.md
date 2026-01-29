---
name: agents-sdk-builder
description: "Use when user explicitly mentions 'OpenAI Agents SDK', 'openai-agents', or asks to build multi-agent systems with OpenAI's agent framework. NOT for general chatbot requests (could be LangChain, CrewAI, etc). This skill provides architecture decisions and patterns; always pair with Context7 for current API syntax."
---

# Agents SDK Builder - Complete Guide

Build multi-agent systems with the OpenAI Agents Python SDK.

> ⚠️ **IMPORTANT: Always Verify with Context7**
>
> OpenAI Agents SDK evolves rapidly. Before implementing:
> ```
> Context7 Library ID: /websites/openai_github_io_openai-agents-python
> ```

---

## When to Activate This Skill

### ✅ ACTIVATE when:
- User says "OpenAI Agents SDK" or "openai-agents"
- User references `from agents import Agent`
- User wants multi-agent with OpenAI's framework specifically

### ❌ DON'T ACTIVATE when:
- Generic "build a chatbot" (ask which framework first)
- "Multi-agent system" without specifying OpenAI (could be LangChain, CrewAI)
- Just "OpenAI" (could mean API, not Agents SDK)

### 🤔 ASK USER when:
- "Build an AI agent" → "Which framework? OpenAI Agents SDK, LangChain, CrewAI?"
- "Multi-agent system" → "Are you using OpenAI Agents SDK specifically?"

---

## AI Workflow (Follow This After Reading)

### Step 1: Clarify Requirements
**Ask user these questions:**

```
□ What's the main task? (chatbot, pipeline, voice, data processing)
□ Single agent or multiple agents?
□ Need conversation memory? (sessions)
□ Need real-time streaming?
□ Deployment target? (local, server, distributed)
```

### Step 2: Verify API with Context7
**Before writing ANY code:**

```python
# Use Context7 MCP to check current syntax
# Library ID: /websites/openai_github_io_openai-agents-python
# Topics: "agent", "tools", "runner"
```

Check:
- [ ] Current model names (they change!)
- [ ] Method signatures you'll use
- [ ] Any new features since this skill was written

### Step 3: Select Architecture
**Use Decision Trees in this skill:**

| User Need | Go To |
|-----------|-------|
| "Should I use handoffs or tools?" | → Decision 1 |
| "Which session type?" | → Decision 2 |
| "How to structure multiple agents?" | → Decision 3 |

### Step 4: Implement
**Use Essential Patterns section, but:**
- Copy pattern structure, not exact syntax
- Verify each API call with Context7
- Start minimal, add complexity incrementally

### Step 5: Validate
**Before delivering code, check:**

```
□ Using await in async context? (not run_sync)
□ Session persisted correctly?
□ Handoff vs as_tool choice appropriate?
□ No hardcoded model versions?
□ Error handling for MaxTurnsExceeded?
```

---

## Task Type Quick Paths

### 🤖 Simple Chatbot
```
Need: Basic conversational agent
Path: Quick Start → Essential Patterns (Function Tools)
Session: SQLiteSession (in-memory for dev)
Skip: Handoffs, Multi-agent patterns
```

### 🔀 Multi-Agent Router (Triage)
```
Need: Route users to specialists
Path: Decision 1 (Handoffs) → Decision 3 (Triage pattern)
Key: Use handoffs for specialist conversations
Example: Customer support with billing/technical/sales agents
```

### 📊 Data Pipeline
```
Need: Process data through stages
Path: Decision 1 (as_tool) → Decision 3 (Sequential pattern)
Key: Orchestrator stays in control, agents as tools
Example: Research → Analyze → Report
```

### 🎤 Voice Agent
```
Need: Real-time voice interaction
Path: Advanced Topics → realtime-voice.md
Key: RealtimeAgent, WebRTC, different from text agents
Verify: Context7 topic "realtime" for current API
```

### 💾 Stateful Conversations
```
Need: Remember conversation history
Path: Decision 2 (Session Strategy) → Essential Patterns (Context)
Key: Choose session backend based on deployment
Production: SQLAlchemy or Redis, not in-memory SQLite
```

---

## Quick Start

```bash
pip install openai-agents
export OPENAI_API_KEY="your-key"
```

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are helpful")
result = await Runner.run(agent, "Hello!")
print(result.final_output)
```

---

## Core Concepts

The SDK has **5 core primitives**:

| Primitive | Purpose | Key Decision |
|-----------|---------|--------------|
| **Agents** | LLMs with instructions, tools, config | Single vs Multi-agent |
| **Tools** | Extend agent capabilities | Function vs Hosted vs Agent-as-Tool |
| **Handoffs** | Delegate to specialized agents | When to transfer control |
| **Guardrails** | Input/output validation | Security vs Performance |
| **Sessions** | Conversation memory | Persistence strategy |

---

## Architecture Decisions

### Decision 1: Handoffs vs Agents-as-Tools

```
┌─────────────────────────────────────────────────────────────┐
│          Do you need full control transfer?                 │
└─────────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
          [YES]                        [NO]
            │                           │
   ┌────────┴────────┐         ┌───────┴───────┐
   │    HANDOFFS     │         │ AGENTS-AS-TOOLS│
   │                 │         │                │
   │ • Specialist    │         │ • Orchestrator │
   │   takes over    │         │   stays in     │
   │   completely    │         │   control      │
   │                 │         │                │
   │ • Conversation  │         │ • Result       │
   │   continues     │         │   returned to  │
   │   with new      │         │   caller       │
   │   agent         │         │                │
   └─────────────────┘         └────────────────┘
```

**Use Handoffs when:**
- User should interact directly with specialist
- Complex multi-turn specialist conversations
- "Transfer to support" type flows

**Use Agents-as-Tools when:**
- Orchestrator needs to aggregate results
- Quick single-query to specialist
- Parallel specialist queries

```python
# HANDOFFS: Control transfers completely
triage = Agent(
    name="Triage",
    handoffs=[billing_agent, support_agent],  # User talks to specialist
)

# AGENTS-AS-TOOLS: Orchestrator stays in control
orchestrator = Agent(
    name="Orchestrator",
    tools=[
        analyst.as_tool(tool_name="analyze"),  # Gets result back
        writer.as_tool(tool_name="write"),
    ],
)
```

### Decision 2: Session Strategy

```
┌──────────────────────────────────────┐
│     What's your deployment env?      │
└──────────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
[Local/Dev]  [Single]   [Distributed]
    │        [Server]       │
    │           │           │
    ▼           ▼           ▼
 SQLite    SQLAlchemy    Redis
 (memory)  (PostgreSQL)  (cluster)
```

| Scenario | Session Type | Why |
|----------|--------------|-----|
| Development/Testing | `SQLiteSession` (in-memory) | Zero setup |
| Single server | `SQLiteSession` (file) | Simple persistence |
| Production single DB | `SQLAlchemySession` | Transactional, scalable |
| Multi-server/K8s | `RedisSession` | Shared state |
| Sensitive data | `EncryptedSession` | Security compliance |

### Decision 3: Multi-Agent Pattern Selection

| Pattern | When to Use | Example |
|---------|------------|---------|
| **Triage** | Route by intent | Customer support routing |
| **Sequential** | Pipeline processing | Research → Analyze → Report |
| **Parallel** | Independent tasks | Multi-source data gathering |
| **Hierarchical** | Complex orchestration | Manager → Team leads → Workers |
| **Reflection** | Quality improvement | Writer → Critic → Revision |

```python
# TRIAGE: Route based on user intent
triage = Agent(
    name="Router",
    instructions="Route to specialist based on query type",
    handoffs=[sales_agent, support_agent, billing_agent],
)

# SEQUENTIAL: Chain of processing
async def sequential_pipeline(input):
    research = await Runner.run(researcher, input)
    analysis = await Runner.run(analyst, research.final_output)
    return await Runner.run(writer, analysis.final_output)

# PARALLEL: Concurrent execution
import asyncio
results = await asyncio.gather(
    Runner.run(agent1, query),
    Runner.run(agent2, query),
    Runner.run(agent3, query),
)
```

---

## Essential Patterns

### Function Tools
```python
from agents import function_tool

@function_tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"

agent = Agent(name="Weather", tools=[get_weather])
```

### Structured Output
```python
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    date: str

agent = Agent(name="Extractor", output_type=Event)
result = await Runner.run(agent, "Meeting tomorrow 3pm")
event = result.final_output_as(Event)  # Typed!
```

### Context Injection
```python
from dataclasses import dataclass

@dataclass
class AppContext:
    user_id: str
    db: Database

@function_tool
async def query(ctx: RunContextWrapper[AppContext], sql: str) -> str:
    return ctx.context.db.execute(sql, user=ctx.context.user_id)

agent = Agent[AppContext](tools=[query])
result = await Runner.run(agent, "...", context=AppContext(...))
```

### Streaming
```python
result = Runner.run_streamed(agent, "Tell a story")
async for event in result.stream_events():
    if event.type == "raw_response_event":
        print(event.data.delta, end="", flush=True)
```

### Clone & Variations
```python
base = Agent(name="Writer", instructions="Write content")
formal = base.clone(instructions="Write formally")
casual = base.clone(instructions="Write casually")
```

### Dynamic Instructions
```python
def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent) -> str:
    return f"User: {ctx.context.name}. Language: {ctx.context.lang}"

agent = Agent(instructions=dynamic_instructions)  # Function, not string
```

---

## Common Mistakes

### ❌ Mistake 1: Hardcoding Model Names
```python
# BAD: Models change frequently
agent = Agent(model_settings=ModelSettings(model="gpt-4o-2024-05-13"))

# GOOD: Use Context7 to verify current model names
agent = Agent(model_settings=ModelSettings(model="gpt-4o"))
```

### ❌ Mistake 2: Forgetting Async Context
```python
# BAD: Using run_sync in async context blocks event loop
async def handler():
    return Runner.run_sync(agent, input)  # BLOCKS!

# GOOD: Use await in async contexts
async def handler():
    return await Runner.run(agent, input)
```

### ❌ Mistake 3: Stateless Session Thinking
```python
# BAD: Creating new session each request loses history
async def chat(msg):
    session = SQLiteSession(user_id)  # Fresh session each time!
    return await Runner.run(agent, msg, session=session)

# GOOD: Persist session or use file-backed
session = SQLiteSession(user_id, "conversations.db")  # File-backed
```

### ❌ Mistake 4: Overusing Handoffs
```python
# BAD: Handoff for simple lookup (loses orchestrator context)
main = Agent(handoffs=[lookup_agent])

# GOOD: Use as_tool for simple queries
main = Agent(tools=[lookup_agent.as_tool(tool_name="lookup")])
```

### ❌ Mistake 5: Ignoring Guardrail Performance
```python
# BAD: Heavy guardrail on every request
async def check(ctx, agent, input):
    return await Runner.run(heavy_checker, input)  # LLM call every time!

# GOOD: Lightweight first, heavy only when needed
async def check(ctx, agent, input):
    if quick_regex_check(input):  # Fast filter first
        return await Runner.run(heavy_checker, input)
    return GuardrailFunctionOutput(tripwire_triggered=False)
```

---

## Advanced Topics

| Topic | Reference | When to Read |
|-------|-----------|--------------|
| 🎤 Voice | [realtime-voice.md](references/realtime-voice.md) | Building voice/phone agents |
| 💾 Sessions | [sessions-advanced.md](references/sessions-advanced.md) | Production session management |
| 📡 Streaming | [streaming.md](references/streaming.md) | Real-time UI updates |
| ⏳ Temporal | [temporal-integration.md](references/temporal-integration.md) | Long-running, fault-tolerant workflows |
| 🔌 MCP | [mcp-integration.md](references/mcp-integration.md) | Connecting external tools via MCP |
| 🎯 Patterns | [agent-patterns.md](references/agent-patterns.md) | Complex multi-agent architectures |
| 🐛 Testing | [testing-debugging.md](references/testing-debugging.md) | Testing and observability |
| 🚀 Production | [production-guide.md](references/production-guide.md) | Deployment, security, monitoring |

---

## Quick Reference

### Installation
```bash
pip install openai-agents                # Core
pip install 'openai-agents[voice]'      # + Voice
pip install 'openai-agents[redis]'      # + Redis
```

### Agent Skeleton
```python
agent = Agent(
    name="Name",
    instructions="..." | function,       # Static or dynamic
    tools=[...],                         # Function/hosted/agent tools
    handoffs=[...],                      # Control transfer
    input_guardrails=[...],              # Input validation
    output_guardrails=[...],             # Output validation
    output_type=PydanticModel,           # Structured output
    model_settings=ModelSettings(...),   # Model config
)
```

### Runner Methods
```python
await Runner.run(agent, input)           # Async (recommended)
Runner.run_sync(agent, input)            # Sync (blocks!)
Runner.run_streamed(agent, input)        # Streaming
```

### Key Exceptions
```python
from agents.exceptions import (
    MaxTurnsExceeded,                    # Too many agent turns
    InputGuardrailTripwireTriggered,     # Input blocked
    OutputGuardrailTripwireTriggered,    # Output blocked
)
```

---

## Resources

- **Official Docs**: https://openai.github.io/openai-agents-python/
- **GitHub**: https://github.com/openai/openai-agents-python
- **Examples**: https://github.com/openai/openai-agents-python/tree/main/examples
- **Traces**: https://platform.openai.com/traces

---

## Context7 Reference

**Always verify before implementing:**

```
Library ID: /websites/openai_github_io_openai-agents-python

Topics by task:
- "agent" - Agent creation, configuration
- "tools" - Function tools, hosted tools
- "handoffs" - Control transfer
- "sessions" - Memory management
- "streaming" - Event handling
- "guardrails" - Validation
- "realtime" - Voice agents
- "mcp" - MCP integration
- "runner" - Execution options
- "tracing" - Debugging, observability
```
