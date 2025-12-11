# Realtime Voice Agents

Build low-latency voice agents using OpenAI's Realtime API with the gpt-realtime model.

## Overview

Realtime voice agents process audio directly using speech-to-speech models, achieving ultra-low latency (typically 300-500ms) without traditional STT→LLM→TTS pipeline delays.

**Key Features:**
- Direct audio processing (no intermediate text)
- Natural interruptions with semantic VAD
- Streaming audio responses
- Tool calling during voice conversations
- Handoffs between voice agents
- Phone integration via SIP

## Installation

```bash
pip install 'openai-agents[voice]'
```

## Basic Setup

### 1. Create RealtimeAgent

```python
from agents.realtime import RealtimeAgent

agent = RealtimeAgent(
    name="Voice Assistant",
    instructions="You are a helpful voice assistant. Keep responses brief and conversational.",
)
```

### 2. Configure RealtimeRunner

```python
from agents.realtime import RealtimeRunner

runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "model_name": "gpt-realtime",
            "voice": "ash",  # alloy, echo, fable, onyx, nova, shimmer, ash, ballad, coral, sage, verse
            "modalities": ["audio"],  # or ["text", "audio"]
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
        }
    },
)
```

### 3. Start Session

```python
session = await runner.run()

async with session:
    # Send audio
    session.send_audio(audio_bytes)
    
    # Or send text
    session.send_message("Hello")
    
    # Listen for events
    async for event in session:
        if event.type == "audio_delta":
            # Play audio_bytes
            play_audio(event.audio)
        elif event.type == "transcript_delta":
            print(event.transcript, end="")
```

## Configuration Options

### Model Settings

```python
config = {
    "model_settings": {
        # Model
        "model_name": "gpt-realtime",  # or gpt-realtime-mini
        
        # Voice
        "voice": "ash",  # Choose from available voices
        
        # Modalities
        "modalities": ["audio"],  # ["text"], ["audio"], or ["text", "audio"]
        
        # Audio Formats
        "input_audio_format": "pcm16",   # pcm16, g711_ulaw, g711_alaw
        "output_audio_format": "pcm16",  # pcm16, g711_ulaw, g711_alaw
        
        # Transcription (optional)
        "input_audio_transcription": {
            "model": "whisper-1",  # or gpt-4o-mini-transcribe
        },
        
        # Turn Detection
        "turn_detection": {
            "type": "semantic_vad",  # or "vad" or None for manual
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500,
            "interrupt_response": True,
        },
    }
}

runner = RealtimeRunner(starting_agent=agent, config=config)
```

### Turn Detection Modes

**Semantic VAD (Recommended):**
- Understands context and meaning
- Handles natural pauses in speech
- Better for conversational flow

```python
"turn_detection": {
    "type": "semantic_vad",
    "interrupt_response": True,  # Allow interruptions
}
```

**Basic VAD:**
- Simple voice activity detection
- Based on audio levels and silence
- More sensitive to interruptions

```python
"turn_detection": {
    "type": "vad",
    "threshold": 0.5,              # Detection sensitivity (0-1)
    "prefix_padding_ms": 300,      # Audio before speech start
    "silence_duration_ms": 500,    # Silence to detect end
}
```

**Manual (No VAD):**
- You control when turns end
- Useful for button-based interfaces

```python
"turn_detection": None

# Then manually trigger:
await session.generate_response()
```

## Event Handling

### Event Types

```python
async for event in session:
    match event.type:
        case "agent_start":
            print(f"Agent started: {event.agent.name}")
        
        case "agent_end":
            print(f"Agent ended: {event.agent.name}")
        
        case "audio_delta":
            # Stream audio output
            play_audio(event.audio)
        
        case "audio_done":
            # Audio generation complete
            print("Audio finished")
        
        case "audio_interrupted":
            # User interrupted agent
            stop_audio_playback()
            clear_audio_queue()
        
        case "transcript_delta":
            # Partial transcript
            print(event.transcript, end="")
        
        case "transcript_done":
            # Complete transcript
            print(f"\nFinal: {event.transcript}")
        
        case "tool_start":
            print(f"Tool called: {event.tool.name}")
        
        case "tool_end":
            print(f"Tool done: {event.tool.name}")
            print(f"Output: {event.output}")
        
        case "handoff":
            print(f"Handoff: {event.from_agent.name} → {event.to_agent.name}")
        
        case "error":
            print(f"Error: {event.error}")
```

