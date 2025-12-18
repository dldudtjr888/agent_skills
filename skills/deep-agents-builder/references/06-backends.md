# Deep Agents 백엔드 옵션

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
| **Virtual** | 로컬 | X | X | 개발/테스트 |
| **Runloop** | 원격 | O | O | 프로덕션 |
| **Daytona** | 원격 | O | O | 프로덕션 |
| **Modal** | 원격 | O | O | 프로덕션 |

---

## Virtual Backend (기본)

개발 및 테스트용 가상 파일시스템입니다.

```python
from deepagents import create_deep_agent

# 기본적으로 Virtual 백엔드 사용
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514"
)

# 특징:
# - LangGraph 상태에 파일 저장
# - 세션 종료 시 데이터 손실
# - 샌드박스 없음 (execute 도구 주의)
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
    # 추가 설정...
)

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    backend=backend
)
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

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    backend=backend
)
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

backend = ModalBackend(
    # Modal 설정...
)

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    backend=backend
)
```

### 특징

- 서버리스 스케일링
- GPU 지원
- 비용 효율적
- 빠른 콜드 스타트

---

## 커스텀 백엔드 구현

Backend 추상화를 확장하여 커스텀 백엔드를 만들 수 있습니다.

```python
from deepagents.backends.base import Backend

class MyCustomBackend(Backend):
    def read_file(self, path: str) -> str:
        """파일 읽기 구현"""
        pass

    def write_file(self, path: str, content: str) -> None:
        """파일 쓰기 구현"""
        pass

    def list_dir(self, path: str) -> list[str]:
        """디렉토리 목록 구현"""
        pass

    def execute(self, command: str) -> str:
        """셸 명령 실행 구현"""
        pass

    # 기타 메서드...

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    backend=MyCustomBackend()
)
```

---

## 백엔드 선택 가이드

### 개발/테스트

```python
# Virtual 백엔드 (기본)
agent = create_deep_agent(model="...")
```

### 프로덕션

```python
# 샌드박스 백엔드 사용 권장
# execute 도구로 임의 코드 실행 가능하므로 격리 필수

from deepagents.backends.runloop import RunloopBackend
agent = create_deep_agent(
    model="...",
    backend=RunloopBackend(api_key="...")
)
```

### 선택 기준

| 요구사항 | 권장 백엔드 |
|---------|------------|
| 빠른 프로토타이핑 | Virtual |
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
