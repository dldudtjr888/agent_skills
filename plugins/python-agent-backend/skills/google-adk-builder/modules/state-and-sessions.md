# State & Sessions (상태 관리 & 세션)

> 메인 스킬: `../SKILL.md`

세션 상태, Runner, SessionService, 콜백/가드레일 패턴을 다룬다.

---

## Session State 스코프

state는 key-value 저장소로, key 접두어에 따라 3가지 스코프를 지원한다.

### 세션 스코프 (기본)

현재 세션에서만 유효. 접두어 없음.

```python
# 도구에서 state 쓰기/읽기
def save_note(note: str, tool_context: ToolContext) -> dict:
    """메모를 저장합니다."""
    tool_context.state["last_note"] = note
    return {"saved": True}

# instruction에서 참조
agent = Agent(
    instruction="이전 메모: {last_note}",
    ...
)
```

### 앱 스코프 (`app:` 접두어)

모든 사용자의 모든 세션에서 공유.

```python
def track_usage(tool_context: ToolContext) -> dict:
    """사용량을 추적합니다."""
    count = tool_context.state.get("app:total_queries", 0)
    tool_context.state["app:total_queries"] = count + 1
    return {"total": count + 1}
```

### 사용자 스코프 (`user:` 접두어)

같은 사용자의 모든 세션에서 공유.

```python
def set_preference(theme: str, tool_context: ToolContext) -> dict:
    """사용자 테마를 설정합니다."""
    tool_context.state["user:theme"] = theme
    return {"theme": theme}

# 다른 세션에서도 참조 가능
agent = Agent(
    instruction="사용자 테마: {user:theme}",
    ...
)
```

### 스코프 비교

| 스코프 | 접두어 | 범위 | 예시 |
|--------|--------|------|------|
| 세션 | (없음) | 현재 세션 | `state["query"]` |
| 앱 | `app:` | 모든 사용자 | `state["app:config"]` |
| 사용자 | `user:` | 동일 사용자 전체 | `state["user:name"]` |

---

## Runners

Runner는 에이전트 실행을 관리하는 엔진이다. 사용자 입력을 받아 에이전트에 전달하고, 세션 상태를 관리한다.

### InMemoryRunner (개발용)

메모리 기반. 프로세스 종료 시 데이터 소멸.

```python
from google.adk.runners import InMemoryRunner
from google.adk.agents import Agent

root_agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="도움이 되는 어시스턴트입니다.",
)

runner = InMemoryRunner(agent=root_agent, app_name="my_app")
```

### Runner (프로덕션용)

외부 SessionService와 연결하여 영구 저장.

```python
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(
    db_url="postgresql://user:pass@localhost:5432/mydb"
)

runner = Runner(
    agent=root_agent,
    app_name="my_app",
    session_service=session_service,
)
```

### 실행 패턴

```python
import asyncio
from google.genai.types import Content, Part

async def chat(runner, user_id: str, session_id: str, message: str):
    """에이전트에 메시지를 보내고 응답을 받는다."""
    new_message = Content(parts=[Part(text=message)])
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="my_app")

    # 세션 생성
    session = await runner.session_service.create_session(
        app_name="my_app",
        user_id="user_123",
    )

    # 대화
    await chat(runner, "user_123", session.id, "안녕하세요!")
    await chat(runner, "user_123", session.id, "이전 대화 기억하나요?")

asyncio.run(main())
```

---

## SessionService

세션 데이터의 저장과 조회를 담당한다.

### InMemorySessionService

```python
from google.adk.sessions import InMemorySessionService

service = InMemorySessionService()
```

### DatabaseSessionService

```python
from google.adk.sessions import DatabaseSessionService

# SQLite
service = DatabaseSessionService(db_url="sqlite:///./sessions.db")

# PostgreSQL
service = DatabaseSessionService(
    db_url="postgresql://user:pass@localhost:5432/mydb"
)

# MySQL
service = DatabaseSessionService(
    db_url="mysql+pymysql://user:pass@localhost:3306/mydb"
)
```

### 세션 CRUD