## Interruptions

### Automatic Interruptions

With VAD enabled, interruptions are automatic:

```python
async for event in session:
    if event.type == "audio_interrupted":
        # Stop playback immediately
        audio_player.stop()
        audio_player.clear_queue()
```

### Manual Interruptions

```python
# User pressed "stop" button
await session.interrupt()
```

## Tools in Voice Agents

### Define Function Tools

```python
from agents import function_tool

@function_tool
async def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

@function_tool
async def book_appointment(date: str, time: str) -> str:
    """Book an appointment."""
    return f"Appointment booked for {date} at {time}"

voice_agent = RealtimeAgent(
    name="Booking Assistant",
    instructions="Help users book appointments. Ask for date and time, then confirm.",
    tools=[get_weather, book_appointment],
)
```

### Tool Approval (Human-in-the-Loop)

```python
from agents import ToolApprovalFunction

async def approve_booking(tool_name: str, arguments: dict) -> bool:
    """Require approval for booking."""
    if tool_name == "book_appointment":
        # Ask user to confirm
        return await ask_user_confirmation(arguments)
    return True  # Auto-approve other tools

voice_agent = RealtimeAgent(
    name="Booking Assistant",
    tools=[get_weather, book_appointment],
    tool_approval_function=approve_booking,
)
```

## Handoffs in Voice Agents

Voice agents can hand off to other voice agents:

```python
booking_agent = RealtimeAgent(
    name="Booking Agent",
    instructions="Help with bookings",
    tools=[book_appointment],
)

support_agent = RealtimeAgent(
    name="Support Agent",
    instructions="Help with support questions",
    tools=[search_kb],
)

triage_agent = RealtimeAgent(
    name="Triage",
    instructions="Route to booking or support based on user needs",
    handoffs=[booking_agent, support_agent],
)

runner = RealtimeRunner(starting_agent=triage_agent, config=config)
```

**Important Notes:**
- Voice and model cannot change during handoffs
- Conversation history is preserved
- Input filters are not applied during handoffs

## Phone Integration (SIP)

### Setup SIP Server

```python
from agents.realtime import OpenAIRealtimeSIPModel

sip_model = OpenAIRealtimeSIPModel(
    model_name="gpt-realtime",
    voice="ash",
)

runner = RealtimeRunner(
    starting_agent=agent,
    config={"model": sip_model},
)

# Start session with call_id from webhook
session = await runner.run(call_id="call_abc123")
```

### Handle Incoming Calls

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/incoming-call")
async def handle_call(request: Request):
    data = await request.json()
    call_id = data["call_id"]
    
    # Start voice agent for this call
    session = await runner.run(call_id=call_id)
    
    # Session runs until call ends
    async with session:
        async for event in session:
            # Handle events
            pass
    
    return {"status": "completed"}
```

## Guardrails for Voice

Only **output guardrails** are supported for realtime agents:

```python
from agents.realtime import RealtimeOutputGuardrail
from pydantic import BaseModel

class ContentCheck(BaseModel):
    is_appropriate: bool
    reasoning: str

checker = Agent(
    name="Content Checker",
    instructions="Check if content is appropriate",
    output_type=ContentCheck,
)

async def check_output(ctx, agent, transcript: str):
    result = await Runner.run(checker, transcript)
    check = result.final_output_as(ContentCheck)
    return GuardrailFunctionOutput(
        output_info=check,
        tripwire_triggered=not check.is_appropriate,
    )

