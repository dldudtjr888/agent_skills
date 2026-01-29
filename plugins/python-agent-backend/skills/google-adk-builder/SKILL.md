---
name: google-adk-builder
description: "Google ADK(Agent Development Kit) 기반 AI 에이전트/멀티에이전트 시스템 구축 스킬. 프로젝트 셋업, 에이전트 정의, 도구 통합, 상태 관리, 멀티에이전트 오케스트레이션, 테스트, 배포를 가이드한다."
version: 1.0.0
category: framework
user-invocable: true
triggers:
  keywords: [google-adk, adk, agent development kit, google agent, 구글 에이전트, LlmAgent, SequentialAgent, ParallelAgent, LoopAgent, adk web, adk run, adk eval, google_search, code_execution, MCPToolset, Agent-as-Tool, Vertex AI Agent Engine]
  intentPatterns:
    - "(만들|생성|작성|구현|빌드|build|create|implement).*(ADK|adk|Google.*agent|구글.*에이전트)"
    - "(ADK|adk|Google Agent).*(설정|setup|시작|start|초기화|init)"
    - "(멀티.*에이전트|multi.*agent).*(ADK|adk|Google)"
    - "(deploy|배포|테스트|test|평가|eval).*(ADK|adk)"
    - "(에이전트|agent).*(Google|구글|Gemini|gemini).*(프레임워크|framework)"
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, Task, TodoWrite, WebFetch, WebSearch]
---

# Google ADK Builder

Google ADK(Agent Development Kit)로 AI 에이전트 및 멀티에이전트 시스템을 구축하는 스킬.
단일 에이전트부터 복잡한 멀티에이전트 오케스트레이션까지 단계적으로 가이드한다.

> 공식 문서: https://google.github.io/adk-docs/
> GitHub: https://github.com/google/adk-python
> 설치: `pip install google-adk` (v1.23.0+)

**모듈 참조**:
- 에이전트 유형별 패턴 -> `modules/agent-types.md`
- 도구 통합 패턴 -> `modules/tool-patterns.md`
- 멀티에이전트 오케스트레이션 -> `modules/multi-agent-patterns.md`
- 상태 관리 & 세션 -> `modules/state-and-sessions.md`
- 테스트 & 배포 -> `modules/testing-and-deployment.md`
- API 빠른 참조 -> `references/api-quick-reference.md`
- 전체 예제 -> `references/complete-examples.md`

---

## 사용 시점

### When to Use
- Google ADK로 새 에이전트 프로젝트를 시작할 때
- 기존 ADK 프로젝트에 새 에이전트/도구를 추가할 때
- 단일 에이전트를 멀티에이전트 시스템으로 확장할 때
- ADK 에이전트에 MCP 도구, Google 내장 도구를 통합할 때
- adk eval로 에이전트 품질을 평가할 때
- Cloud Run 또는 Vertex AI에 에이전트를 배포할 때

### When NOT to Use
- OpenAI Agents SDK 기반 프로젝트 -> `agents-sdk-builder` 스킬 사용
- LangGraph 기반 에이전트 -> `langgraph-builder` 스킬 사용
- LangChain Deep Agents -> `deep-agents-builder` 스킬 사용
- 단순 LLM API 호출 (에이전트 프레임워크 불필요)
- 프론트엔드 전용 작업

---

## 워크플로우

### Phase 1: Plan (계획)

#### Step 1.1: 요구사항 분석
사용자의 에이전트 요구사항을 분석한다:
- 에이전트 목적과 역할 정의
- 필요한 도구 식별 (function tools, MCP, Google 내장)
- 단일 에이전트 vs 멀티에이전트 결정
- 상태 관리 요구사항 파악

#### Step 1.2: 프로젝트 구조 생성

```
my_project/
├── my_agent/
│   ├── __init__.py       # root_agent 익스포트 (필수)
│   ├── agent.py          # 에이전트 정의
│   ├── tools.py          # 도구 함수 (선택)
│   ├── prompt.py         # 프롬프트 문자열 (선택)
│   └── .env              # API 키
├── tests/
│   └── test_eval.json    # 평가 데이터셋
└── main.py               # 프로그래밍 방식 실행 (선택)
```

#### Step 1.3: 환경 설정

