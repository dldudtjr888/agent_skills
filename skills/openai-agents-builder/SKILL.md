---
name: openai-agents-builder
description: "Comprehensive guide for building production-ready multi-agent AI applications using OpenAI Agents Python SDK. Use for: (1) Agent orchestration with tools, handoffs, guardrails (2) Realtime voice agents (3) Durable workflows with Temporal (4) MCP server integration (5) Session memory management (6) Streaming responses (7) Structured outputs (8) Production deployment. Covers all SDK features with up-to-date patterns (November 2025)."
---

# OpenAI Agents Builder - Complete Guide

Build scalable, production-ready multi-agent systems with the OpenAI Agents Python SDK.

## Quick Start

```bash
# Install
pip install openai-agents

# Optional features
pip install 'openai-agents[voice]'    # For realtime voice agents
pip install 'openai-agents[redis]'    # For Redis sessions

# Set API key
export OPENAI_API_KEY="your-key"
```

## Core Concepts

The SDK has **5 core primitives**:

1. **Agents** - LLMs with instructions, tools, and configuration
2. **Tools** - Function tools, hosted tools, or agents-as-tools
3. **Handoffs** - Delegate tasks to specialized agents
4. **Guardrails** - Input/output validation in parallel
5. **Sessions** - Automatic conversation history management

## Essential Patterns

### Basic Agent

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
)

result = await Runner.run(agent, "Hello!")
print(result.final_output)
```

### Function Tools

```python
from agents import Agent, Runner, function_tool

@function_tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"

agent = Agent(
    name="Weather Assistant",
    instructions="Help with weather queries",
    tools=[get_weather],
)
```

### Multi-Agent Handoffs

```python
specialist = Agent(name="Specialist", instructions="Expert help")
triage = Agent(
    name="Triage",
    instructions="Route to specialist when needed",
    handoffs=[specialist],
)
```

### Sessions (Memory)

```python
from agents import SQLiteSession

session = SQLiteSession("user_123")
result = await Runner.run(agent, "Hi!", session=session)
# Next turn remembers context
result = await Runner.run(agent, "What's my name?", session=session)
```

### Streaming

```python
from openai.types.responses import ResponseTextDeltaEvent

result = Runner.run_streamed(agent, "Tell me a story")
async for event in result.stream_events():
    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
```

### Structured Outputs

```python
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    date: str

agent = Agent(
    name="Extractor",
    instructions="Extract calendar events",
    output_type=Event,
)
result = await Runner.run(agent, "Meeting tomorrow at 3pm")
event = result.final_output_as(Event)
```

## Advanced Topics

For comprehensive guides on advanced features, see the references folder:

### 🎤 [Realtime Voice Agents](references/realtime-voice.md)
Build low-latency voice agents using WebRTC/WebSockets with gpt-realtime model. Covers:
- RealtimeAgent and RealtimeRunner setup
- Audio handling and interruptions
- Turn detection and voice activity
- Phone calling via SIP
- Tool use in voice agents

### 💾 [Advanced Sessions](references/sessions-advanced.md)
Comprehensive session management beyond basic SQLite. Covers:
- Redis, SQLAlchemy, encrypted sessions
- Custom session implementations
- Cross-agent session sharing
- Session debugging and cleanup

### 📡 [Streaming Guide](references/streaming.md)
Complete streaming implementation patterns. Covers:
- Event types: raw, item, agent updates
- Filtering and handling events
- Building real-time UIs
- SSE and WebSocket integration

### ⏳ [Temporal Integration](references/temporal-integration.md)
Durable, fault-tolerant agents with Temporal. Covers:
- Setup and configuration
- Activities as tools
- Human-in-the-loop workflows
- Crash recovery and retries
- Production deployment

### 🔌 [MCP Integration](references/mcp-integration.md)
Connect Model Context Protocol servers. Covers:
- Stdio, SSE, and HTTP servers
- Hosted MCP tools
- Tool filtering and caching
- Building custom MCP servers

### 🎯 [Agent Patterns](references/agent-patterns.md)
Production-tested multi-agent architectures. Covers:
- Triage, sequential, hierarchical patterns
- Supervisor-worker patterns
- Reflection and evaluation loops
- Parallel agent execution

### 🐛 [Testing & Debugging](references/testing-debugging.md)
Testing, debugging, and observability. Covers:
- Unit testing agents and tools
- Tracing and trace viewer
- Debugging handoffs and tool calls
- Performance monitoring

### 🚀 [Production Guide](references/production-guide.md)
Deploying agents to production. Covers:
- Error handling and retries
- Rate limiting and quotas
- Security best practices
- Monitoring and alerts
- Cost optimization

## Quick Reference

### Installation

```bash
pip install openai-agents                # Core SDK
pip install 'openai-agents[voice]'      # + Voice support
pip install 'openai-agents[redis]'      # + Redis sessions
```

### Agent Creation

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Agent Name",
    instructions="Your instructions" | dynamic_function,
    tools=[tool1, tool2],
    handoffs=[agent1, agent2],
    input_guardrails=[guardrail1],
    output_guardrails=[guardrail2],
    mcp_servers=[mcp_server],
    output_type=MyPydanticModel,  # For structured output
    model_settings=ModelSettings(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=1000,
    ),
)
```

