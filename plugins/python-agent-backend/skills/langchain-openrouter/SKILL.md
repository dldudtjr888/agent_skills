---
name: langchain-openrouter
description: "LangChain + OpenRouter 통합 가이드 (langchain-openai v1.1.6+). 트리거: 'OpenRouter', 'openrouter.ai', 'ChatOpenAI with base_url', 'OPENROUTER_API_KEY', 'sk-or-v1', 'openrouter provider routing', 'model variants nitro/floor/free'. 한국어 트리거: 'OpenRouter로 LangChain 사용', 'OpenRouter 모델 라우팅', '오픈라우터 API 연동'. 주의: ChatOpenRouter 클래스는 존재하지 않음 - ChatOpenAI + base_url 패턴만 유효. baseline Claude가 잘못된 ChatOpenRouter import를 생성하는 경우가 많으므로 반드시 이 스킬 참조. API/모델명이 자주 변경됨."
---

# LangChain + OpenRouter

Use 400+ models from OpenRouter through LangChain's ChatOpenAI.

## Official Documentation (Always Check for Latest)

- **OpenRouter Docs**: https://openrouter.ai/docs
- **OpenRouter API Reference**: https://openrouter.ai/docs/api/reference/overview
- **OpenRouter Models**: https://openrouter.ai/models
- **LangChain ChatOpenAI**: https://docs.langchain.com/oss/python/integrations/chat/openai
- **langchain-openai PyPI**: https://pypi.org/project/langchain-openai/

## Quick Start

```bash
pip install langchain-openai
export OPENROUTER_API_KEY="sk-or-v1-..."
```

```python
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://your-app.com",  # Optional: for rankings
        "X-Title": "Your App Name",               # Optional: for rankings
    },
)

response = llm.invoke("Hello!")
print(response.content)
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: ChatOpenRouter does not exist
from langchain_openai import ChatOpenRouter  # This class doesn't exist!

# ❌ WRONG: create_agent does not exist in langchain
from langchain.agents import create_agent  # This function doesn't exist!

# ❌ WRONG: langchain.agents.middleware does not exist
from langchain.agents.middleware import AgentMiddleware  # This module doesn't exist!

# ❌ WRONG: Using model_kwargs for extra_body (generates warning)
llm = ChatOpenAI(
    model="...",
    model_kwargs={"extra_body": {"provider": {...}}},  # Warning!
)

# ✅ CORRECT: Use ChatOpenAI with base_url
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# ✅ CORRECT: Use extra_body as direct parameter for OpenRouter options
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    extra_body={"provider": {"sort": "price"}},  # Direct parameter!
)
```

## Reference Guides

- [Chat Completion](references/chat-completion.md) - invoke, stream, batch, async
- [Prompts and Messages](references/prompts-and-messages.md) - message types, templates
- [Chains and LCEL](references/chains-and-lcel.md) - pipe operator, RunnableSequence
- [Tools and Functions](references/tools-and-functions.md) - bind_tools, tool decorator
- [Structured Output](references/structured-output.md) - with_structured_output, Pydantic
- [OpenRouter Features](references/openrouter-features.md) - variants, provider routing
- [Troubleshooting](references/troubleshooting.md) - common errors and solutions

## Version Info

- **langchain-openai**: v1.1.6 (2025-12-18)
- **Python**: ≥3.10
- **Last updated**: December 2025
