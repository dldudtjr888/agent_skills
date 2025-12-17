# Migration Guide: OpenAI Agents SDK → LangChain v1 + OpenRouter

Complete mapping from OpenAI Agents SDK to LangChain v1.0 with OpenRouter.

## Quick Comparison

| OpenAI Agents SDK | LangChain v1 + OpenRouter |
|-------------------|---------------------------|
| `Agent` | `create_agent` |
| `Runner.run()` | `agent.invoke()` |
| `Runner.run_streamed()` | `agent.astream_events()` |
| `handoffs` | `langgraph-supervisor` / `langgraph-swarm` |
| `guardrails` | Middleware |
| `Session` | LangGraph Checkpointer |
| `function_tool` | `@tool` decorator |
| `output_type` | `with_structured_output()` |
| `model_settings` | Model instance parameters |
| `RunContextWrapper` | Middleware state_schema |

## Installation

```bash
# OpenAI Agents SDK (old)
pip install openai-agents

# LangChain v1 + OpenRouter (new)
pip install langchain langchain-openai langgraph
pip install langgraph-supervisor  # For multi-agent
pip install langgraph-swarm       # For swarm pattern
```

## Basic Agent

### OpenAI Agents SDK

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    model="gpt-4o",
)

result = await Runner.run(agent, "Hello!")
print(result.final_output)
```

### LangChain v1 + OpenRouter

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="openai/gpt-4o",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

agent = create_agent(
    model=llm,
    system_prompt="You are a helpful assistant",
)

result = agent.invoke({"messages": [{"role": "user", "content": "Hello!"}]})
print(result["messages"][-1].content)
```

## Function Tools

### OpenAI Agents SDK

```python
from agents import Agent, function_tool

@function_tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"

agent = Agent(
    name="Weather Bot",
    tools=[get_weather],
)
```

### LangChain v1 + OpenRouter

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"

