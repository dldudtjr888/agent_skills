# LangSmith 배포 및 관측성

> **최종 업데이트**: 2025-12-24 (deepagents 0.2+)

Deep Agents를 **프로덕션에 배포**하고 **LangSmith로 모니터링**하는 방법입니다.

---

## 개요

LangSmith는 LangChain 팀의 관측성(Observability) 플랫폼입니다:

- **Tracing**: 에이전트 실행 추적
- **Evaluation**: 품질 평가
- **Monitoring**: 프로덕션 모니터링
- **Debugging**: Polly AI 기반 디버깅

---

## LangGraph Platform 배포

### langgraph.json 설정

```json
{
  "graphs": {
    "agent": "agent:make_graph"
  },
  "dependencies": ["deepagents", "langchain-anthropic"],
  "env": ".env"
}
```

### Graph Factory

```python
# agent.py
from deepagents import create_deep_agent, async_create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

async def make_graph():
    """LangGraph Platform용 그래프 팩토리."""
    store = InMemoryStore()

    return await async_create_deep_agent(
        store=store,
        backend=lambda rt: CompositeBackend(
            default=StateBackend(rt),
            routes={"/memories/": StoreBackend(rt)}
        ),
        system_prompt="You are a helpful assistant."
    )
```

### 배포 명령어

```bash
# LangGraph CLI 설치
pip install langgraph-cli

# 로컬 테스트
langgraph dev

# LangGraph Cloud 배포
langgraph deploy --app my-agent
```

---

## LangSmith 통합

### 설정

```bash
# 환경변수 설정
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your-langsmith-api-key"
export LANGCHAIN_PROJECT="my-deep-agent"
```

### Python 설정

```python
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"
os.environ["LANGCHAIN_PROJECT"] = "my-project"
```

---

## Tracing

### 기본 추적

LangSmith 환경변수 설정 시 자동으로 모든 호출이 추적됩니다:

```python
from deepagents import create_deep_agent

agent = create_deep_agent()

# 이 호출은 자동으로 LangSmith에 추적됨
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Hello"}]
})
```

### 커스텀 추적

```python
from langsmith import traceable

@traceable(name="my_custom_function")
def process_data(data: str) -> str:
    """커스텀 함수 추적."""
    return data.upper()

@traceable(run_type="tool")
def my_tool(input: str) -> str:
    """도구 호출 추적."""
    return f"Result: {input}"
```

### 메타데이터 추가

```python
from langsmith import traceable

@traceable(metadata={"version": "1.0", "environment": "production"})
async def run_agent(query: str):
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": query}]
    })
    return result
```

---

## Evaluation

### 데이터셋 생성

```python
from langsmith import Client

client = Client()

# 데이터셋 생성
dataset = client.create_dataset(
    "agent-test-cases",
    description="Deep Agent 테스트 케이스"
)

# 예제 추가
client.create_examples(
    inputs=[
        {"query": "What is 2 + 2?"},
        {"query": "Write a hello world in Python"}
    ],
    outputs=[
        {"expected": "4"},
        {"expected": "print('Hello, World!')"}
    ],
    dataset_id=dataset.id
)
```

### 평가 실행

```python
from langsmith import evaluate

def predict(inputs: dict) -> dict:
    """에이전트 예측 함수."""
    result = agent.invoke({
        "messages": [{"role": "user", "content": inputs["query"]}]
    })
    return {"response": result["messages"][-1]["content"]}

def correctness_evaluator(run, example) -> dict:
    """정확성 평가자."""
    prediction = run.outputs["response"]
    expected = example.outputs["expected"]

    return {
        "key": "correctness",
        "score": 1.0 if expected in prediction else 0.0
    }

# 평가 실행
results = evaluate(
    predict,
    data="agent-test-cases",
    evaluators=[correctness_evaluator]
)
```

### LLM-as-Judge 평가

```python
from langsmith.evaluation import LangChainStringEvaluator

# GPT-4로 평가
evaluator = LangChainStringEvaluator(
    "criteria",
    config={
        "criteria": {
            "helpfulness": "Is the response helpful and complete?",
            "accuracy": "Is the response factually accurate?"
        }
    }
)

results = evaluate(
    predict,
    data="agent-test-cases",
    evaluators=[evaluator]
)
```

---

## Monitoring

### 대시보드 메트릭

LangSmith 대시보드에서 확인 가능:

| 메트릭 | 설명 |
|--------|------|
| Latency | 응답 시간 (p50, p95, p99) |
| Token Usage | 토큰 사용량 |
| Error Rate | 에러 비율 |
| Cost | 비용 추적 |
| Feedback | 사용자 피드백 |

### 알림 설정

```python
# LangSmith UI에서 설정하거나 API 사용
from langsmith import Client

client = Client()

# 프로젝트 통계 조회
stats = client.read_project(project_name="my-project")
print(f"Total runs: {stats.run_count}")
print(f"Error rate: {stats.error_rate}")
```

---

## Polly AI 디버깅

### 개요

Polly는 LangSmith의 AI 디버깅 어시스턴트입니다:

- Trace 분석
- 에러 원인 파악
- 최적화 제안
- 패턴 인식

### 사용법

1. LangSmith 대시보드에서 Trace 선택
2. "Ask Polly" 버튼 클릭
3. 질문 입력:
   - "Why did this run fail?"
   - "How can I optimize this?"
   - "What's causing the latency?"

---

## LangSmith Fetch CLI

### 설치

```bash
npm install -g @anthropic-ai/langsmith-fetch
# 또는
pip install langsmith-fetch
```

### 사용

```bash
# Trace 조회
langsmith-fetch traces --project my-project --limit 10

# 특정 Trace 상세
langsmith-fetch trace <trace-id>

# 데이터셋 내보내기
langsmith-fetch dataset export agent-test-cases --format jsonl
```

---

## 프로덕션 체크리스트

### 배포 전

- [ ] LangSmith API 키 설정
- [ ] 프로젝트 이름 설정
- [ ] 추적 활성화 확인
- [ ] 에러 핸들링 구현

### 모니터링

- [ ] 대시보드 설정
- [ ] 알림 규칙 생성
- [ ] 에러 알림 설정
- [ ] 비용 알림 설정

### 평가

- [ ] 테스트 데이터셋 생성
- [ ] 평가자 정의
- [ ] 정기 평가 스케줄링
- [ ] 품질 기준선 설정

---

## 비용 최적화

### 추적 샘플링

프로덕션에서 모든 요청을 추적하면 비용이 증가할 수 있습니다:

```python
import random

# 10% 샘플링
if random.random() < 0.1:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
```

### 캐싱

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    cache=True  # 프롬프트 캐싱 활성화
)
```

---

## 참고 자료

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/)
- [LangSmith Evaluation](https://docs.smith.langchain.com/evaluation)
- [Polly AI Assistant](https://blog.langchain.com/polly-ai-assistant/)

