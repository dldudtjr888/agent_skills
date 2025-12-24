# Human-in-the-Loop 및 장기 메모리

> **최종 업데이트**: 2025-12-24 (deepagents 0.2+)

Deep Agents의 **Human-in-the-Loop (HITL)** 워크플로우와 **장기 메모리** 설정 가이드입니다.

---

## Human-in-the-Loop (HITL)

### 개요

HITL은 에이전트가 민감한 도구를 실행하기 전에 사용자 승인을 요청하는 기능입니다.

### 필수 조건

```python
from langgraph.checkpoint.memory import MemorySaver

# checkpointer가 필수!
checkpointer = MemorySaver()
```

### 기본 설정

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(
    checkpointer=MemorySaver(),
    interrupt_on={
        "execute": True,              # execute 도구 모든 호출 승인
        "write_file": True,           # write_file 도구 모든 호출 승인
    }
)
```

### 상세 설정 (InterruptOnConfig)

```python
agent = create_deep_agent(
    checkpointer=MemorySaver(),
    interrupt_on={
        "execute": {
            "allowed_decisions": ["approve", "edit", "reject"]
        },
        "write_file": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    }
)
```

### 결정 옵션

| 결정 | 설명 |
|-----|------|
| `approve` | 도구 호출 승인 |
| `edit` | 도구 인자 수정 후 실행 |
| `reject` | 도구 호출 거부 |

---

## HITL 워크플로우

### 1. 인터럽트 발생

```python
# 에이전트가 write_file 호출 시도
result = agent.invoke({
    "messages": [{"role": "user", "content": "Create a hello.py file"}]
})

# 결과에 인터럽트 상태 포함
if result.get("__interrupt__"):
    print("승인 필요:", result["__interrupt__"])
```

### 2. 사용자 결정

```python
# 승인
agent.invoke(
    {"messages": []},  # 빈 메시지
    config={"decision": "approve"}
)

# 수정 후 승인
agent.invoke(
    {"messages": []},
    config={
        "decision": "edit",
        "edit_args": {"content": "# Modified content\nprint('Hello')"}
    }
)

# 거부
agent.invoke(
    {"messages": []},
    config={"decision": "reject"}
)
```

### 3. 스트리밍에서 HITL

```python
for event in agent.stream({
    "messages": [{"role": "user", "content": "Write code to disk"}]
}):
    if event.get("__interrupt__"):
        # 승인 UI 표시
        decision = show_approval_dialog(event["__interrupt__"])
        # 다음 스트림에서 결정 전달
```

---

## CLI에서의 HITL

DeepAgents CLI는 기본적으로 HITL을 지원합니다:

```bash
$ deepagents

> Write a hello.py file

[Agent proposes to write file]
File: hello.py
Content:
```python
print("Hello, World!")
```

[Approve] [Edit] [Reject]
```

### Auto-Accept 모드

```bash
# 모든 변경 자동 승인 (주의!)
deepagents --auto-accept
```

---

## 장기 메모리 (Long-term Memory)

### 개요

장기 메모리는 대화 세션 간에 정보를 유지하는 기능입니다.

### 핵심 컴포넌트

| 컴포넌트 | 역할 |
|---------|------|
| `store` | LangGraph Store (데이터 저장소) |
| `StoreBackend` | Store를 파일시스템처럼 사용 |
| `CompositeBackend` | 경로별 백엔드 라우팅 |

---

## 장기 메모리 설정

### InMemoryStore (개발용)

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_deep_agent(
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),         # 기본: 임시 저장
        routes={
            "/memories/": StoreBackend(rt)  # /memories/: 영속 저장
        }
    ),
    system_prompt="""
    Save important information to /memories/:
    - User preferences → /memories/user_prefs.md
    - Project context → /memories/project.md

    Working files stay in root (temporary):
    - Research → /research.md
    - Drafts → /draft.md
    """
)
```

### PostgresStore (프로덕션)

```python
from langgraph.store.postgres import PostgresStore
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

store = PostgresStore(
    connection_string="postgresql://user:pass@host:5432/db"
)

agent = create_deep_agent(
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}
    )
)
```

---

## 메모리 패턴

### Memory-First Protocol

CLI에서 사용하는 패턴입니다:

