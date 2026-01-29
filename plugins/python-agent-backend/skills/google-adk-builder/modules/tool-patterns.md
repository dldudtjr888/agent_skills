# Tool Patterns (도구 패턴)

> 메인 스킬: `../SKILL.md`

ADK 에이전트의 도구 통합 패턴. 함수 도구, Google 내장 도구, MCP 도구, Agent-as-Tool을 다룬다.

---

## FunctionTool (함수 도구)

가장 기본적인 도구. Python 함수에 docstring을 작성하면 ADK가 자동으로 FunctionTool로 래핑한다.

### 기본 패턴

```python
def get_weather(city: str) -> dict:
    """도시의 현재 날씨 정보를 조회합니다.

    Args:
        city: 날씨를 조회할 도시 이름 (예: "서울", "부산")

    Returns:
        날씨 정보가 담긴 딕셔너리
    """
    # 실제 API 호출 로직
    return {"city": city, "temp": "20C", "condition": "sunny"}

# 에이전트에 도구 등록
agent = Agent(
    name="weather_bot",
    model="gemini-2.0-flash",
    instruction="날씨 질문에 get_weather 도구를 사용하세요.",
    tools=[get_weather],  # 함수를 직접 전달 -> 자동 FunctionTool 래핑
)
```

### docstring 규칙

LLM은 docstring을 읽고 도구 사용 여부를 결정한다. 반드시 포함해야 할 요소:

1. **첫 줄**: 도구가 하는 일 (한 문장)
2. **Args**: 각 파라미터 설명 (예시 포함 권장)
3. **Returns**: 반환값 설명

```python
# BAD: docstring 누락 -> LLM이 도구 용도를 모름
def search(q: str) -> list:
    return api.search(q)

# GOOD: 상세한 docstring
def search_products(query: str, category: str = "all") -> list[dict]:
    """상품 카탈로그에서 키워드로 상품을 검색합니다.

    Args:
        query: 검색 키워드 (예: "무선 이어폰", "노트북 가방")
        category: 상품 카테고리 필터 (예: "전자기기", "패션", "all")

    Returns:
        검색된 상품 목록. 각 항목은 name, price, rating을 포함.
    """
    return catalog_api.search(query=query, category=category)
```

### 타입 힌트 규칙

ADK는 타입 힌트를 사용하여 LLM에 파라미터 스키마를 전달한다:

```python
# 지원되는 타입
def my_tool(
    text: str,              # 문자열
    count: int,             # 정수
    ratio: float,           # 실수
    enabled: bool,          # 불리언
    tags: list[str],        # 문자열 리스트
    config: dict,           # 딕셔너리
    mode: str = "default",  # 기본값이 있는 선택 파라미터
) -> dict:
    """..."""
    pass
```

---

## ToolContext (도구 컨텍스트)

도구 함수에서 session state에 접근하거나 에이전트 동작을 제어할 때 사용한다.

```python
from google.adk.tools import ToolContext

def save_preference(preference: str, tool_context: ToolContext) -> dict:
    """사용자 선호도를 저장합니다.

    Args:
        preference: 저장할 선호도 값
    """
    # state 읽기/쓰기
    tool_context.state["user_preference"] = preference

    # 사용자 스코프 state (세션 간 유지)
    tool_context.state["user:theme"] = "dark"

    return {"status": "saved", "preference": preference}
```

### ToolContext 주요 기능

| 속성/메서드 | 설명 |
|------------|------|
| `tool_context.state` | session.state 읽기/쓰기 |
| `tool_context.actions.skip_summarization` | LLM 요약 건너뛰기 |
| `tool_context.actions.escalate` | 상위 에이전트로 에스컬레이션 |
| `tool_context.actions.transfer_to_agent` | 다른 에이전트로 전환 |

---

## Google 내장 도구

ADK에서 기본 제공하는 Google 서비스 도구.

### google_search (웹 검색)

```python
from google.adk.tools import google_search

agent = Agent(
    name="search_assistant",
    model="gemini-2.0-flash",
    instruction="질문에 대해 웹 검색을 활용하여 최신 정보를 제공하세요.",
    tools=[google_search],
)
```

### code_execution (코드 실행)

```python
from google.adk.tools import code_execution

agent = Agent(
    name="code_runner",
    model="gemini-2.0-flash",
    instruction="사용자의 코드를 실행하고 결과를 보여주세요.",
    tools=[code_execution],
)
```

### 기타 내장 도구

