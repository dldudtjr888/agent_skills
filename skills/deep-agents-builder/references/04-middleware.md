# Deep Agents 미들웨어 패턴

미들웨어는 에이전트에 **도구, 시스템 프롬프트, 생명주기 훅**을 주입하는 방법입니다.

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
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[WeatherMiddleware()]
)
```

### AgentMiddleware 속성

| 속성 | 타입 | 설명 |
|-----|------|------|
| `tools` | `list[BaseTool]` | 에이전트에 추가할 도구들 |
| `system_prompt` | `str` | 시스템 프롬프트에 추가할 지침 |

---

## FilesystemMiddleware

파일시스템 도구(`ls`, `read_file`, `write_file`, `edit_file`)를 제공합니다.

### 기본 사용

```python
from langchain.agents import create_agent
from deepagents.middleware.filesystem import FilesystemMiddleware

# create_deep_agent에는 기본 포함
# create_agent 사용 시 명시적 추가 필요
agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[
        FilesystemMiddleware()
    ],
)
```

### 커스텀 설정

```python
agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[
        FilesystemMiddleware(
            # 선택적: 커스텀 저장소 백엔드
            backend=custom_backend,

            # 선택적: 커스텀 시스템 프롬프트
            system_prompt="Write to the filesystem when you need to save information...",

            # 선택적: 도구 설명 오버라이드
            custom_tool_descriptions={
                "ls": "Use the ls tool to list files in a directory...",
                "read_file": "Use read_file to read file contents...",
                "write_file": "Use write_file to save information...",
                "edit_file": "Use edit_file for precise text replacements..."
            }
        ),
    ],
)
```

### FilesystemMiddleware 파라미터

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `backend` | `Backend` | 저장소 백엔드 (기본: Virtual) |
| `system_prompt` | `str` | 커스텀 시스템 프롬프트 |
| `custom_tool_descriptions` | `dict[str, str]` | 도구 설명 오버라이드 |

---

## SubAgentMiddleware

서브에이전트 위임을 위한 `task` 도구를 제공합니다.

### 기본 사용

```python
from langchain_core.tools import tool
from langchain.agents import create_agent
from deepagents.middleware.subagents import SubAgentMiddleware

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

agent = create_agent(
    model="claude-sonnet-4-20250514",
    middleware=[
        SubAgentMiddleware(
            default_model="claude-sonnet-4-20250514",
            default_tools=[],
            subagents=[
                {
                    "name": "weather",
                    "description": "This subagent can get weather in cities.",
                    "system_prompt": "Use the get_weather tool to get weather.",
                    "tools": [get_weather],
                }
            ],
        )
    ],
)
```

### 서브에이전트별 모델 오버라이드

```python
SubAgentMiddleware(
    default_model="claude-sonnet-4-20250514",
    default_tools=[],
    subagents=[
        {
            "name": "weather",
            "description": "Weather specialist",
            "system_prompt": "You are a weather expert.",
            "tools": [get_weather],
            "model": "gpt-4.1",  # 이 서브에이전트만 다른 모델 사용
            "middleware": [],   # 추가 미들웨어
        }
    ],
)
```

### SubAgentMiddleware 파라미터

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `default_model` | `str` | 서브에이전트 기본 모델 |
| `default_tools` | `list` | 모든 서브에이전트에 추가할 도구 |
| `subagents` | `list[SubAgent \| CompiledSubAgent]` | 서브에이전트 목록 |

---

## 미들웨어 조합

여러 미들웨어를 함께 사용할 수 있습니다.

```python
from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[
        WeatherMiddleware(),        # 커스텀 미들웨어
        FilesystemMiddleware(),     # 파일시스템 (create_deep_agent에 기본 포함)
        SubAgentMiddleware(...),    # 서브에이전트
    ],
)
```

---

## 미들웨어 주의사항

> **Important**: 미들웨어 기반으로 기본 지침이 자동 주입됩니다.
> 중복을 피하고 **도메인 특화 워크플로우에 집중**하세요.

```python
# 좋은 예: 도메인 특화 지침
system_prompt="When asked about weather, provide both temperature and conditions."

# 나쁜 예: 기본 지침 중복
system_prompt="You are an AI assistant. Use tools when needed. Plan your work..."
```

---

## 다음 단계

- [05-subagents.md](05-subagents.md): 서브에이전트 설계
- [06-backends.md](06-backends.md): 백엔드 옵션