### Running Agents

```python
from agents import Runner

# Async (recommended)
result = await Runner.run(agent, "input", context=ctx, session=session)

# Sync (avoid in async contexts)
result = Runner.run_sync(agent, "input")

# Streaming
result = Runner.run_streamed(agent, "input")
async for event in result.stream_events():
    # Handle events
    pass
```

### Context (Dependency Injection)

```python
from dataclasses import dataclass
from agents import RunContextWrapper

@dataclass
class MyContext:
    user_id: str
    db: Database

@function_tool
async def my_tool(ctx: RunContextWrapper[MyContext]) -> str:
    user_id = ctx.context.user_id
    return f"User: {user_id}"

agent = Agent[MyContext](
    name="Agent",
    tools=[my_tool],
)

result = await Runner.run(
    agent,
    "input",
    context=MyContext(user_id="123", db=db),
)
```

### RunConfig Options

```python
from agents import RunConfig

result = await Runner.run(
    agent,
    "input",
    max_turns=20,
    run_config=RunConfig(
        workflow_name="My Workflow",      # For tracing
        group_id="thread_123",             # Link traces
        trace_metadata={"env": "prod"},    # Custom metadata
        tracing_disabled=False,             # Enable/disable tracing
    ),
)
```

### Error Handling

```python
from agents.exceptions import (
    MaxTurnsExceeded,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

try:
    result = await Runner.run(agent, input_text)
except MaxTurnsExceeded:
    print("Agent took too many turns")
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e}")
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked: {e}")
```

### Function Tools

```python
from agents import function_tool
from typing_extensions import TypedDict

class Location(TypedDict):
    lat: float
    long: float

@function_tool
async def fetch_data(location: Location, radius: int = 10) -> str:
    """
    Fetch data for a location.
    
    Args:
        location: Latitude and longitude coordinates
        radius: Search radius in km (default: 10)
    
    Returns:
        JSON string with results
    """
    # Implementation
    return "data"
```

### Hosted Tools

```python
from agents.hosted_tools import (
    WebSearchTool,
    CodeInterpreterTool,
    FileSearchTool,
    ComputerTool,
)

agent = Agent(
    name="Research Agent",
    tools=[
        WebSearchTool(),
        CodeInterpreterTool(),
    ],
)
```

### Agents as Tools

```python
specialist = Agent(name="Specialist", instructions="Expert help")

orchestrator = Agent(
    name="Orchestrator",
    tools=[
        specialist.as_tool(
            tool_name="expert",
            tool_description="Use for expert-level questions",
        ),
    ],
)
```

### Sessions

