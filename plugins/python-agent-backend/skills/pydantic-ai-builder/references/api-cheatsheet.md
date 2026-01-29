# API 치트시트

PydanticAI 핵심 API 빠른 참조.

---

## 자주 쓰는 Import

```python
# 핵심
from pydantic_ai import Agent, RunContext, ModelRetry, UsageLimits
from pydantic_ai.settings import ModelSettings

# Output 모드
from pydantic_ai import ToolOutput, NativeOutput, PromptedOutput, TextOutput

# Tool 관련
from pydantic_ai import Tool
from pydantic_ai.tools import ToolDefinition

# Deferred Tools (Human-in-the-Loop)
from pydantic_ai.agent import DeferredToolRequests, DeferredToolResults
from pydantic_ai import ApprovalRequired

# 메시지
from pydantic_ai.messages import (
    ModelMessage, ModelRequest, ModelResponse,
    TextPart, ToolCallPart, ToolReturnPart, RetryPromptPart,
    SystemPromptPart, UserPromptPart,
)

# 테스트
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai import capture_run_messages

# 사용량
from pydantic_ai.usage import RunUsage

# MCP
from pydantic_ai.mcp import MCPServerHTTP, MCPServerStdio

# Graph
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

# Fallback
from pydantic_ai.models import FallbackModel
```

---

## Agent 생성자

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `model` | `str \| Model` | 모델 지정 (예: `'openai:gpt-4o'`) |
| `output_type` | `type \| list` | 출력 타입 (BaseModel, 스칼라, Union) |
| `deps_type` | `type` | 의존성 타입 |
| `system_prompt` | `str \| Sequence[str]` | 정적 시스템 프롬프트 |
| `instructions` | `str` | 명령어 (message_history 시 제외) |
| `tools` | `Sequence[Tool]` | 도구 목록 |
| `mcp_servers` | `Sequence[MCPServer]` | MCP 서버 목록 |
| `retries` | `int` | 기본 retry 횟수 (기본: 1) |
| `model_settings` | `ModelSettings \| dict` | 모델 설정 |
| `end_strategy` | `str` | 종료 전략 (`'early'` 등) |

---

## 실행 메서드 비교

| 메서드 | 동기/비동기 | 반환 타입 | 용도 |
|--------|-----------|----------|------|
| `agent.run()` | async | `AgentRunResult` | 일반 비동기 실행 |
| `agent.run_sync()` | sync | `AgentRunResult` | 동기 실행 (스크립트, 테스트) |
| `agent.run_stream()` | async ctx mgr | `StreamedRunResult` | 텍스트/구조화 스트리밍 |
| `agent.run_stream_events()` | async iterable | `AgentStreamEvent` | 상세 이벤트 스트리밍 |
| `agent.iter()` | async ctx mgr | `AgentRun` | 노드별 수동 반복 |

### 공통 파라미터

```python
result = await agent.run(
    'prompt',                              # 사용자 프롬프트
    deps=my_deps,                          # 의존성
    message_history=prev_messages,         # 이전 대화 (result.new_messages() 또는 all_messages())
    model='anthropic:claude-sonnet-4-20250514',  # 모델 오버라이드
    model_settings={'temperature': 0.5},   # 설정 오버라이드
    usage_limits=UsageLimits(...),         # 비용 제한
    usage=shared_usage,                    # 공유 사용량 추적
    deferred_tool_results=results,         # Deferred Tools 승인 결과
    metadata={'key': 'value'},             # 메타데이터
)
```

---

## Tool 등록 비교

| 방식 | RunContext | 재사용 | 사용 시점 |
|------|-----------|--------|----------|
| `@agent.tool` | ✅ 포함 | 해당 Agent만 | 의존성 접근 필요 |
| `@agent.tool_plain` | ❌ 없음 | 해당 Agent만 | 순수 함수 |
| `Tool(fn, takes_ctx=...)` | 선택 | 여러 Agent 공유 | 재사용 가능한 도구 |

---

## Output 모드 비교

| 모드 | 클래스 | 지원 모델 | 정확도 | 비고 |
|------|--------|----------|--------|------|
| Tool (기본) | `ToolOutput()` | 거의 모든 모델 | 높음 | 도구 호출로 스키마 강제 |
| Native | `NativeOutput()` | 일부 (GPT-4o+) | 매우 높음 | 모델 네이티브 기능 |
| Prompted | `PromptedOutput()` | 모든 모델 | 중간 | 프롬프트 삽입 + 파싱 |

---

## AgentRunResult 속성

| 속성/메서드 | 타입 | 설명 |
|------------|------|------|
| `.output` | `OutputT` | 구조화된 출력 (타입 안전) |
| `.usage()` | `Usage` | 토큰 사용량 |
| `.new_messages()` | `list[ModelMessage]` | 이번 실행의 메시지 |
| `.all_messages()` | `list[ModelMessage]` | 전체 메시지 히스토리 |

---

## StreamedRunResult 메서드

| 메서드 | 반환 타입 | 설명 |
|--------|----------|------|
| `stream_text(delta=False)` | `AsyncIterator[str]` | 텍스트 스트리밍 (delta=True: 증분) |
| `stream_output(debounce_by=0.1)` | `AsyncIterator[OutputT]` | 구조화된 출력 스트리밍 |
| `stream_responses(debounce_by=0.1)` | `AsyncIterator[tuple]` | 모델 응답 스트리밍 |
| `get_output()` | `OutputT` (async) | 전체 스트리밍 완료 후 검증된 출력 반환 |
| `.response` | `ModelResponse` | 현재 응답 상태 (property) |

---

## ModelSettings 주요 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `temperature` | `float` | 샘플링 온도 (0.0=결정적, 1.0=창의적) |
| `max_tokens` | `int` | 최대 응답 토큰 수 |
| `top_p` | `float` | 핵 샘플링 (0.0~1.0) |
| `timeout` | `float` | 요청 타임아웃 (초) |

---

## UsageLimits 필드

| 필드 | 설명 |
|------|------|
| `request_limit` | 최대 LLM 요청 횟수 |
| `response_tokens_limit` | 최대 응답 토큰 수 |
| `total_tokens_limit` | 최대 총 토큰 수 (요청+응답) |

---

## 모델 문자열 형식

```
{provider}:{model_name}

예시:
openai:gpt-4o
openai:gpt-4o-mini
anthropic:claude-sonnet-4-20250514
anthropic:claude-3-5-haiku-20241022
google-gla:gemini-2.0-flash
groq:llama-3.3-70b-versatile
mistral:mistral-large-latest
```

---

## 테스트 패턴

```python
# 1. 안전장치 설정
os.environ['ALLOW_MODEL_REQUESTS'] = 'false'

# 2. TestModel로 오버라이드
with agent.override(model=TestModel()):
    result = agent.run_sync('test', deps=mock)

# 3. FunctionModel로 정밀 제어
with agent.override(model=FunctionModel(my_func)):
    result = agent.run_sync('test', deps=mock)

# 4. 메시지 캡처
with capture_run_messages() as msgs:
    result = agent.run_sync('test', deps=mock)
assert len(msgs) > 0
```
