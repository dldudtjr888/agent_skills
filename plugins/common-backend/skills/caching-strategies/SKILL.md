---
name: caching-strategies
description: |
  캐싱 전략 전문 가이드 — Cache-Aside, Write-Through/Behind, 무효화 전략, TTL 설계, 키 설계 패턴.
  Redis/Memcached 실전 패턴 포함. Rust의 zero-copy 캐시 직렬화가 핵심 차별점.
  MUST USE when: (1) Redis/Memcached 캐시 레이어 도입 시, (2) 캐시 무효화 전략(TTL/이벤트/태그) 결정 시,
  (3) Cache-Aside vs Write-Through 패턴 선택 시, (4) 캐시 키 네이밍 컨벤션 설계 시,
  (5) 캐시 스탬피드/thundering herd 방지 시, (6) 응답 속도가 느려서 캐싱을 고려할 때.
  TTL을 감으로 정하지 마라 — 데이터 타입별 가이드라인이 이 스킬에 있다.
version: 1.1.0
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

## When NOT to Use

- **단순 인메모리 변수 캐시** → 언어 내장 dict/HashMap으로 충분
- **CDN/브라우저 캐싱** → 프론트엔드/인프라 레벨 가이드 참조
- **데이터베이스 쿼리 최적화** → `database-design` 스킬의 인덱싱 전략 사용
- **세션 저장소로서의 Redis** → `auth-patterns` 스킬의 세션 관리 참조

## 관련 에이전트
- `@performance-analyst` - 캐싱 전략 분석
