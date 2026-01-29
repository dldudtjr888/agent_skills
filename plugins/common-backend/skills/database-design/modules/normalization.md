# Normalization

데이터 중복 제거와 무결성 보장을 위한 정규화 단계.

## Normalization Forms

### 1NF (First Normal Form)
**규칙**: 모든 컬럼은 원자값만 포함

```sql
-- BAD: 배열/리스트 저장
CREATE TABLE users (
  id bigint PRIMARY KEY,
  phone_numbers text  -- "010-1234, 010-5678"
);

-- GOOD: 별도 테이블
CREATE TABLE users (id bigint PRIMARY KEY);
CREATE TABLE user_phones (
  user_id bigint REFERENCES users(id),
  phone text NOT NULL,
  PRIMARY KEY (user_id, phone)
);
```

### 2NF (Second Normal Form)
**규칙**: 1NF + 부분 종속 제거 (복합 키 일부에만 종속되는 컬럼 제거)

```sql
-- BAD: student_name은 student_id에만 종속
CREATE TABLE enrollments (
  student_id bigint,
  course_id bigint,
  student_name text,  -- 부분 종속!
  grade text,
  PRIMARY KEY (student_id, course_id)
);

-- GOOD: 분리
CREATE TABLE students (
  id bigint PRIMARY KEY,
  name text NOT NULL
);
CREATE TABLE enrollments (
  student_id bigint REFERENCES students(id),
  course_id bigint REFERENCES courses(id),
  grade text,
  PRIMARY KEY (student_id, course_id)
);
```

### 3NF (Third Normal Form)
**규칙**: 2NF + 이행 종속 제거 (비키 컬럼이 다른 비키 컬럼에 종속)

```sql
-- BAD: city는 zip_code에 종속 (이행 종속)
CREATE TABLE customers (
  id bigint PRIMARY KEY,
  zip_code text,
  city text  -- zip_code에 종속!
);

-- GOOD: 분리
CREATE TABLE zip_codes (
  code text PRIMARY KEY,
  city text NOT NULL
);
CREATE TABLE customers (
  id bigint PRIMARY KEY,
  zip_code text REFERENCES zip_codes(code)
);
```

### BCNF (Boyce-Codd Normal Form)
**규칙**: 3NF + 모든 결정자는 후보키

```
3NF에서 이상 현상이 발생할 때만 적용.
대부분의 실무에서는 3NF로 충분.
```

## Denormalization

### When to Denormalize

| 상황 | 역정규화 고려 |
|------|--------------|
| 읽기 빈도 >> 쓰기 빈도 | O |
| JOIN 비용이 매우 높음 | O |
| 실시간 집계 필요 | O |
| 데이터 일관성 최우선 | X |
| 쓰기 빈도 높음 | X |

### Denormalization Patterns

#### 1. 계산된 컬럼 추가
```sql
-- 정규화: 매번 COUNT
SELECT o.*, COUNT(oi.id) as item_count
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id;

-- 역정규화: 컬럼 추가
ALTER TABLE orders ADD COLUMN item_count int DEFAULT 0;

-- 트리거로 동기화
CREATE TRIGGER update_item_count
AFTER INSERT OR DELETE ON order_items
FOR EACH ROW EXECUTE FUNCTION update_order_item_count();
```

#### 2. 조회용 테이블 (Materialized View)
```sql
CREATE MATERIALIZED VIEW order_summary AS
SELECT
  date_trunc('day', created_at) as date,
  COUNT(*) as order_count,
  SUM(total) as total_revenue
FROM orders
GROUP BY 1;

-- 주기적 갱신
REFRESH MATERIALIZED VIEW order_summary;
```

#### 3. 중복 저장
```sql
-- 정규화: JOIN 필요
SELECT o.*, u.name as user_name
FROM orders o
JOIN users u ON u.id = o.user_id;

-- 역정규화: 중복 저장
CREATE TABLE orders (
  id bigint PRIMARY KEY,
  user_id bigint REFERENCES users(id),
  user_name text  -- 중복 저장 (조회 최적화)
);
```

## Data Consistency Strategies

### Trigger-Based
```sql
-- 자동 동기화
CREATE OR REPLACE FUNCTION sync_user_name()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE orders SET user_name = NEW.name WHERE user_id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_name_sync
AFTER UPDATE OF name ON users
FOR EACH ROW EXECUTE FUNCTION sync_user_name();
```

### Application-Level
```python
# 트랜잭션으로 일관성 보장
with db.transaction():
    user.name = new_name
    db.execute("UPDATE orders SET user_name = :name WHERE user_id = :id",
               {"name": new_name, "id": user.id})
```

### Event-Driven
```python
# 이벤트로 비동기 동기화
def on_user_updated(user_id, new_name):
    queue.publish("user.updated", {"id": user_id, "name": new_name})

# Worker에서 처리
def handle_user_updated(event):
    db.execute("UPDATE orders SET user_name = :name WHERE user_id = :id", event)
```

## Decision Guide

```
데이터 무결성이 최우선?
├── Yes → 3NF 유지
└── No → 읽기 성능이 중요?
         ├── Yes → 선택적 역정규화
         │         ├── Materialized View (집계)
         │         ├── 계산 컬럼 (단순 카운트)
         │         └── 중복 저장 (JOIN 회피)
         └── No → 3NF 유지
```
