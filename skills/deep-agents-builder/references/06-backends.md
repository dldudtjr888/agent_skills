# Deep Agents 백엔드 옵션

> **최종 업데이트**: 2025-12-24 (deepagents 0.2+)

백엔드는 에이전트의 **파일시스템 저장소**를 제공합니다.
프로덕션 환경에서는 **샌드박스 백엔드**를 사용하여 코드 실행을 안전하게 격리합니다.

---

## Backend 추상화

Deep Agents 0.2부터 **플러그인 백엔드**를 지원합니다.

### 이전 방식 (Virtual Filesystem)

```python
# 기존: LangGraph 상태를 "가상 파일시스템"으로 사용
# → 상태 기반, 세션 종료 시 데이터 손실
```

### 새로운 방식 (Backend 추상화)

```python
# 현재: 다양한 저장소를 파일시스템으로 플러그인
# → 영속성, 샌드박스 지원, 원격 실행
```

---

## 사용 가능한 백엔드

| 백엔드 | 유형 | 영속성 | 샌드박스 | 용도 |
|--------|------|--------|----------|------|
| **StateBackend** | 로컬 | X | X | 개발/테스트 (기본) |
| **FilesystemBackend** | 로컬 | O | X | 로컬 디스크 |
| **StoreBackend** | 원격 | O | X | LangGraph Store (장기 메모리) |
| **CompositeBackend** | 하이브리드 | - | - | 경로별 라우팅 |
| **Runloop** | 원격 | O | O | 프로덕션 샌드박스 |
| **Daytona** | 원격 | O | O | 프로덕션 개발 환경 |
| **Modal** | 원격 | O | O | 서버리스 GPU |

---

## StateBackend (기본)

개발 및 테스트용 임시 파일시스템입니다.

```python
from deepagents import create_deep_agent

# 기본적으로 StateBackend 사용
agent = create_deep_agent()

# 특징:
# - LangGraph 상태에 파일 저장
# - 세션 종료 시 데이터 손실
# - 샌드박스 없음 (execute 도구 주의)
```

---

## FilesystemBackend

로컬 디스크에 파일을 저장합니다.

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(root_dir="/path/to/project")

agent = create_deep_agent(backend=backend)

# 특징:
# - 실제 디스크 파일 작업
# - 프로젝트 디렉토리 제한
# - 세션 간 영속성
```

---

## StoreBackend

LangGraph Store를 사용하여 영속 저장소를 제공합니다.

```python
from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.store.memory import InMemoryStore
# 프로덕션: from langgraph.store.postgres import PostgresStore

store = InMemoryStore()

agent = create_deep_agent(
    store=store,
    backend=lambda rt: StoreBackend(rt)
)

# 특징:
# - 대화 간 영속성
# - InMemoryStore, PostgresStore 등 지원
# - 장기 메모리에 적합
```

### PostgresStore 사용 (프로덕션)

```python
from langgraph.store.postgres import PostgresStore
from deepagents import create_deep_agent
from deepagents.backends import StoreBackend

store = PostgresStore(
    connection_string="postgresql://user:pass@host:5432/db"
)

agent = create_deep_agent(
    store=store,
    backend=lambda rt: StoreBackend(rt)
)
```

---

## CompositeBackend

경로별로 다른 백엔드를 라우팅합니다.

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
    )
)

# 사용 예:
# write_file("/notes.md", ...)         → StateBackend (임시)
# write_file("/memories/prefs.md", ...)  → StoreBackend (영속)
```

### 장기 메모리 패턴

```python
# 에이전트가 자동으로:
# 1. /memories/ 에 중요 정보 저장 → 영속
# 2. 작업 파일은 / 에 저장 → 임시

# 시스템 프롬프트:
system_prompt = """
Save important information to /memories/:
- User preferences → /memories/user_prefs.md
- Project knowledge → /memories/project_context.md
- API patterns → /memories/api_patterns.md

Working files stay in root:
- Research results → /research.md
- Draft reports → /draft.md
"""
```

---

## Runloop Backend

**Runloop**은 AI 에이전트를 위한 원격 샌드박스 환경을 제공합니다.

### 설정

```bash
pip install runloop
export RUNLOOP_API_KEY="your-key"
```

