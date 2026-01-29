# Persistence & Memory

## Checkpointer (Conversation State)

Saves state between invocations within a thread.

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-123"}}

# Conversation persists across calls
result1 = app.invoke({"messages": [{"role": "user", "content": "My name is Alice"}]}, config)
result2 = app.invoke({"messages": [{"role": "user", "content": "What's my name?"}]}, config)
# result2 knows the name
```

### Production Checkpointers

```python
# PostgreSQL (recommended)
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://user:pass@host/db")

# Redis
from langgraph.checkpoint.redis import RedisSaver
checkpointer = RedisSaver.from_url("redis://localhost:6379")
```

## State Inspection

```python
# Get current state
state = app.get_state(config)
print(state.values)  # Current state
print(state.next)    # Next node(s)

# Get history
for snapshot in app.get_state_history(config):
    print(snapshot.values)
```

## Human-in-the-Loop

```python
app = graph.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["sensitive_node"],
)

# Runs until interrupt
result = app.invoke(input, config)

# Check what's pending
state = app.get_state(config)
print(state.next)  # ['sensitive_node']

# Approve and continue
app.invoke(None, config)
```

## Thread ID Patterns

```python
# Per user
config = {"configurable": {"thread_id": f"user-{user_id}"}}

# Per session
config = {"configurable": {"thread_id": f"session-{session_id}"}}
```

## Common Mistakes

```python
# ❌ InMemorySaver in production (lost on restart!)
# ❌ Same thread_id for all users
# ❌ interrupt without checkpointer

# ✅ Use PostgresSaver/RedisSaver in production
# ✅ Unique thread_id per conversation
# ✅ Always pair interrupt with checkpointer
```
