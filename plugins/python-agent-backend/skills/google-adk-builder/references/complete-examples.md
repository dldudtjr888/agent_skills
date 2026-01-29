# Complete Examples (전체 예제)

> 메인 스킬: `../SKILL.md`

복사 가능한 전체 작동 예제. 단일 에이전트, 멀티에이전트, 고급 패턴을 다룬다.

---

## Example 1: 단일 에이전트 + 도구 (날씨 에이전트)

### 프로젝트 구조

```
weather_project/
├── weather_agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── tools.py
│   ├── prompt.py
│   └── .env
└── main.py
```

### weather_agent/.env

```
GOOGLE_API_KEY=your-api-key-here
```

### weather_agent/prompt.py

```python
SYSTEM_INSTRUCTION = """당신은 날씨 정보 전문 어시스턴트입니다.

## 역할
- 사용자가 날씨를 물으면 get_weather 도구를 사용하세요.
- 여러 도시를 물으면 각 도시별로 도구를 호출하세요.

## 응답 규칙
- 항상 한국어로 응답하세요.
- 온도는 섭씨(C)로 표시하세요.
- 날씨 상태에 맞는 옷차림을 추천하세요.
"""
```

### weather_agent/tools.py

```python
import random

def get_weather(city: str) -> dict:
    """도시의 현재 날씨 정보를 조회합니다.

    Args:
        city: 날씨를 조회할 도시 이름 (예: "서울", "부산", "제주")

    Returns:
        도시명, 온도, 날씨 상태, 습도가 포함된 딕셔너리
    """
    # 실제 구현에서는 날씨 API 호출
    weather_data = {
        "서울": {"temp": 22, "condition": "맑음", "humidity": 45},
        "부산": {"temp": 25, "condition": "구름 조금", "humidity": 60},
        "제주": {"temp": 27, "condition": "흐림", "humidity": 70},
    }

    data = weather_data.get(city, {
        "temp": random.randint(15, 30),
        "condition": "맑음",
        "humidity": random.randint(30, 80),
    })

    return {
        "city": city,
        "temperature": f"{data['temp']}C",
        "condition": data["condition"],
        "humidity": f"{data['humidity']}%",
    }


def get_forecast(city: str, days: int = 3) -> dict:
    """도시의 날씨 예보를 조회합니다.

    Args:
        city: 예보를 조회할 도시 이름
        days: 예보 일수 (기본 3일, 최대 7일)

    Returns:
        일별 날씨 예보 리스트
    """
    forecasts = []
    for i in range(min(days, 7)):
        forecasts.append({
            "day": f"Day {i+1}",
            "temp_high": random.randint(20, 32),
            "temp_low": random.randint(10, 20),
            "condition": random.choice(["맑음", "구름 조금", "흐림", "비"]),
        })
    return {"city": city, "forecasts": forecasts}
```

### weather_agent/agent.py

```python
from google.adk.agents import Agent
from .tools import get_weather, get_forecast
from .prompt import SYSTEM_INSTRUCTION

root_agent = Agent(
    name="weather_assistant",
    model="gemini-2.0-flash",
    description="날씨 정보를 제공하는 어시스턴트",
    instruction=SYSTEM_INSTRUCTION,
    tools=[get_weather, get_forecast],
)
```

### weather_agent/__init__.py

```python
from .agent import root_agent
```

### main.py

```python
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from weather_agent.agent import root_agent


async def chat(runner, user_id: str, session_id: str, message: str):
    """에이전트에 메시지를 보내고 응답을 출력한다."""
    print(f"\n[User] {message}")
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=Content(parts=[Part(text=message)]),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"[Agent] {part.text}")


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="weather_app")

    session = await runner.session_service.create_session(
        app_name="weather_app",
        user_id="demo_user",
    )

    await chat(runner, "demo_user", session.id, "서울 날씨 어때?")
    await chat(runner, "demo_user", session.id, "부산과 제주 날씨도 비교해줘")
    await chat(runner, "demo_user", session.id, "서울 3일 예보 알려줘")


if __name__ == "__main__":
    asyncio.run(main())
```

### 실행

```bash
# 웹 UI
adk web weather_agent

# CLI
adk run weather_agent

# 프로그래밍 방식
python main.py
```

---

## Example 2: 멀티에이전트 리서치 파이프라인

여러 소스에서 병렬로 정보를 수집하고, 종합 보고서를 작성하는 파이프라인.