### 사용

```python
from deepagents import create_deep_agent
from deepagents.backends.runloop import RunloopBackend

backend = RunloopBackend(
    api_key="your-runloop-api-key",
)

agent = create_deep_agent(backend=backend)
```

### 특징

- 격리된 컨테이너 환경
- 파일 영속성
- 안전한 코드 실행
- 자동 정리

---

## Daytona Backend

**Daytona**는 개발 환경 관리 플랫폼입니다.

### 설정

```bash
pip install daytona-sdk
export DAYTONA_API_KEY="your-key"
```

### 사용

```python
from deepagents import create_deep_agent
from deepagents.backends.daytona import DaytonaBackend

backend = DaytonaBackend(
    api_key="your-daytona-api-key",
    workspace_id="your-workspace-id"
)

agent = create_deep_agent(backend=backend)
```

### 특징

- 완전한 개발 환경
- Git 통합
- 언어별 런타임 지원
- 팀 협업

---

## Modal Backend

**Modal**은 서버리스 컴퓨팅 플랫폼입니다.

### 설정

```bash
pip install modal
modal token new
```

### 사용

```python
from deepagents import create_deep_agent
from deepagents.backends.modal import ModalBackend

backend = ModalBackend()

agent = create_deep_agent(backend=backend)
```

### 특징

- 서버리스 스케일링
- GPU 지원
- 비용 효율적
- 빠른 콜드 스타트

---

## 커스텀 백엔드 구현

Backend 추상화를 확장하여 커스텀 백엔드를 만들 수 있습니다.

### BackendProtocol

```python
from deepagents.backends.base import BackendProtocol

class MyCustomBackend(BackendProtocol):
    def read_file(self, path: str) -> str:
        """파일 읽기 구현"""
        pass

    def write_file(self, path: str, content: str) -> None:
        """파일 쓰기 구현"""
        pass

    def list_dir(self, path: str) -> list[str]:
        """디렉토리 목록 구현"""
        pass

    def edit_file(self, path: str, old: str, new: str) -> None:
        """파일 편집 구현"""
        pass

    def glob(self, pattern: str) -> list[str]:
        """glob 패턴 매칭"""
        pass

    def grep(self, pattern: str, path: str) -> list[str]:
        """텍스트 검색"""
        pass
```

### SandboxBackendProtocol

`execute` 도구를 활성화하려면 이 프로토콜도 구현합니다:

```python
from deepagents.backends.base import SandboxBackendProtocol

class MySandboxBackend(SandboxBackendProtocol):
    # BackendProtocol 메서드 +
    def execute(self, command: str) -> str:
        """셸 명령 실행 구현"""
        pass
```

### 사용

```python
agent = create_deep_agent(backend=MyCustomBackend())
```

---

## 백엔드 선택 가이드

### 개발/테스트

```python
# StateBackend (기본)
agent = create_deep_agent()
```

### 로컬 프로젝트 작업

```python
from deepagents.backends import FilesystemBackend
agent = create_deep_agent(backend=FilesystemBackend(root_dir="./project"))
```

### 장기 메모리 필요

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
```

### 프로덕션 (안전한 코드 실행)

```python
from deepagents.backends.runloop import RunloopBackend
agent = create_deep_agent(backend=RunloopBackend(api_key="..."))
```

### 선택 기준

| 요구사항 | 권장 백엔드 |
|---------|------------|
| 빠른 프로토타이핑 | StateBackend (기본) |
| 로컬 파일 작업 | FilesystemBackend |
| 대화 간 메모리 | StoreBackend + CompositeBackend |
| 안전한 코드 실행 | Runloop, Daytona, Modal |
| GPU 필요 | Modal |
| 개발 환경 통합 | Daytona |
| 간단한 샌드박스 | Runloop |

---

## 참고 자료

- [Sandboxes for Deep Agents](https://changelog.langchain.com/announcements/sandboxes-for-deep-agents)
- [Runloop](https://runloop.ai/)
- [Daytona](https://daytona.io/)
- [Modal](https://modal.com/)

---

## 다음 단계

- [08-hitl-memory.md](08-hitl-memory.md): Human-in-the-Loop 및 장기 메모리 상세
