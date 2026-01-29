# JWT Patterns

JSON Web Token 구조, 검증, 저장 패턴.

## JWT Structure

```
header.payload.signature

Header (Base64):
{
  "alg": "RS256",
  "typ": "JWT"
}

Payload (Base64):
{
  "sub": "user123",
  "iat": 1609459200,
  "exp": 1609462800,
  "iss": "auth.example.com",
  "aud": "api.example.com",
  "roles": ["user", "admin"]
}

Signature:
HMACSHA256(base64(header) + "." + base64(payload), secret)
```

## Signing Algorithms

| Algorithm | Type | Use Case |
|-----------|------|----------|
| HS256 | Symmetric | 단일 서비스, 단순한 경우 |
| RS256 | Asymmetric | 마이크로서비스, 공개 검증 필요 |
| ES256 | Asymmetric | 모바일 (작은 토큰 크기) |

### HS256 (HMAC)
```
- 동일한 secret으로 서명/검증
- 단순하지만 secret 공유 필요
```

### RS256 (RSA)
```
- Private key로 서명
- Public key로 검증
- 검증 서버가 secret 없이 검증 가능
```

## Standard Claims

| Claim | Description | Required |
|-------|-------------|----------|
| `sub` | Subject (사용자 ID) | Yes |
| `iat` | Issued At (발급 시간) | Yes |
| `exp` | Expiration (만료 시간) | Yes |
| `iss` | Issuer (발급자) | Recommended |
| `aud` | Audience (수신자) | Recommended |
| `jti` | JWT ID (고유 ID) | Optional |

## Token Lifetime

| Token Type | Recommended Lifetime |
|------------|---------------------|
| Access Token | 15분 ~ 1시간 |
| Refresh Token | 7일 ~ 30일 |
| ID Token | 15분 ~ 1시간 |

## Validation Checklist

```
1. 서명 검증 (signature)
2. 만료 시간 확인 (exp)
3. 발급자 확인 (iss)
4. 수신자 확인 (aud)
5. 발급 시간 확인 (iat)
6. 알고리즘 확인 (alg != "none")
```

## Token Storage

### Web Applications
```
✅ HttpOnly Cookie
   - XSS 공격으로부터 보호
   - Secure 플래그 설정
   - SameSite=Strict 또는 Lax

Set-Cookie: access_token=xxx; HttpOnly; Secure; SameSite=Strict; Path=/
```

### SPA / Mobile
```
❌ localStorage (XSS 취약)
❌ sessionStorage (XSS 취약)
✅ Memory (새로고침 시 손실)
✅ HttpOnly Cookie (BFF 패턴)
✅ Secure Storage (모바일)
```

### BFF Pattern (Backend For Frontend)
```
┌────────┐       ┌──────────┐       ┌──────────┐
│  SPA   │──────>│   BFF    │──────>│   API    │
└────────┘       └──────────┘       └──────────┘
  Session         JWT Storage        JWT Auth
  Cookie          (서버 측)          Validation
```

## Refresh Token Rotation

```python
# 매번 새 Refresh Token 발급
def refresh_tokens(refresh_token):
    # 1. Refresh token 검증
    payload = verify_token(refresh_token)

    # 2. Refresh token 폐기 (재사용 방지)
    revoke_token(refresh_token)

    # 3. 새 토큰 쌍 발급
    new_access = create_access_token(payload['sub'])
    new_refresh = create_refresh_token(payload['sub'])

    return new_access, new_refresh
```

## Token Revocation

### Blacklist
```python
# Redis 등에 폐기된 토큰 저장
def revoke_token(token):
    jti = decode_token(token)['jti']
    redis.setex(f"revoked:{jti}", token_ttl, "1")

def is_revoked(token):
    jti = decode_token(token)['jti']
    return redis.exists(f"revoked:{jti}")
```

### Short-Lived Tokens
```
- Access Token을 짧게 (15분)
- Revocation 없이도 빠른 만료
- Refresh Token만 revocation 관리
```

## Security Considerations

### ❌ Algorithm None Attack
```python
# BAD: 알고리즘 검증 없음
jwt.decode(token, options={"verify_signature": False})

# GOOD: 알고리즘 명시
jwt.decode(token, secret, algorithms=["RS256"])
```

### ❌ Sensitive Data in Payload
```
# BAD
{
  "password": "secret123",
  "credit_card": "1234..."
}

# GOOD
{
  "sub": "user123",
  "roles": ["user"]
}
# 민감 정보는 서버에서 조회
```

### ❌ Long-Lived Access Tokens
```
# BAD: 30일 Access Token
exp = now + 30 days

# GOOD: 짧은 Access + Refresh 조합
access_exp = now + 15 minutes
refresh_exp = now + 7 days
```
