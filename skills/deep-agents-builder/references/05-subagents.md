# Deep Agents 서브에이전트 설계

서브에이전트는 **컨텍스트 격리**와 **전문화**를 통해 복잡한 작업을 효율적으로 처리합니다.

---

## SubAgent 정의

### 기본 구조

```python
subagent = {
    "name": "research-specialist",           # 필수: 고유 이름
    "description": "Deep research tasks",    # 필수: 사용 시점 설명
    "system_prompt": "You are a researcher", # 필수: 시스템 프롬프트 (또는 prompt)
    "tools": [internet_search],              # 필수: 사용할 도구들
    "model": "openai:gpt-4o",                # 선택: 모델 오버라이드
    "middleware": [],                        # 선택: 추가 미들웨어
}
```

### 필수 필드

| 필드 | 타입 | 설명 |
|-----|------|------|
| `name` | `str` | 서브에이전트 고유 식별자 |
| `description` | `str` | 메인 에이전트가 위임 시점 판단에 사용 |
| `system_prompt` | `str` | 서브에이전트 행동 지침 |
| `tools` | `list` | 서브에이전트가 사용할 도구들 |

### 선택 필드

| 필드 | 타입 | 설명 |
|-----|------|------|
| `model` | `str \| BaseChatModel` | 기본 모델 오버라이드 |
| `middleware` | `list[AgentMiddleware]` | 추가 미들웨어 |
| `interrupt_on` | `dict` | 인터럽트 설정 |

---

## 전문화된 서브에이전트 예시

### 웹 검색 전문가

```python
import os
from typing import Literal
from tavily import TavilyClient

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

research_subagent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions",
    "system_prompt": "You are a great researcher. Conduct thorough research.",
    "tools": [internet_search],
    "model": "openai:gpt-4o",
}
```

### 날씨 전문가

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 72°F and sunny"

weather_subagent = {
    "name": "weather-specialist",
    "description": "Use this agent to get weather information for any location",
    "system_prompt": "You are a weather specialist. Use the get_weather tool.",
    "tools": [get_weather],
    "model": "openai:gpt-4o",
}
```

---

## 다중 서브에이전트 구성

```python
from deepagents import create_deep_agent

subagents = [
    {
        "name": "weather-specialist",
        "description": "Use for weather information",
        "system_prompt": "You are a weather specialist.",
        "tools": [get_weather],
    },
    {
        "name": "research-specialist",
        "description": "Use for deep research requiring multiple searches",
        "system_prompt": "You are a research specialist. Conduct thorough research.",
        "tools": [internet_search],
    }
]

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[get_weather, internet_search],  # 메인 에이전트도 직접 사용 가능
    subagents=subagents,
    system_prompt="You are a helpful assistant. Delegate to specialists when appropriate."
)

# 복합 작업 처리
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Research climate change impact on Tokyo and get current weather there"
    }]
})

# 서브에이전트는 컨텍스트 격리 - 메인 에이전트는 최종 결과만 확인
print(result["messages"][-1].content)
```

---

## CompiledSubAgent (사전 빌드)

커스텀 LangGraph 워크플로우를 서브에이전트로 사용합니다.

### LangGraph 그래프 래핑

```python
from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from langgraph.graph import StateGraph

# 커스텀 LangGraph 그래프 생성
def create_weather_graph():
    workflow = StateGraph(...)
    # 복잡한 멀티스텝 로직 구현
    return workflow.compile()

weather_graph = create_weather_graph()

# CompiledSubAgent로 래핑
weather_subagent = CompiledSubAgent(
    name="weather",
    description="This subagent can get weather in cities.",
    runnable=weather_graph
)

# 메인 에이전트에 통합
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    subagents=[weather_subagent],
)
```

### 기존 에이전트 재사용

```python
from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def database_query(sql: str) -> str:
    """Execute SQL query."""
    return f"Query result: {sql}"

# 기존 LangChain 에이전트 생성
custom_db_agent = create_agent(
    model="openai:gpt-4o",
    tools=[database_query],
    system_prompt="You are a database specialist. Write and execute SQL queries.",
)

# CompiledSubAgent로 래핑하여 재사용
db_subagent = CompiledSubAgent(
    name="database-specialist",
    description="Use for database queries and SQL operations",
    runnable=custom_db_agent
)

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    subagents=[db_subagent],
)
```

---

## 서브에이전트 설계 가이드라인

### 연구 계획

```
- 단순 사실 확인: 1개 서브에이전트
- 비교/다면적 주제: 병렬 서브에이전트
- 각 서브에이전트는 한 가지 측면만 연구
- 배치 처리로 오버헤드 최소화
```

### Description 작성 팁

```python
# 좋은 예: 명확한 사용 시점
"description": "Use this agent when you need to search the web for current information"

# 나쁜 예: 모호한 설명
"description": "A helpful research agent"
```

### 컨텍스트 격리 활용

```python
# 서브에이전트의 전체 대화 내역은 격리됨
# 메인 에이전트는 최종 결과만 수신
# → 메인 에이전트 컨텍스트 윈도우 보호
```

---

## 서브에이전트 출력 검증 (0.3.6+)

### 개요

0.3.6부터 서브에이전트의 출력이 자동으로 검증됩니다.

### 검증 항목

| 항목 | 설명 |
|-----|------|
| `messages` 키 | 출력에 `messages` 키 필수 |
| 형식 검증 | 메시지 형식 일관성 확인 |
| 예외 메시지 | 검증 실패 시 명확한 오류 메시지 |

### 동작

```python
# 서브에이전트 출력 검증은 자동으로 활성화
# 메인 에이전트는 유효한 출력만 수신
# 잘못된 출력은 명확한 예외로 처리됨
```

### 에러 예시

```python
# 0.3.6 이전: 불명확한 에러
# 0.3.6 이후: "Subagent 'research-agent' output missing 'messages' key"
```

---

## 에이전트 네이밍 개선 (0.3.6+)

서브에이전트 생성 시 이름 지정이 개선되었습니다:
- 트레이스에서 명확한 에이전트 식별
- 중첩 서브에이전트 추적 용이

---

## 다음 단계

- [06-backends.md](06-backends.md): 백엔드 옵션
