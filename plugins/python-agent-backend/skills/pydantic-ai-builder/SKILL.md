---
name: pydantic-ai-builder
description: PydanticAI 프레임워크로 타입 안전한 AI 에이전트를 빌드하는 가이드. Agent, Tool, Deps, Output 패턴과 멀티에이전트 오케스트레이션 템플릿.
version: 1.0.0
category: framework
user-invocable: true
triggers:
  keywords:
    - pydantic-ai
    - pydanticai
    - pydantic ai
    - pydantic agent
    - AI agent
    - ai 에이전트
  intentPatterns:
    - "(만들|생성|빌드|구현|작성).*(에이전트|agent|봇|bot).*pydantic"
    - "(build|create|implement).*(agent|bot).*pydantic"
    - "pydantic.*(에이전트|agent|봇|bot).*(만들|생성|빌드)"
---

# PydanticAI Agent Builder

Pydantic 팀이 만든 Python 에이전트 프레임워크. FastAPI 스타일의 DX로 타입 안전한 AI 에이전트를 빌드한다.

> 공식 문서: https://ai.pydantic.dev/ | GitHub: https://github.com/pydantic/pydantic-ai

**모듈 참조**:
- 핵심 패턴 상세 → `modules/core-patterns.md`
- 멀티에이전트 & Graph → `modules/multi-agent-patterns.md`
- Streaming, Eval, MCP → `modules/advanced-patterns.md`
- LLM 프로바이더 설정 → `modules/provider-integration.md`
- 빠른 시작 예제 → `references/quick-start-examples.md`
- API 치트시트 → `references/api-cheatsheet.md`

---

## 핵심 컴포넌트

| 컴포넌트 | 역할 | 핵심 클래스 |
|----------|------|------------|
| **Agent** | LLM과의 상호작용 컨테이너 | `Agent[DepsT, OutputT]` |
| **Tool** | 에이전트가 호출하는 함수 | `@agent.tool`, `@agent.tool_plain` |
| **Dependencies** | 런타임 의존성 주입 | `RunContext[DepsT]` |
| **Output** | 구조화된 응답 타입 | `BaseModel`, `ToolOutput`, `NativeOutput` |
| **Model** | LLM 프로바이더 추상화 | `'openai:gpt-4o'`, `'anthropic:claude-sonnet-4-20250514'` |

---

## 사용 시점

- PydanticAI로 새 에이전트를 만들 때
- 기존 에이전트에 Tool/Output을 추가할 때
- 멀티에이전트 시스템을 설계할 때
- LLM 프로바이더를 교체/설정할 때
- 에이전트 테스트를 작성할 때

---

## 워크플로우

### Step 1: 프로젝트 설정

```bash
pip install pydantic-ai
```

환경 변수 설정 (프로바이더별):
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

권장 프로젝트 구조:
```
my_agent/
├── agent.py          # Agent 정의
├── models.py         # Pydantic 스키마 (Input/Output)
├── tools.py          # Tool 함수들
├── deps.py           # Dependencies 정의
├── config.py         # 모델/설정 관리
└── tests/
    └── test_agent.py # TestModel 기반 테스트
```

### Step 2: Agent 정의

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    confidence: float
    tags: list[str]

agent = Agent(
    'openai:gpt-4o',
    deps_type=str,
    output_type=AnalysisResult,
    instructions='데이터를 분석하고 구조화된 결과를 반환하세요.',  # 권장: instructions
)
```

> **참고**: `instructions`는 `message_history` 전달 시 이전 대화의 것을 제외하고 현재 Agent 것만 포함. `system_prompt`는 항상 포함. 일반적으로 `instructions` 권장.

**동적 instructions** (런타임 컨텍스트 활용):
```python
@agent.instructions
def add_context(ctx: RunContext[str]) -> str:
    return f'분석 대상 도메인: {ctx.deps}'
```

### Step 3: Tool 등록

```python
# RunContext 필요한 경우 → @agent.tool
@agent.tool
async def search_database(ctx: RunContext[str], query: str) -> str:
    """데이터베이스에서 관련 정보를 검색합니다.

    Args:
        query: 검색할 키워드
    """
    # ctx.deps로 의존성 접근
    return f"Results for '{query}' in domain '{ctx.deps}'"

# RunContext 불필요한 경우 → @agent.tool_plain
@agent.tool_plain
def calculate_score(value: float, weight: float) -> float:
    """가중치를 적용한 점수를 계산합니다.

    Args:
        value: 원시 값
        weight: 가중치 (0.0~1.0)
    """
    return value * weight
```

### Step 4: Output 구조화

```python
from pydantic_ai import Agent, ToolOutput

# 단일 타입
agent = Agent('openai:gpt-4o', output_type=AnalysisResult)

# Union 타입 (여러 출력 중 선택)
agent = Agent(
    'openai:gpt-4o',
    output_type=[
        ToolOutput(AnalysisResult, name='return_analysis'),
        ToolOutput(ErrorReport, name='return_error'),
    ],
)

# Output Validator
@agent.output_validator
async def validate_output(ctx: RunContext[str], output: AnalysisResult) -> AnalysisResult:
    if output.confidence < 0.0 or output.confidence > 1.0:
        raise ModelRetry('confidence는 0.0~1.0 범위여야 합니다.')
    return output
