# 고급 기능 패턴

Streaming, Testing/Eval, MCP 통합, Durable Execution, Human-in-the-Loop, Logfire 관측성.

---

## Streaming

### 텍스트 스트리밍

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

async def stream_response(prompt: str):
    async with agent.run_stream(prompt) as stream:
        async for chunk in stream.stream_text():
            print(chunk, end='', flush=True)
        print()  # 줄바꿈
```

### 구조화된 출력 스트리밍

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class UserProfile(BaseModel):
    name: str
    bio: str
    skills: list[str]

agent = Agent('openai:gpt-4o', output_type=UserProfile)

async def stream_structured(prompt: str):
    async with agent.run_stream(prompt) as stream:
        async for partial in stream.stream_output():
            # partial은 부분적으로 채워진 UserProfile
            print(partial)

    # 최종 결과 (get_output()으로 전체 스트리밍 완료 후 검증된 출력 반환)
    final_output = await stream.get_output()
    print(final_output)  # 완성된 UserProfile
```

### 이벤트 스트리밍

```python
async def stream_events(prompt: str):
    async with agent.run_stream_events(prompt) as events:
        async for event in events:
            # AgentStreamEvent: 모델 응답, 도구 호출 등 상세 이벤트
            print(event)
```

### 노드별 반복 (iter)

```python
async def iterate_nodes(prompt: str):
    async with agent.iter(prompt) as run:
        async for node in run:
            # 각 노드(도구 호출, 모델 응답 등)를 개별 처리
            print(f'Node: {type(node).__name__}')

    final = run.result
    print(final.output)
```

---

## Testing & Evaluation

### TestModel (기본 테스트)

실제 LLM 호출 없이 모든 Tool을 자동 실행하고 스키마에 맞는 더미 데이터 반환.

```python
import os
import pytest
from pydantic_ai.models.test import TestModel

# 전역 안전장치: 테스트에서 실제 API 호출 차단
os.environ['ALLOW_MODEL_REQUESTS'] = 'false'

def test_agent_basic():
    with agent.override(model=TestModel()):
        result = agent.run_sync('테스트 입력', deps=mock_deps)
        assert isinstance(result.output, MyOutput)

# 커스텀 응답 텍스트
def test_agent_custom_text():
    with agent.override(model=TestModel(custom_output_text='맞춤 응답')):
        result = agent.run_sync('테스트')
        assert '맞춤' in str(result.output)
```

### FunctionModel (정밀 테스트)

도구 호출 로직을 직접 제어하는 고급 테스트.

```python
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart

def custom_model(
    messages: list[ModelMessage], info: 'AgentInfo'
) -> ModelResponse:
    """테스트용 커스텀 모델 함수"""
    # 마지막 사용자 메시지에서 값 추출
    last_msg = str(messages[-1])
    if 'weather' in last_msg.lower():
        return ModelResponse(parts=[TextPart(content='맑음, 25도')])
    return ModelResponse(parts=[TextPart(content='알 수 없음')])

def test_with_function_model():
    with agent.override(model=FunctionModel(custom_model)):
        result = agent.run_sync('서울 weather')
        assert '맑음' in str(result.output)
```

### Pytest Fixture 패턴

```python
@pytest.fixture
def override_agent():
    with agent.override(model=TestModel()):
        yield

async def test_analysis(override_agent: None):
    result = await agent.run('분석해주세요', deps=mock_deps)
    assert result.output.confidence >= 0.0

async def test_tool_execution(override_agent: None):
    result = await agent.run('데이터 조회', deps=mock_deps)
    # TestModel은 모든 Tool을 자동 호출
    assert result.output is not None
```

### 메시지 캡처 & 검증

```python
from pydantic_ai import capture_run_messages

def test_message_flow():
    with agent.override(model=TestModel()):
        with capture_run_messages() as messages:
            result = agent.run_sync('테스트', deps=mock_deps)

        # 메시지 흐름 검증
        assert any('tool' in str(m) for m in messages)
```

---

## MCP 통합 (Model Context Protocol)

### HTTP 기반 MCP 서버

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

agent = Agent(
    'openai:gpt-4o',
    mcp_servers=[
        MCPServerHTTP('http://localhost:8000/mcp'),
    ],
)
```

### Stdio 기반 MCP 서버

```python
from pydantic_ai.mcp import MCPServerStdio