| 도구 | 설명 | 사용 환경 |
|------|------|----------|
| `google_search` | Gemini 웹 검색 | AI Studio / Vertex AI |
| `code_execution` | Gemini 코드 실행 샌드박스 | AI Studio / Vertex AI |
| `vertex_ai_search` | 프라이빗 데이터스토어 검색 | Vertex AI 전용 |
| `rag_retrieval` | Vertex AI RAG Engine | Vertex AI 전용 |

---

## MCP 도구 (Model Context Protocol)

외부 MCP 서버와 연결하여 도구를 사용한다.

### stdio 연결 (로컬 MCP 서버)

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams

mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/workspace"],
    ),
    tool_filter=["read_file", "write_file"],  # 선택: 특정 도구만 사용
)

agent = Agent(
    name="file_manager",
    model="gemini-2.0-flash",
    instruction="파일 시스템을 관리하세요.",
    tools=[mcp_tools],
)
```

### SSE 연결 (원격 MCP 서버)

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams

mcp_tools = MCPToolset(
    connection_params=SseConnectionParams(
        url="https://my-mcp-server.example.com/sse",
    ),
)

agent = Agent(
    name="remote_agent",
    model="gemini-2.0-flash",
    instruction="원격 도구를 활용하여 작업하세요.",
    tools=[mcp_tools],
)
```

### tool_filter 사용

MCP 서버의 모든 도구가 아닌 특정 도구만 노출:

```python
# 방법 1: 도구 이름 리스트
mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(command="npx", args=["..."]),
    tool_filter=["create_issue", "list_issues", "get_issue"],
)

# 방법 2: 커스텀 필터 함수
def my_filter(tool):
    return tool.name.startswith("read_")

mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(command="npx", args=["..."]),
    tool_filter=my_filter,
)
```

---

## Agent-as-Tool (에이전트를 도구로 사용)

다른 에이전트를 `tools` 파라미터에 전달하여 도구처럼 호출한다.
`sub_agents`와 달리 제어권이 호출자에게 유지된다 (stateless 호출).

### 기본 패턴

```python
math_specialist = Agent(
    name="math_expert",
    model="gemini-2.0-flash",
    description="수학 문제를 단계별로 풀어주는 전문가",  # description 필수!
    instruction="수학 문제를 단계별로 풀어주세요.",
)

root_agent = Agent(
    name="tutor",
    model="gemini-2.0-flash",
    instruction="학생의 질문에 답하세요. 수학 문제는 수학 전문가에게 맡기세요.",
    tools=[math_specialist],  # sub_agents가 아닌 tools에 전달
)
```

### sub_agents vs tools (에이전트 전달)

| 방식 | `sub_agents` | `tools` (Agent-as-Tool) |
|------|-------------|----------------------|
| 제어권 | 전환됨 (handoff) | 유지됨 (call & return) |
| 대화 흐름 | 위임받은 에이전트가 직접 응답 | 결과를 받아 호출자가 응답 |
| 적합한 경우 | 역할 전환, 전문 영역 위임 | 단순 계산, 데이터 조회 |
| state 접근 | 공유 session.state | 공유 session.state |

---

## LongRunningFunctionTool (비동기 도구)

장시간 실행되는 도구. 중간 진행 상황을 보고할 수 있다.

```python
from google.adk.tools import LongRunningFunctionTool

def generate_report(topic: str) -> dict:
    """대규모 보고서를 생성합니다. 시간이 걸릴 수 있습니다.

    Args:
        topic: 보고서 주제
    """
    # 장시간 작업 수행
    return {"report": "...", "pages": 50}

long_tool = LongRunningFunctionTool(func=generate_report)

agent = Agent(
    name="reporter",
    model="gemini-2.0-flash",
    tools=[long_tool],
)
```

---

## 도구 선택 가이드

| 용도 | 도구 유형 | 예시 |
|------|----------|------|
| 외부 API 호출 | `FunctionTool` (함수) | REST API, DB 쿼리 |
| 웹 검색 | `google_search` | 최신 뉴스, 사실 확인 |
| 코드 실행 | `code_execution` | 계산, 데이터 분석 |
| 프라이빗 데이터 검색 | `vertex_ai_search` | 사내 문서 검색 |
| 외부 MCP 서버 | `MCPToolset` | 파일 시스템, GitHub, Slack |
| 전문 에이전트 호출 | Agent-as-Tool | 수학, 번역 전문가 |
| 장시간 작업 | `LongRunningFunctionTool` | 보고서 생성, 배치 처리 |
