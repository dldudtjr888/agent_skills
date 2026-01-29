# Schema Design

테이블 설계, 관계 정의, 제약조건 설정의 핵심 패턴.

## Primary Key Strategy

### Identity (권장 - 단일 DB)
```sql
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
);
```

### UUIDv7 (분산 시스템)
```sql
-- 시간 순서 보장, 인덱스 친화적
CREATE TABLE orders (
  id uuid DEFAULT uuid_generate_v7() PRIMARY KEY
);
```

### Avoid: Random UUID
```sql
-- BAD: 인덱스 파편화
id uuid DEFAULT gen_random_uuid() PRIMARY KEY
```

## Relationships

### One-to-Many
```sql
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
);

CREATE TABLE orders (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users(id),
  -- 항상 FK에 인덱스!
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX orders_user_id_idx ON orders(user_id);
```

### Many-to-Many
```sql
CREATE TABLE users (id bigint PRIMARY KEY);
CREATE TABLE roles (id bigint PRIMARY KEY);

CREATE TABLE user_roles (
  user_id bigint REFERENCES users(id) ON DELETE CASCADE,
  role_id bigint REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);
```

### Self-Referencing
```sql
CREATE TABLE categories (
  id bigint PRIMARY KEY,
  name text NOT NULL,
  parent_id bigint REFERENCES categories(id)
);
```

## Constraints

### NOT NULL
```sql
-- 필수 필드는 NOT NULL
email text NOT NULL,
name text NOT NULL
```

### CHECK
```sql
-- 값 검증
age int CHECK (age >= 0 AND age <= 150),
status text CHECK (status IN ('pending', 'active', 'inactive'))
```

### UNIQUE
```sql
-- 고유 제약
email text UNIQUE,
-- 복합 고유
UNIQUE (tenant_id, email)
```

### Foreign Key Actions
```sql
-- CASCADE: 부모 삭제 시 자식도 삭제
REFERENCES users(id) ON DELETE CASCADE

-- SET NULL: 부모 삭제 시 NULL 설정
REFERENCES categories(id) ON DELETE SET NULL

-- RESTRICT: 자식 있으면 부모 삭제 불가 (기본값)
REFERENCES users(id) ON DELETE RESTRICT
```

## Naming Conventions

### Tables
- 소문자, snake_case
- 복수형: `users`, `orders`, `order_items`
- 혼합 대소문자 피하기 (따옴표 필요)

### Columns
- 소문자, snake_case
- Boolean: `is_active`, `has_paid`
- Timestamp: `created_at`, `updated_at`, `deleted_at`

### Indexes
```sql
-- 패턴: {table}_{column(s)}_{type}
CREATE INDEX users_email_idx ON users(email);
CREATE INDEX orders_status_created_idx ON orders(status, created_at);
```

## Common Patterns

### Soft Delete
```sql
CREATE TABLE users (
  id bigint PRIMARY KEY,
  deleted_at timestamptz DEFAULT NULL
);

-- Partial index for active records
CREATE INDEX users_active_idx ON users(id) WHERE deleted_at IS NULL;
```

### Audit Columns
```sql
CREATE TABLE orders (
  id bigint PRIMARY KEY,
  -- ... other columns ...
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL,
  created_by bigint REFERENCES users(id),
  updated_by bigint REFERENCES users(id)
);
```

### Multi-Tenant
```sql
CREATE TABLE orders (
  id bigint PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id),
  -- ... other columns ...
);

-- Tenant 컬럼은 복합 인덱스 첫 번째
CREATE INDEX orders_tenant_created_idx ON orders(tenant_id, created_at);
```
