# OpenRouter Features

OpenRouter-specific features: variants, provider routing, and more.

## Official Documentation

- https://openrouter.ai/docs/guides/routing/provider-selection
- https://openrouter.ai/docs/api/reference/overview
- https://openrouter.ai/docs/guides/routing/model-variants/exacto

## Model Variants

### Dynamic Variants (Work on All Models)

| Variant | Purpose | Use Case |
|---------|---------|----------|
| `:nitro` | Sort by throughput | Fast responses, real-time apps |
| `:floor` | Sort by price | Cost optimization |
| `:online` | Web search enabled | Current information queries |

```python
from langchain_openai import ChatOpenAI

# Fastest provider
llm_fast = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:nitro",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Cheapest provider
llm_cheap = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:floor",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# With web search
llm_search = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:online",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

### Static Variants (Model-Specific)

| Variant | Purpose | Notes |
|---------|---------|-------|
| `:free` | Free tier | Low rate limits, not for production |
| `:extended` | Longer context | Available on select models |
| `:exacto` | Better tool calling | Curated high-quality endpoints |
| `:thinking` | Reasoning mode | Extended reasoning (not for Anthropic) |

```python
# Free tier (rate limited)
llm_free = ChatOpenAI(
    model="meta-llama/llama-3.3-70b-instruct:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Better tool calling
llm_tools = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:exacto",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

## Provider Routing

Control which providers handle your requests using the `extra_body` parameter:

```python
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    extra_body={
        "provider": {
            # Provider options here
        }
    },
)
```

### Provider Order

```python
# Provider slugs are lowercase! Copy exact names from model pages on openrouter.ai
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    extra_body={
        "provider": {
            "order": ["anthropic", "amazon-bedrock", "google"],
            "allow_fallbacks": True,  # Allow other providers if these fail
        }
    },
)
```

### Sort by Attribute

```python
extra_body={
    "provider": {
        "sort": "price",      # or "throughput" or "latency"
    }
}
```

### Zero Data Retention

```python
extra_body={
    "provider": {
        "data_collection": "deny",  # or "allow" (default)
    }
}

# Or stricter ZDR
extra_body={
    "provider": {
        "zdr": True,  # Only ZDR-compliant endpoints
    }
}
```

### Require All Parameters

Ensure provider supports all your request parameters:

```python
extra_body={
    "provider": {
        "require_parameters": True,
    }
}
```

### Ignore/Only Specific Providers

```python
# Exclude providers (use lowercase slugs)
extra_body={
    "provider": {
        "ignore": ["azure", "amazon-bedrock"],
    }
}

# Only use specific providers
extra_body={
    "provider": {
        "only": ["anthropic", "openai"],
    }
}
```

### Price Limits

```python
extra_body={
    "provider": {
        "max_price": {
            "prompt": 1.0,      # Max $/million input tokens
            "completion": 2.0,  # Max $/million output tokens
        }
    }
}
```

### Quantization Filtering

```python
extra_body={
    "provider": {
        "quantizations": ["fp8", "int8"],  # Only use specific quantizations
    }
}
```

### Text Distillation

```python
extra_body={
    "provider": {
        "enforce_distillable_text": True,  # Only route to models allowing text distillation
    }
}
```

## All Provider Options Reference

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `order` | string[] | — | Prioritize specific providers in sequence |
| `allow_fallbacks` | boolean | true | Enable backup providers if primary fails |
| `sort` | string | — | Order by "price", "throughput", or "latency" |
| `require_parameters` | boolean | false | Only route to providers supporting all request parameters |
| `data_collection` | "allow" \| "deny" | "allow" | Filter by data retention policies |
| `zdr` | boolean | — | Restrict to Zero Data Retention endpoints |
| `enforce_distillable_text` | boolean | — | Route only to models allowing text distillation |
| `only` | string[] | — | Whitelist specific providers |
| `ignore` | string[] | — | Blacklist specific providers |
| `quantizations` | string[] | — | Filter by quantization level (int4, int8, fp8, etc.) |
| `max_price` | object | — | Set pricing limits per token type |

### Finding Provider Slugs

Provider slugs are **lowercase** (e.g., `anthropic`, `openai`, `azure`).
To find exact slugs: go to https://openrouter.ai/models, click a model, and use the
copy button next to provider names on the model page.

## Headers for Attribution

```python
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://your-app.com",  # Your site URL
        "X-Title": "Your App Name",               # Your app name
    },
)
```

## Popular Models

| Model ID | Provider | Use Case |
|----------|----------|----------|
| `anthropic/claude-sonnet-4-20250514` | Anthropic | General, balanced |
| `anthropic/claude-opus-4-20250514` | Anthropic | Complex reasoning |
| `openai/gpt-4o` | OpenAI | Multimodal, coding |
| `openai/gpt-4o-mini` | OpenAI | Cost-efficient |
| `google/gemini-2.5-pro-preview` | Google | Long context (1M) |
| `deepseek/deepseek-chat` | DeepSeek | Coding, math |
| `meta-llama/llama-3.3-70b-instruct` | Meta | Open source |

Browse all models: https://openrouter.ai/models

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: Using variant in provider.order
model_kwargs={
    "extra_body": {
        "provider": {
            "order": ["Anthropic:nitro"],  # Wrong! Variants go in model name
        }
    }
}

# ✅ CORRECT: Variant in model name
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:nitro",  # Correct!
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# ❌ WRONG: Using :thinking for Anthropic
model="anthropic/claude-sonnet-4-20250514:thinking"  # Not supported!

# ✅ CORRECT: Use reasoning parameter for Anthropic
# Check Anthropic docs for current reasoning API
```
