# Chat Completion

Basic chat completion with LangChain + OpenRouter.

## Official Documentation

- https://docs.langchain.com/oss/python/integrations/chat/openai
- https://openrouter.ai/docs/api/reference/overview

## Setup

```python
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

## Basic Invocation

```python
# Simple string input
response = llm.invoke("What is 2+2?")
print(response.content)

# Message list input
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is 2+2?"),
]
response = llm.invoke(messages)
print(response.content)

# Tuple format (shorthand)
messages = [
    ("system", "You are a helpful assistant."),
    ("human", "What is 2+2?"),
]
response = llm.invoke(messages)
print(response.content)
```

## Streaming

```python
# Sync streaming
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)

# Async streaming
async for chunk in llm.astream("Tell me a story"):
    print(chunk.content, end="", flush=True)

# Stream with token usage
# NOTE: stream_usage may not work with custom base_url (like OpenRouter)
# OpenRouter provides usage in the final response metadata instead
llm_with_usage = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    stream_usage=True,  # May be ignored for non-OpenAI endpoints
)

# For OpenRouter, check response_metadata after streaming completes
for chunk in llm_with_usage.stream("Hello"):
    print(chunk.content, end="", flush=True)
    # usage_metadata may not be available during streaming with OpenRouter
```

## Async Operations

```python
import asyncio

async def main():
    # Single async call
    response = await llm.ainvoke("Hello!")
    print(response.content)

    # Concurrent calls
    tasks = [
        llm.ainvoke("What is 1+1?"),
        llm.ainvoke("What is 2+2?"),
        llm.ainvoke("What is 3+3?"),
    ]
    responses = await asyncio.gather(*tasks)
    for r in responses:
        print(r.content)

asyncio.run(main())
```

## Batch Processing

```python
# Sync batch
prompts = ["Hello", "How are you?", "Goodbye"]
responses = llm.batch(prompts)

for r in responses:
    print(r.content)

# Async batch
responses = await llm.abatch(prompts)
```

## Parameters

```python
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],

    # Generation parameters
    temperature=0.7,        # 0-2, default varies by model
    max_tokens=1000,        # Max output tokens
    top_p=0.9,              # Nucleus sampling

    # Connection parameters
    timeout=60,             # Request timeout in seconds
    max_retries=2,          # Retry attempts

    # Optional headers for OpenRouter
    default_headers={
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "Your App Name",
    },
)
```

## Response Object

```python
response = llm.invoke("Hello")

# Content
print(response.content)           # The text response

# Metadata
print(response.response_metadata) # Dict with model, finish_reason, etc.
print(response.id)                # Generation ID
print(response.usage_metadata)    # Token usage (if available)

# Message type
print(type(response))             # AIMessage
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: Don't use deprecated LLM class
from langchain_openai import OpenAI  # Use ChatOpenAI instead

# ❌ WRONG: Don't forget base_url for OpenRouter
llm = ChatOpenAI(model="anthropic/claude-sonnet-4-20250514")  # Won't work!

# ✅ CORRECT
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```
