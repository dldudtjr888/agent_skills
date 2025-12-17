# Multi-Agent Patterns

Patterns for building multi-agent systems with LangGraph.

## Architecture Overview

| Pattern | Description | Use Case |
|---------|-------------|----------|
| Supervisor | Central coordinator delegates to workers | Task routing, orchestration |
| Swarm | Agents hand off to each other directly | Collaborative problem solving |
| Hierarchical | Nested supervisors with sub-teams | Complex organizations |
| Parallel | Multiple agents run simultaneously | Independent subtasks |

## Supervisor Pattern

Central supervisor routes tasks to specialized worker agents.

### langgraph-supervisor

```bash
pip install langgraph-supervisor
```

```python
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver

# Define worker agents
research_agent = create_agent(
    model=ChatOpenRouter(model="anthropic/claude-sonnet-4"),
    tools=[web_search, doc_retriever],
    name="researcher",
    system_prompt="You are a research specialist.",
)

coding_agent = create_agent(
    model=ChatOpenRouter(model="openai/gpt-4o"),
    tools=[code_executor, file_writer],
    name="coder",
    system_prompt="You are a coding specialist.",
)

# Create supervisor
workflow = create_supervisor(
    agents=[research_agent, coding_agent],
    model=ChatOpenRouter(model="anthropic/claude-sonnet-4"),
    prompt="Route research tasks to researcher, coding to coder.",
)

# Compile with checkpointing
app = workflow.compile(checkpointer=InMemorySaver())

# Run
result = app.invoke({
    "messages": [{"role": "user", "content": "Research AI trends then write code to visualize them"}]
})
```

### Custom Handoff Tools

```python
from langgraph_supervisor import create_handoff_tool

workflow = create_supervisor(
    agents=[research_agent, coding_agent],
    model=model,
    tools=[
        create_handoff_tool(
            agent_name="researcher",
            name="assign_research",
            description="Assign research tasks to the research specialist",
        ),
        create_handoff_tool(
            agent_name="coder",
            name="assign_coding",
            description="Assign coding tasks to the coding specialist",
        ),
    ],
)
```

### Forward Message Tool

Skip supervisor summarization, forward worker response directly:

```python
from langgraph_supervisor.handoff import create_forward_message_tool

forwarding_tool = create_forward_message_tool("supervisor")

workflow = create_supervisor(
    agents=[...],
    model=model,
    tools=[forwarding_tool],
)
```

## Swarm Pattern

Agents hand off to each other without central coordination.

### langgraph-swarm

```bash
pip install langgraph-swarm
```

```python
from langgraph_swarm import create_handoff_tool, create_swarm
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# Alice can hand off to Bob
alice = create_agent(
    model=model,
    tools=[
        add_numbers,
        create_handoff_tool(agent_name="Bob", description="Transfer to Bob"),
    ],
    name="Alice",
    system_prompt="You are Alice, an addition expert.",
)

# Bob can hand off to Alice
bob = create_agent(
    model=model,
    tools=[
        create_handoff_tool(agent_name="Alice", description="Transfer to Alice"),
    ],
    name="Bob",
    system_prompt="You are Bob, you speak like a pirate.",
)

# Create swarm
checkpointer = InMemorySaver()
workflow = create_swarm(
    agents=[alice, bob],
    default_active_agent="Alice",
)
app = workflow.compile(checkpointer=checkpointer)

# Run
result = app.invoke(
    {"messages": [{"role": "user", "content": "Add 2+2, then talk like a pirate"}]},
    config={"configurable": {"thread_id": "1"}},
)
```

### Custom Handoff with Task Description

```python
from langgraph_swarm import create_handoff_tool
from typing import Annotated
from langchain_core.tools import tool

@tool("transfer_to_specialist")
def custom_handoff(
    task_description: Annotated[str, "What the specialist should do"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    return Command(
        goto="specialist",
        update={
            "messages": [
                ToolMessage(
                    content=f"Task: {task_description}",
                    tool_call_id=tool_call_id,
                )
            ]
        }
    )
```

