# 멀티에이전트 & Graph 패턴

PydanticAI의 5가지 멀티에이전트 복잡도 레벨과 Graph 기반 워크플로우.

---

## 레벨 1: 단일 Agent

가장 단순한 형태. 대부분의 작업은 단일 Agent로 충분하다.

```python
agent = Agent(
    'openai:gpt-4o',
    output_type=Result,
    system_prompt='당신은 전문 분석가입니다.',
)
result = agent.run_sync('분석해주세요')
```

---

## 레벨 2: Agent Delegation (Tool 기반 위임)

부모 Agent가 Tool을 통해 자식 Agent에게 작업을 위임한다. 각 Agent는 다른 모델을 사용할 수 있다.

```python
from pydantic_ai import Agent, RunContext

# 전문 에이전트들 (모듈 레벨에서 정의)
researcher = Agent(
    'openai:gpt-4o',
    output_type=ResearchResult,
    system_prompt='당신은 리서치 전문가입니다. 주어진 주제를 조사하세요.',
)

writer = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=str,
    system_prompt='당신은 글쓰기 전문가입니다. 조사 결과를 바탕으로 글을 작성하세요.',
)

# 오케스트레이터
orchestrator = Agent(
    'openai:gpt-4o',
    deps_type=str,
    output_type=FinalReport,
    system_prompt='당신은 프로젝트 매니저입니다.',
)

@orchestrator.tool
async def do_research(ctx: RunContext[str], topic: str) -> str:
    """주제에 대해 리서치를 수행합니다.

    Args:
        topic: 조사할 주제
    """
    result = await researcher.run(
        f'{topic}에 대해 조사해주세요',
        usage=ctx.usage,  # ✅ 토큰 사용량 통합 추적
    )
    return result.output.summary

@orchestrator.tool
async def write_content(ctx: RunContext[str], research_summary: str) -> str:
    """리서치 결과를 바탕으로 글을 작성합니다.

    Args:
        research_summary: 리서치 요약 내용
    """
    result = await writer.run(
        f'다음 내용을 바탕으로 글을 작성하세요:\n{research_summary}',
        usage=ctx.usage,
    )
    return result.output

# 실행
result = await orchestrator.run('AI 트렌드 보고서를 작성해주세요', deps='tech')
```

**핵심 규칙**:
- `usage=ctx.usage` 전달 → 전체 토큰 사용량 통합 추적
- `deps=ctx.deps` 전달 → 부모의 의존성 공유 (필요시)
- `UsageLimits` 설정 → 비용 폭주 방지

---

## 레벨 3: Programmatic Hand-off (순차 파이프라인)

애플리케이션 코드에서 Agent 실행 순서를 제어한다. 에이전트 간 Human-in-the-Loop 삽입 가능.

```python
from pydantic_ai.usage import RunUsage

async def content_pipeline(topic: str) -> FinalReport:
    usage = RunUsage()  # 전체 사용량 추적

    # Phase 1: 리서치
    research = await researcher.run(
        f'{topic}에 대해 조사해주세요',
        usage=usage,
    )

    # Phase 2: 사용자 승인 (Human-in-the-Loop)
    if not await get_user_approval(research.output):
        return FinalReport(status='rejected')

    # Phase 3: 글 작성 (리서치 결과 전달)
    article = await writer.run(
        f'다음 조사 결과를 바탕으로 글을 작성하세요:\n{research.output.summary}',
        usage=usage,
    )

    # Phase 4: 검토
    review = await reviewer.run(
        f'다음 글을 검토하세요:\n{article.output}',
        usage=usage,
    )

    print(f'총 토큰 사용: {usage}')
    return FinalReport(content=article.output, review=review.output)
```

**언제 Delegation 대신 Hand-off?**
- 에이전트 간 사람 개입이 필요할 때
- 각 에이전트가 서로 다른 deps_type을 사용할 때
- 실행 순서를 명시적으로 제어해야 할 때

---

## 레벨 4: Graph 기반 제어

`pydantic_graph` 모듈로 복잡한 상태 머신을 구성한다. 분기, 병합, 루프가 필요한 워크플로우에 적합.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

# 상태 정의
@dataclass
class PipelineState:
    topic: str = ''
    research: str = ''
    draft: str = ''
    review_score: int = 0
    revision_count: int = 0

