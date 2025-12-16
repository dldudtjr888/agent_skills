# Debugging & Visualization

## Graph Visualization

```python
from IPython.display import Image, display

# Visualize graph structure
display(Image(app.get_graph().draw_mermaid_png()))

# Or save to file
with open("graph.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())
```

**Note**: Requires `pygraphviz` or uses Mermaid.js rendering.

---

## LangSmith Integration (Recommended)

### Setup
```bash
# .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-key>
LANGCHAIN_PROJECT=my-project
```

### Benefits
- Trace every node execution
- View state at each step
- Measure latency and token usage
- Debug failed runs

### Usage
Just set environment variables - tracing is automatic.

---

## State Inspection (with Checkpointer)

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "debug-session"}}

# Run the graph
result = app.invoke(input, config)

# Get current state
snapshot = app.get_state(config)
print("Current values:", snapshot.values)
print("Next nodes:", snapshot.next)

# Get full state history
for state in app.get_state_history(config):
    print(f"Step: {state.metadata.get('step')}")
    print(f"Values: {state.values}")
    print("---")
```

---

## Time-Travel Debugging

```python
# Get history
history = list(app.get_state_history(config))

# Find a past state
past_state = history[3]  # Go back 3 steps

# Resume from that point with modification
app.update_state(
    config,
    {"messages": [("user", "different input")]},
    as_node="agent"  # Pretend this came from "agent" node
)

# Continue execution from modified state
result = app.invoke(None, config)
```

---

## Streaming Debug

```python
# Stream with detailed events
for event in app.stream(input, config, stream_mode="debug"):
    print(f"Event type: {event['type']}")
    if event['type'] == 'task':
        print(f"  Node: {event['payload']['name']}")
    elif event['type'] == 'task_result':
        print(f"  Result: {event['payload']['result']}")
```

### Stream Modes
- `"values"`: Full state after each node
- `"updates"`: Only changed fields
- `"messages"`: LLM message chunks (for streaming responses)
- `"debug"`: Detailed execution events

---

## Common Debug Patterns

### Print State in Node
```python
def debug_node(state):
    print(f"[DEBUG] State keys: {state.keys()}")
    print(f"[DEBUG] Messages count: {len(state.get('messages', []))}")
    # ... normal logic
    return {"result": "..."}
```

### Conditional Breakpoint
```python
def maybe_interrupt(state):
    if state.get("needs_review"):
        return "review"  # Human review node
    return "continue"

graph.add_conditional_edges("process", maybe_interrupt)
```

### Log Node Entry/Exit
```python
import logging
logging.basicConfig(level=logging.DEBUG)

def logged_node(state):
    logging.debug(f"Entering node with state: {state}")
    result = {"output": "..."}
    logging.debug(f"Exiting node with result: {result}")
    return result
```

---

## Error Debugging

### Catch Node Errors
```python
def safe_node(state):
    try:
        # risky operation
        result = external_api_call()
        return {"result": result}
    except Exception as e:
        return {"error": str(e), "result": None}
```

### Retry Pattern
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def llm_call(messages):
    return model.invoke(messages)

def node_with_retry(state):
    response = llm_call(state["messages"])
    return {"messages": [response]}
```

---

## LangGraph Studio (Visual Debugging)

For local development with visual debugging:
```bash
# Start LangGraph dev server with Studio
langgraph dev

# Opens Studio at http://localhost:8123
```

Features:
- Visual graph editor
- Step-by-step execution
- State inspection
- Thread management
