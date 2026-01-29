# REST Principles

RESTful API 설계 핵심 원칙.

## Resource Naming

### Use Nouns, Not Verbs
```
❌ GET /getUsers
❌ POST /createUser
❌ DELETE /deleteUser/123

✅ GET /users
✅ POST /users
✅ DELETE /users/123
```

### Use Plural Forms
```
✅ /users
✅ /orders
✅ /products

❌ /user
❌ /order
```

### Use Lowercase and Hyphens
```
✅ /user-profiles
✅ /order-items

❌ /userProfiles
❌ /user_profiles
```

## HTTP Methods

| Method | Purpose | Idempotent | Safe |
|--------|---------|------------|------|
| GET | Read resource | Yes | Yes |
| POST | Create resource | No | No |
| PUT | Replace resource | Yes | No |
| PATCH | Partial update | Yes | No |
| DELETE | Delete resource | Yes | No |

### Examples
```
GET    /users           # List users
GET    /users/123       # Get user 123
POST   /users           # Create user
PUT    /users/123       # Replace user 123
PATCH  /users/123       # Update user 123
DELETE /users/123       # Delete user 123
```

## URL Hierarchy

### Relationships
```
GET /users/123/orders          # Orders of user 123
GET /users/123/orders/456      # Order 456 of user 123
POST /users/123/orders         # Create order for user 123
```

### Avoid Deep Nesting (max 3 levels)
```
❌ /users/123/orders/456/items/789/reviews

✅ /order-items/789/reviews
```

## Query Parameters

### Filtering
```
GET /orders?status=pending
GET /orders?status=pending&created_after=2024-01-01
```

### Sorting
```
GET /orders?sort=created_at      # Ascending
GET /orders?sort=-created_at     # Descending
GET /orders?sort=-created_at,total
```

### Pagination
```
# Offset-based
GET /orders?page=2&per_page=20

# Cursor-based (recommended)
GET /orders?cursor=abc123&limit=20
```

### Field Selection
```
GET /users/123?fields=id,name,email
```

## Response Format

### Single Resource
```json
{
  "data": {
    "id": 123,
    "name": "John",
    "email": "john@example.com"
  }
}
```

### Collection
```json
{
  "data": [
    {"id": 1, "name": "John"},
    {"id": 2, "name": "Jane"}
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  },
  "links": {
    "next": "/users?page=2",
    "prev": null
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

## HATEOAS

### Include Links
```json
{
  "data": {
    "id": 123,
    "name": "John"
  },
  "links": {
    "self": "/users/123",
    "orders": "/users/123/orders",
    "profile": "/users/123/profile"
  }
}
```

## Idempotency

### Idempotent Methods
```
GET, PUT, DELETE는 여러 번 호출해도 결과 동일

PUT /users/123 { "name": "John" }
# 여러 번 호출해도 항상 같은 결과
```

### Non-Idempotent (POST)
```
POST /orders { ... }
# 매번 새 주문 생성

# Idempotency-Key 헤더로 중복 방지
POST /orders
Idempotency-Key: unique-key-123
```
