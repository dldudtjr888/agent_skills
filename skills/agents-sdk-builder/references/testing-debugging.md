# Testing & Debugging

Testing, debugging, and observability for production agents.

## Unit Testing

### Testing Agents

```python
import pytest
from agents import Agent, Runner

@pytest.mark.asyncio
async def test_agent_basic():
    agent = Agent(
        name="Test Agent",
        instructions="Say hello",
    )
    
    result = await Runner.run(agent, "Hi")
    assert result.final_output
    assert len(result.new_items) > 0

@pytest.mark.asyncio
async def test_agent_with_tools():
    @function_tool
    def add(a: int, b: int) -> int:
        return a + b
    
    agent = Agent(
        name="Math Agent",
        instructions="Use the add tool",
        tools=[add],
    )
    
    result = await Runner.run(agent, "What is 5 + 3?")
    assert "8" in result.final_output
```

### Testing Tools

```python
@pytest.mark.asyncio
async def test_tool_directly():
    @function_tool
    async def fetch_data(query: str) -> str:
        return f"Data for {query}"
    
    # Test tool directly
    result = await fetch_data("test")
    assert result == "Data for test"

@pytest.mark.asyncio
async def test_tool_with_agent():
    agent = Agent(
        name="Agent",
        instructions="Use fetch_data tool",
        tools=[fetch_data],
    )
    
    result = await Runner.run(agent, "Fetch data for X")
    assert "Data for X" in result.final_output
```

### Mocking External APIs

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get', new_callable=AsyncMock)
async def test_api_tool(mock_get):
    # Mock API response
    mock_response = AsyncMock()
    mock_response.text = "API response"
    mock_get.return_value = mock_response
    
    @function_tool
    async def call_api(url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.text
    
    result = await call_api("https://api.example.com")
    assert result == "API response"
```

## Tracing

### View Traces

All agent runs are automatically traced:

```python
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(
        workflow_name="My Workflow",
        group_id="conversation_123",
        trace_metadata={"user_id": "123", "env": "prod"},
    ),
)

# View at: https://platform.openai.com/traces
```

### Custom Tracing

```python
from agents.tracing import trace

with trace(workflow_name="Custom Workflow", group_id="batch_1"):
    result1 = await Runner.run(agent, "Query 1")
    result2 = await Runner.run(agent, "Query 2")
    # Both runs linked by group_id
```

### Disable Tracing

```python
result = await Runner.run(
    agent,
    input,
    run_config=RunConfig(tracing_disabled=True),
)
```

## Debugging

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Agents SDK will log detailed information
result = await Runner.run(agent, "Hello")
```

### Inspect Results

```python
result = await Runner.run(agent, "Hello")

# Check result details
print(f"Final output: {result.final_output}")
print(f"New items: {len(result.new_items)}")
print(f"Agent name: {result.agent.name}")

# Inspect all items
for item in result.new_items:
    print(f"Type: {item.type}")
    if hasattr(item, 'content'):
        print(f"Content: {item.content}")
```

### Debug Handoffs

```python
async def debug_handoffs(result):
    handoff_count = 0
    
    for item in result.new_items:
        if item.type == "handoff_item":
            handoff_count += 1
            print(f"Handoff {handoff_count}: {item.current_agent} -> {item.target_agent}")
    
    print(f"Total handoffs: {handoff_count}")
```

### Debug Tool Calls

```python
async def debug_tools(result):
    tool_calls = [
        item for item in result.new_items
        if item.type == "tool_call_item"
    ]
    
    for tool_call in tool_calls:
        print(f"Tool: {tool_call.name}")
        print(f"Arguments: {tool_call.arguments}")
        
        # Find corresponding output
        output = next(
            (item for item in result.new_items
             if item.type == "tool_call_output_item" and item.call_id == tool_call.call_id),
            None
        )
        if output:
            print(f"Output: {output.output}")
```

## Performance Monitoring

### Measure Latency

```python
import time

start = time.time()
result = await Runner.run(agent, "Hello")
duration = time.time() - start

print(f"Duration: {duration:.2f}s")
print(f"Output length: {len(result.final_output)}")
print(f"Items generated: {len(result.new_items)}")
```

### Track Token Usage

```python
# Enable trace to see token usage
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(workflow_name="Token Tracking"),
)

# View token usage in trace dashboard
```

## Common Issues

### Agent Not Using Tools

**Debug:**
```python
# Check tool descriptions are clear
agent = Agent(
    name="Agent",
    tools=[my_tool],
    model_settings=ModelSettings(tool_choice="required"),  # Force tool use
)

result = await Runner.run(agent, "Use the tool")

# Check if tool was called
tool_used = any(item.type == "tool_call_item" for item in result.new_items)
print(f"Tool used: {tool_used}")
```

### Handoffs Not Working

**Debug:**
```python
# Add handoff_description
specialist = Agent(
    name="Specialist",
    handoff_description="Use for expert-level questions",  # Important!
    instructions="Provide expert help",
)

# Check handoff instructions
triage = Agent(
    name="Triage",
    instructions="Hand off to specialist for complex questions",  # Be explicit
    handoffs=[specialist],
)
```

### Session Not Persisting

**Debug:**
```python
# Verify session ID is consistent
session_id = "user_123"
session = SQLiteSession(session_id, "test.db")

# First turn
result1 = await Runner.run(agent, "My name is Alice", session=session)

# Check session has items
items = await session.get_items()
print(f"Session has {len(items)} items")

# Second turn
result2 = await Runner.run(agent, "What's my name?", session=session)
```

## Best Practices

1. **Write Tests Early**: Test agents and tools independently
2. **Use Tracing**: Enable for all production runs
3. **Log Errors**: Capture and log all exceptions
4. **Monitor Latency**: Track performance over time
5. **Version Agents**: Track instruction changes
6. **Test Handoffs**: Verify routing works as expected

## Resources

- [Tracing Dashboard](https://platform.openai.com/traces)
- [Debugging Guide](https://openai.github.io/openai-agents-python/debugging/)