voice_agent = RealtimeAgent(
    name="Assistant",
    instructions="Be helpful",
    output_guardrails=[
        RealtimeOutputGuardrail(
            guardrail_function=check_output,
            debounce_length=100,  # Check every 100 chars
        )
    ],
)
```

**Guardrail Features:**
- Run on transcripts (not audio directly)
- Debounced to avoid performance issues
- Can interrupt generation mid-response

## Complete Example

```python
import asyncio
from agents.realtime import RealtimeAgent, RealtimeRunner
from agents import function_tool

@function_tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"

async def main():
    # Create agent
    agent = RealtimeAgent(
        name="Weather Assistant",
        instructions="Help users check weather. Keep responses brief.",
        tools=[get_weather],
    )
    
    # Configure runner
    runner = RealtimeRunner(
        starting_agent=agent,
        config={
            "model_settings": {
                "model_name": "gpt-realtime",
                "voice": "ash",
                "modalities": ["audio"],
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "semantic_vad",
                    "interrupt_response": True,
                },
            }
        },
    )
    
    # Start session
    session = await runner.run()
    
    async with session:
        print("Voice session started!")
        
        # In real app, connect to microphone and speaker
        # For now, simulate with text
        session.send_message("What's the weather in Tokyo?")
        
        async for event in session:
            if event.type == "transcript_delta":
                print(event.transcript, end="")
            elif event.type == "audio_delta":
                # play_audio(event.audio)
                pass
            elif event.type == "tool_start":
                print(f"\n[Calling tool: {event.tool.name}]")
            elif event.type == "audio_interrupted":
                print("\n[User interrupted]")

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

### 1. Optimize Instructions

Voice agents need concise, natural instructions:

```python
# Good
instructions = "You're a helpful assistant. Keep responses brief and conversational."

# Avoid
instructions = "You are a highly sophisticated artificial intelligence system designed to..."
```

### 2. Handle Interruptions Gracefully

```python
async for event in session:
    if event.type == "audio_interrupted":
        # Critical: Stop playback immediately
        audio_player.stop()
        audio_player.clear_queue()
        
        # Optional: Log interruption
        logger.info("User interrupted agent")
```

### 3. Choose Appropriate Voice

Test different voices for your use case:
- **ash, ballad, coral, sage, verse**: New gpt-realtime exclusive voices
- **alloy, echo, fable, onyx, nova, shimmer**: Available across models

### 4. Tune Turn Detection

Adjust sensitivity based on your environment:

```python
# Noisy environment - less sensitive
"turn_detection": {
    "type": "semantic_vad",
    "threshold": 0.7,  # Higher threshold
    "silence_duration_ms": 700,  # Longer silence
}

# Quiet environment - more responsive
"turn_detection": {
    "type": "semantic_vad",
    "threshold": 0.3,  # Lower threshold
    "silence_duration_ms": 300,  # Shorter silence
}
```

### 5. Monitor Latency

```python
import time

start = time.time()

async for event in session:
    if event.type == "audio_delta":
        latency = (time.time() - start) * 1000
        print(f"Time to first audio: {latency}ms")
        break
```

### 6. Error Recovery

```python
try:
    async with session:
        async for event in session:
            if event.type == "error":
                logger.error(f"Session error: {event.error}")
                # Attempt reconnection
                await session.reconnect()
except Exception as e:
    logger.error(f"Fatal error: {e}")
    # Notify user and cleanup
```

## Troubleshooting

### High Latency

- Use gpt-realtime-mini for faster responses
- Reduce audio quality if needed
- Check network connectivity
- Use semantic_vad instead of basic vad

### Frequent Interruptions

- Increase `silence_duration_ms`
- Increase VAD `threshold`
- Switch to manual turn detection

### Audio Quality Issues

- Use pcm16 format for best quality
- Ensure proper sample rate (24kHz recommended)
- Check microphone/speaker hardware

### Tools Not Being Called

- Ensure tool descriptions are clear
- Keep tool names simple
- Test with text modality first
- Check tool function signatures

## Resources

- [Realtime API Docs](https://openai.github.io/openai-agents-python/realtime/)
- [Voice Examples](https://github.com/openai/openai-agents-python/tree/main/examples/realtime)
- [Realtime API Reference](https://platform.openai.com/docs/guides/realtime)
