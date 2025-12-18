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
version: 1.0.0
---

# Deep Agents 에이전트 빌더 가이드

LangChain **Deep Agents**로 복잡한 멀티스텝 작업을 수행하는 에이전트를 구축하는 종합 가이드입니다.

---

## 빠른 시작

```bash
pip install deepagents tavily-python
```

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[my_tool],
    system_prompt="Your domain-specific instructions"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Research AI agents"}]
})
```

---

## 핵심 4요소

| 구성요소 | 도구 | 역할 |
|---------|------|------|
| **Planning** | `write_todos`, `read_todos` | 작업 분해 및 추적 |
| **Filesystem** | `read_file`, `write_file`, `edit_file` | 컨텍스트 관리 |
| **Subagents** | `task` | 전문화된 하위 에이전트 위임 |
| **Shell** | `execute` | 셸 명령어 실행 |

---

## 주요 API

### create_deep_agent()

```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",  # 기본 모델
    tools=[],                                      # 커스텀 도구
    system_prompt="",                              # 도메인별 지침
    middleware=[],                                 # 미들웨어
    subagents=[],                                  # 서브에이전트
    backend=None                                   # 파일시스템 백엔드
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

### 커스텀 미들웨어

```python
from langchain.agents.middleware import AgentMiddleware

class MyMiddleware(AgentMiddleware):
    tools = [my_tool]
    system_prompt = "Custom instructions"
```

---

## 내장 도구

| 도구 | 용도 |
|-----|------|
| `write_todos` | 작업 목록 생성 |
| `read_todos` | 현재 TODO 확인 |
| `ls` | 디렉토리 목록 |
| `read_file` | 파일 읽기 (페이지네이션) |
| `write_file` | 파일 생성/덮어쓰기 |
| `edit_file` | 정확한 문자열 교체 |
| `glob` | 패턴 매칭 파일 검색 |
| `grep` | 텍스트 패턴 검색 |
| `execute` | 셸 명령어 실행 |
| `task` | 서브에이전트 위임 |

---

## 문서 라우팅

상세 정보는 아래 문서를 참조하세요:

| 주제 | 문서 |
|-----|------|
| 설치 및 첫 에이전트 | [01-quickstart.md](references/01-quickstart.md) |
| Planning, Filesystem, Subagents, Shell | [02-core-concepts.md](references/02-core-concepts.md) |
| `create_deep_agent()` 파라미터 상세 | [03-api-reference.md](references/03-api-reference.md) |
| AgentMiddleware, FilesystemMiddleware | [04-middleware.md](references/04-middleware.md) |
| SubAgent, CompiledSubAgent, 태스크 위임 | [05-subagents.md](references/05-subagents.md) |
| Virtual, Runloop, Daytona, Modal 백엔드 | [06-backends.md](references/06-backends.md) |
| **naviseoAI 프로젝트 통합** | [07-naviseoai-integration.md](references/07-naviseoai-integration.md) |

---

## 참고 자료

- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [Deep Agents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents Blog](https://blog.langchain.com/deep-agents/)
