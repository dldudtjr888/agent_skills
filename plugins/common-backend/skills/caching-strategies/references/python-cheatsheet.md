# Python Caching Cheatsheet

## redis-py

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Basic operations
r.set("key", "value", ex=300)  # TTL 5분
value = r.get("key")

# JSON data
r.set("user:123", json.dumps(user_dict), ex=300)
user = json.loads(r.get("user:123") or "{}")

# Hash
r.hset("user:123", mapping={"name": "John", "email": "john@example.com"})
user = r.hgetall("user:123")

# Delete
r.delete("user:123")
r.delete("user:123", "user:456")  # Multiple
```

## Cache-Aside Pattern

```python
from functools import wraps
import redis
import json

cache = redis.Redis()

def cached(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Check cache
            cached_value = cache.get(key)
            if cached_value:
                return json.loads(cached_value)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(key, json.dumps(result), ex=ttl)

            return result
        return wrapper
    return decorator

@cached(ttl=300)
async def get_user(user_id: int):
    return await db.get_user(user_id)
```

## aiocache (Async)

```python
from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer

cache = Cache(Cache.REDIS, serializer=JsonSerializer())

@cached(ttl=300, cache=Cache.REDIS, serializer=JsonSerializer())
async def get_user(user_id: int):
    return await db.get_user(user_id)

# Manual usage
await cache.set("key", {"data": "value"}, ttl=300)
value = await cache.get("key")
await cache.delete("key")
```

## cachetools (In-Memory)

```python
from cachetools import TTLCache, cached

# In-memory cache with max 1000 items, 5 min TTL
cache = TTLCache(maxsize=1000, ttl=300)

@cached(cache)
def get_config(key: str):
    return db.get_config(key)
```

## FastAPI with Cache

```python
from fastapi import FastAPI, Depends
import redis

app = FastAPI()
cache = redis.Redis()

async def get_cached_or_fetch(key: str, fetch_func, ttl=300):
    cached = cache.get(key)
    if cached:
        return json.loads(cached)

    data = await fetch_func()
    cache.set(key, json.dumps(data), ex=ttl)
    return data

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return await get_cached_or_fetch(
        f"user:{user_id}",
        lambda: db.get_user(user_id),
        ttl=300
    )
```
