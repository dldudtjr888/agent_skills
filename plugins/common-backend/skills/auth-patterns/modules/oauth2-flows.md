# OAuth2 Flows

OAuth2 인증 플로우 선택 가이드.

## Flow Selection

| 애플리케이션 타입 | 권장 플로우 |
|-----------------|-----------|
| 서버 사이드 웹앱 | Authorization Code |
| SPA (React, Vue) | Authorization Code + PKCE |
| 모바일 앱 | Authorization Code + PKCE |
| CLI 도구 | Device Authorization |
| Server-to-Server | Client Credentials |
| 레거시 (비권장) | Resource Owner Password |

## Authorization Code Flow

가장 안전한 기본 플로우.

```
┌──────┐                              ┌──────────────┐
│ User │                              │ Auth Server  │
└──┬───┘                              └──────┬───────┘
   │                                         │
   │ 1. Login Request                        │
   │─────────────────────────────────────────>
   │                                         │
   │ 2. Redirect to Auth Server              │
   │<─────────────────────────────────────────
   │                                         │
   │ 3. User Authenticates                   │
   │─────────────────────────────────────────>
   │                                         │
   │ 4. Redirect with Authorization Code     │
   │<─────────────────────────────────────────
   │                                         │
   │        ┌────────────┐                   │
   │        │ App Server │                   │
   │        └─────┬──────┘                   │
   │              │                          │
   │              │ 5. Exchange Code         │
   │              │─────────────────────────>│
   │              │                          │
   │              │ 6. Access + Refresh Token│
   │              │<─────────────────────────│
```

### Implementation
```
1. Redirect to Authorization Endpoint
   GET /authorize
     ?response_type=code
     &client_id=xxx
     &redirect_uri=https://app.com/callback
     &scope=openid profile
     &state=random_state

2. Receive Authorization Code
   GET /callback?code=xxx&state=random_state

3. Exchange Code for Tokens
   POST /token
     grant_type=authorization_code
     &code=xxx
     &redirect_uri=https://app.com/callback
     &client_id=xxx
     &client_secret=yyy
```

## Authorization Code + PKCE

SPA, 모바일 앱용 (client_secret 없이).

```
PKCE = Proof Key for Code Exchange

1. 클라이언트가 code_verifier (랜덤 문자열) 생성
2. code_challenge = BASE64URL(SHA256(code_verifier))
3. 인증 요청에 code_challenge 포함
4. 토큰 교환에 code_verifier 포함
5. 서버가 code_verifier 검증
```

### Implementation
```
1. Generate PKCE
   code_verifier = random_string(43-128 chars)
   code_challenge = base64url(sha256(code_verifier))

2. Authorization Request
   GET /authorize
     ?response_type=code
     &client_id=xxx
     &redirect_uri=xxx
     &code_challenge=xxx
     &code_challenge_method=S256

3. Token Exchange
   POST /token
     grant_type=authorization_code
     &code=xxx
     &redirect_uri=xxx
     &client_id=xxx
     &code_verifier=xxx  (NO client_secret)
```

## Client Credentials Flow

Server-to-Server 통신용.

```
POST /token
  grant_type=client_credentials
  &client_id=xxx
  &client_secret=yyy
  &scope=api:read
```

## Refresh Token Flow

Access Token 갱신.

```
POST /token
  grant_type=refresh_token
  &refresh_token=xxx
  &client_id=xxx
```

### Refresh Token Rotation
```
매번 새 Refresh Token 발급 (권장)
1. Client: refresh_token=old_token
2. Server: Returns new_access_token + new_refresh_token
3. Server: Invalidates old_refresh_token
```

## Security Considerations

### State Parameter
```
CSRF 방지용

1. 인증 요청 전 랜덤 state 생성
2. 세션에 저장
3. 콜백에서 state 검증
```

### Token Storage
```
❌ localStorage (XSS 취약)
❌ sessionStorage (XSS 취약)
✅ HttpOnly Cookie (웹앱)
✅ Secure Storage (모바일)
```

### HTTPS Only
```
모든 OAuth2 통신은 HTTPS 필수
redirect_uri도 HTTPS
```

## Common Mistakes

### ❌ Implicit Flow 사용
```
# 더 이상 권장되지 않음
response_type=token  # BAD

# PKCE 사용
response_type=code + PKCE  # GOOD
```

### ❌ state 검증 누락
```python
# BAD
def callback(code):
    tokens = exchange_code(code)

# GOOD
def callback(code, state):
    if state != session['oauth_state']:
        raise SecurityError("Invalid state")
    tokens = exchange_code(code)
```

### ❌ redirect_uri 검증 누락
```
# 서버 측에서 허용된 redirect_uri만 처리
# Open Redirect 취약점 방지
```
