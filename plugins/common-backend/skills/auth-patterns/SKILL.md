---
name: auth-patterns
description: |
  인증/인가 패턴 가이드. OAuth2, JWT, RBAC/ABAC, 세션 관리.
  프레임워크 무관 개념 + Python/Rust 치트시트 포함.
version: 1.0.0
category: security
user-invocable: true
triggers:
  keywords:
    - authentication
    - authorization
    - 인증
    - 인가
    - oauth
    - oauth2
    - jwt
    - rbac
    - abac
    - session
    - 세션
    - token
    - 토큰
    - login
    - 로그인
    - logout
    - password
    - 비밀번호
  intentPatterns:
    - "(구현|설계).*(인증|로그인|토큰)"
    - "(적용|추가).*(권한|RBAC|ABAC)"
    - "(관리).*(세션|토큰)"
---

# Authentication & Authorization Patterns

인증(Authentication)과 인가(Authorization)의 핵심 개념과 구현 패턴.

## 목차

| Module | 설명 |
|--------|------|
| [oauth2-flows](modules/oauth2-flows.md) | OAuth2 인증 플로우 |
| [jwt-patterns](modules/jwt-patterns.md) | JWT 구조, 검증, 저장 |
| [rbac-abac](modules/rbac-abac.md) | 역할/속성 기반 접근 제어 |
| [session-management](modules/session-management.md) | 세션 관리, 보안 |

## Quick References

| Reference | 설명 |
|-----------|------|
| [security-checklist](references/security-checklist.md) | 인증 구현 체크리스트 |
| [token-comparison](references/token-comparison.md) | JWT vs 세션 vs API Key |
| [python-cheatsheet](references/python-cheatsheet.md) | PyJWT, Authlib |
| [rust-cheatsheet](references/rust-cheatsheet.md) | jsonwebtoken, oauth2-rs |

## 핵심 개념

### Authentication vs Authorization
- **Authentication (인증)**: "당신이 누구인가?" - 신원 확인
- **Authorization (인가)**: "당신이 무엇을 할 수 있는가?" - 권한 확인

### Token Types
| Type | Use Case | Lifetime |
|------|----------|----------|
| Access Token | API 요청 인증 | 짧음 (15분~1시간) |
| Refresh Token | Access Token 갱신 | 김 (7일~30일) |
| ID Token | 사용자 정보 (OIDC) | 짧음 |

## Workflow

```
1. 인증 방식 선택
   ├── 웹앱 → OAuth2 + Session/JWT
   ├── SPA → OAuth2 PKCE + JWT
   ├── 모바일 → OAuth2 PKCE + Refresh Token
   └── Server-to-Server → Client Credentials

2. 토큰 저장소 선택
   ├── 웹앱 → HttpOnly Cookie
   └── 모바일 → Secure Storage

3. 권한 모델 선택
   ├── 단순 → RBAC
   └── 복잡 → ABAC
```

## 관련 에이전트

- `@security-reviewer` - 인증/인가 보안 리뷰
