---
name: rust-db-patterns
description: >-
  Rust 데이터베이스 패턴. sqlx::query_as!/query!() 컴파일타임 쿼리 검증, sqlx::PgPool 커넥션 풀,
  Diesel ORM schema.rs/models.rs, SeaORM Entity/ActiveModel/Migration, deadpool 커넥션 풀 관리,
  트랜잭션 격리 수준, sqlx::migrate!() 마이그레이션, Redis(fred/deadpool-redis) 캐시 레이어 패턴.
  MUST USE: sqlx/diesel/seaorm 사용, DB 쿼리 작성, 마이그레이션 설정, 트랜잭션 관리,
  커넥션 풀 설정, PostgreSQL/MySQL/SQLite 연동, ORM 모델 설계 시 반드시 사용.
  러스트 DB 연동, 쿼리 작성, 마이그레이션 생성, 커넥션 풀 설정, ORM 패턴 구현 시 반드시 활성화.
version: 1.0.0
category: database
user-invocable: true
triggers:
  keywords:
    - sqlx
    - diesel
    - seaorm
    - database
    - db
    - 데이터베이스
    - query
    - 쿼리
    - migration
    - transaction
  intentPatterns:
    - "(만들|구현).*(데이터베이스|db|sqlx|diesel)"
    - "(sqlx|diesel|seaorm).*(패턴|쿼리)"
---

# Rust Database Patterns

Rust 데이터베이스 접근 패턴 (SQLx, Diesel, SeaORM).

## 관련 참조

- **common-backend/database-design**: 스키마 설계, 정규화, 인덱싱 전략

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Connection Pooling | [modules/connection-pooling.md](modules/connection-pooling.md) | SQLx/Diesel/SeaORM 풀 설정, 튜닝 |
| 2 | Query Optimization | [modules/query-optimization.md](modules/query-optimization.md) | 쿼리 빌더 패턴, 성능 최적화 |
| 3 | Migration Patterns | [modules/migration-patterns.md](modules/migration-patterns.md) | sqlx-cli, diesel_cli 마이그레이션 |
| 4 | Transaction Handling | [modules/transaction-handling.md](modules/transaction-handling.md) | 중첩 트랜잭션, 에러 롤백 |

## ORM 비교

| 항목 | SQLx | Diesel | SeaORM |
|------|------|--------|--------|
| 타입 | 쿼리 빌더 | ORM | ORM |
| 컴파일 타임 검사 | ✓ (매크로) | ✓ (DSL) | ✓ |
| 비동기 | ✓ | ✗ | ✓ |
| 러닝 커브 | 낮음 | 높음 | 중간 |

## SQLx Patterns

### 연결 풀

```rust
use sqlx::postgres::PgPoolOptions;

let pool = PgPoolOptions::new()
    .max_connections(10)
    .connect(&database_url)
    .await?;
```

### 쿼리 매크로

```rust
// 컴파일 타임 검사
let user = sqlx::query_as!(
    User,
    "SELECT id, name, email FROM users WHERE id = $1",
    user_id
)
.fetch_one(&pool)
.await?;

// 동적 쿼리
let users = sqlx::query_as::<_, User>(
    "SELECT * FROM users WHERE status = $1"
)
.bind(status)
.fetch_all(&pool)
.await?;
```

### 트랜잭션

```rust
let mut tx = pool.begin().await?;

sqlx::query!("INSERT INTO users (name) VALUES ($1)", name)
    .execute(&mut *tx)
    .await?;

sqlx::query!("INSERT INTO profiles (user_id) VALUES ($1)", user_id)
    .execute(&mut *tx)
    .await?;

tx.commit().await?;
```

## Repository Pattern

```rust
#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: i64) -> Result<Option<User>, DbError>;
    async fn find_by_email(&self, email: &str) -> Result<Option<User>, DbError>;
    async fn create(&self, user: &NewUser) -> Result<User, DbError>;
    async fn update(&self, user: &User) -> Result<User, DbError>;
    async fn delete(&self, id: i64) -> Result<(), DbError>;
}

pub struct PgUserRepository {
    pool: PgPool,
}

#[async_trait]
impl UserRepository for PgUserRepository {
    async fn find_by_id(&self, id: i64) -> Result<Option<User>, DbError> {
        sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
            .fetch_optional(&self.pool)
            .await
            .map_err(Into::into)
    }
    // ...
}
```

## 체크리스트

- [ ] 연결 풀 설정
- [ ] Repository 패턴 적용
- [ ] 트랜잭션 관리
- [ ] 마이그레이션 설정
- [ ] N+1 쿼리 방지
- [ ] 에러 처리
