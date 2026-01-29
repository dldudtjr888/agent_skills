# Agent Types (에이전트 유형)

> 메인 스킬: `../SKILL.md`

ADK는 4가지 에이전트 유형을 제공한다. LLM 기반 에이전트(LlmAgent)와 3가지 워크플로우 에이전트(Sequential, Parallel, Loop), 그리고 커스텀 에이전트(BaseAgent)를 지원한다.

---

## LlmAgent (기본 에이전트)

LLM을 사용하여 추론, 도구 선택, 응답 생성을 수행하는 핵심 에이전트.
`Agent`는 `LlmAgent`의 별칭이다.

### 주요 파라미터

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `name` | Yes | 고유 식별자 (snake_case) |
| `model` | No* | LLM 모델 문자열 (v1.21+ 선택, 부모 에이전트로부터 상속 가능) |
| `instruction` | No | 시스템 프롬프트. `{var}`로 state 참조 가능 |
| `description` | No | sub_agent/tool 사용 시 필수 (LLM이 위임 판단에 사용) |
| `tools` | No | 도구 리스트 (함수, BaseTool, 에이전트) |
| `sub_agents` | No | 하위 에이전트 리스트 (LLM 기반 위임) |
| `output_key` | No | 응답을 session.state에 자동 저장할 키 |
| `input_schema` | No | Pydantic 모델 (구조화된 입력 검증) |
| `output_schema` | No | Pydantic 모델 (구조화된 출력 강제) |
| `generate_content_config` | No | 모델 설정 (temperature, safety 등) |

> **No***: v1.21+에서 `model`은 선택 사항. 부모 에이전트가 설정한 모델을 자동 상속한다. root_agent에서는 반드시 지정해야 한다.

### 기본 예제

```python
from google.adk.agents import Agent

root_agent = Agent(
    name="weather_assistant",
    model="gemini-2.0-flash",
    description="날씨 정보를 제공하는 어시스턴트",
    instruction="""당신은 날씨 정보 전문가입니다.
사용자가 날씨를 물으면 get_weather 도구를 사용하세요.
현재 사용자: {user_name}""",
    tools=[get_weather],
    output_key="weather_result",
)
```

### instruction 템플릿

instruction에서 `{key}` 형식으로 session.state 값을 참조할 수 있다:

```python
# session.state["user_name"] = "홍길동" 이면
# instruction에서 {user_name} -> "홍길동"으로 치환

agent = Agent(
    name="greeter",
    model="gemini-2.0-flash",
    instruction="사용자 {user_name}님에게 인사하세요. 선호 언어: {user:language}",
)
```

### 구조화된 출력

```python
from pydantic import BaseModel

class WeatherReport(BaseModel):
    city: str
    temperature: float
    condition: str
    summary: str

agent = Agent(
    name="structured_weather",
    model="gemini-2.0-flash",
    instruction="날씨 정보를 구조화된 형태로 제공하세요.",
    output_schema=WeatherReport,
)
```

---

## SequentialAgent (순차 에이전트)

서브 에이전트를 순서대로 실행한다. 에이전트 간 데이터 전달은 `output_key` -> `session.state`를 통해 이루어진다.

### 파라미터

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `name` | Yes | 고유 식별자 |
| `sub_agents` | Yes | 순차 실행할 에이전트 리스트 |
| `description` | No | 설명 |

### 예제: 리서치 파이프라인

```python
from google.adk.agents import Agent, SequentialAgent

researcher = Agent(
    name="researcher",
    model="gemini-2.0-flash",
    instruction="주제 '{topic}'에 대해 조사하세요.",
    output_key="research_data",
)

writer = Agent(
    name="writer",
    model="gemini-2.0-flash",
    instruction="조사 결과를 바탕으로 보고서를 작성하세요: {research_data}",
    output_key="final_report",
)

root_agent = SequentialAgent(
    name="research_pipeline",
    sub_agents=[researcher, writer],
)
```

### 데이터 흐름

```
researcher (output_key="research_data")
    -> session.state["research_data"] = "조사 결과..."
        -> writer (instruction에서 {research_data} 참조)
            -> session.state["final_report"] = "최종 보고서..."
```

---

## ParallelAgent (병렬 에이전트)

서브 에이전트를 동시에 실행한다. 각 에이전트는 독립적으로 실행되므로 고유한 `output_key`를 사용해야 한다.

### 파라미터

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `name` | Yes | 고유 식별자 |
| `sub_agents` | Yes | 병렬 실행할 에이전트 리스트 |
| `description` | No | 설명 |

