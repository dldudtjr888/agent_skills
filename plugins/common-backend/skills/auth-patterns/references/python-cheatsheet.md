# Python Auth Cheatsheet

## PyJWT

### Install
```bash
pip install pyjwt
```

### Create Token
```python
import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: str, secret: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iss": "myapp",
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

### Verify Token
```python
def verify_token(token: str, secret: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub", "iss"]}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
```

### RS256 (Asymmetric)
```python
# 서명 (private key)
token = jwt.encode(payload, private_key, algorithm="RS256")

# 검증 (public key)
payload = jwt.decode(token, public_key, algorithms=["RS256"])
```

---

## Authlib

### OAuth2 Client
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id='...',
    client_secret='...',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Redirect to Google
@app.get('/login')
async def login(request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

# Handle callback
@app.get('/callback')
async def auth_callback(request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    return user_info
```

---

## Password Hashing (bcrypt)

```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

---

## FastAPI Security

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token, SECRET_KEY)
    user = await get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/users/me")
async def read_users_me(user: User = Depends(get_current_user)):
    return user
```

---

## Session with Redis

```python
import redis
import secrets
from datetime import timedelta

redis_client = redis.Redis()
SESSION_TTL = timedelta(hours=1)

def create_session(user_id: str) -> str:
    session_id = secrets.token_urlsafe(32)
    redis_client.setex(
        f"session:{session_id}",
        SESSION_TTL,
        user_id
    )
    return session_id

def get_session(session_id: str) -> str | None:
    user_id = redis_client.get(f"session:{session_id}")
    if user_id:
        redis_client.expire(f"session:{session_id}", SESSION_TTL)
        return user_id.decode()
    return None

def delete_session(session_id: str):
    redis_client.delete(f"session:{session_id}")
```

---

## Quick Reference

| Task | Library | Example |
|------|---------|---------|
| JWT Create | pyjwt | `jwt.encode(payload, secret, algorithm="HS256")` |
| JWT Verify | pyjwt | `jwt.decode(token, secret, algorithms=["HS256"])` |
| Password Hash | bcrypt | `bcrypt.hashpw(password, bcrypt.gensalt())` |
| OAuth2 Client | authlib | `oauth.google.authorize_redirect()` |
| CSRF Token | secrets | `secrets.token_urlsafe(32)` |