# 노드 정의
@dataclass
class ResearchNode(BaseNode[PipelineState]):
    topic: str = ''

    async def run(self, ctx: GraphRunContext[PipelineState]) -> WriteNode:
        result = await researcher.run(f'{self.topic}에 대해 조사하세요')
        ctx.state.research = result.output.summary
        return WriteNode()

@dataclass
class WriteNode(BaseNode[PipelineState]):
    async def run(self, ctx: GraphRunContext[PipelineState]) -> ReviewNode:
        result = await writer.run(
            f'다음 내용으로 글을 작성하세요:\n{ctx.state.research}'
        )
        ctx.state.draft = result.output
        return ReviewNode()

@dataclass
class ReviewNode(BaseNode[PipelineState]):
    async def run(
        self, ctx: GraphRunContext[PipelineState]
    ) -> WriteNode | End[str]:
        result = await reviewer.run(f'글을 검토하세요:\n{ctx.state.draft}')
        ctx.state.review_score = result.output.score

        # 분기: 점수 낮으면 재작성, 높으면 완료
        if result.output.score < 7 and ctx.state.revision_count < 3:
            ctx.state.revision_count += 1
            ctx.state.research += f'\n피드백: {result.output.feedback}'
            return WriteNode()  # 다시 작성
        else:
            return End(ctx.state.draft)  # 완료

# 그래프 조립 & 실행
graph = Graph(nodes=[ResearchNode, WriteNode, ReviewNode])
result = await graph.run(
    ResearchNode(topic='AI 트렌드'),
    state=PipelineState(topic='AI 트렌드'),
)
print(result.output)  # 최종 글
```

### Graph 핵심 개념

| 개념 | 설명 |
|------|------|
| `BaseNode[StateT]` | 노드 기본 클래스, `run()` 메서드 구현 |
| `GraphRunContext[StateT]` | `ctx.state`로 상태 접근 |
| `End[T]` | 그래프 종료, 최종 결과 반환 |
| `Graph` | 노드 목록으로 그래프 구성, `run()` 실행 |
| 리턴 타입 어노테이션 | `-> NodeA | NodeB | End[str]`로 엣지 정의 |

### Graph 시각화

```python
# Mermaid 다이어그램 생성
mermaid_code = graph.mermaid_code()
print(mermaid_code)

# PNG 이미지 저장
graph.mermaid_save('pipeline.png')
```

### 상태 영속성 (State Persistence)

```python
from pydantic_graph.persistence.file import FileStatePersistence

persistence = FileStatePersistence('pipeline_state.json')

# 실행 중 상태 자동 저장
async with graph.iter(
    ResearchNode(topic='AI'),
    state=PipelineState(),
    persistence=persistence,
) as run:
    async for node in run:
        print(f'실행 중: {type(node).__name__}')

# 중단 후 재개
async with graph.iter_from_persistence(persistence) as run:
    async for node in run:
        print(f'재개: {type(node).__name__}')
```

---

## 레벨 5: Deep Agent

자율형 에이전트로, 계획-실행-검증 루프를 수행한다.

주요 특징:
- 작업 계획 및 진행 추적
- 파일 시스템 조작
- 하위 에이전트에 작업 위임
- 샌드박스 환경에서 코드 실행
- 대화 요약을 통한 컨텍스트 관리
- 민감 작업에 대한 사람 승인

> 참고: https://github.com/vstorm-co/pydantic-deepagents

---

## 관측성 (Observability)

```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

# 이후 모든 Agent 실행이 자동으로 트레이싱됨
# - 어떤 Agent가 어떤 요청을 처리했는지
# - 위임 결정과 트리거
# - Agent별 레이턴시와 토큰 사용량
# - Tool 실행 상세 (DB 쿼리, HTTP 요청)
```

---

## 패턴 선택 가이드

```
단순 Q&A, 분류, 변환
  → 레벨 1 (단일 Agent)

전문가에게 위임 필요 (리서치→작성→검토)
  → 레벨 2 (Delegation)

에이전트 간 사람 개입, 서로 다른 deps
  → 레벨 3 (Hand-off)

분기/병합/루프, 복잡한 상태 관리
  → 레벨 4 (Graph)

자율형 계획-실행-검증
  → 레벨 5 (Deep Agent)
```