### 예제: 멀티소스 검색

```python
from google.adk.agents import Agent, ParallelAgent

flight_agent = Agent(
    name="flight_finder",
    model="gemini-2.0-flash",
    instruction="{destination}행 항공편을 검색하세요.",
    output_key="flights",
)

hotel_agent = Agent(
    name="hotel_finder",
    model="gemini-2.0-flash",
    instruction="{destination}의 호텔을 검색하세요.",
    output_key="hotels",
)

root_agent = ParallelAgent(
    name="travel_search",
    sub_agents=[flight_agent, hotel_agent],
)
```

### 주의사항
- 각 sub_agent의 `output_key`는 반드시 고유해야 한다 (충돌 방지)
- 병렬 에이전트는 서로의 결과에 의존하지 않아야 한다
- 결과 종합이 필요하면 SequentialAgent로 감싸서 aggregator를 추가한다

---

## LoopAgent (반복 에이전트)

서브 에이전트를 반복 실행한다. `max_iterations` 또는 `escalate` 시그널로 종료한다.

### 파라미터

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `name` | Yes | 고유 식별자 |
| `sub_agents` | Yes | 반복 실행할 에이전트 리스트 |
| `max_iterations` | No | 최대 반복 횟수 (안전장치, 반드시 설정 권장) |

### 예제: 코드 생성 + 리뷰 루프

```python
from google.adk.agents import Agent, LoopAgent, SequentialAgent

generator = Agent(
    name="code_generator",
    model="gemini-2.0-flash",
    instruction="요구사항에 맞는 코드를 작성하세요: {requirement}",
    output_key="code_draft",
)

reviewer = Agent(
    name="code_reviewer",
    model="gemini-2.0-flash",
    instruction="""코드를 리뷰하세요: {code_draft}
품질이 충분하면 escalate하여 루프를 종료하세요.
개선이 필요하면 피드백을 제공하세요.""",
    output_key="review_feedback",
)

root_agent = LoopAgent(
    name="code_refinement",
    max_iterations=5,
    sub_agents=[
        SequentialAgent(
            name="generate_and_review",
            sub_agents=[generator, reviewer],
        ),
    ],
)
```

### 루프 종료 방법
1. `max_iterations` 도달
2. 에이전트가 `escalate` 시그널 전송 (instruction에서 "escalate" 키워드 사용 유도)
3. `EventActions`에서 `escalate=True` 설정 (콜백 사용)

---

## Custom Agent (BaseAgent 확장)

임의의 오케스트레이션 로직이 필요한 경우 `BaseAgent`를 상속한다.

### 예제: 조건부 라우팅

```python
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai.types import Content, Part

class ConditionalRouter(BaseAgent):
    """입력 조건에 따라 다른 에이전트를 실행하는 커스텀 에이전트."""

    simple_agent: LlmAgent
    complex_agent: LlmAgent
    complexity_threshold: int = 100

    async def _run_async_impl(self, ctx: InvocationContext):
        user_msg = ctx.session.events[-1].content.parts[0].text
        if len(user_msg) > self.complexity_threshold:
            target = self.complex_agent
        else:
            target = self.simple_agent

        async for event in target.run_async(ctx):
            yield event
```

### 사용 시점
- 워크플로우 에이전트(Sequential/Parallel/Loop)로 표현할 수 없는 복잡한 조건 분기
- 동적 에이전트 선택 (런타임 조건에 따라)
- 커스텀 상태 머신 구현

---

## 에이전트 유형 선택 가이드

| 요구사항 | 에이전트 유형 | 예시 |
|----------|-------------|------|
| 단일 LLM 작업 | `Agent` (LlmAgent) | 챗봇, Q&A |
| 순차 처리 파이프라인 | `SequentialAgent` | 조사 -> 분석 -> 작성 |
| 독립 작업 병렬 실행 | `ParallelAgent` | 동시 검색, 멀티소스 수집 |
| 반복 개선 | `LoopAgent` | 생성 -> 리뷰 -> 수정 |
| 복잡한 조건 분기 | Custom (`BaseAgent`) | 동적 라우팅, 상태 머신 |
| LLM 기반 자동 위임 | `Agent` + `sub_agents` | 전문가 팀 오케스트레이션 |
| 병렬 수집 + 종합 | `SequentialAgent`[`ParallelAgent`, `Agent`] | Fan-Out/Gather |