```bash
pip install google-adk
```

```bash
# .env (AI Studio 사용 시)
GOOGLE_API_KEY=your-api-key

# .env (Vertex AI 사용 시)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-central1
```

### Phase 2: Implement (구현)

#### Step 2.1: 기본 에이전트 정의

```python
# my_agent/agent.py
from google.adk.agents import Agent

root_agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="당신은 도움이 되는 어시스턴트입니다.",
    tools=[],
)
```

```python
# my_agent/__init__.py
from .agent import root_agent
```

#### Step 2.2: 도구 정의
상세 -> `modules/tool-patterns.md`

```python
# my_agent/tools.py
def get_weather(city: str) -> dict:
    """도시의 현재 날씨 정보를 조회합니다.

    Args:
        city: 날씨를 조회할 도시 이름 (예: "서울", "부산")

    Returns:
        날씨 정보 딕셔너리 (temp, condition)
    """
    return {"city": city, "temp": "20C", "condition": "sunny"}
```

#### Step 2.3: 프롬프트 분리

```python
# my_agent/prompt.py
SYSTEM_INSTRUCTION = """당신은 날씨 정보 전문 어시스턴트입니다.
사용자가 날씨를 물으면 get_weather 도구를 사용하세요.
항상 한국어로 응답하세요."""
```

#### Step 2.4: 멀티에이전트 구성 (필요 시)
상세 -> `modules/multi-agent-patterns.md`

```python
from google.adk.agents import Agent, SequentialAgent

researcher = Agent(name="researcher", model="gemini-2.0-flash",
                   instruction="주제를 조사하세요.", output_key="research")
writer = Agent(name="writer", model="gemini-2.0-flash",
               instruction="조사 결과({research})를 바탕으로 보고서를 작성하세요.")

root_agent = SequentialAgent(
    name="pipeline",
    sub_agents=[researcher, writer],
)
```

### Phase 3: Verify (검증)

#### Step 3.1: 로컬 실행

```bash
# 대화형 웹 UI (localhost:8000)
adk web my_agent

# CLI 실행
adk run my_agent
```

#### Step 3.2: 프로그래밍 방식 테스트

```python
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="test_user"
    )
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=Content(parts=[Part(text="서울 날씨 어때?")]),
    ):
        if event.content and event.content.parts:
            print(event.content.parts[0].text)

asyncio.run(main())
```

#### Step 3.3: adk eval 실행
상세 -> `modules/testing-and-deployment.md`

```bash
adk eval my_agent tests/test_eval.json
```

### Phase 4: Deploy (배포)
상세 -> `modules/testing-and-deployment.md`

| 옵션 | 명령어 / 방법 |
|------|--------------|
| 로컬 개발 | `adk web` / `adk run` |
| Cloud Run | Dockerfile + `gcloud run deploy` |
| Vertex AI | `agent_engines.create()` |
| Custom Server | FastAPI + Runner 래핑 |

---

## 핵심 규칙

### 프로젝트 구조
1. `__init__.py`에 반드시 `root_agent`를 익스포트해야 한다
2. 에이전트 디렉토리명은 Python 패키지 규칙 (snake_case, 하이픈 금지)
3. `.env` 파일은 에이전트 디렉토리 내부에 배치
4. 프롬프트는 `prompt.py`에 분리하여 유지보수성 확보

### 에이전트 정의
1. `name`은 고유하고 설명적으로 설정 (영문 snake_case 권장)
2. `instruction`은 명확하고 구체적으로 (역할, 행동 규칙, 제약 포함)
3. `description`은 sub_agent 또는 agent-as-tool일 때 반드시 작성
4. `output_key`로 에이전트 응답을 session.state에 자동 저장

### 도구 정의
1. 도구 함수에 반드시 docstring 작성 (LLM이 도구 선택에 사용)
2. Args 섹션에 각 파라미터 설명 포함
3. 반환값은 `dict` 또는 `str` 타입 권장
4. `ToolContext` 파라미터로 state 접근 가능

### 멀티에이전트
1. `SequentialAgent`: 순서가 중요한 파이프라인
2. `ParallelAgent`: 독립적 작업 병렬 실행
3. `LoopAgent`: 반복 개선 (max_iterations 필수)
4. `sub_agents`로 LLM 기반 위임, `tools`로 stateless 호출
5. `output_key` -> `session.state` -> 다음 에이전트 instruction `{key}`로 전달

