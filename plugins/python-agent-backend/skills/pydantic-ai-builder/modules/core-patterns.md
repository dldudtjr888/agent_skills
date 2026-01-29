# 핵심 패턴 상세

Agent, Tool, Dependencies, Output의 상세 패턴과 Good/Bad 예제.

---

## Agent 생성 패턴

### 기본 Agent

```python
from pydantic_ai import Agent

# 최소 구성
agent = Agent('openai:gpt-4o')

# 전체 구성
agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
    output_type=MyOutput,
    system_prompt='당신은 데이터 분석 전문가입니다.',
    retries=3,
    model_settings={'temperature': 0.1, 'max_tokens': 2000},
)
```

### instructions vs system_prompt

> **공식 권장**: 일반적으로 `system_prompt` 대신 `instructions` 사용을 권장.

```python
# ✅ 권장: instructions (message_history 전달 시 이전 메시지에서 제외, 현재 Agent 것만 포함)
agent = Agent(
    'openai:gpt-4o',
    instructions='당신은 금융 분석가입니다. 항상 수치 근거를 제시하세요.',
)

# 동적 instructions (런타임 컨텍스트 활용)
@agent.instructions
def add_user_context(ctx: RunContext[UserDeps]) -> str:
    return f'현재 사용자: {ctx.deps.user_name}, 권한: {ctx.deps.role}'

# system_prompt: message_history 전달 시에도 항상 포함됨
agent = Agent(
    'openai:gpt-4o',
    system_prompt='이 프롬프트는 message_history에 관계없이 항상 포함됩니다.',
)

# 동적 system_prompt
@agent.system_prompt
def add_rules() -> str:
    return '응답은 항상 한국어로 작성하세요.'
```

**차이점 요약**:
- `instructions`: `message_history` 전달 시 이전 대화의 instructions는 제외, 현재 Agent의 instructions만 포함
- `system_prompt`: `message_history` 전달 시에도 항상 포함
- 복수 프롬프트는 합쳐짐 (instructions끼리, system_prompt끼리)

### ModelSettings 튜닝

```python
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

agent = Agent(
    'openai:gpt-4o',
    model_settings=ModelSettings(
        temperature=0.0,       # 결정적 출력
        max_tokens=4096,       # 최대 토큰
        top_p=0.9,             # 핵 샘플링
    ),
)

# 실행 시 오버라이드
result = agent.run_sync(
    'prompt',
    model_settings={'temperature': 0.7},  # 이번 실행만 변경
)
```

---

## Tool 패턴

### 3가지 등록 방식

```python
# 방식 1: @agent.tool — RunContext 포함 (기본, 가장 많이 사용)
@agent.tool
async def get_weather(ctx: RunContext[MyDeps], city: str) -> str:
    """지정된 도시의 날씨를 조회합니다.

    Args:
        city: 날씨를 조회할 도시명
    """
    api = ctx.deps.weather_api
    return await api.get(city)

# 방식 2: @agent.tool_plain — RunContext 불필요
@agent.tool_plain
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다.

    Args:
        expression: 계산할 수학 표현식 (예: '2 + 3 * 4')
    """
    return str(eval(expression))  # 실제로는 안전한 파서 사용

# 방식 3: Agent 생성자의 tools 파라미터
from pydantic_ai import Tool

agent = Agent(
    'openai:gpt-4o',
    tools=[
        Tool(get_weather, takes_ctx=True),
        Tool(calculate, takes_ctx=False),
    ],
)
```

### Docstring 스키마 생성

```python
# ✅ GOOD: Google 스타일 docstring → 자동 스키마 생성
@agent.tool_plain(docstring_format='google', require_parameter_descriptions=True)
def search_products(category: str, min_price: float, max_price: float) -> str:
    """상품을 검색합니다.

    Args:
        category: 상품 카테고리 (예: 'electronics', 'clothing')
        min_price: 최소 가격 (USD)
        max_price: 최대 가격 (USD)
    """
    return f"Searching {category}: ${min_price}-${max_price}"

# ❌ BAD: docstring 없음 → LLM이 파라미터 의미 추론 불가
@agent.tool_plain
def search_products(category: str, min_price: float, max_price: float) -> str:
    return f"Searching {category}: ${min_price}-${max_price}"
```