```

### Step 5: 의존성 주입

```python
from dataclasses import dataclass

@dataclass
class AgentDeps:
    db_connection: DatabaseClient
    api_key: str
    user_id: str

agent = Agent(
    'openai:gpt-4o',
    deps_type=AgentDeps,
    output_type=AnalysisResult,
)

@agent.tool
async def fetch_user_data(ctx: RunContext[AgentDeps]) -> str:
    """사용자 데이터를 조회합니다."""
    return await ctx.deps.db_connection.get_user(ctx.deps.user_id)

# 실행 시 의존성 전달
result = await agent.run(
    '이 사용자의 활동을 분석해주세요.',
    deps=AgentDeps(db_connection=db, api_key='...', user_id='user-123'),
)
```

### Step 6: 실행 & 테스트

```python
# 동기 실행
result = agent.run_sync('분석해주세요', deps=my_deps)
print(result.output)  # AnalysisResult 타입

# 비동기 실행
result = await agent.run('분석해주세요', deps=my_deps)

# 스트리밍
async with agent.run_stream('분석해주세요', deps=my_deps) as stream:
    async for chunk in stream.stream_text():
        print(chunk, end='')

# 토큰/비용 제한
from pydantic_ai import UsageLimits
result = await agent.run(
    '분석해주세요',
    deps=my_deps,
    usage_limits=UsageLimits(response_tokens_limit=1000, request_limit=5),
)
```

**테스트** (실제 LLM 호출 없이):
```python
import os
from pydantic_ai.models.test import TestModel

os.environ['ALLOW_MODEL_REQUESTS'] = 'false'  # 실수 방지

def test_agent():
    with agent.override(model=TestModel()):
        result = agent.run_sync('테스트 입력', deps=mock_deps)
        assert isinstance(result.output, AnalysisResult)
```

---

## Best Practices

1. **Output 먼저 정의** — BaseModel로 Input/Output 스키마를 먼저 설계한 후 Agent 구현
2. **모든 경계에서 검증** — Pydantic 검증 활용, ValidationError는 LLM에 자동 피드백되어 retry
3. **Docstring 필수** — Tool 함수에 Google/NumPy/Sphinx 스타일 docstring 작성 (스키마 품질 결정)
4. **Deps로 상태 관리** — 전역 변수 대신 `deps_type`과 `RunContext`로 의존성 주입
5. **FallbackModel 활용** — 프로바이더 장애 대비 다중 모델 체인
6. **UsageLimits 설정** — 토큰/요청 수 제한으로 비용 제어
7. **TestModel로 테스트** — 실제 LLM 호출 없이 빠르고 결정적인 테스트
8. **Logfire 연동** — OpenTelemetry 기반 관측성 확보

---

## 안티패턴

- ❌ `output_type` 없이 문자열만 받기 — 타입 안전성 포기, 다운스트림 파싱 필요
- ❌ Tool에 docstring 누락 — LLM이 파라미터 의미를 추론 불가, 스키마 품질 저하
- ❌ `deps` 없이 전역 상태 사용 — 테스트 불가, 병렬 실행 시 레이스 컨디션
- ❌ retry 설정 없이 LLM 호출 — 일시적 오류(rate limit, timeout)에 취약
- ❌ 모든 로직을 하나의 Agent에 집중 — 관심사 분리 위반, 프롬프트 비대화
- ❌ Agent를 deps에 포함 — Agent는 stateless global로 설계, deps에 넣지 않음
- ❌ `ALLOW_MODEL_REQUESTS` 미설정 — 테스트에서 실수로 실제 API 호출 가능

---

## 멀티에이전트 복잡도 레벨

| 레벨 | 패턴 | 적합한 경우 |
|------|------|------------|
| 1 | 단일 Agent | 단순 Q&A, 분류, 변환 |
| 2 | Agent Delegation (tool) | 전문 에이전트에 작업 위임 |
| 3 | Programmatic Hand-off | 순차적 파이프라인, 사람 개입 |
| 4 | Graph 기반 제어 | 복잡한 상태 머신, 분기/병합 |
| 5 | Deep Agent | 자율형 계획-실행-검증 루프 |

> 상세 → `modules/multi-agent-patterns.md`

---

## 지원 프로바이더 (주요)

| 프로바이더 | 모델 문자열 예시 | 비고 |
|-----------|-----------------|------|
| OpenAI | `'openai:gpt-4o'` | 기본 |
| Anthropic | `'anthropic:claude-sonnet-4-20250514'` | |
| Google Gemini | `'google-gla:gemini-2.0-flash'` | |
| Groq | `'groq:llama-3.3-70b-versatile'` | |
| AWS Bedrock | `'bedrock:...'` | |
| Mistral | `'mistral:...'` | |
| DeepSeek | OpenAI 호환 API 사용 | |

> 상세 설정 → `modules/provider-integration.md`

---

**Remember**: Agent는 FastAPI의 `app`처럼 전역으로 정의하고, 실행 시 `deps`로 런타임 컨텍스트를 주입한다. 작게 시작하고, 필요할 때 Tool과 Agent를 추가한다.
