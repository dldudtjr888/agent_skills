# Streaming Guide

Complete guide to streaming agent responses for real-time user interfaces.

## Overview

Streaming allows you to receive agent responses progressively, enabling:
- Real-time UI updates (typewriter effect)
- Progress indicators for tool calls
- Responsive user experience
- Early error detection

## Basic Streaming

### Simple Text Streaming

```python
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

agent = Agent(
    name="Storyteller",
    instructions="Tell engaging stories",
)

result = Runner.run_streamed(agent, "Tell me a short story")

async for event in result.stream_events():
    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
```

## Event Types

### 1. Raw Response Events

Low-level events directly from the LLM:

```python
async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            # Text token
            print(event.data.delta, end="")
        
        elif isinstance(event.data, ResponseFunctionToolCallDelta):
            # Tool call in progress
            print(f"Tool: {event.data.name}")
        
        elif isinstance(event.data, ResponseDone):
            # Response complete
            print("\nDone!")
```

### 2. Run Item Stream Events

High-level semantic events:

```python
from agents import ItemHelpers

async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        match event.name:
            case "message_output_created":
                # New message generated
                text = ItemHelpers.text_message_output(event.item)
                print(f"\nMessage: {text}")
            
            case "tool_called":
                # Tool was invoked
                print(f"\nCalling tool: {event.item.name}")
            
            case "tool_output":
                # Tool completed
                print(f"\nTool result: {event.item.output}")
            
            case "handoff_requested":
                # Handoff initiated
                print(f"\nHandoff requested to: {event.item.target_agent}")
            
            case "handoff_occured":
                # Handoff completed
                print(f"\nHandoff completed")
            
            case "reasoning_item_created":
                # Reasoning output (o1 models)
                print(f"\nReasoning: {event.item.content}")
            
            case "mcp_approval_requested":
                # MCP tool needs approval
                print(f"\nApproval needed for: {event.item.tool_name}")
```

### 3. Agent Updated Events

Agent changes (handoffs):

```python
async for event in result.stream_events():
    if event.type == "agent_updated_stream_event":
        print(f"\nAgent changed: {event.old_agent.name} → {event.new_agent.name}")
```

## Complete Example

```python
import asyncio
from agents import Agent, Runner, ItemHelpers, function_tool
import random

@function_tool
def roll_dice(sides: int = 6) -> int:
    """Roll a dice with specified number of sides."""
    return random.randint(1, sides)

async def main():
    agent = Agent(
        name="Game Master",
        instructions="You are a game master. Roll dice when asked and narrate results.",
        tools=[roll_dice],
    )
    
    result = Runner.run_streamed(agent, "Roll a 20-sided dice!")
    
    print("=== Streaming Events ===\n")
    
    async for event in result.stream_events():
        # Skip raw events for cleaner output
        if event.type == "raw_response_event":
            continue
        
        # Agent updates
        if event.type == "agent_updated_stream_event":
            print(f"[Agent: {event.new_agent.name}]")
            continue
        
        # High-level events
        if event.type == "run_item_stream_event":
            if event.name == "tool_called":
                print(f"\n🔧 Calling tool: {event.item.name}")
                print(f"   Arguments: {event.item.arguments}")
            
            elif event.name == "tool_output":
                print(f"✅ Tool result: {event.item.output}\n")
            
            elif event.name == "message_output_created":
                text = ItemHelpers.text_message_output(event.item)
                print(f"💬 {text}")
    
    print("\n\n=== Final Result ===")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Filtering Events

### Filter by Event Type

```python
async for event in result.stream_events():
    # Only show text, skip everything else
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="")
```

### Filter by Event Name

```python
async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        # Only show tool-related events
        if event.name in ["tool_called", "tool_output"]:
            print(f"{event.name}: {event.item}")
```

## Building Real-Time UIs

### FastAPI + Server-Sent Events (SSE)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent
import json

app = FastAPI()

@app.post("/chat/stream")
async def chat_stream(message: str):
    agent = Agent(
        name="Assistant",
        instructions="Be helpful and concise",
    )
    
    async def event_generator():
        result = Runner.run_streamed(agent, message)
        
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    # Send text delta as SSE
                    yield f"data: {json.dumps({'type': 'text', 'content': event.data.delta})}\n\n"
            
            elif event.type == "run_item_stream_event":
                if event.name == "tool_called":
                    yield f"data: {json.dumps({'type': 'tool', 'name': event.item.name})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

### WebSocket Streaming

```python
from fastapi import WebSocket
import json

@app.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data["message"]
            
            # Stream response
            result = Runner.run_streamed(agent, message)
            
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    if isinstance(event.data, ResponseTextDeltaEvent):
                        await websocket.send_json({
                            "type": "text",
                            "content": event.data.delta,
                        })
                
                elif event.type == "run_item_stream_event":
                    if event.name == "tool_called":
                        await websocket.send_json({
                            "type": "tool",
                            "tool_name": event.item.name,
                        })
            
            # Send done signal
            await websocket.send_json({"type": "done"})
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

### React Frontend

```javascript
// Using SSE
const EventSource = require('eventsource');

function streamChat(message, onChunk, onComplete) {
  const eventSource = new EventSource(`/chat/stream?message=${encodeURIComponent(message)}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'text') {
      onChunk(data.content);
    } else if (data.type === 'tool') {
      console.log('Tool called:', data.name);
    } else if (data.type === 'done') {
      eventSource.close();
      onComplete();
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
  };
}

// Usage
streamChat(
  "Tell me a story",
  (chunk) => console.log(chunk),  // Print each chunk
  () => console.log("Done!")       // Called when complete
);
```

## Progressive UI Updates

### Typewriter Effect

```python
import asyncio

