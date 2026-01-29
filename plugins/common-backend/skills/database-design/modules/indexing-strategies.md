# Indexing Strategies

효율적인 쿼리를 위한 인덱스 설계 전략.

## Index Types

### B-tree (Default)
```sql
-- 대부분의 경우 기본 선택
CREATE INDEX users_email_idx ON users(email);

-- 지원 연산자: =, <, >, <=, >=, BETWEEN, IN, LIKE 'prefix%'
```

### Hash
```sql
-- 동등 비교만 지원 (=)
CREATE INDEX users_email_hash ON users USING hash(email);

-- B-tree보다 약간 빠르지만 제한적
```

### GIN (Generalized Inverted Index)
```sql
-- 배열, JSONB, 전문 검색
CREATE INDEX products_tags_idx ON products USING gin(tags);
CREATE INDEX products_data_idx ON products USING gin(data);

-- 지원 연산자: @>, ?, ?&, ?|, @@
```

### GiST (Generalized Search Tree)
```sql
-- 지리 데이터, 범위 검색
CREATE INDEX locations_geom_idx ON locations USING gist(geom);
```

### BRIN (Block Range Index)
```sql
-- 시계열 데이터, 자연 정렬된 대용량 테이블
CREATE INDEX events_created_idx ON events USING brin(created_at);

-- 매우 작은 인덱스 크기, 순차 데이터에 효과적
```

## Composite Index

### Column Order Matters
```sql
-- WHERE status = ? AND created_at > ?
CREATE INDEX orders_status_created_idx ON orders(status, created_at);

-- Leftmost Prefix Rule:
-- 이 인덱스가 지원하는 쿼리:
-- ✅ WHERE status = 'pending'
-- ✅ WHERE status = 'pending' AND created_at > '2024-01-01'
-- ❌ WHERE created_at > '2024-01-01' (alone)
```

### Equality First, Range Last
```sql
-- GOOD: 동등 비교 먼저, 범위 비교 나중
CREATE INDEX idx ON orders(status, created_at);
-- WHERE status = 'pending' AND created_at > '2024-01-01'

-- BAD: 범위 비교 먼저
CREATE INDEX idx ON orders(created_at, status);
-- 범위 조건 이후 컬럼은 인덱스 활용 불가
```

## Covering Index (Index-Only Scan)

### Include Columns
```sql
-- 테이블 조회 없이 인덱스만으로 결과 반환
CREATE INDEX users_email_idx ON users(email) INCLUDE (name, created_at);

-- 이 쿼리는 테이블 접근 없음
SELECT email, name, created_at FROM users WHERE email = 'user@example.com';
```

## Partial Index

### Filtered Index
```sql
-- 활성 사용자만 인덱싱
CREATE INDEX users_active_email_idx ON users(email)
WHERE deleted_at IS NULL;

-- 대기 주문만 인덱싱
CREATE INDEX orders_pending_idx ON orders(created_at)
WHERE status = 'pending';
```

### Benefits
- 인덱스 크기 감소 (5-20배)
- 쓰기 성능 향상
- 쿼리 성능 향상

## Expression Index

### Computed Values
```sql
-- 소문자 검색
CREATE INDEX users_email_lower_idx ON users(lower(email));
SELECT * FROM users WHERE lower(email) = 'user@example.com';

-- JSONB 필드
CREATE INDEX products_brand_idx ON products((data->>'brand'));
SELECT * FROM products WHERE data->>'brand' = 'Nike';
```

## Index Maintenance

### Bloat Detection
```sql
-- 인덱스 bloat 확인
SELECT
  indexrelname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  idx_scan as scans
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Reindex
```sql
-- 인덱스 재구성
REINDEX INDEX users_email_idx;
REINDEX TABLE users;

-- 온라인 재구성 (PostgreSQL 12+)
REINDEX INDEX CONCURRENTLY users_email_idx;
```

### Unused Indexes
```sql
-- 사용되지 않는 인덱스 찾기
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Index Selection Guide

```
쿼리 패턴 분석
│
├── 동등 비교만? (WHERE col = ?)
│   └── B-tree (기본)
│
├── 배열/JSONB 검색?
│   └── GIN
│
├── 시계열 데이터, 순차 정렬?
│   └── BRIN (대용량 테이블)
│
├── 여러 컬럼 조합?
│   └── Composite Index
│       └── 동등 조건 먼저, 범위 조건 나중
│
├── 특정 조건만 검색? (status = 'active')
│   └── Partial Index
│
└── 계산된 값 검색? (lower(email))
    └── Expression Index
```

## Anti-Patterns

### Over-Indexing
```sql
-- BAD: 모든 컬럼에 인덱스
CREATE INDEX idx1 ON users(email);
CREATE INDEX idx2 ON users(name);
CREATE INDEX idx3 ON users(created_at);
CREATE INDEX idx4 ON users(email, name);
CREATE INDEX idx5 ON users(email, created_at);

-- 쓰기 성능 저하, 저장 공간 낭비
```

### Missing FK Indexes
```sql
-- BAD: FK에 인덱스 없음
ALTER TABLE orders ADD COLUMN user_id bigint REFERENCES users(id);
-- JOIN 성능 저하!

-- GOOD: FK에 인덱스 추가
CREATE INDEX orders_user_id_idx ON orders(user_id);
```

### Wrong Column Order
```sql
-- Query: WHERE created_at > ? AND status = ?

-- BAD: 범위 컬럼 먼저
CREATE INDEX idx ON orders(created_at, status);

-- GOOD: 동등 컬럼 먼저
CREATE INDEX idx ON orders(status, created_at);
```