### 상태 관리
1. `session.state["key"]` -> 세션 스코프 (기본)
2. `session.state["app:key"]` -> 앱 스코프 (모든 사용자)
3. `session.state["user:key"]` -> 사용자 스코프 (세션 간 유지)
4. 개발: `InMemoryRunner`, 프로덕션: `Runner` + `DatabaseSessionService`

---

## 안티패턴

### __init__.py 미설정

```python
# BAD: __init__.py가 비어있거나 root_agent 미익스포트
# -> adk web/run 실행 시 에이전트를 찾지 못함

# GOOD:
# __init__.py
from .agent import root_agent
```

### docstring 누락

```python
# BAD: LLM이 도구 용도를 모름
def get_weather(city: str) -> dict:
    return {"temp": "20C"}

# GOOD: 상세한 docstring
def get_weather(city: str) -> dict:
    """도시의 현재 날씨 정보를 조회합니다.

    Args:
        city: 날씨를 조회할 도시 이름

    Returns:
        날씨 정보 딕셔너리
    """
    return {"city": city, "temp": "20C"}
```

### 단일 에이전트 과부하

```python
# BAD: 모든 역할을 하나의 에이전트에 몰아넣기
root_agent = Agent(
    name="do_everything",
    instruction="검색, 분석, 코드 작성, 번역을 모두 수행하세요.",
    tools=[search, analyze, code, translate],
)

# GOOD: 역할별 분리 + 오케스트레이션
root_agent = Agent(
    name="orchestrator",
    instruction="요청을 분석하여 적절한 전문 에이전트에게 위임하세요.",
    sub_agents=[researcher, analyst, coder, translator],
)
```

### 글로벌 변수 상태 공유

```python
# BAD: 세션 간 오염 위험
shared_data = {}

# GOOD: session.state 사용
def save_result(result: str, tool_context: ToolContext) -> dict:
    tool_context.state["last_result"] = result
    return {"status": "saved"}
```

### ParallelAgent state key 충돌

```python
# BAD: 같은 output_key 사용 -> 결과 덮어쓰기
ParallelAgent(sub_agents=[
    Agent(name="a", output_key="result", ...),
    Agent(name="b", output_key="result", ...),  # 충돌!
])

# GOOD: 고유한 output_key
ParallelAgent(sub_agents=[
    Agent(name="a", output_key="result_a", ...),
    Agent(name="b", output_key="result_b", ...),
])
```

---

## 빠른 예제

### 최소 에이전트

```python
# hello_agent/__init__.py
from google.adk.agents import Agent

root_agent = Agent(
    name="hello",
    model="gemini-2.0-flash",
    instruction="친절한 한국어 어시스턴트입니다.",
)
```

```bash
adk web hello_agent  # http://localhost:8000
```

### 전체 예제
- 단일 에이전트 + 도구 -> `references/complete-examples.md` Section 1
- 멀티에이전트 파이프라인 -> `references/complete-examples.md` Section 2
- 반복 코드 리뷰 에이전트 -> `references/complete-examples.md` Section 3

---

## 모듈 인덱스

| # | 파일 | 설명 |
|---|------|------|
| 1 | `modules/agent-types.md` | LlmAgent, SequentialAgent, ParallelAgent, LoopAgent, Custom Agent |
| 2 | `modules/tool-patterns.md` | FunctionTool, MCP 도구, Google 내장, Agent-as-Tool |
| 3 | `modules/multi-agent-patterns.md` | 위임, Fan-Out/Gather, 반복 개선, Pipeline |
| 4 | `modules/state-and-sessions.md` | session.state 스코프, Runner, SessionService, Callbacks |
| 5 | `modules/testing-and-deployment.md` | adk eval, golden dataset, Cloud Run, Vertex AI |

| # | 파일 | 설명 |
|---|------|------|
| 1 | `references/api-quick-reference.md` | 핵심 클래스/메서드 빠른 참조 |
| 2 | `references/complete-examples.md` | 전체 작동 예제 (단일/멀티/고급) |
