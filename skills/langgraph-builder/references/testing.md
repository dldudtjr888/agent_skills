# Testing Patterns

## Unit Tests (Node Functions)

```python
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from src.nodes import agent_node, process_node

def test_agent_node_returns_messages():
    state = {"messages": [HumanMessage(content="hello")]}
    result = agent_node(state)
    
    assert "messages" in result
    assert len(result["messages"]) > 0

def test_process_node_updates_state():
    state = {"input": "test data", "processed": False}
    result = process_node(state)
    
    assert result["processed"] == True
```

---

## Integration Tests (Full Graph)

```python
import pytest
from src.graph import create_graph

@pytest.fixture
def app():
    graph = create_graph()
    return graph.compile()

def test_graph_basic_flow(app):
    result = app.invoke({
        "messages": [("user", "Hello, how are you?")]
    })
    
    assert "messages" in result
    assert len(result["messages"]) >= 2  # User + AI response

def test_graph_with_tools(app):
    result = app.invoke({
        "messages": [("user", "What's 2 + 2?")]
    })
    
    # Check tool was called (if applicable)
    messages = result["messages"]
    tool_calls = [m for m in messages if hasattr(m, 'tool_calls') and m.tool_calls]
    assert len(tool_calls) > 0 or "4" in messages[-1].content
```

---

## Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_graph():
    result = await app.ainvoke({
        "messages": [("user", "async test")]
    })
    assert result["messages"]

@pytest.mark.asyncio
async def test_async_streaming():
    chunks = []
    async for chunk in app.astream({"messages": [("user", "stream test")]}):
        chunks.append(chunk)
    assert len(chunks) > 0
```

---

## Persistence Tests

```python
from langgraph.checkpoint.memory import InMemorySaver

def test_conversation_persistence():
    checkpointer = InMemorySaver()
    app = graph.compile(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "test-thread"}}
    
    # First turn
    result1 = app.invoke(
        {"messages": [("user", "My name is Alice")]},
        config
    )
    
    # Second turn - should remember
    result2 = app.invoke(
        {"messages": [("user", "What's my name?")]},
        config
    )
    
    # Check conversation continued
    assert len(result2["messages"]) > len(result1["messages"])

def test_state_snapshot():
    checkpointer = InMemorySaver()
    app = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "snapshot-test"}}
    
    app.invoke({"messages": [("user", "test")]}, config)
    
    # Get state snapshot
    state = app.get_state(config)
    assert state.values is not None
    assert "messages" in state.values
```

---

## Mocking External Calls

```python
from unittest.mock import patch, MagicMock

def test_with_mocked_llm():
    mock_response = AIMessage(content="Mocked response")
    
    with patch('src.nodes.model') as mock_model:
        mock_model.invoke.return_value = mock_response
        
        result = app.invoke({"messages": [("user", "test")]})
        
        assert "Mocked response" in result["messages"][-1].content

def test_with_mocked_tool():
    with patch('src.tools.search_tool') as mock_tool:
        mock_tool.invoke.return_value = "Mock search result"
        
        result = app.invoke({
            "messages": [("user", "search for something")]
        })
        
        mock_tool.invoke.assert_called()
```

---

## Interrupt/Resume Tests

```python
def test_human_in_the_loop():
    checkpointer = InMemorySaver()
    app = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["review"]
    )
    config = {"configurable": {"thread_id": "hitl-test"}}
    
    # Run until interrupt
    result = app.invoke({"messages": [("user", "process this")]}, config)
    
    # Check we're paused
    state = app.get_state(config)
    assert "review" in state.next
    
    # Resume with human input
    app.update_state(config, {"approved": True})
    final = app.invoke(None, config)
    
    assert final  # Continued after review
```

---

## Edge Case Tests

```python
def test_empty_input():
    result = app.invoke({"messages": []})
    # Should handle gracefully
    assert result is not None

def test_very_long_conversation():
    config = {"configurable": {"thread_id": "long-conv"}}
    
    for i in range(20):
        app.invoke(
            {"messages": [("user", f"Message {i}")]},
            config
        )
    
    state = app.get_state(config)
    # Check it doesn't crash with many messages
    assert len(state.values["messages"]) > 0

def test_special_characters():
    result = app.invoke({
        "messages": [("user", "Test with émojis 🚀 and spëcial çharacters")]
    })
    assert result["messages"]
```

---

## pytest.ini Configuration

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

---

## Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_graph.py

# Run with verbose output
pytest -v -s

# Run async tests only
pytest -m asyncio
```
