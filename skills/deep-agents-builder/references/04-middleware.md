# Deep Agents 미들웨어 패턴

> **최종 업데이트**: 2025-12-24 (deepagents 0.2+)

미들웨어는 에이전트에 **도구, 시스템 프롬프트, 생명주기 훅**을 주입하는 방법입니다.

---

## 기본 미들웨어 스택 (7개)

`create_deep_agent()`는 자동으로 다음 미들웨어를 순서대로 적용합니다:

| 순서 | 미들웨어 | 역할 | 도구 |
|------|---------|------|------|
| 1 | **TodoListMiddleware** | 작업 계획 및 추적 | `write_todos`, `read_todos` |
| 2 | **FilesystemMiddleware** | 파일 작업 및 셸 실행 | `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` |
| 3 | **SubAgentMiddleware** | 서브에이전트 위임 | `task` |
| 4 | **SummarizationMiddleware** | 컨텍스트 압축 | - |
| 5 | **AnthropicPromptCachingMiddleware** | 프롬프트 캐싱 (Anthropic만) | - |
| 6 | **PatchToolCallsMiddleware** | 중단된 도구 호출 복구 | - |
| 7 | **HumanInTheLoopMiddleware** | 도구 승인 요청 | - |

---

## 1. TodoListMiddleware

### 개요

작업 분해 및 진행 상황 추적을 위한 미들웨어입니다.

### 도구

| 도구 | 설명 |
|-----|------|
| `write_todos` | 작업 목록 생성/업데이트 |
| `read_todos` | 현재 작업 목록 확인 |

### 사용

```python
from deepagents.middleware import TodoListMiddleware

TodoListMiddleware(
    system_prompt="Use the write_todos tool to plan complex tasks..."
)
```

---

## 2. FilesystemMiddleware

### 개요

파일 작업과 컨텍스트 오프로딩을 위한 미들웨어입니다.
백엔드가 `SandboxBackendProtocol`을 구현하면 `execute` 도구도 추가됩니다.

### 도구

| 도구 | 설명 | 비고 |
|-----|------|------|
| `ls` | 디렉토리 목록 | 절대 경로 사용 |
| `read_file` | 파일 읽기 | 페이지네이션 지원 |
| `write_file` | 파일 생성/덮어쓰기 | |
| `edit_file` | 정확한 문자열 교체 | |
| `glob` | 패턴 매칭 파일 검색 | 예: `**/*.py` |
| `grep` | 텍스트 패턴 검색 | |
| `execute` | 셸 명령 실행 | 샌드박스 백엔드만 |

### 파라미터

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `backend` | `Backend \| BackendFactory` | 저장소 백엔드 (기본: StateBackend) |
| `system_prompt` | `str` | 커스텀 시스템 프롬프트 |
| `custom_tool_descriptions` | `dict[str, str]` | 도구 설명 오버라이드 |
| `token_limit` | `int` | 토큰 한계 (기본: 20,000) - 초과 시 파일시스템으로 오프로드 |

### 사용

```python
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

FilesystemMiddleware(
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}
    ),
    system_prompt="Write to the filesystem when you need to save information...",
    custom_tool_descriptions={
        "ls": "Use the ls tool to list files in a directory...",
        "read_file": "Use read_file to read file contents...",
    }
)
```

---

## 3. SubAgentMiddleware

### 개요

서브에이전트 위임을 위한 `task` 도구를 제공합니다.

### 파라미터

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `default_model` | `str` | 서브에이전트 기본 모델 |
| `default_tools` | `list` | 모든 서브에이전트에 추가할 도구 |
| `default_middleware` | `list` | 모든 서브에이전트에 적용할 미들웨어 |
| `subagents` | `list[SubAgent \| CompiledSubAgent]` | 서브에이전트 목록 |
| `general_purpose_agent` | `bool` | 범용 서브에이전트 포함 (기본: True) |

### 사용

```python
from langchain_core.tools import tool
from deepagents.middleware.subagents import SubAgentMiddleware

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

SubAgentMiddleware(
    default_model="claude-sonnet-4-5-20250929",
    default_tools=[],
    subagents=[
        {
            "name": "weather",
            "description": "This subagent can get weather in cities.",
            "system_prompt": "Use the get_weather tool to get weather.",
            "tools": [get_weather],
            "model": "gpt-4o",  # 선택적 오버라이드
        }
    ],
)
```