### Tool Retry

```python
from pydantic_ai import ModelRetry

@agent.tool
async def query_api(ctx: RunContext[MyDeps], endpoint: str) -> str:
    """외부 API를 호출합니다.

    Args:
        endpoint: API 엔드포인트 경로
    """
    if not endpoint.startswith('/'):
        # ModelRetry → LLM에게 다시 시도하라고 피드백
        raise ModelRetry('endpoint는 /로 시작해야 합니다. 다시 시도하세요.')
    return await ctx.deps.client.get(endpoint)

# retry 횟수 설정
@agent.tool(retries=3)
async def risky_tool(ctx: RunContext[MyDeps], param: str) -> str:
    """실패할 수 있는 작업을 수행합니다."""
    ...
```

### Prepare Tool (동적 활성화)

```python
from pydantic_ai import RunContext
from pydantic_ai.tools import ToolDefinition

async def check_permission(
    ctx: RunContext[MyDeps], tool_def: ToolDefinition
) -> ToolDefinition | None:
    """관리자만 사용 가능한 Tool"""
    if ctx.deps.role != 'admin':
        return None  # None 반환 → Tool 비활성화
    return tool_def

@agent.tool(prepare=check_permission)
async def delete_record(ctx: RunContext[MyDeps], record_id: str) -> str:
    """레코드를 삭제합니다."""
    ...
```

---

## Output 패턴

### 기본 구조화 출력

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent

class ReviewResult(BaseModel):
    score: int = Field(ge=1, le=10, description='1-10 점수')
    pros: list[str] = Field(description='장점 목록')
    cons: list[str] = Field(description='단점 목록')
    recommendation: str = Field(description='최종 추천 의견')

agent = Agent('openai:gpt-4o', output_type=ReviewResult)
result = agent.run_sync('iPhone 16 리뷰를 작성해주세요')
print(result.output.score)  # int
print(result.output.pros)   # list[str]
```

### 3가지 Output 모드

```python
from pydantic_ai import Agent, ToolOutput, NativeOutput, PromptedOutput

# 1. ToolOutput (기본) — 도구 호출로 스키마 강제
agent = Agent('openai:gpt-4o', output_type=ToolOutput(ReviewResult))

# 2. NativeOutput — 모델의 네이티브 Structured Outputs 사용
#    (모든 모델이 지원하지 않음, OpenAI gpt-4o 이상 권장)
agent = Agent('openai:gpt-4o', output_type=NativeOutput(ReviewResult))

# 3. PromptedOutput — 프롬프트에 스키마 삽입, 텍스트 응답 파싱
#    (모든 모델 지원, 정확도 낮을 수 있음)
agent = Agent('openai:gpt-4o', output_type=PromptedOutput(ReviewResult))
```

### Union Output (다중 타입)

```python
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput

class SuccessResult(BaseModel):
    data: dict
    confidence: float

class ErrorResult(BaseModel):
    error_code: str
    message: str

# Union → LLM이 상황에 맞는 타입 선택
agent = Agent(
    'openai:gpt-4o',
    output_type=[
        ToolOutput(SuccessResult, name='return_success'),
        ToolOutput(ErrorResult, name='return_error'),
    ],
)

result = agent.run_sync('데이터를 분석해주세요')
if isinstance(result.output, SuccessResult):
    print(f"성공: {result.output.data}")
else:
    print(f"오류: {result.output.message}")
```

### Output Validator

```python
from pydantic_ai import Agent, ModelRetry, RunContext