```python
# 생성
session = await service.create_session(
    app_name="my_app",
    user_id="user_123",
    state={"initial_key": "initial_value"},  # 초기 state 설정 (선택)
)

# 조회
session = await service.get_session(
    app_name="my_app",
    user_id="user_123",
    session_id=session.id,
)

# 사용자의 모든 세션 조회
sessions = await service.list_sessions(
    app_name="my_app",
    user_id="user_123",
)

# 삭제
await service.delete_session(
    app_name="my_app",
    user_id="user_123",
    session_id=session.id,
)
```

---

## Callbacks (콜백)

에이전트, 모델, 도구의 실행 전후에 커스텀 로직을 삽입한다.

### 6가지 콜백 유형

| 콜백 | 실행 시점 | 반환값 | 용도 |
|------|----------|--------|------|
| `before_agent_callback` | 에이전트 실행 전 | `Content` or `None` | 에이전트 레벨 가드레일 |
| `after_agent_callback` | 에이전트 실행 후 | `Content` or `None` | 결과 후처리 |
| `before_model_callback` | LLM 호출 전 | `LlmResponse` or `None` | 입력 필터링, 캐싱 |
| `after_model_callback` | LLM 호출 후 | `LlmResponse` or `None` | 출력 필터링, 로깅 |
| `before_tool_callback` | 도구 실행 전 | `dict` or `None` | 입력 검증 |
| `after_tool_callback` | 도구 실행 후 | `dict` or `None` | 결과 변환 |

### 입력 가드레일 (before_model_callback)

```python
from google.genai import types

def content_safety_check(callback_context, llm_request) -> types.LlmResponse | None:
    """금지된 주제를 필터링합니다."""
    user_msg = str(llm_request.contents[-1])
    blocked_topics = ["개인정보", "비밀번호", "신용카드"]

    for topic in blocked_topics:
        if topic in user_msg:
            return types.LlmResponse(
                content=types.Content(
                    parts=[types.Part(text=f"죄송합니다. {topic} 관련 요청은 처리할 수 없습니다.")],
                    role="model",
                )
            )
    return None  # 정상 진행

agent = Agent(
    name="safe_agent",
    model="gemini-2.0-flash",
    instruction="도움이 되는 어시스턴트입니다.",
    before_model_callback=content_safety_check,
)
```

### 출력 로깅 (after_model_callback)

```python
import logging

logger = logging.getLogger(__name__)

def log_response(callback_context, llm_response) -> types.LlmResponse | None:
    """모델 응답을 로깅합니다."""
    if llm_response.content and llm_response.content.parts:
        text = llm_response.content.parts[0].text or ""
        logger.info(f"Model response: {text[:100]}...")
    return None  # 응답 그대로 전달

agent = Agent(
    name="logged_agent",
    model="gemini-2.0-flash",
    after_model_callback=log_response,
)
```

### 도구 입력 검증 (before_tool_callback)

```python
def validate_tool_input(callback_context, tool_name: str, args: dict) -> dict | None:
    """도구 입력을 검증합니다."""
    if tool_name == "delete_user" and not args.get("confirm"):
        return {"error": "삭제 작업은 confirm=True가 필요합니다."}
    return None  # 정상 진행

agent = Agent(
    name="validated_agent",
    model="gemini-2.0-flash",
    before_tool_callback=validate_tool_input,
)
```

### 에이전트 레벨 가드레일 (before_agent_callback)

```python
from google.genai.types import Content, Part

def check_authorization(callback_context) -> Content | None:
    """에이전트 실행 전 권한을 확인합니다."""
    user_role = callback_context.state.get("user:role", "guest")
    if user_role == "guest":
        return Content(
            parts=[Part(text="이 기능은 로그인 후 사용할 수 있습니다.")],
            role="model",
        )
    return None  # 정상 진행

agent = Agent(
    name="protected_agent",
    model="gemini-2.0-flash",
    before_agent_callback=check_authorization,
)
```

---

## 콜백 선택 가이드

| 목적 | 콜백 유형 |
|------|----------|
| 금지 주제 필터링 | `before_model_callback` |
| 응답 로깅/모니터링 | `after_model_callback` |
| 도구 입력 검증 | `before_tool_callback` |
| 도구 결과 변환 | `after_tool_callback` |
| 에이전트 접근 제어 | `before_agent_callback` |
| 결과 후처리 | `after_agent_callback` |
| 전역 가드레일 (모든 에이전트) | Runner Plugin |
