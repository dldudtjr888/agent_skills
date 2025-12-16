# Production Deployment Checklist

## Pre-Deployment

### Essential
- [ ] Replace `InMemorySaver` with persistent checkpointer (Postgres, Redis, etc.)
- [ ] Add error handling to all nodes
- [ ] Set appropriate timeouts for LLM calls
- [ ] Configure rate limiting
- [ ] Enable LangSmith tracing
- [ ] Test with realistic data volume

### Recommended
- [ ] Visualize graph and verify flow
- [ ] Test edge cases (empty input, long conversations, special characters)
- [ ] Monitor token usage
- [ ] Add retry logic for LLM calls
- [ ] Implement graceful degradation

---

## Checkpointer Options

### Development
```python
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()  # Lost on restart
```

### Production
```python
# PostgreSQL (recommended)
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@host:5432/db"
)

# Redis
from langgraph.checkpoint.redis import RedisSaver
checkpointer = RedisSaver.from_url("redis://localhost:6379")

# SQLite (single-server only)
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("state.db")
```

---

## Error Handling

```python
from langchain_core.runnables import RunnableConfig
import logging

logger = logging.getLogger(__name__)

def robust_node(state: State, config: RunnableConfig) -> dict:
    try:
        result = perform_operation(state)
        return {"result": result, "error": None}
    except TimeoutError:
        logger.error("Operation timed out")
        return {"result": None, "error": "timeout"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"result": None, "error": str(e)}
```

---

## Timeout Configuration

```python
from langchain_openai import ChatOpenAI

# Set timeout on model
model = ChatOpenAI(
    model="gpt-4o",
    timeout=30,  # seconds
    max_retries=2
)

# Or use tenacity for custom retry
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_with_retry(messages):
    return model.invoke(messages)
```

---

## Monitoring

### LangSmith (Required)
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<key>
LANGCHAIN_PROJECT=production-agent
```

### Custom Metrics
```python
import time
from prometheus_client import Counter, Histogram

node_calls = Counter('node_calls_total', 'Total node calls', ['node_name'])
node_duration = Histogram('node_duration_seconds', 'Node duration', ['node_name'])

def instrumented_node(state):
    node_calls.labels(node_name='my_node').inc()
    
    start = time.time()
    result = actual_node_logic(state)
    duration = time.time() - start
    
    node_duration.labels(node_name='my_node').observe(duration)
    return result
```

---

## Multi-Agent Specific

- [ ] Verify agent state isolation
- [ ] Check context preservation during handoffs
- [ ] Ensure supervisor has termination condition (no infinite loops)
- [ ] Test concurrent agent execution
- [ ] Monitor individual agent performance

---

## Security

- [ ] Sanitize user inputs before passing to tools
- [ ] Validate tool outputs
- [ ] Use environment variables for secrets (never hardcode)
- [ ] Implement authentication for API endpoints
- [ ] Set up audit logging for sensitive operations

```python
# Input sanitization example
def sanitize_input(user_input: str) -> str:
    # Remove potential injection attempts
    return user_input.strip()[:10000]  # Limit length

def secure_node(state):
    safe_input = sanitize_input(state["user_input"])
    # ... process safe_input
```

---

## Deployment Options

### LangGraph Platform (Managed)
```bash
# Deploy to LangGraph Cloud
langgraph deploy

# Or self-hosted
langgraph up
```

### Custom Deployment
```python
# FastAPI wrapper
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = await graph_app.ainvoke(
        {"messages": [("user", request.message)]},
        config
    )
    return {"response": result["messages"][-1].content}
```

---

## Scaling Considerations

### Horizontal Scaling
- Use distributed checkpointer (Postgres/Redis)
- Stateless application servers
- Load balancer for API endpoints

### Vertical Scaling
- Increase worker processes for CPU-bound tasks
- Use async nodes for I/O-bound operations
- Consider streaming for long operations

---

## Post-Deployment

- [ ] Set up alerting for errors
- [ ] Monitor latency percentiles (p50, p95, p99)
- [ ] Track token usage and costs
- [ ] Review LangSmith traces regularly
- [ ] Plan for state migration (schema changes)
