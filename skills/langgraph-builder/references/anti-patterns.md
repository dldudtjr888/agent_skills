# Anti-Patterns to Avoid

## 1. State Mutation

```python
# ❌ WRONG: Mutating state directly
def node(state):
    state["items"].append(new_item)
    state["count"] += 1
    return state

# ✅ CORRECT: Return new state
def node(state):
    return {
        "items": [*state["items"], new_item],
        "count": state["count"] + 1
    }
```

**Why**: Breaks checkpointing, replay, and time-travel debugging.

---

## 2. Side Effects in Conditional Edges

```python
# ❌ WRONG: LLM call in routing function
def route(state):
    result = llm.invoke("decide next step")  # Side effect!
    return "node_a" if "yes" in result else "node_b"

# ✅ CORRECT: Routing reads state only
def route(state):
    return state["next_action"]  # Decided in previous node
```

**Why**: Routing functions must be deterministic for replay.

---

## 3. Interrupt Without Checkpointer

```python
# ❌ WRONG: interrupt without persistence
app = graph.compile(interrupt_before=["review"])

# ✅ CORRECT: Always pair with checkpointer
app = graph.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["review"]
)
```

**Why**: Can't resume without saved state.

---

## 4. Manual DB Writes in Nodes

```python
# ❌ WRONG: Duplicates checkpointer's job
def node(state):
    db.save(state)  # Manual persistence
    return {"result": "done"}

# ✅ CORRECT: Let checkpointer handle persistence
def node(state):
    return {"result": "done"}

app = graph.compile(checkpointer=PostgresSaver(...))
```

**Why**: Breaks replay semantics, duplicates effort.

---

## 5. Large Data in State

```python
# ❌ WRONG: Storing raw file content
class State(TypedDict):
    document_content: str  # Could be megabytes
    image_data: bytes

# ✅ CORRECT: Store references only
class State(TypedDict):
    document_path: str
    image_url: str
```

**Why**: State is checkpointed frequently; large state = slow + expensive.

---

## 6. Forgetting to Compile

```python
# ❌ WRONG: Using StateGraph directly
graph = StateGraph(State)
graph.add_node(...)
result = graph.invoke(input)  # Error!

# ✅ CORRECT: Compile first
app = graph.compile()
result = app.invoke(input)
```

---

## 7. Missing Reducer for Lists

```python
# ❌ WRONG: List gets overwritten
class State(TypedDict):
    messages: list  # No reducer

# ✅ CORRECT: Use reducer to append
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
```

---

## 8. Infinite Loops in Multi-Agent

```python
# ❌ WRONG: No termination condition
def supervisor_route(state):
    return random.choice(["agent_a", "agent_b"])  # Never ends!

# ✅ CORRECT: Include finish condition
def supervisor_route(state):
    if state["task_complete"]:
        return END
    return state["next_agent"]
```

---

## 9. Blocking Calls Without Async

```python
# ❌ WRONG: Sync blocking in async context
async def node(state):
    result = requests.get(url)  # Blocks event loop

# ✅ CORRECT: Use async libraries
async def node(state):
    async with httpx.AsyncClient() as client:
        result = await client.get(url)
```

---

## 10. Hardcoding Thread IDs

```python
# ❌ WRONG: Same thread for all users
config = {"configurable": {"thread_id": "main"}}

# ✅ CORRECT: Unique thread per conversation
config = {"configurable": {"thread_id": f"user-{user_id}-{session_id}"}}
```
