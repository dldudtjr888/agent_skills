# 디버깅 및 테스트 가이드

> **최종 업데이트**: 2026-01-23 (deepagents 0.3.8)

Deep Agents **디버깅** 및 **테스트** 방법입니다.

---

## 디버그 모드

### 기본 설정

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    debug=True  # 디버그 모드 활성화
)
```

### 디버그 출력

디버그 모드에서 확인 가능한 정보:

- 도구 호출 상세
- 메시지 흐름
- 토큰 사용량
- 미들웨어 처리 순서

---

## 스트리밍 디버깅

### 이벤트 타입 확인

```python
async def debug_stream(agent, query: str):
    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": query}]},
        version="v2"
    ):
        event_type = event["event"]

        if event_type == "on_chat_model_start":
            print(f"[LLM 시작] 입력: {len(event['data']['messages'])} 메시지")

        elif event_type == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            print(f"[스트림] {chunk.content}", end="")

        elif event_type == "on_tool_start":
            print(f"\n[도구 시작] {event['name']}")
            print(f"  입력: {event['data']['input']}")

        elif event_type == "on_tool_end":
            print(f"[도구 완료] {event['name']}")
            print(f"  출력: {event['data']['output'][:100]}...")

        elif event_type == "on_chat_model_end":
            print(f"\n[LLM 완료]")
```

### 이벤트 필터링

```python
# 특정 이벤트만 수신
async for event in agent.astream_events(
    {"messages": [...]},
    include_names=["ChatAnthropic"],  # 특정 컴포넌트만
    include_types=["on_tool_start", "on_tool_end"]  # 특정 타입만
):
    print(event)
```

---

## 로깅 설정

### LangChain 로거

```python
import logging

# LangChain 로거 활성화
logging.getLogger("langchain").setLevel(logging.DEBUG)
logging.getLogger("langgraph").setLevel(logging.DEBUG)

# 핸들러 추가
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger("langchain").addHandler(handler)
```

### 커스텀 로거

```python
import logging

logger = logging.getLogger("deepagents")
logger.setLevel(logging.DEBUG)

# 파일 핸들러
file_handler = logging.FileHandler("agent_debug.log")
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
```

---

## 단위 테스트

### 기본 테스트 구조

```python
import pytest
from deepagents import create_deep_agent

@pytest.fixture
def agent():
    """테스트용 에이전트 생성."""
    return create_deep_agent(
        system_prompt="You are a test assistant."
    )

@pytest.mark.asyncio
async def test_basic_response(agent):
    """기본 응답 테스트."""
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Say hello"}]
    })

    assert len(result["messages"]) > 0
    last_message = result["messages"][-1]
    assert last_message["role"] == "assistant"
    assert len(last_message["content"]) > 0
```

### 도구 호출 테스트

```python
@pytest.mark.asyncio
async def test_tool_usage(agent):
    """도구 사용 테스트."""
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "List files in the current directory"
        }]
    })

    # 도구 호출 확인
    messages = result["messages"]
    tool_calls = [
        m for m in messages
        if hasattr(m, "tool_calls") and m.tool_calls
    ]

    assert len(tool_calls) > 0
    assert any("ls" in str(tc) for tc in tool_calls)
```

### 메모리 테스트

```python
from langgraph.store.memory import InMemoryStore
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

@pytest.mark.asyncio
async def test_memory_persistence():
    """메모리 영속성 테스트."""
    store = InMemoryStore()

    agent = create_deep_agent(
        store=store,
        backend=lambda rt: CompositeBackend(
            default=StateBackend(rt),
            routes={"/memories/": StoreBackend(rt)}
        )
    )

    # 정보 저장
    await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Remember that my name is Alice"
        }]
    })

    # 정보 확인
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "What is my name?"
        }]
    })

    assert "Alice" in result["messages"][-1]["content"]
```

---

## 통합 테스트

### HITL 테스트

```python
from langgraph.checkpoint.memory import MemorySaver

@pytest.mark.asyncio
async def test_human_in_the_loop():
    """HITL 워크플로우 테스트."""
    checkpointer = MemorySaver()

    agent = create_deep_agent(
        checkpointer=checkpointer,
        interrupt_on={"write_file": True}
    )

    config = {"configurable": {"thread_id": "test-thread"}}

    # 파일 쓰기 요청 → 인터럽트 예상
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Create a file called test.txt"
        }]
    }, config=config)

    # 인터럽트 확인
    assert result.get("__interrupt__") is not None

    # 승인 후 재개
    result = await agent.ainvoke(
        {"messages": []},
        config={**config, "decision": "approve"}
    )

    # 완료 확인
    assert result.get("__interrupt__") is None
