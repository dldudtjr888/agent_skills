---
name: api-design
description: |
  API 설계 가이드. REST 원칙, GraphQL 개념, 버저닝, 문서화.
  언어/프레임워크 무관 개념 + Python/Rust 치트시트 포함.
version: 1.0.0
category: api
user-invocable: true
triggers:
  keywords:
    - api design
    - rest
    - restful
    - graphql
    - endpoint
    - 엔드포인트
    - api versioning
    - openapi
    - swagger
    - api documentation
  intentPatterns:
    - "(설계|디자인).*(API|엔드포인트)"
    - "(작성|생성).*(REST|GraphQL)"
    - "(문서화).*(API|스웨거)"
---

# API Design Guide

REST/GraphQL API 설계의 핵심 원칙과 패턴.

## 목차

| Module | 설명 |
|--------|------|
| [rest-principles](modules/rest-principles.md) | REST 설계 원칙 |
| [graphql-concepts](modules/graphql-concepts.md) | GraphQL 스키마, 쿼리 |
| [versioning-strategies](modules/versioning-strategies.md) | API 버저닝 |
| [documentation-patterns](modules/documentation-patterns.md) | OpenAPI, 문서화 |

## Quick References

| Reference | 설명 |
|-----------|------|
| [http-status-guide](references/http-status-guide.md) | HTTP 상태 코드 가이드 |
| [naming-conventions](references/naming-conventions.md) | URL/파라미터 네이밍 |
| [openapi-template](references/openapi-template.md) | OpenAPI 템플릿 |
| [python-cheatsheet](references/python-cheatsheet.md) | FastAPI, Flask |
| [rust-cheatsheet](references/rust-cheatsheet.md) | Axum, Actix-web |

## 핵심 원칙

### REST API
- 리소스 명사, 복수형: `/users`, `/orders`
- HTTP 메서드로 동작 표현: GET, POST, PUT, DELETE
- 일관된 에러 응답 형식
- 버저닝 전략 수립

### GraphQL
- 단일 엔드포인트: `/graphql`
- 클라이언트가 필요한 데이터만 요청
- 타입 시스템으로 문서화
- N+1 쿼리 방지 (DataLoader)

## 관련 에이전트

- `@api-design-reviewer` - API 설계 리뷰