### 프로젝트 구조

```
research_project/
├── research_agent/
│   ├── __init__.py
│   ├── agent.py
│   └── .env
└── main.py
```

### research_agent/agent.py

```python
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import google_search

# Phase 1: 병렬 정보 수집
web_researcher = Agent(
    name="web_researcher",
    model="gemini-2.0-flash",
    description="웹에서 최신 정보를 검색하는 연구원",
    instruction="""주제 '{topic}'에 대해 웹 검색을 수행하세요.
최신 뉴스, 트렌드, 주요 사실을 수집하세요.
결과를 요약하여 제공하세요.""",
    tools=[google_search],
    output_key="web_research",
)

academic_researcher = Agent(
    name="academic_researcher",
    model="gemini-2.0-flash",
    description="학술적 관점에서 주제를 분석하는 연구원",
    instruction="""주제 '{topic}'에 대해 학술적 관점에서 분석하세요.
이론적 배경, 주요 연구 결과, 전문가 의견을 정리하세요.""",
    output_key="academic_research",
)

market_analyst = Agent(
    name="market_analyst",
    model="gemini-2.0-flash",
    description="시장 동향과 비즈니스 관점을 분석하는 분석가",
    instruction="""주제 '{topic}'에 대해 시장/비즈니스 관점에서 분석하세요.
시장 규모, 주요 기업, 성장 전망을 정리하세요.""",
    output_key="market_analysis",
)

# Phase 2: 보고서 작성
report_writer = Agent(
    name="report_writer",
    model="gemini-2.0-flash",
    description="수집된 정보를 종합하여 보고서를 작성하는 작가",
    instruction="""다음 자료를 종합하여 전문적인 보고서를 작성하세요:

## 웹 리서치
{web_research}

## 학술 분석
{academic_research}

## 시장 분석
{market_analysis}

보고서 형식:
1. 요약 (Executive Summary)
2. 현황 분석
3. 주요 발견사항
4. 전망 및 시사점
5. 결론""",
    output_key="final_report",
)

# 파이프라인 조합
root_agent = SequentialAgent(
    name="research_pipeline",
    sub_agents=[
        ParallelAgent(
            name="parallel_research",
            sub_agents=[web_researcher, academic_researcher, market_analyst],
        ),
        report_writer,
    ],
)
```

### research_agent/__init__.py

```python
from .agent import root_agent
```

### main.py

```python
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from research_agent.agent import root_agent


async def run_research(topic: str):
    runner = InMemoryRunner(agent=root_agent, app_name="research_app")

    session = await runner.session_service.create_session(
        app_name="research_app",
        user_id="researcher",
        state={"topic": topic},  # 초기 state에 주제 설정
    )

    print(f"Researching: {topic}\n")
    async for event in runner.run_async(
        user_id="researcher",
        session_id=session.id,
        new_message=Content(parts=[Part(text=f"{topic}에 대해 조사해줘")]),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)


if __name__ == "__main__":
    asyncio.run(run_research("2026년 AI 에이전트 시장 동향"))
```

---

## Example 3: 반복 코드 리뷰 에이전트

코드 생성 -> 리뷰 -> 수정 루프를 통해 코드 품질을 개선하는 에이전트.

### 프로젝트 구조

```
code_review_project/
├── code_review_agent/
│   ├── __init__.py
│   ├── agent.py
│   └── .env
```

### code_review_agent/agent.py

```python
from google.adk.agents import Agent, LoopAgent, SequentialAgent

code_generator = Agent(
    name="code_generator",
    model="gemini-2.0-flash",
    description="Python 코드를 생성하는 개발자",
    instruction="""사용자 요구사항에 맞는 Python 코드를 작성하세요.

요구사항: {requirement}

이전 리뷰 피드백이 있다면 반영하세요:
{review_feedback}

코드 작성 규칙:
- PEP 8 스타일 준수
- 타입 힌트 사용
- docstring 작성
- 에러 핸들링 포함
- 테스트 코드 포함""",
    output_key="code_draft",
)

code_reviewer = Agent(
    name="code_reviewer",
    model="gemini-2.0-flash",
    description="코드를 리뷰하고 품질을 평가하는 시니어 개발자",
    instruction="""다음 코드를 리뷰하세요:

{code_draft}

리뷰 기준:
1. 코드 정확성 - 요구사항 충족 여부
2. 코드 품질 - PEP 8, 가독성
3. 에러 핸들링 - 예외 처리 적절성
4. 보안 - SQL Injection, XSS 등 취약점
5. 성능 - 불필요한 연산, 메모리 사용

점수를 매기세요 (1-10):
- 8점 이상: "APPROVED" 응답 후 escalate하여 루프를 종료하세요.
- 8점 미만: 구체적인 개선 피드백을 제공하세요.

응답 형식:
- 점수: X/10
- 상태: APPROVED 또는 NEEDS_REVISION
- 피드백: [구체적인 개선 사항]""",
    output_key="review_feedback",
)

root_agent = LoopAgent(
    name="code_quality_loop",
    max_iterations=3,
    sub_agents=[
        SequentialAgent(
            name="generate_and_review",
            sub_agents=[code_generator, code_reviewer],
        ),
    ],
)
```