---

## 4. SummarizationMiddleware

### 개요

컨텍스트가 너무 길어지면 자동으로 요약합니다.

### 동작

- **임계값**: 170k 토큰 또는 모델 최대 컨텍스트의 85%
- **동작**: 오래된 메시지를 요약하여 컨텍스트 압축

### 사용

```python
from deepagents.middleware.summarization import SummarizationMiddleware

# create_deep_agent()에 기본 포함
# 커스텀 설정이 필요하면 직접 사용
```

---

## 5. AnthropicPromptCachingMiddleware

### 개요

Anthropic 모델의 프롬프트 캐싱으로 비용을 최적화합니다.

### 동작

- Anthropic 모델 사용 시 자동 활성화
- 반복되는 시스템 프롬프트 캐싱

---

## 6. PatchToolCallsMiddleware

### 개요

체크포인트에서 중단된 도구 호출을 복구합니다.

### 동작

- Human-in-the-loop 인터럽트 후 재개 시 도구 호출 상태 복구

---

## 7. HumanInTheLoopMiddleware

### 개요

특정 도구 실행 전 사용자 승인을 요청합니다.

### 조건

`interrupt_on` 파라미터가 설정된 경우에만 활성화됩니다.

### 사용

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(
    checkpointer=MemorySaver(),  # 필수!
    interrupt_on={
        "execute": True,  # 모든 실행 승인 필요
        "write_file": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    }
)
```

---

## AgentMiddleware 기본

### 커스텀 미들웨어 생성

```python
from langchain_core.tools import tool
from langchain.agents.middleware import AgentMiddleware
from deepagents import create_deep_agent

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

@tool
def get_temperature(city: str) -> str:
    """Get the temperature in a city."""
    return f"The temperature in {city} is 70°F."

class WeatherMiddleware(AgentMiddleware):
    tools = [get_weather, get_temperature]
    system_prompt = """You have access to weather tools.
    Use them to provide comprehensive weather information."""

agent = create_deep_agent(
    middleware=[WeatherMiddleware()]
)
```

### AgentMiddleware 속성

| 속성 | 타입 | 설명 |
|-----|------|------|
| `tools` | `list[BaseTool]` | 에이전트에 추가할 도구들 |
| `system_prompt` | `str` | 시스템 프롬프트에 추가할 지침 |

### 생명주기 훅

```python
class MyMiddleware(AgentMiddleware):
    def before_agent(self, state):
        """에이전트 실행 전 호출"""
        pass

    def after_agent(self, state):
        """에이전트 실행 후 호출"""
        pass

    def before_model(self, messages):
        """모델 호출 전 호출"""
        return messages

    def after_model(self, response):
        """모델 호출 후 호출"""
        return response

    def wrap_tool_call(self, tool_call):
        """도구 호출 래핑"""
        return tool_call

    # 비동기 버전
    async def abefore_agent(self, state): ...
    async def aafter_agent(self, state): ...
```

---

## 미들웨어 조합

여러 미들웨어를 함께 사용할 수 있습니다.

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    middleware=[
        WeatherMiddleware(),        # 커스텀 미들웨어
        # FilesystemMiddleware(),   # 기본 포함됨
        # SubAgentMiddleware(),     # 기본 포함됨
    ],
)
```

> **중요**: 커스텀 미들웨어는 기본 스택에 **추가**됩니다. 기본 미들웨어를 대체하지 않습니다.

---

## 미들웨어 주의사항

### 좋은 예

```python
# 도메인 특화 지침
system_prompt = "When asked about weather, provide both temperature and conditions."
```

### 나쁜 예

```python
# 기본 지침 중복 (미들웨어가 이미 주입)
system_prompt = "You are an AI assistant. Use tools when needed. Plan your work..."
```

---

## 다음 단계

- [05-subagents.md](05-subagents.md): 서브에이전트 설계
- [06-backends.md](06-backends.md): 백엔드 옵션
- [08-hitl-memory.md](08-hitl-memory.md): Human-in-the-Loop 상세