agent = create_agent(
    model=llm,
    tools=[get_weather],
)
```

### Async Tools

```python
# OpenAI Agents SDK
@function_tool
async def async_search(query: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/search?q={query}")
        return response.text

# LangChain v1
from langchain_core.tools import tool

@tool
async def async_search(query: str) -> str:
    """Search asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/search?q={query}")
        return response.text

# Use with agent
result = await agent.ainvoke({"messages": [...]})
```

## Multi-Agent Handoffs

### Basic Handoffs

#### OpenAI Agents SDK

```python
specialist = Agent(name="Specialist", instructions="Expert help")
triage = Agent(
    name="Triage",
    instructions="Route to specialist when needed",
    handoffs=[specialist],
)
```

#### LangChain v1 + OpenRouter (Supervisor)

```python
from langgraph_supervisor import create_supervisor

specialist = create_agent(
    model=llm,
    name="specialist",
    system_prompt="Expert help",
)

workflow = create_supervisor(
    agents=[specialist],
    model=llm,
    prompt="Route to specialist when needed",
)
```

### Conditional Handoffs

Complex routing logic based on message content or state.

#### OpenAI Agents SDK

```python
from agents import Agent, handoff

sales_agent = Agent(name="Sales", instructions="Handle sales inquiries")
support_agent = Agent(name="Support", instructions="Handle support tickets")
billing_agent = Agent(name="Billing", instructions="Handle billing issues")

def route_condition(context, message):
    """Determine which agent to route to."""
    content = message.lower()
    if "buy" in content or "price" in content:
        return sales_agent
    elif "broken" in content or "error" in content:
        return support_agent
    elif "invoice" in content or "payment" in content:
        return billing_agent
    return None

triage = Agent(
    name="Triage",
    instructions="Route to appropriate department",
    handoffs=[
        handoff(sales_agent, condition=lambda ctx, msg: "buy" in msg.lower()),
        handoff(support_agent, condition=lambda ctx, msg: "broken" in msg.lower()),
        handoff(billing_agent, condition=lambda ctx, msg: "invoice" in msg.lower()),
    ],
)
```

#### LangChain v1 + OpenRouter (Custom Routing)

```python
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langchain.agents import create_agent, AgentState
from typing import Literal

# Define agents
sales_agent = create_agent(
    model=llm, name="sales",
    system_prompt="Handle sales inquiries",
)
support_agent = create_agent(
    model=llm, name="support",
    system_prompt="Handle support tickets",
)
billing_agent = create_agent(
    model=llm, name="billing",
    system_prompt="Handle billing issues",
)

# Custom state with routing info
class RoutingState(AgentState):
    route_to: str | None = None

# Routing function
def route_message(state: RoutingState) -> Literal["sales", "support", "billing", "triage"]:
    """Determine routing based on message content."""
    last_message = state["messages"][-1].content.lower()
    
    if any(word in last_message for word in ["buy", "price", "purchase"]):
        return "sales"
    elif any(word in last_message for word in ["broken", "error", "bug", "issue"]):
        return "support"
    elif any(word in last_message for word in ["invoice", "payment", "bill"]):
        return "billing"
    else:
        return "triage"

# Triage agent decides routing
triage_agent = create_agent(
    model=llm,
    name="triage",
    system_prompt="""You are a triage agent. Analyze the user's request and respond with:
    - "ROUTE:sales" for sales inquiries
    - "ROUTE:support" for technical issues
    - "ROUTE:billing" for billing questions
    Or handle simple queries directly.""",
)

def triage_router(state):
    """Parse triage output for routing."""
    response = state["messages"][-1].content
    if "ROUTE:sales" in response:
        return "sales"
    elif "ROUTE:support" in response:
        return "support"
    elif "ROUTE:billing" in response:
        return "billing"
    return END

# Build graph
graph = StateGraph(RoutingState)
graph.add_node("triage", triage_agent)
graph.add_node("sales", sales_agent)
graph.add_node("support", support_agent)
graph.add_node("billing", billing_agent)

graph.set_entry_point("triage")
graph.add_conditional_edges("triage", triage_router)
graph.add_edge("sales", END)
graph.add_edge("support", END)
graph.add_edge("billing", END)

app = graph.compile()
```

### Handoffs with Context Transfer

Passing information between agents during handoff.

#### OpenAI Agents SDK

```python
@dataclass
class CustomerContext:
    customer_id: str
    priority: str
    previous_tickets: list

specialist = Agent(name="Specialist", instructions="Use customer context for personalized help")
triage = Agent(
    name="Triage",
    handoffs=[specialist],
    handoff_context_builder=lambda ctx, msg: CustomerContext(
        customer_id=ctx.context.customer_id,
        priority="high" if ctx.context.is_vip else "normal",
        previous_tickets=ctx.context.tickets,
    ),
)
```

#### LangChain v1 + OpenRouter (State Transfer)

```python
from langgraph_swarm import create_handoff_tool, create_swarm
from langgraph.types import Command
from langchain_core.tools import tool, InjectedState, InjectedToolCallId
from langchain_core.messages import ToolMessage
from typing import Annotated

# Custom state with context
class CustomerState(AgentState):
    customer_id: str | None = None
    priority: str = "normal"
    previous_tickets: list = []
    handoff_context: dict = {}

# Custom handoff tool with context
@tool("transfer_to_specialist")
def transfer_with_context(
    reason: Annotated[str, "Why transferring to specialist"],
    summary: Annotated[str, "Summary of conversation so far"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Transfer to specialist with full context."""
    
    # Build context for specialist
    context = {
        "customer_id": state.get("customer_id"),
        "priority": state.get("priority", "normal"),
        "previous_tickets": state.get("previous_tickets", []),
        "transfer_reason": reason,
        "conversation_summary": summary,
    }
    
    return Command(
        goto="specialist",
        update={
            "handoff_context": context,
            "messages": [
                ToolMessage(
                    content=f"Transferred from triage. Context: {context}",
                    tool_call_id=tool_call_id,
                )
            ],
        },
    )

# Specialist reads context
specialist = create_agent(
    model=llm,
    name="specialist",
    system_prompt="""You are a specialist. 
    The handoff_context contains customer information and why you were called.
    Use this context to provide personalized assistance.""",
    tools=[create_handoff_tool(agent_name="triage", description="Return to triage")],
)

triage = create_agent(
    model=llm,
    name="triage",
    system_prompt="Gather customer info and transfer to specialist when needed.",
    tools=[transfer_with_context],
)

workflow = create_swarm(
    [triage, specialist],
    default_active_agent="triage",
    state_schema=CustomerState,
)
```

### Bidirectional Handoffs

Agents can hand off to each other and return.

#### OpenAI Agents SDK

```python
agent_a = Agent(
    name="AgentA",
    instructions="Do task A, hand to B for task B",
    handoffs=[agent_b],
)
agent_b = Agent(
    name="AgentB", 
    instructions="Do task B, hand back to A when done",
    handoffs=[agent_a],
)
```

#### LangChain v1 + OpenRouter (Swarm)

```python
from langgraph_swarm import create_handoff_tool, create_swarm

# Each agent has handoff tools to others
agent_a = create_agent(
    model=llm,
    name="AgentA",
    system_prompt="Do task A, hand to B for task B",
    tools=[
        create_handoff_tool(
            agent_name="AgentB",
            description="Transfer to Agent B for B-type tasks",
        )
    ],
)

agent_b = create_agent(
    model=llm,
    name="AgentB",
    system_prompt="Do task B, hand back to A when done",
    tools=[
        create_handoff_tool(
            agent_name="AgentA", 
            description="Transfer back to Agent A",
        )
    ],
)

workflow = create_swarm(
    [agent_a, agent_b],
    default_active_agent="AgentA",
)
app = workflow.compile()

# Track handoff history
result = app.invoke(
    {"messages": [{"role": "user", "content": "Do A then B then A again"}]},
    config={"recursion_limit": 20},  # Prevent infinite loops
)
```

## Guardrails

### Basic Guardrails

#### OpenAI Agents SDK

```python
from agents import Agent, InputGuardrail, GuardrailFunctionOutput

async def check_input(ctx, agent, input_data):
    return GuardrailFunctionOutput(
        output_info=result,
        tripwire_triggered=not result.is_safe,
    )

agent = Agent(
    input_guardrails=[InputGuardrail(guardrail_function=check_input)],
)
```

#### LangChain v1 + OpenRouter (Middleware)

```python
from langchain.agents.middleware import AgentMiddleware

class SafetyMiddleware(AgentMiddleware):
    def before_model(self, state):
        last_message = state["messages"][-1].content
        if not is_safe(last_message):
            raise ValueError("Unsafe input detected")
        return state
    
    def after_model(self, state, response):
        if not is_safe(response.content):
            raise ValueError("Unsafe output detected")
        return state

agent = create_agent(
    model=llm,
    middleware=[SafetyMiddleware()],
)
```

### Guardrail Chains (Multiple Sequential Checks)

#### OpenAI Agents SDK

```python
async def check_pii(ctx, agent, input_data):
    has_pii = detect_pii(input_data)
    return GuardrailFunctionOutput(tripwire_triggered=has_pii)

async def check_toxicity(ctx, agent, input_data):
    is_toxic = detect_toxicity(input_data)
    return GuardrailFunctionOutput(tripwire_triggered=is_toxic)

async def check_relevance(ctx, agent, input_data):
    is_relevant = check_topic_relevance(input_data)
    return GuardrailFunctionOutput(tripwire_triggered=not is_relevant)

agent = Agent(
    input_guardrails=[
        InputGuardrail(guardrail_function=check_pii),
        InputGuardrail(guardrail_function=check_toxicity),
        InputGuardrail(guardrail_function=check_relevance),
    ],
)
```

#### LangChain v1 + OpenRouter (Middleware Chain)

```python
from langchain.agents.middleware import AgentMiddleware, PIIMiddleware

class ToxicityMiddleware(AgentMiddleware):
    """Check for toxic content."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def before_model(self, state):
        content = state["messages"][-1].content
        toxicity_score = self._detect_toxicity(content)
        
        if toxicity_score > self.threshold:
            raise ValueError(f"Toxic content detected (score: {toxicity_score})")
        return state
    
    def _detect_toxicity(self, text: str) -> float:
        # Use toxicity detection API/model
        return 0.0  # Placeholder

class RelevanceMiddleware(AgentMiddleware):
    """Check if query is relevant to allowed topics."""
    
    def __init__(self, allowed_topics: list[str]):
        self.allowed_topics = allowed_topics
    
    def before_model(self, state):
        content = state["messages"][-1].content
        if not self._is_relevant(content):
            raise ValueError("Query is off-topic")
        return state
    
    def _is_relevant(self, text: str) -> bool:
        # Check topic relevance
        return True  # Placeholder

class OutputValidationMiddleware(AgentMiddleware):
    """Validate model output before returning."""
    
    def after_model(self, state, response):
        content = response.content
        
        # Check for hallucination markers
        if self._might_be_hallucination(content):
            # Modify response or raise
            state["messages"][-1] = self._add_caveat(response)
        
        return state

# Combine middlewares - order matters!
agent = create_agent(
    model=llm,
    middleware=[
        # 1. PII check first (fast, blocks early)
        PIIMiddleware("email", strategy="redact"),
        PIIMiddleware("credit_card", strategy="mask"),
        
        # 2. Toxicity check
        ToxicityMiddleware(threshold=0.7),
        
        # 3. Relevance check
        RelevanceMiddleware(allowed_topics=["support", "sales", "billing"]),
        
        # 4. Output validation (after model)
        OutputValidationMiddleware(),
    ],
)
```

### LLM-Based Guardrails

Using another LLM to check inputs/outputs.

#### OpenAI Agents SDK

```python
from agents import Agent, InputGuardrail

guardrail_agent = Agent(
    name="GuardrailChecker",
    instructions="Return SAFE or UNSAFE for the input",
    model="gpt-4o-mini",
)

async def llm_check(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data)
    return GuardrailFunctionOutput(
        tripwire_triggered=("UNSAFE" in result.final_output)
    )

agent = Agent(input_guardrails=[InputGuardrail(guardrail_function=llm_check)])
```

#### LangChain v1 + OpenRouter

```python
from langchain.agents.middleware import AgentMiddleware
from pydantic import BaseModel

class SafetyCheck(BaseModel):
    is_safe: bool
    reason: str

class LLMGuardrailMiddleware(AgentMiddleware):
    """Use a cheap LLM to check input/output safety."""
    
    def __init__(self):
        # Use cheap, fast model for guardrails
        self.guardrail_llm = ChatOpenRouter(
            model="openai/gpt-4o-mini",
            variant="floor",
        ).with_structured_output(SafetyCheck)
    
    def before_model(self, state):
        content = state["messages"][-1].content
        
        check = self.guardrail_llm.invoke(
            f"Is this user input safe and appropriate? Input: {content}"
        )
        
        if not check.is_safe:
            raise ValueError(f"Input blocked: {check.reason}")
        
        return state
    
    def after_model(self, state, response):
        content = response.content
        
        check = self.guardrail_llm.invoke(
            f"Is this AI response safe and appropriate? Response: {content}"
        )
        
        if not check.is_safe:
            # Replace response with safe version
            response.content = f"I apologize, but I cannot provide that response. {check.reason}"
        
        return state

agent = create_agent(
    model=llm,
    middleware=[LLMGuardrailMiddleware()],
)
```

## Sessions (Memory)

### OpenAI Agents SDK

```python
from agents import SQLiteSession

session = SQLiteSession("user_123")
result = await Runner.run(agent, "Hi!", session=session)
result = await Runner.run(agent, "What's my name?", session=session)
```

### LangChain v1 + OpenRouter (Checkpointer)

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver

# In-memory (dev)
checkpointer = InMemorySaver()

# SQLite (persistent)
checkpointer = SqliteSaver.from_conn_string("sessions.db")

# PostgreSQL (production)
checkpointer = PostgresSaver.from_conn_string("postgresql://...")

# Compile agent with checkpointer
compiled = agent.compile(checkpointer=checkpointer)

# Use thread_id for session
config = {"configurable": {"thread_id": "user_123"}}
result = compiled.invoke({"messages": [...]}, config=config)
```

## Streaming

### OpenAI Agents SDK

```python
from openai.types.responses import ResponseTextDeltaEvent

result = Runner.run_streamed(agent, "Tell me a story")
async for event in result.stream_events():
    if isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="")
```

### LangChain v1 + OpenRouter

```python
async for event in agent.astream_events(
    {"messages": [{"role": "user", "content": "Tell me a story"}]},
    version="v2",
):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
```

## Structured Output

### OpenAI Agents SDK

```python
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    date: str

agent = Agent(output_type=Event)
result = await Runner.run(agent, "Meeting tomorrow")
event = result.final_output_as(Event)
```

### LangChain v1 + OpenRouter

```python
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    date: str

structured_llm = llm.with_structured_output(Event)
agent = create_agent(model=structured_llm, tools=[])

result = agent.invoke({"messages": [{"role": "user", "content": "Meeting tomorrow"}]})
# result is Event instance
```

## Context (Dependency Injection)

### OpenAI Agents SDK

```python
from dataclasses import dataclass
from agents import RunContextWrapper

@dataclass
class AppContext:
    user_id: str
    db: Database

@function_tool
async def query_db(ctx: RunContextWrapper[AppContext], query: str) -> str:
    return ctx.context.db.query(query)

result = await Runner.run(
    agent, "Query data",
    context=AppContext(user_id="123", db=db),
)
```

### LangChain v1 + OpenRouter (Middleware State)

```python
from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware

class AppState(AgentState):
    user_id: str
    db_results: dict

class ContextMiddleware(AgentMiddleware):
    state_schema = AppState
    
    def __init__(self, user_id: str, db: Database):
        self.user_id = user_id
        self.db = db
    
    def before_model(self, state: AppState):
        state["user_id"] = self.user_id
        return state

@tool
def query_db(query: str) -> str:
    """Query the database."""
    # Access via RunnableConfig or closure
    return "results"

agent = create_agent(
    model=llm,
    tools=[query_db],
    middleware=[ContextMiddleware(user_id="123", db=db)],
)
```

## Model Settings

### OpenAI Agents SDK

```python
from agents import Agent, ModelSettings

agent = Agent(
    model_settings=ModelSettings(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=1000,
    ),
)
```

### LangChain v1 + OpenRouter

```python
llm = ChatOpenAI(
    model="openai/gpt-4o",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    temperature=0.7,
    max_tokens=1000,
)

agent = create_agent(model=llm, tools=[])
```

## Error Handling

### OpenAI Agents SDK

```python
from agents.exceptions import MaxTurnsExceeded, InputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, input_text)
except MaxTurnsExceeded:
    print("Too many turns")
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e}")
```

### LangChain v1 + OpenRouter

```python
from langgraph.errors import GraphRecursionError
from langchain_core.exceptions import OutputParserException

try:
    result = agent.invoke(
        input,
        config={"recursion_limit": 20},
    )
except GraphRecursionError:
    print("Too many turns")
except OutputParserException as e:
    print(f"Output parsing failed: {e}")
```

## OpenRouter-Specific Benefits

After migration, leverage OpenRouter features:

```python
# Multiple model providers with single API key
claude_llm = ChatOpenAI(model="anthropic/claude-sonnet-4", ...)
gpt_llm = ChatOpenAI(model="openai/gpt-4o", ...)
llama_llm = ChatOpenAI(model="meta-llama/llama-4-maverick", ...)

# Cost optimization with :floor
cheap_llm = ChatOpenAI(model="openai/gpt-4o-mini:floor", ...)

# Speed optimization with :nitro
fast_llm = ChatOpenAI(model="anthropic/claude-sonnet-4:nitro", ...)

# Tool accuracy with :exacto
tool_llm = ChatOpenAI(model="anthropic/claude-sonnet-4:exacto", ...)

# Auto fallback between providers
response = llm.invoke(
    messages,
    extra_body={
        "provider": {
            "order": ["Anthropic", "Azure", "OpenAI"],
            "allow_fallbacks": True,
        }
    }
)
```

## Migration Checklist

### Core Migration

- [ ] Replace `openai-agents` with `langchain`, `langchain-openai`, `langgraph`
- [ ] Update `Agent` → `create_agent`
- [ ] Update `Runner.run()` → `agent.invoke()`
- [ ] Update `@function_tool` → `@tool`

### Multi-Agent

- [ ] Update `handoffs` → `langgraph-supervisor` or `langgraph-swarm`
- [ ] Migrate conditional handoffs to custom routing
- [ ] Update context passing to state-based approach

### Guardrails

- [ ] Update guardrails → Middleware
- [ ] Convert guardrail chains to middleware stack
- [ ] Test middleware order (before_model runs in order, after_model in reverse)

### State & Memory

- [ ] Update Session → Checkpointer
- [ ] Migrate session storage (SQLite, PostgreSQL)

### Streaming & Output

- [ ] Update streaming event handling
- [ ] Update structured output to `with_structured_output()`

### OpenRouter

- [ ] Configure OpenRouter API key and base_url
- [ ] Test with model variants (:nitro, :floor, :exacto)
- [ ] Configure provider fallbacks

## Resources

- LangChain v1 Migration Guide: https://docs.langchain.com/oss/python/migrate/langchain-v1
- LangChain v1 Release Notes: https://docs.langchain.com/oss/python/releases-v1
- LangGraph Overview: https://docs.langchain.com/oss/python/langgraph
- OpenRouter Docs: https://openrouter.ai/docs
- OpenRouter Models: https://openrouter.ai/models
- langgraph-supervisor: https://github.com/langchain-ai/langgraph-supervisor-py
- langgraph-swarm: https://github.com/langchain-ai/langgraph-swarm-py
