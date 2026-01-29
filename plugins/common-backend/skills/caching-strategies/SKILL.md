---
name: caching-strategies
description: |
  캐싱 전략 가이드. Cache-Aside, Write-Through, 무효화 전략, TTL 설계.
version: 1.0.0
category: performance
user-invocable: true
triggers:
  keywords:
    - cache
    - caching
    - 캐시
    - 캐싱
    - redis
    - memcached
    - invalidation
    - 무효화
    - ttl
  intentPatterns:
    - "(구현|설계).*(캐시|캐싱)"
    - "(전략|패턴).*(무효화|TTL)"
---

# Caching Strategies Guide

캐싱 패턴과 무효화 전략.

## Cache Patterns

### Cache-Aside (Lazy Loading)
```
1. 캐시 확인
2. 없으면 DB 조회
3. 캐시에 저장
4. 반환
```

### Write-Through
```
1. DB에 쓰기
2. 캐시 갱신
```

### Write-Behind (Write-Back)
```
1. 캐시에 쓰기
2. 비동기로 DB 반영
```

## Cache-Aside 구현

```python
def get_user(user_id):
    # 1. 캐시 확인
    cached = cache.get(f"user:{user_id}")
    if cached:
        return cached

    # 2. DB 조회
    user = db.get_user(user_id)

    # 3. 캐시 저장
    cache.set(f"user:{user_id}", user, ttl=300)

    return user
```

## Invalidation Strategies

### TTL-Based
```python
cache.set(key, value, ttl=300)  # 5분 후 만료
```

### Event-Based
```python
def update_user(user_id, data):
    db.update(user_id, data)
    cache.delete(f"user:{user_id}")
```

### Tag-Based
```python
cache.set(key, value, tags=["user:123"])
cache.invalidate_tag("user:123")  # 관련 캐시 모두 삭제
```

## TTL Guidelines

| Data Type | TTL |
|-----------|-----|
| 정적 설정 | 1시간+ |
| 사용자 프로필 | 5-15분 |
| 세션 데이터 | 30분 |
| 실시간 데이터 | 캐시 X 또는 초단위 |

## Cache Key Design

```
# 패턴
{namespace}:{entity}:{id}:{version}

# 예시
user:profile:123
order:list:user:123:page:1
product:detail:456:v2
```

## 관련 에이전트
- `@performance-analyst` - 캐싱 전략 분석
