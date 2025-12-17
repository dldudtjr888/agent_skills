# Debugging Guide

Debug OpenRouter + LangGraph agents with logging, tracing, and common error solutions.

## LangSmith Tracing

### Setup

```bash
# Environment variables
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="lsv2_pt_xxxxx"
export LANGCHAIN_PROJECT="my-agent-project"
```

```python
# Or programmatically
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "lsv2_pt_xxxxx"
os.environ["LANGCHAIN_PROJECT"] = "my-agent-project"
```

### Trace-Specific Tags

```python
# Add metadata for filtering traces
result = agent.invoke(
    {"messages": [...]},
    config={
        "tags": ["production", "chat"],
        "metadata": {
            "user_id": "user_123",
            "session_id": "sess_456",
        }
    }
)
```

### Run-Level Callbacks

```python
from langchain_core.callbacks import BaseCallbackHandler

class DebugCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM Start: {serialized.get('name')}")
        print(f"Prompts: {prompts[:100]}...")
    
    def on_llm_end(self, response, **kwargs):
        print(f"LLM End: {response.generations[0][0].text[:100]}...")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"Tool Start: {serialized.get('name')} - Input: {input_str}")
    
    def on_tool_end(self, output, **kwargs):
        print(f"Tool End: {output[:100]}...")
    
    def on_tool_error(self, error, **kwargs):
        print(f"Tool Error: {error}")

# Use in agent
result = agent.invoke(
    {"messages": [...]},
    config={"callbacks": [DebugCallbackHandler()]}
)
```

## Logging Setup

### Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        if hasattr(record, "tool_name"):
            log_data["tool_name"] = record.tool_name
        if hasattr(record, "tokens"):
            log_data["tokens"] = record.tokens
        
        return json.dumps(log_data)

# Configure
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())

logger = logging.getLogger("agent")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

### Logging Middleware

```python
from langchain.agents.middleware import AgentMiddleware
import logging
import time

logger = logging.getLogger("agent.middleware")

class LoggingMiddleware(AgentMiddleware):
    """Log all agent operations."""
    
    def __init__(self, log_messages: bool = False):
        self.log_messages = log_messages
    
    def before_model(self, state):
        self._start_time = time.time()
        
        if self.log_messages:
            last_msg = state["messages"][-1]
            logger.info(
                f"Model input",
                extra={
                    "message_role": last_msg.type,
                    "message_length": len(str(last_msg.content)),
                }
            )
        return state
    
    def after_model(self, state, response):
        elapsed = time.time() - self._start_time
        
        usage = getattr(response, "usage_metadata", None)
        logger.info(
            f"Model response",
            extra={
                "elapsed_seconds": elapsed,
                "tokens": {
                    "input": usage.input_tokens if usage else None,
                    "output": usage.output_tokens if usage else None,
                },
                "finish_reason": response.response_metadata.get("finish_reason"),
            }
        )
        return state
```

## Debugging Multi-Agent

### Visualize Graph

```python
from IPython.display import Image, display

# Draw graph structure
graph_image = app.get_graph().draw_mermaid_png()
display(Image(graph_image))

# Or save to file
with open("graph.png", "wb") as f:
    f.write(graph_image)
```

### Trace Agent Routing

```python
class RoutingDebugMiddleware(AgentMiddleware):
    """Track which agents are called and in what order."""
    
    def __init__(self):
        self.call_history = []
    
    def before_model(self, state):
        agent_name = state.get("active_agent", "unknown")
        self.call_history.append({
            "agent": agent_name,
            "timestamp": time.time(),
            "message_count": len(state["messages"]),
        })
        print(f"[DEBUG] Agent '{agent_name}' receiving control")
        return state
    
    def get_history(self):
        return self.call_history
```

### Print State at Each Step

