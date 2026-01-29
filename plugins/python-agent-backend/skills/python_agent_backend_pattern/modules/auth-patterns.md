# Authentication & Authorization Patterns

> 메인 스킬: `../SKILL.md`

## JWT 인증

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class TokenPayload(BaseModel):
    sub: str          # user_id
    role: str = "user"

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 사용
@router.get("/me")
async def get_me(user: TokenPayload = Depends(get_current_user)):
    return {"user_id": user.sub, "role": user.role}
```

## Role-Based Access Control

```python
from enum import StrEnum

class Role(StrEnum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

ROLE_HIERARCHY: dict[Role, set[str]] = {
    Role.ADMIN: {"read", "write", "delete", "admin"},
    Role.MODERATOR: {"read", "write", "delete"},
    Role.USER: {"read", "write"},
}

def require_permission(permission: str):
    """Depends 팩토리: 권한 검증"""
    async def checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        allowed = ROLE_HIERARCHY.get(Role(user.role), set())
        if permission not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker

# 사용
@router.delete("/{market_id}", status_code=204)
async def delete_market(
    market_id: int,
    user: TokenPayload = Depends(require_permission("delete")),
    service: MarketService = Depends(get_market_service),
):
    await service.delete(market_id)
```

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})

# 사용
@router.get("/")
@limiter.limit("100/minute")
async def list_markets(request: Request):
    ...
```
