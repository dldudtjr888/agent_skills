# Deep Agents 빠른 시작 가이드

## 설치

```bash
pip install deepagents tavily-python
```

## 환경변수

```bash
# 필수: 사용할 LLM의 API 키
export ANTHROPIC_API_KEY="your-key"
# 또는
export OPENAI_API_KEY="your-key"

# 선택: 웹 검색용
export TAVILY_API_KEY="your-key"
```

## 첫 에이전트 생성

### 기본 에이전트

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is LangGraph?"}]
})

print(result["messages"][-1].content)
```

### 커스텀 도구 추가

```python
from langchain_core.tools import tool
from deepagents import create_deep_agent

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[get_weather],
    system_prompt="You are a helpful assistant with weather information."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather in Seoul?"}]
})
```

### 웹 검색 에이전트

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search."""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[internet_search],
    system_prompt="Conduct research and write a polished report."
)
```

## 다양한 모델 사용

```python
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

# Claude Sonnet 4.5 (기본값)
claude_model = init_chat_model(
    model="anthropic:claude-sonnet-4-5-20250929",
    temperature=0.0
)

# Google Gemini 3 Pro
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-3-pro-preview",
    temperature=0.0
)

# OpenAI GPT-4
openai_model = init_chat_model(
    model="openai:gpt-4-turbo-preview",
    temperature=0.0
)

# 모델 선택하여 에이전트 생성
agent = create_deep_agent(model=gemini_model)
```

## LangGraph 개발 서버

```bash
# 개발 서버 시작
langgraph dev

# 기능:
# - Studio 웹 인터페이스: http://localhost:8123
# - GraphQL API
# - 실시간 스트리밍
# - 파일 상태 시각화
```

### 커스텀 UI 연결 (선택)

```bash
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui
yarn install
yarn dev
```

## 다음 단계

- [02-core-concepts.md](02-core-concepts.md): 핵심 4요소 이해
- [03-api-reference.md](03-api-reference.md): API 파라미터 상세
