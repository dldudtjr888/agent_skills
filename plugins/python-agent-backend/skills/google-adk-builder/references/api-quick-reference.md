# API Quick Reference (빠른 참조)

> 메인 스킬: `../SKILL.md`

Google ADK 핵심 클래스, 메서드, CLI 명령어의 빠른 참조.

---

## Core Agent Classes

### LlmAgent / Agent

```python
from google.adk.agents import Agent  # Agent == LlmAgent

Agent(
    name: str,                          # 필수. 고유 식별자
    model: str | BaseLlm = None,        # LLM 모델 (예: "gemini-2.0-flash")
    instruction: str = "",              # 시스템 프롬프트. {state_key} 템플릿 지원
    description: str = "",              # sub_agent/tool 사용 시 필수
    tools: list = [],                   # [함수, BaseTool, Agent]
    sub_agents: list = [],              # [Agent] LLM 기반 위임
    output_key: str = None,             # 응답 -> session.state[output_key]
    input_schema: BaseModel = None,     # Pydantic 입력 스키마
    output_schema: BaseModel = None,    # Pydantic 출력 스키마
    generate_content_config: dict = None,  # temperature, safety 등
    before_agent_callback = None,       # (ctx) -> Content | None
    after_agent_callback = None,        # (ctx) -> Content | None
    before_model_callback = None,       # (ctx, req) -> LlmResponse | None
    after_model_callback = None,        # (ctx, resp) -> LlmResponse | None
    before_tool_callback = None,        # (ctx, name, args) -> dict | None
    after_tool_callback = None,         # (ctx, name, result) -> dict | None
)
```

### SequentialAgent

```python
from google.adk.agents import SequentialAgent

SequentialAgent(
    name: str,              # 필수
    sub_agents: list,       # 필수. 순차 실행할 에이전트 리스트
    description: str = "",
)
```

### ParallelAgent

```python
from google.adk.agents import ParallelAgent

ParallelAgent(
    name: str,              # 필수
    sub_agents: list,       # 필수. 병렬 실행할 에이전트 리스트
    description: str = "",
)
```

### LoopAgent

```python
from google.adk.agents import LoopAgent

LoopAgent(
    name: str,              # 필수
    sub_agents: list,       # 필수. 반복 실행할 에이전트 리스트
    max_iterations: int = None,  # 최대 반복 횟수 (권장: 반드시 설정)
    description: str = "",
)
```

### BaseAgent (Custom Agent)

```python
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext

class MyAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        # 커스텀 로직
        yield event  # Event 객체 yield
```

---

## Tool Classes

### FunctionTool

```python
from google.adk.tools import FunctionTool

# 자동 래핑 (권장)
agent = Agent(tools=[my_function])

# 수동 생성
tool = FunctionTool(func=my_function)
```

### MCPToolset

```python
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioConnectionParams,
    SseConnectionParams,
)

# stdio 연결
mcp = MCPToolset(
    connection_params=StdioConnectionParams(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-xxx"],
    ),
    tool_filter=["tool_a", "tool_b"],  # 선택
)

# SSE 연결
mcp = MCPToolset(
    connection_params=SseConnectionParams(url="https://..."),
)
```

### Google 내장 도구

```python
from google.adk.tools import google_search
from google.adk.tools import code_execution
```

### LongRunningFunctionTool

```python
from google.adk.tools import LongRunningFunctionTool

tool = LongRunningFunctionTool(func=my_long_function)
```

### ToolContext

```python
from google.adk.tools import ToolContext

def my_tool(param: str, tool_context: ToolContext) -> dict:
    tool_context.state["key"] = "value"       # state 쓰기
    val = tool_context.state.get("key")       # state 읽기
    tool_context.actions.escalate = True       # 에스컬레이션
    tool_context.actions.transfer_to_agent = "agent_name"  # 전환
    tool_context.actions.skip_summarization = True  # 요약 건너뛰기
    return {"result": "..."}
```

---

## Runner & Session Classes

### Runners

```python
from google.adk.runners import InMemoryRunner, Runner

# 개발용
runner = InMemoryRunner(agent=root_agent, app_name="my_app")

# 프로덕션용
runner = Runner(
    agent=root_agent,
    app_name="my_app",
    session_service=my_session_service,
)
```

### SessionService

```python
from google.adk.sessions import InMemorySessionService, DatabaseSessionService

# 메모리
service = InMemorySessionService()

# 데이터베이스
service = DatabaseSessionService(db_url="postgresql://...")
```

### Session CRUD

```python
# 생성
session = await service.create_session(
    app_name="my_app", user_id="user_id", state={})

# 조회
session = await service.get_session(
    app_name="my_app", user_id="user_id", session_id="sid")

# 목록
sessions = await service.list_sessions(
    app_name="my_app", user_id="user_id")

# 삭제
await service.delete_session(
    app_name="my_app", user_id="user_id", session_id="sid")
```

### 실행

```python
from google.genai.types import Content, Part

async for event in runner.run_async(
    user_id="user_id",
    session_id="session_id",
    new_message=Content(parts=[Part(text="메시지")]),
):
    if event.content and event.content.parts:
        print(event.content.parts[0].text)
```

---

## Callback Signatures

```python
# Agent 콜백
def before_agent(callback_context) -> Content | None: ...
def after_agent(callback_context) -> Content | None: ...

# Model 콜백
def before_model(callback_context, llm_request) -> LlmResponse | None: ...
def after_model(callback_context, llm_response) -> LlmResponse | None: ...

# Tool 콜백
def before_tool(callback_context, tool_name: str, args: dict) -> dict | None: ...
def after_tool(callback_context, tool_name: str, result: dict) -> dict | None: ...
```

### 콜백 반환값 규칙
- `None` 반환: 정상 진행 (기본 동작)
- 값 반환: 기본 동작을 대체 (short-circuit)

---

## State 스코프

```python
# 세션 스코프 (기본)
state["key"] = "value"

# 앱 스코프 (모든 사용자 공유)
state["app:key"] = "value"

# 사용자 스코프 (세션 간 유지)
state["user:key"] = "value"
```

---

## CLI Commands

```bash
# 웹 UI 실행
adk web <agent_dir> [--port PORT] [--host HOST]

# CLI 대화형 실행
adk run <agent_dir>

# 에이전트 평가
adk eval <agent_dir> <eval_file> [--model MODEL]
```

---

## Import Map

```python
# 에이전트
from google.adk.agents import Agent, LlmAgent
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext

# 도구
from google.adk.tools import FunctionTool, LongRunningFunctionTool
from google.adk.tools import ToolContext
from google.adk.tools import google_search, code_execution
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset, StdioConnectionParams, SseConnectionParams
)

# 실행
from google.adk.runners import InMemoryRunner, Runner

# 세션
from google.adk.sessions import InMemorySessionService, DatabaseSessionService

# 타입
from google.genai.types import Content, Part
from google.genai import types  # LlmResponse 등
```