## Context Engineering

**Context engineering** is the art of deciding *what information* each agent receives. This is critical for multi-agent performance.

### Principles

1. **Minimal Context**: Give agents only what they need
2. **Structured Handoffs**: Pass context explicitly, not implicitly
3. **Summarization**: Compress long histories before handoffs
4. **Role Clarity**: Each agent should know its boundaries

### Full vs. Filtered Context

```python
from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware

class ContextFilterMiddleware(AgentMiddleware):
    """Filter messages before agent sees them."""
    
    def __init__(self, keep_last_n: int = 5, keep_system: bool = True):
        self.keep_last_n = keep_last_n
        self.keep_system = keep_system
    
    def before_model(self, state):
        messages = state["messages"]
        
        # Keep system message
        filtered = []
        if self.keep_system and messages and messages[0].type == "system":
            filtered.append(messages[0])
            messages = messages[1:]
        
        # Keep last N messages
        filtered.extend(messages[-self.keep_last_n:])
        
        state["messages"] = filtered
        return state

# Apply to specific agents
specialist = create_agent(
    model=llm,
    name="specialist",
    middleware=[ContextFilterMiddleware(keep_last_n=3)],  # Only sees recent context
)
```

### Context Summarization Before Handoff

```python
class HandoffSummaryMiddleware(AgentMiddleware):
    """Summarize conversation before handoff to another agent."""
    
    def __init__(self, summarizer_llm):
        self.summarizer = summarizer_llm
    
    def before_model(self, state):
        # Check if this is a handoff (has handoff context)
        if state.get("handoff_context"):
            # Summarize previous conversation for new agent
            messages = state["messages"]
            
            if len(messages) > 10:
                # Create summary
                history = "\n".join([f"{m.type}: {m.content}" for m in messages[:-1]])
                summary = self.summarizer.invoke(
                    f"Summarize this conversation in 2-3 sentences:\n{history}"
                )
                
                # Replace history with summary + last message
                state["messages"] = [
                    SystemMessage(content=f"Previous conversation summary: {summary.content}"),
                    messages[-1],
                ]
        
        return state
```

### Structured Context Transfer

```python
from pydantic import BaseModel
from typing import Optional

class HandoffContext(BaseModel):
    """Structured context passed during handoffs."""
    from_agent: str
    to_agent: str
    reason: str
    task_summary: str
    key_facts: list[str] = []
    user_preferences: dict = {}
    constraints: list[str] = []

class StructuredState(AgentState):
    handoff_context: Optional[HandoffContext] = None

@tool("transfer_with_context")
def structured_handoff(
    target_agent: Annotated[str, "Agent to transfer to"],
    reason: Annotated[str, "Why transferring"],
    task_summary: Annotated[str, "Summary of what needs to be done"],
    key_facts: Annotated[list[str], "Important facts to remember"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Transfer with structured context."""
    
    context = HandoffContext(
        from_agent=state.get("active_agent", "unknown"),
        to_agent=target_agent,
        reason=reason,
        task_summary=task_summary,
        key_facts=key_facts,
    )
    
    return Command(
        goto=target_agent,
        update={
            "handoff_context": context.model_dump(),
            "messages": [
                ToolMessage(
                    content=f"Received from {context.from_agent}: {context.task_summary}",
                    tool_call_id=tool_call_id,
                )
            ],
        },
    )
```

### Agent-Specific System Prompts with Context

```python
def build_context_aware_prompt(base_prompt: str, context: HandoffContext) -> str:
    """Build system prompt that includes handoff context."""
    
    prompt = base_prompt
    
    if context:
        prompt += f"""

## Handoff Context
You were called by {context.from_agent} because: {context.reason}

Task: {context.task_summary}

Key facts to remember:
{chr(10).join(f'- {fact}' for fact in context.key_facts)}

Constraints:
{chr(10).join(f'- {c}' for c in context.constraints)}
"""
    
    return prompt

# Dynamic prompt middleware
class DynamicPromptMiddleware(AgentMiddleware):
    def __init__(self, base_prompt: str):
        self.base_prompt = base_prompt
    
    def before_model(self, state):
        context = state.get("handoff_context")
        
        if context:
            # Inject context into system message
            full_prompt = build_context_aware_prompt(
                self.base_prompt, 
                HandoffContext(**context)
            )
            
            # Update system message
            if state["messages"] and state["messages"][0].type == "system":
                state["messages"][0] = SystemMessage(content=full_prompt)
            else:
                state["messages"].insert(0, SystemMessage(content=full_prompt))
        
        return state
```

