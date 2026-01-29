# Migration Patterns

안전한 스키마 변경과 무중단 마이그레이션 전략.

## Zero-Downtime Migration

### Principles
1. **Backward Compatible**: 이전 코드와 호환
2. **Reversible**: 롤백 가능
3. **Incremental**: 작은 단위로 분할
4. **Tested**: 스테이징에서 먼저 테스트

### Common Patterns

#### Add Column (Safe)
```sql
-- 기본값 없이 NULL 허용 컬럼 추가 (빠름)
ALTER TABLE users ADD COLUMN middle_name text;

-- 기본값이 필요하면 나중에 별도로
UPDATE users SET middle_name = '' WHERE middle_name IS NULL;
ALTER TABLE users ALTER COLUMN middle_name SET DEFAULT '';
```

#### Add NOT NULL Column (Multi-Step)
```sql
-- Step 1: NULL 허용 컬럼 추가
ALTER TABLE users ADD COLUMN status text;

-- Step 2: 기존 데이터 채우기 (배치)
UPDATE users SET status = 'active' WHERE status IS NULL;

-- Step 3: NOT NULL 추가
ALTER TABLE users ALTER COLUMN status SET NOT NULL;
```

#### Rename Column (Multi-Step)
```sql
-- Step 1: 새 컬럼 추가
ALTER TABLE users ADD COLUMN full_name text;

-- Step 2: 데이터 복사
UPDATE users SET full_name = name;

-- Step 3: 애플리케이션에서 새 컬럼 사용

-- Step 4: 이전 컬럼 삭제 (다음 배포)
ALTER TABLE users DROP COLUMN name;
```

#### Change Column Type
```sql
-- Step 1: 새 컬럼 추가
ALTER TABLE orders ADD COLUMN total_v2 numeric(12,2);

-- Step 2: 트리거로 동기화
CREATE TRIGGER sync_total
BEFORE INSERT OR UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION sync_total_columns();

-- Step 3: 기존 데이터 마이그레이션
UPDATE orders SET total_v2 = total::numeric(12,2);

-- Step 4: 애플리케이션에서 새 컬럼 사용

-- Step 5: 트리거 제거, 이전 컬럼 삭제
```

## Lock-Free Operations

### Create Index Concurrently
```sql
-- BAD: 테이블 락 발생
CREATE INDEX users_email_idx ON users(email);

-- GOOD: 락 없이 인덱스 생성
CREATE INDEX CONCURRENTLY users_email_idx ON users(email);
```

### Add Constraint with NOT VALID
```sql
-- Step 1: 제약조건 추가 (기존 데이터 검증 안 함)
ALTER TABLE orders
ADD CONSTRAINT orders_total_positive
CHECK (total >= 0) NOT VALID;

-- Step 2: 배경에서 기존 데이터 검증
ALTER TABLE orders VALIDATE CONSTRAINT orders_total_positive;
```

## Dangerous Operations

### Avoid in Production

| Operation | Risk | Alternative |
|-----------|------|-------------|
| `DROP COLUMN` | 즉시 실행, 데이터 손실 | 컬럼 무시 후 나중에 삭제 |
| `ALTER TYPE` | 테이블 재작성 | 새 컬럼 추가 방식 |
| `ADD NOT NULL` | 테이블 스캔 | 단계별 마이그레이션 |
| `CREATE INDEX` | 테이블 락 | `CONCURRENTLY` 사용 |

### Safe Order
```sql
-- 1. 새 구조 추가 (비파괴적)
ALTER TABLE users ADD COLUMN new_col text;

-- 2. 데이터 마이그레이션

-- 3. 애플리케이션 전환

-- 4. 이전 구조 제거 (다음 배포)
```

## Rollback Strategy

### Version Control
```sql
-- migrations/001_add_user_status.sql
ALTER TABLE users ADD COLUMN status text DEFAULT 'active';

-- migrations/001_add_user_status_down.sql
ALTER TABLE users DROP COLUMN status;
```

### Feature Flags
```python
# 기능 플래그로 새 스키마 점진적 활성화
if feature_enabled("new_user_status"):
    user.status = compute_status()
else:
    user.legacy_status = compute_legacy_status()
```

### Blue-Green Schema
```sql
-- Blue: 현재 스키마
-- Green: 새 스키마

-- 트래픽 전환 전 둘 다 동기화
-- 문제 시 Blue로 즉시 롤백
```

## Large Table Migration

### Batch Processing
```python
# 대용량 테이블 배치 업데이트
batch_size = 10000
while True:
    result = db.execute("""
        UPDATE users
        SET status = 'active'
        WHERE id IN (
            SELECT id FROM users
            WHERE status IS NULL
            LIMIT :batch_size
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id
    """, {"batch_size": batch_size})

    if result.rowcount == 0:
        break

    time.sleep(0.1)  # DB 부하 분산
```

### pt-online-schema-change (MySQL)
```bash
# MySQL 대용량 테이블 무중단 변경
pt-online-schema-change \
  --alter "ADD COLUMN status VARCHAR(20)" \
  D=mydb,t=users \
  --execute
```

### pg_repack (PostgreSQL)
```bash
# 테이블 재구성 (bloat 제거)
pg_repack -d mydb -t users
```

## Migration Checklist

### Before Migration
- [ ] 스테이징에서 테스트
- [ ] 롤백 스크립트 준비
- [ ] 예상 실행 시간 측정
- [ ] 락 영향 분석
- [ ] 백업 확인

### During Migration
- [ ] 모니터링 대시보드 확인
- [ ] 에러 로그 모니터링
- [ ] 성능 메트릭 확인

### After Migration
- [ ] 데이터 무결성 확인
- [ ] 애플리케이션 정상 동작 확인
- [ ] 인덱스 사용 확인 (EXPLAIN)
