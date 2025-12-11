# Tracing Reference Guide

Complete guide to Opik tracing capabilities.

**Quick Navigation:**
- [Core Concepts](#core-concepts) - Traces, spans, threads
- [Implementation Methods](#implementation-methods) - 4 ways to add tracing
- [Advanced Features](#advanced-features) - Threads, multimodal, distributed, costs
- [Troubleshooting](#troubleshooting)

---

## Core Concepts

- **Trace**: Complete record of an interaction (one user request → one response)
- **Span**: Individual operation within a trace (LLM call, retrieval, tool use)
- **Thread**: Group of related traces (multi-turn conversation)

## Implementation Methods

### 1. Function Decorators (Recommended)

**Basic usage:**
```python
import opik

@opik.track
def my_function(input: str) -> str:
    # Automatically logs input, output, timing, errors
    return process(input)
```

**Nested functions** (automatic parent-child relationships):
```python
@opik.track
def retrieve_context(query: str) -> list:
    # This becomes a span
    return search(query)

@opik.track
def generate_answer(question: str, context: list) -> str:
    # This becomes a span
    return llm(question, context)

@opik.track  # This becomes the parent trace
def rag_pipeline(question: str) -> str:
    context = retrieve_context(question)
    answer = generate_answer(question, context)
    return answer
```

**Custom parameters:**
```python
@opik.track(
    name="custom_trace_name",
    tags=["production", "v2"],
    metadata={"user_id": "123", "model": "gpt-4"},
    project_name="my-project"
)
def my_function(input):
    return output
```

### 2. Framework Integrations

**OpenAI:**
```python
from opik.integrations.openai import track_openai
import openai

client = track_openai(openai.OpenAI())
# All client.chat.completions.create() calls automatically tracked
```

**LangChain:**
```python
from opik.integrations.langchain import OpikTracer

callbacks = [OpikTracer(tags=["langchain"], project_name="my-project")]
chain.invoke(input, config={"callbacks": callbacks})
```

**LangGraph:**
```python
from opik.integrations.langchain import OpikTracer

config = {"callbacks": [OpikTracer()]}
result = graph.invoke(input, config)
```

**OpenAI Agents:**
```python
from opik.integrations.openai_agents import track_agents

client = openai.OpenAI()
track_agents(client)  # One-time setup

# All agent runs automatically tracked
agent = client.beta.agents.create(...)
run = agent.run(...)
```

**See references/integrations.md for 40+ frameworks**

### 3. Low-Level SDK (Full Control)

```python
from opik import Opik

client = Opik()

# Create trace
trace = client.trace(
    name="my_application",
    input={"question": "What is AI?"},
    metadata={"version": "1.0"}
)

# Create span
span = trace.span(
    name="llm_call",
    type="llm",  # Types: llm, tool, retrieval, general
    input={"prompt": "Explain AI"},
    metadata={"model": "gpt-4", "temperature": 0.7}
)

# Update span with output
span.update(
    output={"response": "AI is..."},
    usage={"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60}
)

# End trace
trace.update(output={"answer": "AI is..."})
```

### 4. Context Managers

```python
from opik import opik_context

# Trace-level context
with opik_context.track_trace(name="my_trace") as trace_ctx:
    trace_ctx.update_current_trace(
        input={"question": "What is AI?"},
        tags=["test"]
    )
    
    # Span-level context
    with opik_context.track_span(name="retrieval") as span_ctx:
        span_ctx.update_current_span(
            input={"query": "AI definition"},
            output={"docs": ["...", "..."]}
        )
    
    with opik_context.track_span(name="generation"):
        opik_context.update_current_span(
            input={"prompt": "..."},
            output={"text": "AI is..."}
        )
    
    trace_ctx.update_current_trace(
        output={"answer": "AI is..."}
    )
```

## Advanced Features

### Multi-turn Conversations (Threads)

Group related traces together:

```python
# Using decorator
@opik.track(thread_id="conversation-abc123")
def handle_message(message: str, thread_id: str) -> str:
    return chatbot_response(message)

# Using SDK
trace = client.trace(
    name="chat_turn",
    input={"message": "Hello"},
    thread_id="conversation-abc123"
)
```

**Thread features**:
- Automatic grouping in UI
- Thread-level evaluation
- Inactive after 15 minutes (configurable)
- Filter and search by thread_id

**Configure timeout**:
```bash
# Self-hosted only
export OPIK_TRACE_THREAD_TIMEOUT_TO_MARK_AS_INACTIVE=900  # 15 minutes in seconds
```

### User Feedback & Annotations

**Via SDK:**
```python
from opik import Opik
from opik.api_objects.helpers import FeedbackScoreDict

client = Opik()

# Log feedback for trace
client.log_traces_feedback_scores(
    scores=[
        FeedbackScoreDict(
            id="trace-id-here",
            name="helpfulness",
            value=0.9,
            reason="Very helpful and accurate"
        ),
        FeedbackScoreDict(
            id="trace-id-here",
            name="accuracy",
            value=1.0
        )
    ]
)

# Log feedback for span
client.log_spans_feedback_scores(
    scores=[
        FeedbackScoreDict(
            id="span-id-here",
            name="retrieval_quality",
            value=0.8,
            reason="Good but could be more specific"
        )
    ]
)
```

**Via UI:**
- Click trace → "Annotate" button
- Add scores, comments, tags
- View aggregated scores

### Multimodal Traces

Track images, videos, audio, and other media:

```python
from opik import Attachment, opik_context

# From file path
image = Attachment(
    data="/path/to/image.png",
    content_type="image/png"
)

# From base64
video = Attachment(
    data="base64_encoded_video_data",
    content_type="video/mp4"
)

# From URL (automatically detected)
audio = Attachment(
    data="https://example.com/audio.wav",
    content_type="audio/wav"
)

# Add to trace
opik_context.update_current_trace(
    input={
        "image": image,
        "prompt": "Describe this image"
    }
)

# Or add to span
opik_context.update_current_span(
    output={"generated_image": image}
)
```

**Supported formats**:
- Images: PNG, JPEG, GIF, WebP
- Video: MP4, WebM, AVI
- Audio: WAV, MP3, OGG
- Documents: PDF (as image preview)

**Auto-optimization**: Files >250KB automatically stored separately

### Distributed Tracing

Track requests across multiple services:

**Service A (Client):**
```python
from opik import opik_context
import requests

@opik.track
def call_service_b(data):
    # Get trace headers
    headers = opik_context.get_distributed_trace_headers()
    
    # Pass to Service B
    response = requests.post(
        "http://service-b/endpoint",
        json=data,
        headers=headers
    )
    return response.json()
```

**Service B (Server):**
```python
from flask import Flask, request
from opik import track

app = Flask(__name__)

@app.route("/endpoint", methods=["POST"])
@track  # Automatically picks up distributed trace headers
def process_request(opik_distributed_trace_headers=None):
    # This span will be child of Service A's trace
    data = request.json
    result = process(data)
    return {"result": result}
```

**Headers format:**
```python
{
    "opik_trace_id": "trace-uuid",
    "opik_parent_span_id": "span-uuid"
}
```

### Cost Tracking

**Automatic tracking** for supported models:
- OpenAI (GPT-3.5, GPT-4, GPT-4o, o1, etc.)
- Anthropic (Claude 3.x, Claude Sonnet 4.x)
- Google (Gemini)
- Cohere
- Many more via LiteLLM

**What's tracked:**
```python
usage = {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150,
    "cost": 0.0015  # USD
}
```

**View in dashboard:**
- Total costs by project/model
- Cost trends over time
- Per-trace cost breakdown
- Filter by date range

**Manual cost tracking:**
```python
span.update(
    usage={
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150
    }
)
# Cost calculated automatically based on model
```

## Project Organization

**Set via environment:**
```bash
export OPIK_PROJECT_NAME="my-project"
```

**Set via SDK:**
```python
import opik
opik.configure(project_name="my-project")
```

**Set per trace:**
```python
@opik.track(project_name="specific-project")
def my_function():
    pass
```

## Flushing Traces

**Automatic** (default): Traces batched and sent asynchronously

**Manual flush** (for short-lived scripts):
```python
import opik

# ... your code ...

# Ensure all traces are sent before exit
opik.flush()
```

**Immediate flush** (debugging):
```python
@opik.track(flush=True)  # Synchronous, slower
def my_function():
    pass
```

## Privacy & Filtering

**Exclude sensitive data:**
```python
@opik.track
def my_function(user_input: str, api_key: str) -> str:
    # Don't log api_key
    # Opik logs function args by default - be careful with PII
    
    # Option: Use guardrails to strip PII before logging
    from opik.guardrails import PIIGuardrail
    guardrail = PIIGuardrail()
    cleaned_input = guardrail.validate(input=user_input)
    
    return process(cleaned_input)
```

**Best practices:**
- Don't log credentials, API keys, tokens
- Use guardrails to detect/strip PII
- Review traces before production deployment
- Use self-hosted Opik for sensitive data

## Performance Considerations

**Batching** (automatic):
- Traces sent in batches
- Minimal performance impact
- Configure batch size if needed

**Network overhead:**
- ~1-5ms per tracked function (async)
- Negligible for LLM calls (which take seconds)
- Use sampling for very high-volume scenarios

**Sampling** (for high traffic):
```python
import random

@opik.track
def my_function(input):
    # Only track 10% of calls
    if random.random() > 0.1:
        return process(input)  # Not tracked
    
    return process(input)  # Tracked
```

## Troubleshooting

**Traces not appearing:**
1. Check configuration: `opik configure`
2. Verify network: `curl https://api.comet.com`
3. Force flush: `opik.flush()`
4. Check project name matches
5. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

**Nested traces not showing hierarchy:**
- Ensure parent function also has `@opik.track`
- Check function is called within parent's execution

**High memory usage:**
- Reduce batch size
- Flush more frequently
- Use sampling for high-volume scenarios