## Conditional Handoffs

Route to different agents based on conditions.

### Message Content Routing

```python
from langgraph.graph import StateGraph, END
from typing import Literal

def route_by_content(state) -> Literal["sales", "support", "billing", "general"]:
    """Route based on message content."""
    last_message = state["messages"][-1].content.lower()
    
    # Keyword-based routing
    if any(w in last_message for w in ["buy", "price", "purchase", "order"]):
        return "sales"
    elif any(w in last_message for w in ["broken", "error", "bug", "not working"]):
        return "support"
    elif any(w in last_message for w in ["invoice", "payment", "bill", "charge"]):
        return "billing"
    else:
        return "general"

# Build routing graph
graph = StateGraph(AgentState)
graph.add_node("router", lambda s: s)  # Pass-through
graph.add_node("sales", sales_agent)
graph.add_node("support", support_agent)
graph.add_node("billing", billing_agent)
graph.add_node("general", general_agent)

graph.set_entry_point("router")
graph.add_conditional_edges("router", route_by_content)

# All agents return to END
for node in ["sales", "support", "billing", "general"]:
    graph.add_edge(node, END)

app = graph.compile()
```

### LLM-Based Routing

```python
from pydantic import BaseModel

class RoutingDecision(BaseModel):
    target_agent: Literal["researcher", "coder", "writer"]
    confidence: float
    reasoning: str

class LLMRouterMiddleware(AgentMiddleware):
    """Use LLM to decide routing."""
    
    def __init__(self, router_llm):
        self.router = router_llm.with_structured_output(RoutingDecision)
    
    def before_model(self, state):
        # Only route if at entry
        if len(state["messages"]) == 1:
            decision = self.router.invoke(
                f"""Analyze this request and decide which agent should handle it:
                Request: {state["messages"][-1].content}
                
                Available agents:
                - researcher: For finding information, analysis
                - coder: For writing or fixing code
                - writer: For creating documents, emails, content
                """
            )
            
            state["route_to"] = decision.target_agent
            state["routing_confidence"] = decision.confidence
        
        return state

# Use in graph
def llm_router(state) -> str:
    return state.get("route_to", "general")

graph.add_conditional_edges("entry", llm_router)
```

### State-Based Routing

```python
class TaskState(AgentState):
    task_type: str = ""
    complexity: str = "low"  # low, medium, high
    requires_tools: list[str] = []

def route_by_state(state: TaskState) -> str:
    """Route based on task state."""
    
    # High complexity → senior agent
    if state["complexity"] == "high":
        return "senior_agent"
    
    # Tool requirements
    if "code_execution" in state["requires_tools"]:
        return "coder"
    if "web_search" in state["requires_tools"]:
        return "researcher"
    
    # Default by task type
    return {
        "research": "researcher",
        "coding": "coder",
        "writing": "writer",
    }.get(state["task_type"], "general")
```

### Confidence-Based Escalation

```python
class EscalationMiddleware(AgentMiddleware):
    """Escalate to senior agent if confidence is low."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.threshold = confidence_threshold
    
    def after_model(self, state, response):
        # Check if response indicates low confidence
        content = response.content.lower()
        low_confidence_markers = [
            "i'm not sure",
            "i think",
            "possibly",
            "might be",
            "uncertain",
        ]
        
        if any(marker in content for marker in low_confidence_markers):
            # Flag for escalation
            state["needs_escalation"] = True
            state["escalation_reason"] = "Low confidence response"
        
        return state

def escalation_router(state) -> str:
    if state.get("needs_escalation"):
        return "senior_agent"
    return END
```

