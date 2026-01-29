# API Naming Conventions

## URL Path

### Rules
```
✅ 소문자
✅ 하이픈(-) 구분
✅ 복수형 명사
✅ 리소스 중심

❌ 대문자
❌ 언더스코어(_)
❌ 동사
❌ 파일 확장자
```

### Examples
```
✅ /users
✅ /user-profiles
✅ /order-items

❌ /Users
❌ /user_profiles
❌ /getUsers
❌ /users.json
```

## Query Parameters

### Rules
```
snake_case 또는 camelCase (일관성 유지)
```

### Common Parameters
```
?page=1&per_page=20      # 페이지네이션
?sort=-created_at        # 정렬 (- = DESC)
?filter[status]=active   # 필터
?fields=id,name,email    # 필드 선택
?include=orders,profile  # 관계 포함
```

## Request/Response Body

### JSON Fields
```json
// snake_case (Python 스타일)
{
  "user_id": 123,
  "first_name": "John",
  "created_at": "2024-01-01T00:00:00Z"
}

// camelCase (JavaScript 스타일)
{
  "userId": 123,
  "firstName": "John",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

### Boolean Fields
```json
{
  "is_active": true,     // is_ prefix
  "has_orders": true,    // has_ prefix
  "can_edit": false      // can_ prefix
}
```

### Date/Time
```json
{
  "created_at": "2024-01-01T00:00:00Z",  // ISO 8601
  "updated_at": "2024-01-01T12:30:00+09:00"
}
```

## Headers

```
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
X-Request-ID: uuid
X-API-Key: key
```

## Error Codes

```
VALIDATION_ERROR
AUTHENTICATION_ERROR
AUTHORIZATION_ERROR
NOT_FOUND
CONFLICT
RATE_LIMIT_EXCEEDED
INTERNAL_ERROR
```