```
~/.deepagents/
└── agent-name/
    └── memories/
        ├── project-overview.md    # 프로젝트 개요
        ├── api-patterns.md        # API 패턴
        ├── user-preferences.md    # 사용자 선호
        └── lessons-learned.md     # 학습된 교훈
```

### 시스템 프롬프트 예시

```python
system_prompt = """
## Memory Management

### Read First
At the start of each task, check /memories/ for relevant context:
- read_file("/memories/project.md")
- read_file("/memories/user_prefs.md")

### Save Important Info
Store valuable information for future conversations:
- User preferences → /memories/user_prefs.md
- Project knowledge → /memories/project.md
- API patterns → /memories/api_patterns.md
- Lessons learned → /memories/lessons.md

### Working Files (Temporary)
Keep task-specific files in root:
- /research.md - Current research
- /draft.md - Work in progress
- /todos.md - Task list
"""
```

---

## 메모리 조직

### 권장 구조

```
/memories/
├── context/
│   ├── project.md           # 프로젝트 개요
│   ├── architecture.md      # 아키텍처 결정
│   └── conventions.md       # 코딩 규칙
├── knowledge/
│   ├── api_patterns.md      # API 패턴
│   ├── troubleshooting.md   # 문제 해결 기록
│   └── best_practices.md    # 모범 사례
└── preferences/
    ├── user_prefs.md        # 사용자 선호
    └── communication.md     # 커뮤니케이션 스타일
```

### 파일명 규칙

- 설명적인 이름 사용: `api-patterns.md` (O), `notes.md` (X)
- 주제별 분류: `/memories/knowledge/` 하위에 관련 파일
- 날짜 포함 (선택): `2025-01-decision-log.md`

---

## HITL + 장기 메모리 조합

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
checkpointer = MemorySaver()

agent = create_deep_agent(
    # 상태 영속화 (HITL용)
    checkpointer=checkpointer,

    # 장기 메모리
    store=store,
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}
    ),

    # HITL 설정
    interrupt_on={
        "execute": True,
        "write_file": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    },

    system_prompt="""
    You have access to persistent memory in /memories/.
    Read relevant context before starting tasks.
    Save important discoveries for future sessions.

    File writes require user approval.
    Shell commands require user approval.
    """
)
```

---

## Checkpointer 옵션

### MemorySaver (개발용)

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
```

### SqliteSaver (로컬 영속)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("./checkpoints.db")
```

### PostgresSaver (프로덕션)

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@host:5432/db"
)
```

---

## 보안 고려사항

### HITL 권장 도구

| 도구 | HITL 권장 | 이유 |
|-----|----------|------|
| `execute` | **필수** | 임의 코드 실행 |
| `write_file` | 권장 | 파일 시스템 변경 |
| `edit_file` | 권장 | 파일 수정 |
| `read_file` | 선택 | 민감 파일 접근 시 |

### 프로덕션 체크리스트

- [ ] HITL 활성화 (`interrupt_on`)
- [ ] 샌드박스 백엔드 사용 (Runloop, Daytona, Modal)
- [ ] PostgresStore로 영속 메모리
- [ ] PostgresSaver로 체크포인트 영속화
- [ ] API 키 환경변수로 관리

---

## 트러블슈팅

### HITL이 작동하지 않음

```python
# 문제: interrupt_on 설정했는데 인터럽트 없음
# 해결: checkpointer 필수!

agent = create_deep_agent(
    checkpointer=MemorySaver(),  # ← 필수!
    interrupt_on={"execute": True}
)
```

### 메모리가 유지되지 않음

```python
# 문제: 세션 간 메모리 손실
# 해결: StoreBackend + CompositeBackend 사용

agent = create_deep_agent(
    store=store,  # ← store 필수!
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}  # ← 경로 라우팅
    )
)
```

### 인터럽트 후 재개 실패

```python
# 문제: 인터럽트 후 재개 시 상태 손실
# 해결: 동일한 thread_id 사용

config = {"configurable": {"thread_id": "my-thread"}}
result = agent.invoke({"messages": [...]}, config=config)

# 재개 시 동일한 config 사용
agent.invoke({"messages": []}, config=config)
```

---

## 참고 자료

- [LangGraph Human-in-the-Loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [DeepAgents CLI](https://blog.langchain.com/introducing-deepagents-cli/)