## Hierarchical Pattern

Nested supervisors managing sub-teams.

```python
# Level 1: Sub-team supervisors
research_team = create_supervisor(
    agents=[web_researcher, paper_researcher],
    model=model,
    prompt="Coordinate research tasks",
)

dev_team = create_supervisor(
    agents=[frontend_dev, backend_dev],
    model=model,
    prompt="Coordinate development tasks",
)

# Level 2: Top-level supervisor
top_supervisor = create_supervisor(
    agents=[research_team, dev_team],
    model=model,
    prompt="Route to research or dev team",
)
```

### Hierarchical with Context Propagation

```python
class HierarchicalState(AgentState):
    current_level: int = 0
    parent_context: dict = {}
    child_results: list = []

class HierarchyMiddleware(AgentMiddleware):
    """Track hierarchical context."""
    
    def __init__(self, level: int):
        self.level = level
    
    def before_model(self, state: HierarchicalState):
        state["current_level"] = self.level
        
        # Log hierarchy path
        path = state.get("hierarchy_path", [])
        path.append(f"level_{self.level}")
        state["hierarchy_path"] = path
        
        return state
    
    def after_model(self, state: HierarchicalState, response):
        # Propagate results upward
        if self.level > 0:
            state["child_results"].append({
                "level": self.level,
                "content": response.content,
            })
        
        return state
```

## Parallel Execution

Run multiple agents simultaneously.

```python
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from typing import TypedDict, Annotated
from operator import add

class ParallelState(TypedDict):
    query: str
    results: Annotated[list, add]  # Results accumulate

def fan_out(state):
    """Send query to multiple agents in parallel."""
    return [
        Send("agent1", {"query": state["query"], "results": []}),
        Send("agent2", {"query": state["query"], "results": []}),
        Send("agent3", {"query": state["query"], "results": []}),
    ]

def run_agent(state, agent):
    result = agent.invoke({"messages": [{"role": "user", "content": state["query"]}]})
    return {"results": [result["messages"][-1].content]}

def combine_results(state):
    """Combine results from parallel agents."""
    combined = "\n\n".join([
        f"Result {i+1}: {r}" 
        for i, r in enumerate(state["results"])
    ])
    return {"final_result": combined}

# Build graph
graph = StateGraph(ParallelState)
graph.add_node("router", lambda s: s)
graph.add_node("agent1", lambda s: run_agent(s, agent1))
graph.add_node("agent2", lambda s: run_agent(s, agent2))
graph.add_node("agent3", lambda s: run_agent(s, agent3))
graph.add_node("combine", combine_results)

graph.set_entry_point("router")
graph.add_conditional_edges("router", fan_out)

# All agents converge to combine
for agent in ["agent1", "agent2", "agent3"]:
    graph.add_edge(agent, "combine")

graph.add_edge("combine", END)

app = graph.compile()
```

## Memory and State

### Short-term Memory (Checkpointing)

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = InMemorySaver()  # Dev
# checkpointer = SqliteSaver.from_conn_string("db.sqlite")  # Prod

app = workflow.compile(checkpointer=checkpointer)

# Thread-based conversation
config = {"configurable": {"thread_id": "user_123"}}
result = app.invoke(input, config=config)
```

### Long-term Memory (Store)

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

app = workflow.compile(
    checkpointer=checkpointer,
    store=store,
)

# Access store in agents
# store.put(namespace, key, value)
# store.get(namespace, key)
```

### Cross-Agent Memory

```python
class SharedMemoryMiddleware(AgentMiddleware):
    """Share memory across agents."""
    
    def __init__(self, store):
        self.store = store
    
    def before_model(self, state):
        # Load shared context
        agent_name = state.get("active_agent", "default")
        shared = self.store.get(("shared",), "context")
        
        if shared:
            state["shared_context"] = shared.value
        
        return state
    
    def after_model(self, state, response):
        # Save learnings to shared memory
        agent_name = state.get("active_agent", "default")
        
        # Extract key learnings (simplified)
        learnings = state.get("learnings", [])
        learnings.append({
            "agent": agent_name,
            "learned": response.content[:100],
        })
        
        self.store.put(("shared",), "learnings", learnings)
        
        return state
```

