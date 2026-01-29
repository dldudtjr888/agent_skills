# Multi-Agent Patterns (멀티에이전트 패턴)

> 메인 스킬: `../SKILL.md`
> 에이전트 유형: `agent-types.md`

멀티에이전트 시스템의 오케스트레이션 패턴. 계층적 위임, Fan-Out/Gather, 반복 개선, 파이프라인 패턴을 다룬다.

---

## Pattern 1: Hierarchical Delegation (계층적 위임)

root_agent가 LLM을 사용하여 요청을 분석하고, 적절한 sub_agent에게 위임한다.

### 구조

```
root_agent (orchestrator)
├── billing_agent
├── tech_support_agent
└── general_agent
```

### 코드

```python
from google.adk.agents import Agent

billing_agent = Agent(
    name="billing_specialist",
    model="gemini-2.0-flash",
    description="결제, 환불, 구독 관련 문의를 처리합니다.",
    instruction="결제 관련 문의에 정확하게 답변하세요.",
    tools=[check_payment, process_refund],
)

tech_support_agent = Agent(
    name="tech_support",
    model="gemini-2.0-flash",
    description="기술적 문제, 오류, 설정 관련 문의를 처리합니다.",
    instruction="기술 문제를 진단하고 해결 방법을 안내하세요.",
    tools=[check_system_status, run_diagnostics],
)

general_agent = Agent(
    name="general_assistant",
    model="gemini-2.0-flash",
    description="일반적인 질문과 안내를 처리합니다.",
    instruction="일반적인 질문에 친절하게 답변하세요.",
)

root_agent = Agent(
    name="customer_service",
    model="gemini-2.0-flash",
    instruction="""고객 문의를 분석하여 적절한 전문 에이전트에게 위임하세요.
- 결제/환불 관련 -> billing_specialist
- 기술 문제 -> tech_support
- 기타 -> general_assistant""",
    sub_agents=[billing_agent, tech_support_agent, general_agent],
)
```

### 핵심 규칙
- 각 sub_agent의 `description`을 반드시 작성 (root_agent가 위임 판단에 사용)
- root_agent의 `instruction`에 위임 조건을 명시
- sub_agent는 독립적으로 동작할 수 있어야 한다

---

## Pattern 2: Fan-Out / Gather (병렬 수집 + 종합)

여러 에이전트가 동시에 정보를 수집하고, 결과를 하나의 에이전트가 종합한다.

### 구조

```
SequentialAgent (pipeline)
├── ParallelAgent (fan_out)
│   ├── flight_finder (output_key="flights")
│   ├── hotel_finder (output_key="hotels")
│   └── activity_finder (output_key="activities")
└── Agent (aggregator, reads flights/hotels/activities)
```

### 코드

```python
from google.adk.agents import Agent, SequentialAgent, ParallelAgent

flight_finder = Agent(
    name="flight_finder",
    model="gemini-2.0-flash",
    instruction="{destination}행 항공편을 검색하세요.",
    tools=[search_flights],
    output_key="flights",
)

hotel_finder = Agent(
    name="hotel_finder",
    model="gemini-2.0-flash",
    instruction="{destination}의 호텔을 검색하세요.",
    tools=[search_hotels],
    output_key="hotels",
)

activity_finder = Agent(
    name="activity_finder",
    model="gemini-2.0-flash",
    instruction="{destination}의 관광 활동을 검색하세요.",
    tools=[search_activities],
    output_key="activities",
)

aggregator = Agent(
    name="trip_planner",
    model="gemini-2.0-flash",
    instruction="""다음 정보를 종합하여 여행 계획을 작성하세요:
- 항공편: {flights}
- 호텔: {hotels}
- 활동: {activities}""",
    output_key="trip_plan",
)

root_agent = SequentialAgent(
    name="travel_pipeline",
    sub_agents=[
        ParallelAgent(
            name="info_collector",
            sub_agents=[flight_finder, hotel_finder, activity_finder],
        ),
        aggregator,
    ],
)
```

### 핵심 규칙
- ParallelAgent의 각 에이전트는 고유한 `output_key` 사용
- aggregator의 instruction에서 `{key}` 형식으로 수집된 데이터 참조
- 병렬 에이전트는 서로 독립적이어야 한다 (의존성 없음)

---

## Pattern 3: Iterative Refinement (반복 개선)

생성 -> 비평 -> 수정 루프를 통해 결과 품질을 개선한다.

### 구조

```
LoopAgent (max_iterations=5)
└── SequentialAgent
    ├── Agent (generator)
    └── Agent (critic)  -- escalate로 루프 종료
```

