# Middleware

LangChain 1.0 핵심 기능. 에이전트 실행 각 단계에 훅 추가.

## Basic Usage

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, PIIMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[
        SummarizationMiddleware(...),
        PIIMiddleware(...),
    ],
)
```

## SummarizationMiddleware

토큰 한도 도달 시 대화 자동 요약.

```python
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search, calculator],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",           # 요약용 모델 (저렴한 모델 권장)
            trigger=("tokens", 4000),      # 4000 토큰 초과 시 트리거
            keep=("messages", 20),         # 최근 20개 메시지 유지
        ),
    ],
)
```

## PIIMiddleware

개인정보(PII) 탐지 및 처리.

```python
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        # 이메일 마스킹
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        # 신용카드 마스킹
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
    ],
)

# 커스텀 PII 타입 (정규식)
agent = create_agent(
    model="gpt-4o",
    middleware=[
        PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block"),
    ],
)
```

### PIIMiddleware Parameters

| Parameter | Options |
|-----------|---------|
| `pii_type` | "email", "credit_card", "ip", "mac_address", "url" |
| `strategy` | "block", "redact", "mask", "hash" |
| `apply_to_input` | True/False |
| `apply_to_output` | True/False |
| `detector` | 커스텀 정규식 |

## Built-in Middleware

| Middleware | 용도 |
|------------|------|
| `SummarizationMiddleware` | 대화 요약 |
| `PIIMiddleware` | 개인정보 처리 |
| `HumanInTheLoopMiddleware` | 승인 필요 단계 |
| `ToolRetryMiddleware` | 도구 재시도 |
| `ModelFallbackMiddleware` | 폴백 모델 |
| `ModelCallLimitMiddleware` | 호출 제한 |

## Docs

- https://docs.langchain.com/oss/python/langchain/middleware/built-in
- https://reference.langchain.com/python/langchain/middleware/
