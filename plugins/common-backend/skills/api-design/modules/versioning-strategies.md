# API Versioning Strategies

API 버저닝 방법과 선택 가이드.

## Versioning Methods

### 1. URL Path (Recommended)
```
GET /v1/users
GET /v2/users
```
**Pros:** 명확함, 캐시 친화적
**Cons:** URL 변경

### 2. Header
```
GET /users
Accept: application/vnd.api+json;version=1
```
**Pros:** 깔끔한 URL
**Cons:** 테스트 어려움, 캐시 복잡

### 3. Query Parameter
```
GET /users?version=1
```
**Pros:** 단순
**Cons:** 비표준, 캐시 문제

## Recommendation

```
대부분의 경우 → URL Path (/v1/)
REST 순수주의 → Header (Accept)
레거시 호환 → Query Parameter
```

## Version Lifecycle

```
v1 (Current)     → Production
v2 (Development) → Beta
v0 (Deprecated)  → Sunset 예정
```

### Deprecation Process
```
1. v2 릴리스 발표 (6개월 전)
2. v1에 Sunset 헤더 추가
3. 마이그레이션 가이드 제공
4. v1 종료 (Sunset 날짜)
```

### Sunset Header
```http
HTTP/1.1 200 OK
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Deprecation: true
Link: <https://api.example.com/v2/users>; rel="successor-version"
```

## Breaking vs Non-Breaking Changes

### Non-Breaking (버전 업 불필요)
- 새 필드 추가
- 새 엔드포인트 추가
- Optional 파라미터 추가

### Breaking (버전 업 필요)
- 필드 제거/이름 변경
- 필수 파라미터 추가
- 응답 구조 변경
- 동작 변경

## Compatibility Strategies

### Additive Changes
```json
// v1
{ "id": 1, "name": "John" }

// v1.1 (호환)
{ "id": 1, "name": "John", "email": "john@example.com" }
```

### Field Aliasing
```json
// 이전 이름 유지
{
  "id": 1,
  "user_name": "john",      // deprecated
  "username": "john"        // new
}
```

### Expand Pattern
```
GET /users/123?expand=orders,profile

{
  "id": 123,
  "name": "John",
  "orders": [...],
  "profile": {...}
}
```

## Multiple Versions Support

### Router Setup
```python
# FastAPI
app.include_router(v1_router, prefix="/v1")
app.include_router(v2_router, prefix="/v2")
```

### Shared Logic
```
/v1/users → UserServiceV1 → UserRepository
/v2/users → UserServiceV2 → UserRepository
                            ↑
                      공유 데이터 계층
```

## Best Practices

1. **버전 1부터 시작**: `/v1/` not `/v0/`
2. **Major 버전만**: `/v1/`, `/v2/` (not `/v1.1/`)
3. **충분한 유예 기간**: 최소 6개월
4. **명확한 문서화**: 변경 내역, 마이그레이션 가이드
5. **Sunset 헤더 사용**: 자동화된 경고