agent = Agent(
    'openai:gpt-4o',
    mcp_servers=[
        MCPServerStdio('npx', ['-y', '@modelcontextprotocol/server-filesystem', '/tmp']),
    ],
)
```

### MCP 사용 시 주의점

- MCP 서버의 Tool은 Agent의 Tool과 함께 등록됨
- 서버 연결은 `async with agent.run(...)` 컨텍스트에서 자동 관리
- `run_sync()`에서는 MCP 서버 사용 불가 (비동기 필수)

---

## Durable Execution (내구성 실행)

API 장애나 애플리케이션 오류 시 진행 상태를 보존하고 재개.

```python
# 그래프 기반 영속성 활용
from pydantic_graph.persistence.file import FileStatePersistence

persistence = FileStatePersistence('agent_state.json')

async with graph.iter(
    start_node,
    state=my_state,
    persistence=persistence,
) as run:
    async for node in run:
        print(f'완료: {type(node).__name__}')

# 장애 후 재개
async with graph.iter_from_persistence(persistence) as run:
    async for node in run:
        print(f'재개: {type(node).__name__}')
```

---

## Human-in-the-Loop (Deferred Tools)

민감한 작업에 대해 사용자 승인을 요구하는 패턴.

### 기본 승인 요청

```python
from pydantic_ai import Agent, RunContext

# requires_approval=True → 실행 전 승인 필요
@agent.tool(requires_approval=True)
async def delete_all_data(ctx: RunContext[MyDeps]) -> str:
    """모든 데이터를 삭제합니다. 사용자 승인이 필요합니다."""
    if not ctx.tool_call_approved:
        return '승인되지 않았습니다.'
    await ctx.deps.db.delete_all()
    return '삭제 완료'
```

### 승인 워크플로우

```python
from pydantic_ai.agent import DeferredToolRequests, DeferredToolResults

# 1) 실행 → DeferredToolRequests 반환
result = await agent.run('모든 데이터를 삭제해주세요', deps=my_deps)

if isinstance(result.output, DeferredToolRequests):
    requests = result.output

    # 2) 사용자에게 승인 요청
    results = DeferredToolResults()
    for call in requests.approvals:
        approved = await ask_user_approval(call)
        results.approvals[call.tool_call_id] = approved

    # 3) 승인 결과로 재실행
    final = await agent.run(
        '계속 진행',
        message_history=result.new_messages(),
        deferred_tool_results=results,
        deps=my_deps,
    )
    print(final.output)
```

### 조건부 승인 (런타임 판단)

```python
from pydantic_ai import ApprovalRequired

@agent.tool
async def transfer_money(ctx: RunContext[MyDeps], amount: float) -> str:
    """금액을 이체합니다."""
    if amount > 10000:
        raise ApprovalRequired('고액 이체는 승인이 필요합니다.')
    return await ctx.deps.bank.transfer(amount)
```

---

## Logfire 관측성

### 기본 설정

```python
import logfire

# 환경 변수: LOGFIRE_TOKEN=...
logfire.configure()
logfire.instrument_pydantic_ai()

# 이후 모든 Agent 실행이 자동 트레이싱
result = await agent.run('분석해주세요', deps=my_deps)
```

### 트레이싱되는 정보

- 모델 요청/응답 (프롬프트, 완성, 토큰 수)
- Tool 호출 (이름, 인자, 반환값, 소요 시간)
- 에이전트 위임 체인
- 검증 오류 및 retry
- 전체 요청 레이턴시

### OpenTelemetry 호환

```python
# Logfire는 OpenTelemetry 기반이므로 기존 관측성 도구와 통합 가능
# Jaeger, Zipkin, Datadog 등으로 트레이스 전송 가능
logfire.configure(
    send_to_logfire=False,  # 외부 OTLP 엔드포인트로만 전송
)
```

---

## UsageLimits (비용 제어)

```python
from pydantic_ai import Agent, UsageLimits

result = await agent.run(
    '분석해주세요',
    deps=my_deps,
    usage_limits=UsageLimits(
        request_limit=10,            # 최대 요청 수
        response_tokens_limit=2000,  # 최대 응답 토큰
        total_tokens_limit=5000,     # 최대 총 토큰
    ),
)

# 사용량 확인
print(result.usage())
# Usage(requests=3, request_tokens=1200, response_tokens=800, total_tokens=2000)
```

**멀티에이전트에서 사용량 통합**:
```python
from pydantic_ai.usage import RunUsage

usage = RunUsage()
r1 = await agent1.run('task1', usage=usage)
r2 = await agent2.run('task2', usage=usage)
print(f'총 사용량: {usage}')  # 두 에이전트의 합산
```