@agent.output_validator
async def validate_result(
    ctx: RunContext[MyDeps], output: ReviewResult
) -> ReviewResult:
    # DB 조회 등 비동기 검증 가능
    if output.score > 10:
        raise ModelRetry('score는 1-10 범위여야 합니다.')
    if len(output.pros) == 0:
        raise ModelRetry('장점을 최소 1개 이상 작성하세요.')
    return output
```

### Output Function (도구 호출 대신 함수 실행)

```python
from pydantic_ai import Agent

def run_sql(query: str) -> list[dict]:
    """SQL 쿼리를 실행하고 결과를 반환합니다.

    Args:
        query: 실행할 SQL SELECT 쿼리
    """
    # 실제 DB 쿼리 실행
    return db.execute(query)

agent = Agent('openai:gpt-4o', output_type=[run_sql, ErrorResult])
```

---

## Dependencies 패턴

### 단순 타입

```python
# 문자열 하나만 필요한 경우
agent = Agent('openai:gpt-4o', deps_type=str)
result = agent.run_sync('질문', deps='user-context-value')
```

### 복합 Dataclass

```python
from dataclasses import dataclass
from httpx import AsyncClient

@dataclass
class AppDeps:
    db: DatabaseClient
    http_client: AsyncClient
    user_id: str
    api_key: str

agent = Agent('openai:gpt-4o', deps_type=AppDeps)

@agent.tool
async def fetch_data(ctx: RunContext[AppDeps], query: str) -> str:
    """데이터를 조회합니다."""
    # ✅ deps를 통해 클라이언트 접근
    response = await ctx.deps.http_client.get(
        f'/api/data?q={query}',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    return response.text

# 실행
async with AsyncClient() as client:
    deps = AppDeps(db=db, http_client=client, user_id='u-1', api_key='key')
    result = await agent.run('데이터를 조회해주세요', deps=deps)
```

### Deps 사용 규칙

```python
# ✅ GOOD: deps로 의존성 주입 → 테스트 시 mock 가능
@agent.tool
async def get_user(ctx: RunContext[AppDeps]) -> str:
    return await ctx.deps.db.find_user(ctx.deps.user_id)

# ❌ BAD: 전역 변수 직접 참조 → 테스트 불가, 병렬 실행 위험
db_client = DatabaseClient()  # 전역

@agent.tool_plain
def get_user_bad() -> str:
    return db_client.find_user(global_user_id)  # 전역 상태 의존

# ❌ BAD: Agent를 deps에 포함 → Agent는 stateless global
@dataclass
class BadDeps:
    other_agent: Agent  # Agent를 deps에 넣지 않음

# ✅ GOOD: Agent는 모듈 레벨에서 정의, tool 내에서 호출
sub_agent = Agent('openai:gpt-4o-mini')

@agent.tool
async def delegate(ctx: RunContext[AppDeps]) -> str:
    result = await sub_agent.run('하위 작업', usage=ctx.usage)
    return result.output
```

---

## 멀티턴 대화 (message_history)

이전 대화 컨텍스트를 유지하며 연속 실행하는 패턴.

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', instructions='친절한 한국어 도우미입니다.')

# 첫 번째 대화
result1 = agent.run_sync('아인슈타인에 대해 알려줘')
print(result1.output)

# 두 번째 대화 — message_history로 컨텍스트 유지
result2 = agent.run_sync(
    '그의 가장 유명한 방정식은?',
    message_history=result1.new_messages(),  # 이전 대화 전달
)
print(result2.output)  # "그"가 아인슈타인임을 이해함

# 세 번째 대화 — 전체 히스토리 누적
result3 = agent.run_sync(
    '그걸 쉽게 설명해줘',
    message_history=result2.all_messages(),  # 전체 대화 전달
)
```

**메시지 접근 메서드**:
- `result.new_messages()` — 현재 실행에서 생성된 메시지만
- `result.all_messages()` — 이전 히스토리 + 현재 메시지 전부

**주의**: `message_history`가 비어 있지 않으면 `instructions`가 새로 생성되지 않음 (기존 히스토리에 포함된 것으로 간주). `system_prompt`는 항상 포함됨.