### 코드

```python
from google.adk.agents import Agent, LoopAgent, SequentialAgent

generator = Agent(
    name="sql_generator",
    model="gemini-2.0-flash",
    instruction="""요구사항에 맞는 SQL 쿼리를 작성하세요: {requirement}
이전 피드백이 있다면 반영하세요: {review_feedback}""",
    output_key="sql_draft",
)

critic = Agent(
    name="sql_reviewer",
    model="gemini-2.0-flash",
    instruction="""SQL 쿼리를 리뷰하세요: {sql_draft}

검증 항목:
1. 문법 정확성
2. 성능 (인덱스 활용)
3. SQL Injection 방지
4. 결과 정확성

품질이 충분하면 "APPROVED"를 응답하고 escalate하세요.
개선이 필요하면 구체적인 피드백을 제공하세요.""",
    output_key="review_feedback",
)

root_agent = LoopAgent(
    name="sql_refinement",
    max_iterations=5,
    sub_agents=[
        SequentialAgent(
            name="generate_and_review",
            sub_agents=[generator, critic],
        ),
    ],
)
```

### 핵심 규칙
- `max_iterations` 반드시 설정 (무한 루프 방지)
- critic의 instruction에 명확한 종료 조건 명시
- generator는 이전 피드백(`review_feedback`)을 참조하도록 설계

---

## Pattern 4: Pipeline (순차 파이프라인)

단계별로 데이터를 가공하는 ETL 스타일 파이프라인.

### 코드

```python
from google.adk.agents import Agent, SequentialAgent

extractor = Agent(
    name="data_extractor",
    model="gemini-2.0-flash",
    instruction="원본 데이터에서 핵심 정보를 추출하세요: {raw_input}",
    output_key="extracted_data",
)

transformer = Agent(
    name="data_transformer",
    model="gemini-2.0-flash",
    instruction="추출된 데이터를 분석하고 구조화하세요: {extracted_data}",
    output_key="transformed_data",
)

reporter = Agent(
    name="report_generator",
    model="gemini-2.0-flash",
    instruction="분석 결과를 보고서로 작성하세요: {transformed_data}",
    output_key="final_report",
)

root_agent = SequentialAgent(
    name="etl_pipeline",
    sub_agents=[extractor, transformer, reporter],
)
```

---

## 데이터 전달 패턴

### output_key -> session.state -> instruction {key}

에이전트 간 데이터 전달의 기본 메커니즘:

```python
# Agent A: 결과를 state에 저장
agent_a = Agent(
    name="agent_a",
    output_key="result_a",  # -> session.state["result_a"] = "에이전트 A의 결과"
    ...
)

# Agent B: state에서 읽기
agent_b = Agent(
    name="agent_b",
    instruction="Agent A의 결과를 참고하세요: {result_a}",
    ...
)
```

### tool_context.state (도구 내 state 접근)

```python
def process_data(data: str, tool_context: ToolContext) -> dict:
    """데이터를 처리합니다.

    Args:
        data: 처리할 원본 데이터
    """
    # 다른 에이전트가 저장한 결과 읽기
    previous = tool_context.state.get("previous_result", "")

    result = f"processed: {data} + {previous}"
    tool_context.state["processed_data"] = result
    return {"result": result}
```

---

## 에이전트 전환 메커니즘

### transfer_to_agent (대등한 전환)

현재 에이전트에서 다른 에이전트로 대화 제어권을 넘긴다 (peer handoff):

```python
# sub_agents로 등록된 에이전트 간 전환
# LLM이 instruction을 기반으로 자동 전환
root_agent = Agent(
    name="router",
    model="gemini-2.0-flash",
    instruction="한국어 질문은 korean_agent에게, 영어 질문은 english_agent에게 전환하세요.",
    sub_agents=[korean_agent, english_agent],
)
```

### escalate_to_agent (상위 복귀)

하위 에이전트가 상위 에이전트로 제어권을 반환한다:

```python
# LoopAgent에서 탈출할 때 주로 사용
critic = Agent(
    name="critic",
    instruction="""... 품질이 충분하면 escalate하세요.""",
    # LLM이 "escalate"를 이해하고 EventActions.escalate=True를 설정
)
```

### 전환 선택 기준

| 상황 | 메커니즘 |
|------|---------|
| 전문가에게 질문 위임 | `sub_agents` + transfer |
| 루프 종료 | `escalate` |
| 일회성 계산/조회 | Agent-as-Tool (`tools`) |
| 조건부 라우팅 | Custom Agent (`BaseAgent`) |