```python
# Stream with debug output
for chunk in app.stream(
    {"messages": [{"role": "user", "content": "Test"}]},
    stream_mode="updates",
):
    node_name = list(chunk.keys())[0]
    node_output = chunk[node_name]
    
    print(f"\n{'='*50}")
    print(f"Node: {node_name}")
    print(f"Keys: {node_output.keys() if isinstance(node_output, dict) else 'N/A'}")
    
    if "messages" in node_output:
        last_msg = node_output["messages"][-1]
        print(f"Last message type: {type(last_msg).__name__}")
        print(f"Content preview: {str(last_msg.content)[:200]}...")
```

## Common Errors and Solutions

### 1. Rate Limiting (429)

**Error:**
```
Error code: 429 - Rate limit exceeded
```

**Causes:**
- Too many requests per minute
- Free tier limits (50 or 1,000 req/day)
- Provider-specific limits

**Solutions:**

```python
# 1. Add retry with backoff
from langchain.agents.middleware import ToolRetryMiddleware

agent = create_agent(
    model=llm,
    middleware=[
        ToolRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
        )
    ],
)

# 2. Use rate limiting middleware
import asyncio
from collections import deque
import time

class RateLimitMiddleware(AgentMiddleware):
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.request_times = deque()
    
    async def before_model_async(self, state):
        now = time.time()
        
        # Remove old requests
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Wait if at limit
        if len(self.request_times) >= self.rpm:
            wait_time = 60 - (now - self.request_times[0])
            await asyncio.sleep(wait_time)
        
        self.request_times.append(time.time())
        return state

# 3. Use :floor variant for cheaper rate limits
llm = ChatOpenRouter(model="anthropic/claude-sonnet-4", variant="floor")
```

### 2. Context Length Exceeded

**Error:**
```
Error: context_length_exceeded - Request exceeds maximum context length
```

**Causes:**
- Conversation too long
- Large tool outputs
- System prompt too verbose

**Solutions:**

```python
# 1. Use summarization middleware
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model=llm,
    middleware=[
        SummarizationMiddleware(
            trigger="token_count",
            threshold=100000,  # Summarize when exceeding
            keep=50000,        # Keep this many tokens
        )
    ],
)

# 2. Truncate tool outputs
@tool
def search_with_limit(query: str) -> str:
    """Search with output limit."""
    results = do_search(query)
    return results[:5000]  # Limit output length

# 3. Use longer context model
llm = ChatOpenRouter(model="google/gemini-2.5-pro")  # 2M context
```

### 3. Tool Calling Failures

**Error:**
```
OutputParserException: Could not parse tool call
```

**Causes:**
- Model returning malformed JSON
- Tool schema mismatch
- Model not supporting tool calling

**Solutions:**

```python
# 1. Use :exacto variant for better tool calling
llm = ChatOpenRouter(model="anthropic/claude-sonnet-4", variant="exacto")

# 2. Simplify tool schemas
from langchain_core.tools import tool

# Bad: Complex nested schema
@tool
def complex_tool(config: dict) -> str:
    """Do something with config."""
    pass

# Good: Simple flat parameters
@tool
def simple_tool(name: str, value: int) -> str:
    """Do something with name and value."""
    pass

# 3. Add tool calling retry
from langchain.agents.middleware import ToolRetryMiddleware

agent = create_agent(
    model=llm,
    middleware=[ToolRetryMiddleware(max_retries=3)],
)

# 4. Verify tool schemas
for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Schema: {tool.args_schema.schema()}")
```

### 4. Recursion Limit Exceeded

**Error:**
```
GraphRecursionError: Recursion limit of X reached
```

**Causes:**
- Agent looping without progress
- Circular handoffs between agents
- Tool always failing and retrying

**Solutions:**

```python
# 1. Increase limit if genuinely needed
result = app.invoke(
    {"messages": [...]},
    config={"recursion_limit": 100},
)

# 2. Add progress detection
class LoopDetectionMiddleware(AgentMiddleware):
    def __init__(self, max_identical: int = 3):
        self.max_identical = max_identical
        self.recent_outputs = []
    
    def after_model(self, state, response):
        output = response.content
        
        # Check for identical outputs
        if self.recent_outputs.count(output) >= self.max_identical:
            raise Exception("Agent appears to be stuck in a loop")
        
        self.recent_outputs.append(output)
        if len(self.recent_outputs) > 10:
            self.recent_outputs.pop(0)
        
        return state

# 3. Better system prompt
system_prompt = """
You are a helpful assistant. 
IMPORTANT: If you cannot make progress on a task after 2 attempts, 
explain what's blocking you and ask for clarification.
"""
```

