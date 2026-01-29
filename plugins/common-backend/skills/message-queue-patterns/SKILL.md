---
name: message-queue-patterns
description: |
  메시지 큐 패턴 가이드. Pub/Sub, 이벤트 드리븐, 비동기 패턴, Saga.
version: 1.0.0
category: messaging
user-invocable: true
triggers:
  keywords:
    - message queue
    - 메시지 큐
    - pubsub
    - event driven
    - 이벤트 드리븐
    - kafka
    - rabbitmq
    - sqs
    - saga
    - async
    - background job
  intentPatterns:
    - "(구현|설계).*(메시지|이벤트|큐)"
    - "(적용|사용).*(Pub/Sub|비동기)"
---

# Message Queue Patterns Guide

메시지 큐와 이벤트 드리븐 아키텍처 패턴.

## Message Patterns

### Point-to-Point (Queue)
```
Producer → Queue → Consumer
- 하나의 Consumer만 메시지 처리
- 작업 분산
```

### Pub/Sub (Topic)
```
Publisher → Topic → Subscriber 1
                 → Subscriber 2
                 → Subscriber 3
- 모든 Subscriber가 메시지 수신
- 이벤트 브로드캐스팅
```

## Delivery Guarantees

| Guarantee | Description | Use Case |
|-----------|-------------|----------|
| At-most-once | 최대 1번 (손실 가능) | 로그 |
| At-least-once | 최소 1번 (중복 가능) | 대부분 |
| Exactly-once | 정확히 1번 | 결제 |

## Event-Driven Patterns

### Event Sourcing
```
- 상태 대신 이벤트 저장
- 이벤트 재생으로 상태 복원
- 완전한 감사 추적
```

### CQRS
```
Command (Write) → Event Store
Query (Read)   ← Read Model (Projection)
```

### Saga Pattern
```
Choreography:
  Order → Payment → Inventory → Shipping
  (각 서비스가 다음 이벤트 발행)

Orchestration:
  Saga Orchestrator가 각 단계 조율
  실패 시 보상 트랜잭션 실행
```

## Queue Comparison

| Feature | Kafka | RabbitMQ | SQS |
|---------|-------|----------|-----|
| 처리량 | 높음 | 중간 | 중간 |
| 지연 | 낮음 | 낮음 | 중간 |
| 순서 보장 | 파티션 내 | 큐 내 | FIFO만 |
| 메시지 보존 | 설정 가능 | 소비 후 삭제 | 14일 |
| 관리 | 복잡 | 중간 | 관리형 |

## Best Practices

### Idempotency
```python
def handle_message(message):
    if db.exists(f"processed:{message.id}"):
        return  # 이미 처리됨

    process(message)
    db.set(f"processed:{message.id}", 1, ttl=86400)
```

### Dead Letter Queue
```
실패한 메시지 → DLQ로 이동
- 나중에 수동 처리
- 디버깅/분석
```

### Retry with Backoff
```
1차 시도 → 실패
1초 대기 → 재시도 → 실패
2초 대기 → 재시도 → 실패
4초 대기 → 재시도 → 실패
DLQ로 이동
```

## 관련 에이전트
- `@performance-analyst` - 메시지 처리 성능 분석