## Model Selection per Agent

Cost optimization by assigning appropriate models:

```python
# Supervisor: needs good routing judgment
supervisor_llm = ChatOpenRouter(
    model="anthropic/claude-sonnet-4",
    temperature=0.3,
)

# Research: needs comprehensive understanding
research_llm = ChatOpenRouter(
    model="anthropic/claude-sonnet-4",
    variant="online",  # Web search enabled
)

# Coding: needs code expertise
coding_llm = ChatOpenRouter(
    model="openai/gpt-4o",
    temperature=0.2,
)

# Simple tasks: cost-efficient
simple_llm = ChatOpenRouter(
    model="openai/gpt-4o-mini",
    variant="floor",  # Cheapest provider
)
```

## Error Handling in Multi-Agent

```python
from langgraph.errors import GraphRecursionError

try:
    result = app.invoke(
        input,
        config={"recursion_limit": 50},
    )
except GraphRecursionError:
    # Agent loop exceeded limit
    print("Agent exceeded recursion limit")
```

### Agent Timeout

```python
import asyncio

async def run_with_timeout():
    try:
        result = await asyncio.wait_for(
            app.ainvoke(input),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        print("Agent timed out")
```

### Per-Agent Error Handling

```python
class ErrorHandlingMiddleware(AgentMiddleware):
    """Handle errors gracefully per agent."""
    
    def __init__(self, fallback_response: str = "I encountered an issue."):
        self.fallback = fallback_response
    
    def modify_model_request(self, request):
        original = request._handler
        
        async def safe_handler(req):
            try:
                return await original(req)
            except Exception as e:
                # Log error
                print(f"Agent error: {e}")
                
                # Return fallback
                from langchain_core.messages import AIMessage
                return AIMessage(content=f"{self.fallback} Error: {str(e)[:100]}")
        
        request._handler = safe_handler
        return request
```

## Debugging Multi-Agent

### Enable Tracing

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your-key"
```

### Visualize Graph

```python
from IPython.display import Image

Image(app.get_graph().draw_mermaid_png())
```

### Print State at Each Step

```python
for chunk in app.stream(input, stream_mode="updates"):
    node = list(chunk.keys())[0]
    output = chunk[node]
    
    print(f"\n{'='*50}")
    print(f"Node: {node}")
    
    if isinstance(output, dict) and "messages" in output:
        last_msg = output["messages"][-1]
        print(f"Message type: {type(last_msg).__name__}")
        print(f"Content: {str(last_msg.content)[:200]}...")
```

### Trace Handoffs

```python
class HandoffTracingMiddleware(AgentMiddleware):
    """Track all handoffs for debugging."""
    
    def __init__(self):
        self.handoffs = []
    
    def before_model(self, state):
        if state.get("handoff_context"):
            self.handoffs.append({
                "timestamp": time.time(),
                "from": state["handoff_context"].get("from_agent"),
                "to": state.get("active_agent"),
                "reason": state["handoff_context"].get("reason"),
            })
            print(f"[HANDOFF] {self.handoffs[-1]}")
        
        return state
    
    def get_handoff_history(self):
        return self.handoffs
```

## Resources

### GitHub
- langgraph-supervisor: https://github.com/langchain-ai/langgraph-supervisor-py
- langgraph-swarm: https://github.com/langchain-ai/langgraph-swarm-py

### Documentation
- LangGraph Overview: https://docs.langchain.com/oss/python/langgraph
- Persistence/Checkpointing: https://docs.langchain.com/oss/python/langgraph/persistence
- Memory Guide: https://docs.langchain.com/oss/python/langgraph/add-memory
- Agents Quickstart: https://docs.langchain.com/oss/python/langchain/quickstart
