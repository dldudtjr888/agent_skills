---
name: observability
description: |
  관측성 가이드. 로깅 패턴, 메트릭 설계, 분산 트레이싱, 알림 전략.
version: 1.0.0
category: observability
user-invocable: true
triggers:
  keywords:
    - observability
    - 관측성
    - logging
    - 로깅
    - metrics
    - 메트릭
    - tracing
    - 트레이싱
    - alerting
    - 알림
    - monitoring
    - 모니터링
    - prometheus
    - grafana
  intentPatterns:
    - "(설정|구성).*(로깅|메트릭|트레이싱)"
    - "(설계|구현).*(알림|모니터링)"
---

# Observability Guide

로깅, 메트릭, 트레이싱의 핵심 패턴.

## Three Pillars

### 1. Logs
- 이벤트 기록
- 구조화된 로깅 (JSON)
- 로그 레벨 (DEBUG, INFO, WARN, ERROR)

### 2. Metrics
- 수치 데이터
- RED Method (Rate, Errors, Duration)
- USE Method (Utilization, Saturation, Errors)

### 3. Traces
- 요청 흐름 추적
- 분산 시스템 디버깅
- Span, Trace ID

## Structured Logging

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "User logged in",
  "user_id": "123",
  "request_id": "abc-123",
  "duration_ms": 45
}
```

## Metrics Patterns

### RED Method (Request-focused)
```
- Rate: 초당 요청 수
- Errors: 에러율
- Duration: 응답 시간
```

### USE Method (Resource-focused)
```
- Utilization: CPU, 메모리 사용률
- Saturation: 큐 길이, 대기 스레드
- Errors: 시스템 에러
```

## Log Levels

| Level | Use Case |
|-------|----------|
| DEBUG | 개발 디버깅 |
| INFO | 정상 동작 기록 |
| WARN | 잠재적 문제 |
| ERROR | 오류 발생 |

## Alert Best Practices

### Good Alerts
- 실행 가능한 조치가 있음
- 비즈니스 영향이 있음
- 적절한 임계값

### Alert Fatigue 방지
- 불필요한 알림 제거
- 알림 그룹화
- 심각도 분류

## 관련 에이전트
- `@performance-analyst` - 성능 분석
