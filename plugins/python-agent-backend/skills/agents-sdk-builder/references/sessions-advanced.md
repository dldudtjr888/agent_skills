# Advanced Sessions

Comprehensive session management for production agents.

## Session Types

### SQLite (Development)

```python
from agents import SQLiteSession

# In-memory
session = SQLiteSession("session_id")

# File-based
session = SQLiteSession("session_id", "conversations.db")
```

### SQLAlchemy (Production)

```python
from agents import SQLAlchemySession
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/db")

session = SQLAlchemySession(
    session_id="user_123",
    engine=engine,
    create_tables=True,
)
```

### Redis

```python
from agents.extensions.memory import RedisSession
import redis.asyncio as redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

session = RedisSession(
    session_id="user_123",
    redis_client=redis_client,
    ttl=3600,  # 1 hour expiry
)
```

### Encrypted Sessions

```python
from agents.extensions.memory import EncryptedSession, SQLiteSession

base_session = SQLiteSession("user_123", "encrypted.db")

session = EncryptedSession(
    session_id="user_123",
    underlying_session=base_session,
    encryption_key="your-secret-key-32-bytes-long!",
    ttl=600,  # 10 minutes
)
```

## Custom Session Implementation

```python
from agents.memory.session import SessionABC
from agents.items import TResponseInputItem
from typing import List

class MyCustomSession(SessionABC):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.items = []
    
    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        """Retrieve conversation history."""
        if limit:
            return self.items[-limit:]
        return self.items
    
    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """Store new items."""
        self.items.extend(items)
    
    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return last item."""
        if self.items:
            return self.items.pop()
        return None
    
    async def clear_session(self) -> None:
        """Clear all items."""
        self.items.clear()
```

## Session Operations

### Correction Workflow

```python
session = SQLiteSession("user_123")

# Initial conversation
result = await Runner.run(agent, "What's 2+2?", session=session)
print(result.final_output)  # "4"

# User wants to correct
await session.pop_item()  # Remove agent response
await session.pop_item()  # Remove user message

# Ask corrected question
result = await Runner.run(agent, "What's 2+3?", session=session)
print(result.final_output)  # "5"
```

### Cross-Agent Sharing

```python
session = SQLiteSession("shared_conversation")

# First agent
agent1 = Agent(name="Researcher", instructions="Research topics")
await Runner.run(agent1, "Research AI safety", session=session)

# Second agent sees history
agent2 = Agent(name="Writer", instructions="Write summaries")
await Runner.run(agent2, "Summarize the research", session=session)
```

## Best Practices

### Use Meaningful IDs

```python
# Good
session = SQLiteSession(f"user_{user_id}_chat_{chat_id}")

# Avoid
session = SQLiteSession("session1")
```

### Session Cleanup

```python
# Clear old sessions
async def cleanup_old_sessions(db_path: str, days: int = 30):
    cutoff = datetime.now() - timedelta(days=days)
    # Delete sessions older than cutoff
    pass
```

### Error Recovery

```python
try:
    result = await Runner.run(agent, input, session=session)
except Exception as e:
    # Session state is preserved
    logger.error(f"Error: {e}")
    # Can retry or recover
    result = await Runner.run(agent, fallback_input, session=session)
```

## Resources

- [Sessions Documentation](https://openai.github.io/openai-agents-python/sessions/)
