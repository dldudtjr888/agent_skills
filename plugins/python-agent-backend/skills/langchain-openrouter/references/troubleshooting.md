# Troubleshooting

Common errors and solutions for LangChain + OpenRouter.

## Official Documentation

- https://openrouter.ai/docs/faq
- https://status.openrouter.ai

## Rate Limiting (429)

**Error:**
```
RateLimitError: Error code: 429 - Rate limit exceeded
```

**Causes:**
- Too many requests per minute
- Free tier limits (low daily limits)
- Provider-specific rate limits

**Solutions:**

```python
# 1. Add retry with backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=60),
)
def invoke_with_retry(llm, prompt):
    return llm.invoke(prompt)

# 2. Use max_retries parameter
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    max_retries=3,
)

# 3. Use :floor variant for less contention
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:floor",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

## Authentication Errors (401)

**Error:**
```
AuthenticationError: Error code: 401 - Invalid API key
```

**Solutions:**

```python
# Check your API key
import os
print(os.environ.get("OPENROUTER_API_KEY", "NOT SET"))

# Ensure correct format
# OpenRouter keys start with "sk-or-v1-"
api_key = os.environ["OPENROUTER_API_KEY"]
assert api_key.startswith("sk-or-"), f"Invalid key format: {api_key[:10]}..."
```

## Model Not Found (404)

**Error:**
```
NotFoundError: Error code: 404 - Model not found
```

**Solutions:**

```python
# 1. Check model ID format (provider/model-name)
model = "anthropic/claude-sonnet-4-20250514"  # Correct format

# 2. Browse available models
# https://openrouter.ai/models

# 3. Check if model requires specific access
# Some models are gated or require approval
```

## Context Length Exceeded

**Error:**
```
BadRequestError: context_length_exceeded
```

**Solutions:**

```python
# 1. Use a model with longer context
llm = ChatOpenAI(
    model="google/gemini-2.5-pro-preview",  # 1M context
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# 2. Truncate messages
def truncate_messages(messages, max_chars=50000):
    total = 0
    result = []
    for msg in reversed(messages):
        msg_len = len(str(msg.content))
        if total + msg_len > max_chars:
            break
        result.insert(0, msg)
        total += msg_len
    return result

# 3. Use :extended variant if available
model = "some-model:extended"
```

## Tool Calling Failures

**Error:**
```
OutputParserException: Could not parse tool call
```

**Solutions:**

```python
# 1. Use :exacto variant for better tool calling
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:exacto",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# 2. Simplify tool schemas
from langchain_core.tools import tool

# Bad: Complex nested types
@tool
def bad_tool(config: dict) -> str:
    """Do something."""
    pass

# Good: Simple flat types
@tool
def good_tool(name: str, count: int) -> str:
    """Do something with name and count."""
    pass

# 3. Add better docstrings
@tool
def well_documented_tool(query: str) -> str:
    """Search for information about a topic.

    Use this tool when the user asks about facts, data,
    or needs to look something up.

    Args:
        query: The search query, e.g., "weather in Tokyo"

    Returns:
        Search results as a string.
    """
    pass
```

## Timeout Errors

**Error:**
```
TimeoutError: Request timed out
```

**Solutions:**

```python
# Increase timeout
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=120,  # 2 minutes
)

# Use streaming for long responses
for chunk in llm.stream("Write a long essay"):
    print(chunk.content, end="", flush=True)
```

## Provider Unavailable

**Error:**
```
ServiceUnavailableError: Provider temporarily unavailable
```

**Solutions:**

```python
# Enable fallbacks (provider slugs are lowercase)
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    extra_body={
        "provider": {
            "order": ["anthropic", "amazon-bedrock", "google"],
            "allow_fallbacks": True,
        }
    },
)

# Check status
# https://status.openrouter.ai
```

## Debugging Tips

```python
# 1. Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# 2. Check response metadata
response = llm.invoke("Hello")
print(response.response_metadata)

# 3. Get generation details from OpenRouter
# Use the generation ID to query stats
gen_id = response.response_metadata.get("id")
# GET https://openrouter.ai/api/v1/generation?id={gen_id}
```

## Common Import Errors

```python
# ❌ WRONG: Old import path
from langchain.chat_models import ChatOpenAI  # Deprecated!

# ✅ CORRECT: Current import
from langchain_openai import ChatOpenAI

# ❌ WRONG: Non-existent class
from langchain_openai import ChatOpenRouter  # Doesn't exist!

# ✅ CORRECT: Use ChatOpenAI with base_url
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1", ...)
```
