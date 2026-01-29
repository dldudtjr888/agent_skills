---
name: deployment-patterns
description: |
  배포 패턴 가이드. Docker 베스트 프랙티스, Kubernetes 개념, 12-Factor App, Blue-Green/Canary.
version: 1.0.0
category: deployment
user-invocable: true
triggers:
  keywords:
    - deployment
    - 배포
    - docker
    - dockerfile
    - kubernetes
    - k8s
    - container
    - 컨테이너
    - twelve factor
    - 12 factor
    - blue green
    - canary
    - rolling update
  intentPatterns:
    - "(설정|구성).*(Docker|컨테이너|K8s)"
    - "(전략|패턴).*(배포|롤아웃)"
---

# Deployment Patterns Guide

Docker, Kubernetes, 배포 전략의 핵심 패턴.

## Quick Reference

### Dockerfile Best Practices
```dockerfile
# Multi-stage build
FROM python:3.11 AS builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
RUN useradd -m appuser
USER appuser
COPY . .
CMD ["python", "app.py"]
```

### Kubernetes Essentials
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 5
```

### 12-Factor App
1. Codebase - 하나의 코드베이스
2. Dependencies - 명시적 의존성
3. Config - 환경 변수
4. Backing Services - 첨부 리소스
5. Build/Release/Run - 단계 분리
6. Processes - 무상태 프로세스
7. Port Binding - 포트 바인딩
8. Concurrency - 프로세스 모델
9. Disposability - 빠른 시작/종료
10. Dev/Prod Parity - 환경 일치
11. Logs - 이벤트 스트림
12. Admin Processes - 일회성 관리

### Deployment Strategies
| Strategy | Downtime | Risk | Rollback |
|----------|----------|------|----------|
| Rolling | No | Medium | Slow |
| Blue-Green | No | Low | Instant |
| Canary | No | Low | Fast |
| Recreate | Yes | High | N/A |

## 관련 에이전트
- `@deployment-advisor` - 배포 전략 조언
