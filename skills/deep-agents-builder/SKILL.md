---
name: deep-agents-builder
description: |
  This skill should be used when the user asks to build agents with LangChain Deep Agents,
  create planning agents, implement subagent delegation, or configure agent middleware.
  Examples:
  - "Deep Agents로 에이전트 만들기"
  - "langchain agent builder"
  - "서브에이전트 설계"
  - "에이전트 미들웨어 구성"
  - "deepagents CLI 사용법"
  - "에이전트 영속 메모리 설정"
version: 2.0.0
---

# Deep Agents 에이전트 빌더 가이드

LangChain **Deep Agents**로 복잡한 멀티스텝 작업을 수행하는 에이전트를 구축하는 종합 가이드입니다.

> **최종 업데이트**: 2025-12-24 (deepagents 0.2+ 기준)

---

## 빠른 시작

### 설치

```bash
# SDK 설치
pip install deepagents tavily-python

# CLI 설치 (선택)
pip install deepagents-cli
```

### 기본 에이전트

```python
from deepagents import create_deep_agent

# 기본 모델: claude-sonnet-4-5-20250929
agent = create_deep_agent(
    tools=[my_tool],
    system_prompt="Your domain-specific instructions"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Research AI agents"}]
})
```

### CLI 사용

```bash
# 기본 에이전트 실행
deepagents

# 이름 지정 에이전트
deepagents agent my-researcher

# 에이전트 목록
deepagents list
```

---

## 핵심 구성요소 (7개 미들웨어)

| 미들웨어 | 도구 | 역할 |
|---------|------|------|
| **TodoListMiddleware** | `write_todos`, `read_todos` | 작업 분해 및 추적 |
| **FilesystemMiddleware** | `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` | 컨텍스트 관리 |
| **SubAgentMiddleware** | `task` | 전문화된 하위 에이전트 위임 |
| **SummarizationMiddleware** | - | 170k 토큰 초과 시 자동 압축 |
| **AnthropicPromptCachingMiddleware** | - | Anthropic 모델 프롬프트 캐싱 |
| **PatchToolCallsMiddleware** | - | 체크포인트 중단된 도구 호출 복구 |
| **HumanInTheLoopMiddleware** | - | 도구 실행 전 승인 요청 (interrupt_on 설정 시) |

---

## 주요 API

### create_deep_agent()

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-5-20250929",  # 기본 모델
    tools=[],                                       # 커스텀 도구
    system_prompt="",                               # 도메인별 지침 (기본 프롬프트에 추가)
    middleware=[],                                  # 추가 미들웨어
    subagents=[],                                   # 서브에이전트
    backend=None,                                   # 파일시스템 백엔드
    checkpointer=MemorySaver(),                     # 상태 영속화 (HITL 필수)
    store=None,                                     # LangGraph Store (장기 메모리)
    interrupt_on={"execute": True},                 # Human-in-the-loop 설정
    response_format=None,                           # 구조화된 출력 포맷
    debug=False,                                    # 디버그 모드
    name="my-agent",                                # 에이전트 이름
)
```

### 서브에이전트 정의

```python
subagent = {
    "name": "research-specialist",
    "description": "Deep research tasks",
    "system_prompt": "You are a researcher",
    "tools": [internet_search],
    "model": "openai:gpt-4o"  # 선택적 모델 오버라이드
}
```

### Human-in-the-Loop

```python
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

## 백엔드 옵션

| 백엔드 | 영속성 | 샌드박스 | 용도 |
|--------|--------|----------|------|
| **StateBackend** | X | X | 개발/테스트 (기본) |
| **FilesystemBackend** | O | X | 로컬 디스크 |
| **StoreBackend** | O | X | LangGraph Store (장기 메모리) |
| **CompositeBackend** | 하이브리드 | - | 경로별 라우팅 |
| **Runloop/Daytona/Modal** | O | O | 프로덕션 샌드박스 |

### 장기 메모리 설정

```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_deep_agent(
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}
    )
)
# /memories/ 경로는 영속, 나머지는 임시
```

---

## 문서 라우팅

상세 정보는 아래 문서를 참조하세요:

| 주제 | 문서 |
|-----|------|
| 설치, CLI, 첫 에이전트 | [01-quickstart.md](references/01-quickstart.md) |
| Planning, Filesystem, Subagents, Shell | [02-core-concepts.md](references/02-core-concepts.md) |
| `create_deep_agent()` 파라미터 상세 | [03-api-reference.md](references/03-api-reference.md) |
| 7개 미들웨어 스택 상세 | [04-middleware.md](references/04-middleware.md) |
| SubAgent, CompiledSubAgent, 태스크 위임 | [05-subagents.md](references/05-subagents.md) |
| StateBackend, StoreBackend, 샌드박스 | [06-backends.md](references/06-backends.md) |
| **naviseoAI 프로젝트 통합** | [07-naviseoai-integration.md](references/07-naviseoai-integration.md) |
| **Human-in-the-Loop, 장기 메모리** | [08-hitl-memory.md](references/08-hitl-memory.md) |
| **MCP 도구 통합** | [09-mcp-integration.md](references/09-mcp-integration.md) |
| **LangSmith 배포/모니터링** | [10-langsmith-production.md](references/10-langsmith-production.md) |
| **디버깅 및 테스트** | [11-debugging-testing.md](references/11-debugging-testing.md) |

---

## 참고 자료

- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [Deep Agents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [API Reference](https://reference.langchain.com/python/deepagents/)
- [DeepAgents CLI Blog](https://blog.langchain.com/introducing-deepagents-cli/)
- [LangChain Changelog](https://changelog.langchain.com/)

---

**Sources:**
- [Deep Agents Overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [GitHub Repository](https://github.com/langchain-ai/deepagents)
- [API Reference](https://reference.langchain.com/python/deepagents/)
- [DeepAgents CLI](https://blog.langchain.com/introducing-deepagents-cli/)
