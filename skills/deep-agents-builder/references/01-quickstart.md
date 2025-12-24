# Deep Agents 빠른 시작 가이드

> **최종 업데이트**: 2025-12-24 (deepagents 0.2+)

## 설치

### SDK 설치

```bash
pip install deepagents tavily-python
```

### CLI 설치 (선택)

```bash
pip install deepagents-cli
# 또는
uv pip install deepagents-cli
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

---

## 첫 에이전트 생성

### 기본 에이전트

```python
from deepagents import create_deep_agent

# 기본 모델: claude-sonnet-4-5-20250929
agent = create_deep_agent()

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
    tools=[internet_search],
    system_prompt="Conduct research and write a polished report."
)
```

---

## DeepAgents CLI

### 기본 사용

```bash
# 기본 에이전트 실행 (대화형)
deepagents

# 특정 이름의 에이전트 실행
deepagents agent my-researcher

# 에이전트 목록 확인
deepagents list

# 에이전트 메모리 초기화
deepagents reset my-researcher
```

### CLI 주요 기능

| 기능 | 설명 |
|-----|------|
| **파일 작업** | 프로젝트 파일 읽기, 쓰기, 편집 |
| **셸 명령** | 승인 후 셸 명령 실행 |
| **웹 검색** | Tavily로 웹 검색 |
| **HTTP 요청** | API 호출 |
| **영속 메모리** | `~/.deepagents/AGENT_NAME/memories/`에 지식 저장 |
| **Human-in-the-Loop** | 파일 쓰기 전 diff 표시 및 승인 요청 |

### Memory-First Protocol

CLI는 자동으로 이전 대화의 지식을 활용합니다:

```
~/.deepagents/
└── my-researcher/
    └── memories/
        ├── project-overview.md
        ├── api-patterns.md
        └── user-preferences.md
```

---

## 다양한 모델 사용

### 문자열 형식 (권장)

```python
from deepagents import create_deep_agent

# Claude Sonnet 4.5 (기본값)
agent = create_deep_agent(model="anthropic:claude-sonnet-4-5-20250929")

# OpenAI GPT-4o
agent = create_deep_agent(model="openai:gpt-4o")

# Google Gemini
agent = create_deep_agent(model="google:gemini-2.0-flash")
```

### LangChain 모델 객체

```python
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

# init_chat_model 사용
model = init_chat_model(
    "anthropic:claude-sonnet-4-5-20250929",
    temperature=0.0
)
agent = create_deep_agent(model=model)

# 직접 클래스 사용
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0
)
agent = create_deep_agent(model=gemini_model)
```

---

## 스트리밍

### 기본 스트리밍

```python
for event in agent.stream({
    "messages": [{"role": "user", "content": "Research AI agents"}]
}):
    print(event)
```

### 비동기 스트리밍

```python
async for event in agent.astream({
    "messages": [{"role": "user", "content": "Research AI agents"}]
}):
    print(event)
```

---

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

---

## 다음 단계

- [02-core-concepts.md](02-core-concepts.md): 핵심 4요소 이해
- [03-api-reference.md](03-api-reference.md): API 파라미터 상세
- [08-hitl-memory.md](08-hitl-memory.md): Human-in-the-Loop 및 장기 메모리