### 5. Model Unavailable

**Error:**
```
Error: Model anthropic/claude-opus-4 is currently unavailable
```

**Solutions:**

```python
# 1. Use fallback providers
response = llm.invoke(
    messages,
    extra_body={
        "provider": {
            "order": ["Anthropic", "Azure", "AWS Bedrock"],
            "allow_fallbacks": True,
        }
    }
)

# 2. Implement fallback models
from langchain.agents.middleware import AgentMiddleware

class ModelFallbackMiddleware(AgentMiddleware):
    def __init__(self, fallbacks: list[str]):
        self.fallbacks = fallbacks
    
    def modify_model_request(self, request):
        original = request._handler
        
        async def handler_with_fallback(req):
            try:
                return await original(req)
            except Exception as e:
                if "unavailable" in str(e).lower():
                    for fallback in self.fallbacks:
                        try:
                            req = req.override(model=ChatOpenRouter(model=fallback))
                            return await original(req)
                        except:
                            continue
                raise
        
        request._handler = handler_with_fallback
        return request
```

### 6. Streaming Errors

**Error:**
```
Error during streaming: Connection reset
```

**Solutions:**

```python
# 1. Add timeout and retry for streaming
async def stream_with_retry(agent, input, max_retries=3):
    for attempt in range(max_retries):
        try:
            async for event in agent.astream_events(input, version="v2"):
                yield event
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)

# 2. Handle partial responses
async def robust_stream(agent, input):
    buffer = []
    try:
        async for event in agent.astream_events(input, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                buffer.append(chunk)
                yield chunk
    except Exception as e:
        # Return accumulated content on error
        yield f"\n[Stream interrupted: {e}]"
        yield f"\nPartial response: {''.join(buffer)}"
```

### 7. Memory/Checkpointing Issues

**Error:**
```
Error: Thread not found or state corruption
```

**Solutions:**

```python
# 1. Verify checkpointer is working
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Test persistence
config = {"configurable": {"thread_id": "test_123"}}
result1 = app.invoke({"messages": [...]}, config)
result2 = app.invoke({"messages": [...]}, config)

# Verify history is maintained
assert len(result2["messages"]) > len(result1["messages"])

# 2. Handle missing threads gracefully
def safe_invoke(app, input, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        return app.invoke(input, config)
    except Exception as e:
        if "not found" in str(e).lower():
            # Start fresh
            return app.invoke(input, config)
        raise
```

## Debug Checklist

### Before Debugging

- [ ] Enable LangSmith tracing
- [ ] Set log level to DEBUG
- [ ] Prepare minimal reproduction case

### During Debugging

- [ ] Check LangSmith traces for exact error location
- [ ] Verify API key is valid
- [ ] Check model availability on OpenRouter
- [ ] Verify tool schemas are correct
- [ ] Check message format (role, content)
- [ ] Monitor token usage

### After Fixing

- [ ] Add test case for the bug
- [ ] Document the issue and solution
- [ ] Consider adding middleware to prevent recurrence

## Useful Commands

```bash
# Check OpenRouter status
curl https://status.openrouter.ai/api/v2/status.json

# Verify API key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models | jq '.data[0]'

# Check model availability
curl https://openrouter.ai/api/v1/models | jq '.data[] | select(.id == "anthropic/claude-sonnet-4")'

# Test basic completion
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-sonnet-4", "messages": [{"role": "user", "content": "Hi"}]}'
```

## Resources

- LangSmith Dashboard: https://smith.langchain.com
- LangSmith Docs: https://docs.smith.langchain.com
- OpenRouter Status: https://status.openrouter.ai
- OpenRouter Models: https://openrouter.ai/models
- LangGraph Overview: https://docs.langchain.com/oss/python/langgraph
- API Reference: https://docs.langchain.com/oss/python/reference/overview