```python
from agents import SQLiteSession, SQLAlchemySession
from agents.extensions.memory import RedisSession, EncryptedSession

# In-memory
session = SQLiteSession("session_id")

# File-based
session = SQLiteSession("session_id", "path/to/db.sqlite")

# SQLAlchemy (production)
session = SQLAlchemySession("session_id", engine=engine, create_tables=True)

# Redis
session = RedisSession("session_id", redis_client=redis_client)

# Encrypted with TTL
session = EncryptedSession(
    session_id="session_id",
    underlying_session=base_session,
    encryption_key="key",
    ttl=600,
)
```

### Guardrails

```python
from agents import InputGuardrail, GuardrailFunctionOutput
from pydantic import BaseModel

class Check(BaseModel):
    is_safe: bool

guardrail_agent = Agent(
    name="Checker",
    instructions="Check if input is safe",
    output_type=Check,
)

async def check_input(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data)
    check = result.final_output_as(Check)
    return GuardrailFunctionOutput(
        output_info=check,
        tripwire_triggered=not check.is_safe,
    )

agent = Agent(
    name="Assistant",
    input_guardrails=[InputGuardrail(guardrail_function=check_input)],
)
```

### Model Settings

```python
from agents import ModelSettings

settings = ModelSettings(
    model="gpt-4o",
    temperature=0.7,
    top_p=0.9,
    max_tokens=1000,
    tool_choice="auto",  # or "required", or specific tool name
)

agent = Agent(
    name="Agent",
    model_settings=settings,
)
```

## Common Patterns

### Pattern: Context-Aware Tools

```python
@dataclass
class AppContext:
    db: Database
    user_id: str

@function_tool
async def query_db(ctx: RunContextWrapper[AppContext], query: str) -> str:
    db = ctx.context.db
    user_id = ctx.context.user_id
    # Execute query with context
    return "results"

agent = Agent[AppContext](
    name="Data Agent",
    tools=[query_db],
)

result = await Runner.run(
    agent,
    "Show my data",
    context=AppContext(db=db, user_id="123"),
)
```

### Pattern: Guardrailed Output

```python
from agents import OutputGuardrail

class Quality(BaseModel):
    is_high_quality: bool
    score: float

quality_agent = Agent(
    name="Quality Checker",
    instructions="Rate output quality 0-1",
    output_type=Quality,
)

async def check_quality(ctx, agent, output):
    result = await Runner.run(quality_agent, f"Rate: {output}")
    quality = result.final_output_as(Quality)
    return GuardrailFunctionOutput(
        output_info=quality,
        tripwire_triggered=quality.score < 0.7,
    )

agent = Agent(
    name="Writer",
    instructions="Write high-quality content",
    output_guardrails=[OutputGuardrail(guardrail_function=check_quality)],
)
```

### Pattern: Persistent Conversation

```python
session = SQLiteSession("user_123", "conversations.db")

messages = [
    "Hi, I'm Alice",
    "What's my name?",
    "What have we discussed?",
]

for msg in messages:
    result = await Runner.run(agent, msg, session=session)
    print(f"User: {msg}")
    print(f"Agent: {result.final_output}\n")
```

### Pattern: Retry on Tool Failure

```python
@function_tool
async def api_call(url: str) -> str:
    """Call external API with retry."""
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            if attempt == 2:
                return f"Error after 3 attempts: {e}"
            await asyncio.sleep(2 ** attempt)
```

## Resources

- **Official Docs**: https://openai.github.io/openai-agents-python/
- **GitHub**: https://github.com/openai/openai-agents-python
- **Examples**: https://github.com/openai/openai-agents-python/tree/main/examples
- **Traces Dashboard**: https://platform.openai.com/traces
- **Temporal Integration**: https://temporal.io/blog/announcing-openai-agents-sdk-integration

## Version Info

This skill is current as of **November 2025** and covers:
- OpenAI Agents SDK v0.5+
- Realtime API (gpt-realtime model)
- MCP integration support
- Temporal integration (Public Preview)

For the most up-to-date information, always consult the official documentation.