async def typewriter_effect(text_stream):
    """Display text with typewriter effect."""
    async for event in text_stream:
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
                await asyncio.sleep(0.02)  # Slight delay for effect
```

### Progress Indicators

```python
async def with_progress(result):
    """Show progress for long-running operations."""
    tool_count = 0
    
    async for event in result.stream_events():
        if event.type == "run_item_stream_event":
            if event.name == "tool_called":
                tool_count += 1
                print(f"\n[Step {tool_count}: {event.item.name}...]", end="")
            
            elif event.name == "tool_output":
                print(" ✓")
            
            elif event.name == "message_output_created":
                print(f"\n\n{ItemHelpers.text_message_output(event.item)}")
```

### Loading States

```python
class StreamingUI:
    def __init__(self):
        self.is_streaming = False
        self.current_text = ""
        self.tool_in_progress = None
    
    async def handle_stream(self, result):
        self.is_streaming = True
        self.current_text = ""
        
        try:
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    if isinstance(event.data, ResponseTextDeltaEvent):
                        self.current_text += event.data.delta
                        self.update_ui()
                
                elif event.type == "run_item_stream_event":
                    if event.name == "tool_called":
                        self.tool_in_progress = event.item.name
                        self.update_ui()
                    
                    elif event.name == "tool_output":
                        self.tool_in_progress = None
                        self.update_ui()
        
        finally:
            self.is_streaming = False
            self.update_ui()
    
    def update_ui(self):
        """Update UI components."""
        if self.tool_in_progress:
            print(f"⏳ {self.tool_in_progress}...", end="\r")
        else:
            print(f"{self.current_text}", end="\r")
```

## Multi-Agent Streaming

### Tracking Agent Switches

```python
async def stream_with_agents(result):
    current_agent = None
    
    async for event in result.stream_events():
        # Track agent changes
        if event.type == "agent_updated_stream_event":
            current_agent = event.new_agent.name
            print(f"\n[{current_agent}]")
        
        # Show text with agent context
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="")
```

### Handoff Visualization

```python
async def visualize_handoffs(result):
    agents_used = []
    
    async for event in result.stream_events():
        if event.type == "run_item_stream_event":
            if event.name == "handoff_requested":
                print(f"\n📤 Handoff: {event.item.current_agent} → {event.item.target_agent}")
                agents_used.append(event.item.target_agent)
            
            elif event.name == "handoff_occured":
                print(f"✅ Handoff complete")
    
    print(f"\n\nAgents used: {' → '.join(agents_used)}")
```

## Error Handling

### Graceful Error Recovery

```python
async def stream_with_error_handling(result):
    try:
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="")
    
    except Exception as e:
        print(f"\n\nError during streaming: {e}")
        
        # Still get partial result
        if hasattr(result, 'final_output'):
            print(f"\nPartial output: {result.final_output}")
```

### Timeout Handling

```python
import asyncio

async def stream_with_timeout(result, timeout=30):
    try:
        async with asyncio.timeout(timeout):
            async for event in result.stream_events():
                # Process events
                pass
    
    except asyncio.TimeoutError:
        print(f"\n\nStream timed out after {timeout}s")
        # Cleanup
```

## Performance Optimization

### Buffering

Buffer small chunks for efficiency:

```python
class BufferedStreamer:
    def __init__(self, buffer_size=10):
        self.buffer = []
        self.buffer_size = buffer_size
    
    async def stream(self, result):
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    self.buffer.append(event.data.delta)
                    
                    if len(self.buffer) >= self.buffer_size:
                        self.flush()
        
        # Flush remaining
        self.flush()
    
    def flush(self):
        if self.buffer:
            print(''.join(self.buffer), end="", flush=True)
            self.buffer.clear()
```

### Selective Event Processing

Only process events you need:

```python
# Fast: Only text
async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="")

# Slower: Process all events
async for event in result.stream_events():
    # Heavy processing for every event
    log_event(event)
    update_metrics(event)
    notify_observers(event)
```

## Best Practices

### 1. Always Handle Completion

```python
async for event in result.stream_events():
    # Process events
    pass

# After loop, get final result
print(f"\nFinal output: {result.final_output}")
print(f"New items: {len(result.new_items)}")
```

### 2. Use Appropriate Event Level

```python
# For UI: Use high-level events
async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        # Clean semantic events
        pass

# For logging: Use raw events
async for event in result.stream_events():
    if event.type == "raw_response_event":
        # Detailed LLM events
        pass
```

### 3. Test Without Streaming First

```python
# First, test without streaming
result = await Runner.run(agent, "test")
assert result.final_output  # Verify it works

# Then add streaming
result = Runner.run_streamed(agent, "test")
async for event in result.stream_events():
    # Add streaming logic
    pass
```

### 4. Separate Concerns

```python
async def process_stream(result):
    """Process streaming events."""
    async for event in result.stream_events():
        yield event

async def render_ui(event_stream):
    """Render UI from events."""
    async for event in event_stream:
        update_display(event)

# Usage
events = process_stream(result)
await render_ui(events)
```

## Troubleshooting

### Events Not Streaming

- Ensure using `run_streamed()` not `run()`
- Check you're iterating with `async for`
- Verify `flush=True` when printing

### Partial Content

- Always check `result.final_output` after loop
- Some content may only appear in final result
- Use both streaming AND final result

### Memory Leaks

- Don't accumulate all events in memory
- Process and discard events
- Use generators for large streams

## Resources

- [Streaming Documentation](https://openai.github.io/openai-agents-python/streaming/)
- [Event Reference](https://openai.github.io/openai-agents-python/ref/stream_events/)
- [Streaming Examples](https://github.com/openai/openai-agents-python/tree/main/examples)