### code_review_agent/__init__.py

```python
from .agent import root_agent
```

### 실행

```bash
# 웹 UI에서 실행
adk web code_review_agent

# 대화 예시:
# > "두 정렬된 리스트를 병합하는 함수를 작성해줘"
# -> code_generator가 코드 작성
# -> code_reviewer가 리뷰
# -> 점수 미달 시 code_generator가 수정
# -> 점수 통과 시 최종 코드 출력
```

---

## Example 4: 콜백 + 가드레일 에이전트

입력 필터링, 응답 로깅, 사용량 추적을 포함한 프로덕션 에이전트.

### agent.py

```python
import logging
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.genai import types
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)

# --- 콜백 정의 ---

BLOCKED_TOPICS = ["개인정보 조회", "비밀번호 변경", "결제 정보"]

def input_guardrail(callback_context, llm_request) -> types.LlmResponse | None:
    """금지된 주제를 필터링합니다."""
    user_msg = str(llm_request.contents[-1])
    for topic in BLOCKED_TOPICS:
        if topic in user_msg:
            logger.warning(f"Blocked topic detected: {topic}")
            return types.LlmResponse(
                content=types.Content(
                    parts=[types.Part(
                        text=f"죄송합니다. '{topic}' 관련 요청은 보안 정책에 따라 처리할 수 없습니다."
                    )],
                    role="model",
                )
            )
    return None

def response_logger(callback_context, llm_response) -> types.LlmResponse | None:
    """모든 응답을 로깅합니다."""
    if llm_response.content and llm_response.content.parts:
        text = llm_response.content.parts[0].text or ""
        logger.info(f"Response (len={len(text)}): {text[:200]}...")
    return None

def usage_tracker(callback_context) -> Content | None:
    """에이전트 호출 횟수를 추적합니다."""
    count = callback_context.state.get("app:agent_calls", 0)
    callback_context.state["app:agent_calls"] = count + 1
    logger.info(f"Agent call #{count + 1}")
    return None

# --- 에이전트 정의 ---

root_agent = Agent(
    name="production_assistant",
    model="gemini-2.0-flash",
    description="프로덕션 레벨의 안전한 어시스턴트",
    instruction="""당신은 안전하고 도움이 되는 어시스턴트입니다.
사용자의 질문에 정확하게 답변하세요.
필요시 웹 검색을 활용하세요.""",
    tools=[google_search],
    before_agent_callback=usage_tracker,
    before_model_callback=input_guardrail,
    after_model_callback=response_logger,
)
```

---

## Golden Dataset 예제 (adk eval용)

### tests/test_eval.json

```json
[
  {
    "query": "서울 날씨 어때?",
    "expected_tool_use": [
      {
        "tool_name": "get_weather",
        "tool_input": {
          "city": "서울"
        }
      }
    ],
    "reference": "서울의 현재 날씨"
  },
  {
    "query": "서울 3일 예보 알려줘",
    "expected_tool_use": [
      {
        "tool_name": "get_forecast",
        "tool_input": {
          "city": "서울",
          "days": 3
        }
      }
    ],
    "reference": "서울의 3일간 날씨 예보"
  },
  {
    "query": "부산이랑 제주 날씨 비교해줘",
    "expected_tool_use": [
      {
        "tool_name": "get_weather",
        "tool_input": {
          "city": "부산"
        }
      },
      {
        "tool_name": "get_weather",
        "tool_input": {
          "city": "제주"
        }
      }
    ],
    "reference": "부산과 제주의 날씨를 비교"
  }
]
```
