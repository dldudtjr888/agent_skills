# common-backend

공통 백엔드 패턴 플러그인 - 언어에 무관한 백엔드 설계 패턴 및 가이드

## 설치

```bash
/plugin install common-backend@hibye-plugins
```

## 개요

이 플러그인은 Python, Rust, Java, Go 등 어떤 언어로 백엔드를 개발하든 공통적으로 적용되는 설계 패턴과 가이드를 제공합니다.

- **개념 중심**: 언어 무관한 설계 원칙과 패턴
- **언어별 치트시트**: Python, Rust 구현 예시 포함
- **리뷰 에이전트**: 설계 리뷰 및 조언 제공

## 스킬 (8개)

| 스킬 | 설명 | 키워드 |
|------|------|--------|
| `database-design` | 스키마 설계, 정규화, 인덱싱, 마이그레이션 | schema, normalization, index |
| `auth-patterns` | OAuth2, JWT, RBAC/ABAC, 세션 관리 | oauth, jwt, rbac, session |
| `api-design` | REST 원칙, GraphQL, 버저닝, 문서화 | rest, graphql, openapi |
| `caching-strategies` | 캐시 패턴, 무효화, TTL 설계 | cache, redis, invalidation |
| `message-queue-patterns` | Pub/Sub, 이벤트 드리븐, Saga | kafka, rabbitmq, event-driven |
| `deployment-patterns` | Docker, K8s, 12-Factor, Blue-Green | docker, kubernetes, container |
| `cicd-patterns` | 파이프라인, 테스트 전략, 배포 자동화 | cicd, pipeline, github-actions |
| `observability` | 로깅, 메트릭, 트레이싱, 알림 | logging, metrics, tracing |

## 에이전트 (5개)

| 에이전트 | 역할 |
|----------|------|
| `api-design-reviewer` | API 설계 리뷰 (REST/GraphQL 베스트 프랙티스) |
| `database-reviewer` | DB 스키마/쿼리 리뷰 (정규화, 인덱싱, 성능) |
| `security-reviewer` | 보안 아키텍처 리뷰 (인증, OWASP) |
| `deployment-advisor` | 배포 전략 조언 (Docker, K8s, CI/CD) |
| `performance-analyst` | 성능 분석 (캐싱, 쿼리, 확장성) |

## 다른 플러그인과의 관계

```
common-backend (개념/패턴)
       ↓ 참조
python-agent-backend (파이썬 구현)
rust-backend (러스트 구현)
```

**예시**: JWT 인증 구현 시
1. `common-backend/auth-patterns` → 개념 이해
2. `python-agent-backend` 또는 `rust-backend` → 언어별 구현

## 구조

```
common-backend/
├── agents/           # 리뷰/분석 에이전트
├── skills/           # 8개 스킬
│   └── {skill}/
│       ├── SKILL.md
│       ├── modules/  # 개념 가이드
│       └── references/  # 치트시트, 템플릿
└── README.md
```
