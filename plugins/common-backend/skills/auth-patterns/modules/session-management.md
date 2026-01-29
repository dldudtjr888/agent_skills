# Session Management

세션 기반 인증과 보안 패턴.

## Session vs JWT

| Aspect | Session | JWT |
|--------|---------|-----|
| 저장 위치 | 서버 (Redis, DB) | 클라이언트 |
| 확장성 | 분산 저장소 필요 | Stateless |
| 무효화 | 즉시 가능 | 어려움 |
| 크기 | 작음 (ID만) | 큼 (payload 포함) |
| 보안 | 서버 제어 | 클라이언트 노출 |

## Session Flow

```
1. Login
   Client → Server: credentials
   Server: Create session, store in Redis
   Server → Client: Set-Cookie: session_id=xxx

2. Subsequent Requests
   Client → Server: Cookie: session_id=xxx
   Server: Lookup session in Redis
   Server: Return user data

3. Logout
   Server: Delete session from Redis
   Server → Client: Clear cookie
```

## Session Storage

### Redis (Recommended)
```python
import redis

redis_client = redis.Redis()

def create_session(user_id):
    session_id = generate_secure_id()
    session_data = {"user_id": user_id, "created_at": time.time()}
    redis_client.setex(
        f"session:{session_id}",
        SESSION_TTL,  # 30분
        json.dumps(session_data)
    )
    return session_id

def get_session(session_id):
    data = redis_client.get(f"session:{session_id}")
    if data:
        # 세션 갱신 (sliding expiration)
        redis_client.expire(f"session:{session_id}", SESSION_TTL)
        return json.loads(data)
    return None

def delete_session(session_id):
    redis_client.delete(f"session:{session_id}")
```

### Database
```sql
CREATE TABLE sessions (
    id text PRIMARY KEY,
    user_id bigint REFERENCES users(id),
    data jsonb,
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz NOT NULL
);

CREATE INDEX sessions_user_id_idx ON sessions(user_id);
CREATE INDEX sessions_expires_at_idx ON sessions(expires_at);
```

## Cookie Security

### Secure Attributes
```
Set-Cookie: session_id=xxx;
    HttpOnly;        # JavaScript 접근 불가 (XSS 방지)
    Secure;          # HTTPS만
    SameSite=Strict; # CSRF 방지
    Path=/;
    Max-Age=1800     # 30분
```

### SameSite Options
| Value | Description |
|-------|-------------|
| Strict | 동일 사이트 요청만 쿠키 전송 |
| Lax | GET 요청은 허용 (기본값) |
| None | 모든 요청에 쿠키 전송 (Secure 필수) |

## Session Attacks & Mitigations

### Session Fixation
```
공격: 공격자가 세션 ID를 피해자에게 강제
방어: 로그인 시 새 세션 ID 발급
```

```python
def login(credentials):
    user = authenticate(credentials)
    if user:
        # 기존 세션 무효화
        if current_session_id:
            delete_session(current_session_id)
        # 새 세션 생성
        new_session_id = create_session(user.id)
        return new_session_id
```

### Session Hijacking
```
공격: 세션 ID 탈취 (네트워크 스니핑)
방어: HTTPS, Secure 쿠키, IP/User-Agent 검증
```

```python
def validate_session(session_id, request):
    session = get_session(session_id)
    if not session:
        return None

    # IP 변경 감지
    if session.get('ip') != request.remote_addr:
        delete_session(session_id)
        return None

    # User-Agent 변경 감지
    if session.get('user_agent') != request.user_agent:
        delete_session(session_id)
        return None

    return session
```

### CSRF (Cross-Site Request Forgery)
```
공격: 다른 사이트에서 인증된 요청 전송
방어: CSRF 토큰, SameSite 쿠키
```

```python
# CSRF Token 생성
def get_csrf_token(session_id):
    token = generate_secure_token()
    redis_client.setex(f"csrf:{session_id}", 3600, token)
    return token

# CSRF Token 검증
def validate_csrf(session_id, token):
    stored = redis_client.get(f"csrf:{session_id}")
    return stored and stored == token

# 사용
@app.post("/api/transfer")
def transfer(request):
    if not validate_csrf(request.session_id, request.csrf_token):
        raise CSRFError()
```

## Session Lifecycle

### Sliding Expiration
```python
# 활동 시 세션 연장
def refresh_session(session_id):
    redis_client.expire(f"session:{session_id}", SESSION_TTL)
```

### Absolute Expiration
```python
# 최대 수명 제한
def create_session(user_id):
    session_data = {
        "user_id": user_id,
        "created_at": time.time(),
        "absolute_expiry": time.time() + MAX_SESSION_AGE  # 24시간
    }

def validate_session(session_id):
    session = get_session(session_id)
    if session and time.time() > session['absolute_expiry']:
        delete_session(session_id)
        return None
    return session
```

### Concurrent Session Control
```python
# 사용자당 최대 세션 수 제한
def create_session(user_id):
    # 기존 세션 조회
    sessions = redis_client.keys(f"session:*:user:{user_id}")
    if len(sessions) >= MAX_SESSIONS:
        # 가장 오래된 세션 삭제
        oldest = min(sessions, key=lambda s: get_session(s)['created_at'])
        delete_session(oldest)

    session_id = create_session_impl(user_id)
    return session_id
```

## Logout

### Single Device
```python
def logout(session_id):
    delete_session(session_id)
    # 쿠키 삭제
    response.delete_cookie('session_id')
```

### All Devices
```python
def logout_all(user_id):
    # 사용자의 모든 세션 삭제
    sessions = redis_client.keys(f"session:*:user:{user_id}")
    for session_id in sessions:
        redis_client.delete(session_id)
```