```

### 서브에이전트 테스트

```python
@pytest.mark.asyncio
async def test_subagent_delegation():
    """서브에이전트 위임 테스트."""
    from langchain_core.tools import tool

    @tool
    def specialized_task(input: str) -> str:
        """Specialized task handler."""
        return f"Processed: {input}"

    agent = create_deep_agent(
        subagents=[{
            "name": "specialist",
            "description": "Handles specialized tasks",
            "tools": [specialized_task]
        }]
    )

    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Handle this specialized task"
        }]
    })

    # 서브에이전트 호출 확인
    messages = result["messages"]
    assert any("Processed:" in str(m) for m in messages)
```

---

## Mock 테스트

### LLM Mock

```python
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_with_mock_llm():
    """Mock LLM으로 테스트."""
    mock_response = AIMessage(content="Mocked response")

    with patch("langchain_anthropic.ChatAnthropic.ainvoke") as mock:
        mock.return_value = mock_response

        agent = create_deep_agent()
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Test"}]
        })

        assert "Mocked response" in str(result)
```

### 도구 Mock

```python
@pytest.mark.asyncio
async def test_with_mock_tool():
    """Mock 도구로 테스트."""
    from langchain_core.tools import tool

    @tool
    def mock_file_system(path: str) -> str:
        """Mock file system."""
        return "file1.txt\nfile2.txt\nfile3.txt"

    agent = create_deep_agent(tools=[mock_file_system])

    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "List files"
        }]
    })

    assert "file1.txt" in str(result)
```

---

## 성능 테스트

### 응답 시간 측정

```python
import time
import statistics

@pytest.mark.asyncio
async def test_response_time():
    """응답 시간 테스트."""
    agent = create_deep_agent()

    times = []
    for _ in range(10):
        start = time.time()
        await agent.ainvoke({
            "messages": [{"role": "user", "content": "Hi"}]
        })
        times.append(time.time() - start)

    avg_time = statistics.mean(times)
    p95_time = statistics.quantiles(times, n=20)[18]

    print(f"Average: {avg_time:.2f}s")
    print(f"P95: {p95_time:.2f}s")

    assert avg_time < 5.0  # 5초 이내
    assert p95_time < 10.0  # P95 10초 이내
```

### 메모리 사용량

```python
import tracemalloc

@pytest.mark.asyncio
async def test_memory_usage():
    """메모리 사용량 테스트."""
    tracemalloc.start()

    agent = create_deep_agent()

    for i in range(100):
        await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"Message {i}"
            }]
        })

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")

    assert peak < 500 * 1024 * 1024  # 500MB 이내
```

---

## 트러블슈팅

### 일반적인 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| 도구가 호출되지 않음 | 시스템 프롬프트 부족 | 도구 사용 지침 추가 |
| 무한 루프 | 종료 조건 미설정 | max_iterations 설정 |
| 메모리 누수 | 세션 정리 안됨 | 체크포인터 정리 |
| 느린 응답 | 컨텍스트 과다 | SummarizationMiddleware 확인 |

### 디버그 체크리스트

1. [ ] `debug=True` 설정 확인
2. [ ] LangSmith 추적 활성화
3. [ ] 로깅 레벨 DEBUG 설정
4. [ ] 스트리밍 이벤트 확인
5. [ ] 도구 입출력 검증
6. [ ] 메모리 상태 확인

### 에러 메시지 해석

```python
# "Checkpointer is required for HITL"
# → checkpointer=MemorySaver() 추가 필요

# "Tool not found: execute"
# → 샌드박스 백엔드 필요 (Runloop, Daytona, Modal)

# "Context length exceeded"
# → SummarizationMiddleware 확인, 토큰 제한 조정
```

---

## pytest 설정

### pytest.ini

```ini
[pytest]
asyncio_mode = auto
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### conftest.py

```python
import pytest
from deepagents import create_deep_agent

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 설정."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_agent():
    """테스트용 에이전트."""
    return create_deep_agent(debug=True)
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/

# 특정 마커
pytest tests/ -m "not slow"

# 커버리지
pytest tests/ --cov=deepagents --cov-report=html
```

---

## 참고 자료

- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [LangSmith Testing](https://docs.smith.langchain.com/testing)
- [LangGraph Testing](https://langchain-ai.github.io/langgraph/how-tos/test/)

