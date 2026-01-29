# 빠른 시작 예제

PydanticAI 에이전트 빌드를 위한 완성된 예제 5가지.

---

## 예제 1: 단순 Q&A 에이전트

가장 기본적인 형태. 모델과 프롬프트만으로 동작.

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt='당신은 친절한 한국어 도우미입니다. 간결하게 답변하세요.',
)

# 동기 실행
result = agent.run_sync('파이썬에서 리스트 컴프리헨션이 뭐야?')
print(result.output)

# 비동기 실행
import asyncio

async def main():
    result = await agent.run('async/await 설명해줘')
    print(result.output)

asyncio.run(main())
```

---

## 예제 2: Tool + Deps 포함 에이전트

외부 데이터를 Tool로 조회하고, 의존성을 주입하는 패턴.

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
import httpx

@dataclass
class WeatherDeps:
    api_key: str
    client: httpx.AsyncClient

agent = Agent(
    'openai:gpt-4o',
    deps_type=WeatherDeps,
    system_prompt=(
        '당신은 날씨 안내 도우미입니다. '
        'get_weather 도구를 사용해 실제 날씨 정보를 조회한 후 답변하세요.'
    ),
)

@agent.tool
async def get_weather(ctx: RunContext[WeatherDeps], city: str) -> str:
    """지정된 도시의 현재 날씨를 조회합니다.

    Args:
        city: 날씨를 조회할 도시명 (영문)
    """
    response = await ctx.deps.client.get(
        'https://api.weatherapi.com/v1/current.json',
        params={'key': ctx.deps.api_key, 'q': city},
    )
    data = response.json()
    current = data['current']
    return f"{city}: {current['temp_c']}°C, {current['condition']['text']}"

# 실행
async def main():
    async with httpx.AsyncClient() as client:
        deps = WeatherDeps(api_key='your-api-key', client=client)
        result = await agent.run('서울과 도쿄 날씨 비교해줘', deps=deps)
        print(result.output)

import asyncio
asyncio.run(main())
```

---

## 예제 3: 구조화된 Output 에이전트

Pydantic BaseModel로 타입 안전한 구조화된 응답을 받는 패턴.

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry

class CodeReview(BaseModel):
    score: int = Field(ge=1, le=10, description='코드 품질 점수 (1-10)')
    issues: list[str] = Field(description='발견된 문제점 목록')
    suggestions: list[str] = Field(description='개선 제안 목록')
    summary: str = Field(description='전체 요약 (2-3문장)')

agent = Agent(
    'openai:gpt-4o',
    output_type=CodeReview,
    system_prompt=(
        '당신은 시니어 코드 리뷰어입니다. '
        '제출된 코드를 분석하고 구조화된 리뷰를 작성하세요.'
    ),
)

# Output Validator로 추가 검증
@agent.output_validator
def validate_review(output: CodeReview) -> CodeReview:
    if output.score > 5 and len(output.issues) > 5:
        raise ModelRetry(
            '점수가 5 이상인데 문제가 5개 넘습니다. '
            '점수를 낮추거나 사소한 문제를 제거하세요.'
        )
    return output

# 실행
code = '''
def process(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
'''

result = agent.run_sync(f'다음 코드를 리뷰해주세요:\n```python\n{code}\n```')
print(f'점수: {result.output.score}/10')
print(f'문제: {result.output.issues}')
print(f'제안: {result.output.suggestions}')
print(f'요약: {result.output.summary}')
```

---

## 예제 4: 멀티에이전트 파이프라인

Delegation 패턴으로 리서치→분석→보고서 파이프라인 구성.

```python
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# Output 모델 정의
class ResearchData(BaseModel):
    findings: list[str]
    sources: list[str]

class AnalysisResult(BaseModel):
    key_insights: list[str]
    trends: list[str]
    risk_factors: list[str]

class FinalReport(BaseModel):
    title: str
    executive_summary: str
    insights: list[str]
    recommendations: list[str]

# 전문 에이전트들
researcher = Agent(
    'openai:gpt-4o-mini',  # 빠르고 저렴한 모델
    output_type=ResearchData,
    system_prompt='주어진 주제에 대해 핵심 사실과 데이터를 조사하세요.',
)

analyst = Agent(
    'openai:gpt-4o',  # 복잡한 분석용 고성능 모델
    output_type=AnalysisResult,
    system_prompt='조사 데이터를 분석하여 인사이트, 트렌드, 리스크를 도출하세요.',
)

# 오케스트레이터
report_agent = Agent(
    'openai:gpt-4o',
    output_type=FinalReport,
    system_prompt=(
        '당신은 보고서 작성 전문가입니다. '
        'research와 analyze 도구를 활용하여 종합 보고서를 작성하세요.'
    ),
)

@report_agent.tool
async def research(ctx: RunContext[None], topic: str) -> str:
    """주제에 대해 리서치를 수행합니다.

    Args:
        topic: 조사할 주제
    """
    result = await researcher.run(
        f'{topic}에 대해 조사하세요.',
        usage=ctx.usage,
    )
    findings = '\n'.join(f'- {f}' for f in result.output.findings)
    return f'조사 결과:\n{findings}'

@report_agent.tool
async def analyze(ctx: RunContext[None], data: str) -> str:
    """조사 데이터를 분석합니다.

    Args:
        data: 분석할 조사 데이터
    """
    result = await analyst.run(
        f'다음 데이터를 분석하세요:\n{data}',
        usage=ctx.usage,
    )
    insights = '\n'.join(f'- {i}' for i in result.output.key_insights)
    return f'분석 결과:\n{insights}'

# 실행
async def main():
    result = await report_agent.run('2025년 AI 산업 동향 보고서를 작성해주세요')
    report = result.output
    print(f'제목: {report.title}')
    print(f'요약: {report.executive_summary}')
    print(f'인사이트: {report.insights}')
    print(f'추천: {report.recommendations}')
    print(f'총 토큰: {result.usage()}')

import asyncio
asyncio.run(main())
```

---

## 예제 5: Streaming + 비용 제한

실시간 스트리밍 응답과 UsageLimits를 결합한 패턴.

```python
from pydantic_ai import Agent, UsageLimits

agent = Agent(
    'openai:gpt-4o',
    system_prompt='당신은 스토리텔러입니다. 흥미로운 이야기를 들려주세요.',
)

async def stream_with_limits():
    # 텍스트 스트리밍 + 비용 제한
    async with agent.run_stream(
        '한국 전래동화 스타일로 AI에 대한 이야기를 써줘',
        usage_limits=UsageLimits(
            response_tokens_limit=500,
            request_limit=3,
        ),
    ) as stream:
        async for chunk in stream.stream_text(delta=True):
            print(chunk, end='', flush=True)

    print(f'\n\n사용량: {stream.usage()}')

import asyncio
asyncio.run(stream_with_limits())
```

### 테스트 버전

```python
import os
from pydantic_ai.models.test import TestModel

os.environ['ALLOW_MODEL_REQUESTS'] = 'false'

def test_streaming():
    with agent.override(model=TestModel()):
        # run_sync로 테스트 (스트리밍 대신)
        result = agent.run_sync('테스트 스토리')
        assert isinstance(result.output, str)
        assert len(result.output) > 0
```
