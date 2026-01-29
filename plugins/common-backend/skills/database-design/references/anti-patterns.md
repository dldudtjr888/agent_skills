# Database Anti-Patterns

## Schema Anti-Patterns

### ❌ int for IDs
```sql
-- BAD
id int PRIMARY KEY  -- 2.1B 한계

-- GOOD
id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

### ❌ varchar(255) without reason
```sql
-- BAD
name varchar(255)  -- 왜 255?

-- GOOD
name text  -- 제한 불필요
```

### ❌ timestamp without timezone
```sql
-- BAD
created_at timestamp  -- 타임존 정보 손실

-- GOOD
created_at timestamptz DEFAULT now()
```

### ❌ float for money
```sql
-- BAD
price float  -- 0.1 + 0.2 != 0.3

-- GOOD
price numeric(10,2)
```

### ❌ Random UUID as PK
```sql
-- BAD (인덱스 파편화)
id uuid DEFAULT gen_random_uuid()

-- GOOD (시간 순서)
id uuid DEFAULT uuid_generate_v7()
```

## Query Anti-Patterns

### ❌ SELECT *
```sql
-- BAD
SELECT * FROM users WHERE id = 1;

-- GOOD
SELECT id, name, email FROM users WHERE id = 1;
```

### ❌ N+1 Queries
```sql
-- BAD
SELECT id FROM users;
-- Then for each user:
SELECT * FROM orders WHERE user_id = ?;

-- GOOD
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
```

### ❌ OFFSET Pagination
```sql
-- BAD (깊은 페이지 느림)
SELECT * FROM orders LIMIT 20 OFFSET 100000;

-- GOOD (커서 기반)
SELECT * FROM orders WHERE id > 100000 LIMIT 20;
```

### ❌ Unparameterized Queries
```sql
-- BAD (SQL Injection)
f"SELECT * FROM users WHERE email = '{email}'"

-- GOOD
"SELECT * FROM users WHERE email = :email"
```

## Index Anti-Patterns

### ❌ Missing FK Index
```sql
-- BAD
user_id bigint REFERENCES users(id)
-- FK 컬럼에 인덱스 없으면 JOIN 느림

-- GOOD
CREATE INDEX orders_user_id_idx ON orders(user_id);
```

### ❌ Over-indexing
```sql
-- BAD: 모든 컬럼에 개별 인덱스
CREATE INDEX idx1 ON t(a);
CREATE INDEX idx2 ON t(b);
CREATE INDEX idx3 ON t(a,b);
CREATE INDEX idx4 ON t(b,a);

-- 쓰기 성능 저하, 저장 공간 낭비
```

### ❌ Wrong Column Order
```sql
-- Query: WHERE a = ? AND b > ?

-- BAD
CREATE INDEX idx ON t(b, a);  -- 범위 컬럼 먼저

-- GOOD
CREATE INDEX idx ON t(a, b);  -- 동등 컬럼 먼저
```

## Security Anti-Patterns

### ❌ GRANT ALL
```sql
-- BAD
GRANT ALL PRIVILEGES ON ALL TABLES TO app_user;

-- GOOD: 최소 권한
GRANT SELECT, INSERT ON orders TO app_user;
```

### ❌ No RLS on Multi-Tenant
```sql
-- BAD: 애플리케이션에서만 필터
SELECT * FROM data WHERE tenant_id = ?;

-- GOOD: DB 레벨 격리
ALTER TABLE data ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON data
  USING (tenant_id = current_setting('app.tenant_id')::bigint);
```

## Connection Anti-Patterns

### ❌ No Connection Pooling
```python
# BAD: 매 요청마다 새 연결
def handle_request():
    conn = psycopg2.connect(...)
    # ...
    conn.close()

# GOOD: 풀 사용
pool = ConnectionPool(min=5, max=20)
```

### ❌ Long-Running Transactions
```python
# BAD: 트랜잭션 내 외부 API 호출
with db.transaction():
    order = db.get(order_id)
    payment = call_payment_api(order)  # 5초 걸림
    order.status = 'paid'

# GOOD: 트랜잭션 최소화
payment = call_payment_api(order_id)
with db.transaction():
    db.update(order_id, status='paid', payment_id=payment.id)
```
