# Migration Patterns

데이터베이스 마이그레이션 전략 및 도구 사용법.

## SQLx 마이그레이션

### 설정

```bash
# sqlx-cli 설치
cargo install sqlx-cli --features postgres

# 마이그레이션 디렉토리 생성
sqlx migrate add create_users_table
```

### 마이그레이션 파일 구조

```
migrations/
├── 20240101000000_create_users_table.sql
├── 20240102000000_add_email_index.sql
└── 20240103000000_create_posts_table.sql
```

### 마이그레이션 작성

```sql
-- 20240101000000_create_users_table.sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

### Reversible 마이그레이션

```sql
-- 20240102000000_add_posts_table.up.sql
CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 20240102000000_add_posts_table.down.sql
DROP TABLE posts;
```

### 코드에서 실행

```rust
use sqlx::migrate::Migrator;
use sqlx::PgPool;

pub async fn run_migrations(pool: &PgPool) -> Result<(), sqlx::migrate::MigrateError> {
    // 임베디드 마이그레이션
    sqlx::migrate!("./migrations")
        .run(pool)
        .await
}

// 또는 런타임에 경로 지정
pub async fn run_migrations_from_path(
    pool: &PgPool,
    path: &str,
) -> Result<(), sqlx::migrate::MigrateError> {
    let migrator = Migrator::new(std::path::Path::new(path)).await?;
    migrator.run(pool).await
}
```

### CLI 명령어

```bash
# 마이그레이션 실행
sqlx migrate run

# 롤백
sqlx migrate revert

# 상태 확인
sqlx migrate info

# 데이터베이스 생성
sqlx database create

# 데이터베이스 삭제
sqlx database drop
```

## Diesel 마이그레이션

### 설정

```bash
# diesel_cli 설치
cargo install diesel_cli --no-default-features --features postgres

# 프로젝트 설정
diesel setup

# 마이그레이션 생성
diesel migration generate create_users
```

### 마이그레이션 파일

```sql
-- migrations/2024-01-01-000000_create_users/up.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- migrations/2024-01-01-000000_create_users/down.sql
DROP TABLE users;
```

### 코드에서 실행

```rust
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};

pub const MIGRATIONS: EmbeddedMigrations = embed_migrations!("migrations");

pub fn run_migrations(
    conn: &mut impl MigrationHarness<diesel::pg::Pg>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    conn.run_pending_migrations(MIGRATIONS)?;
    Ok(())
}
```

### CLI 명령어

```bash
# 마이그레이션 실행
diesel migration run

# 롤백
diesel migration revert

# 모든 마이그레이션 재실행
diesel migration redo

# 스키마 재생성
diesel print-schema > src/schema.rs
```

## SeaORM 마이그레이션

### 설정

```bash
# sea-orm-cli 설치
cargo install sea-orm-cli

# 마이그레이션 생성
sea-orm-cli migrate generate create_users_table
```

### 마이그레이션 코드

```rust
// migration/src/m20240101_000000_create_users_table.rs
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager
            .create_table(
                Table::create()
                    .table(Users::Table)
                    .if_not_exists()
                    .col(
                        ColumnDef::new(Users::Id)
                            .integer()
                            .not_null()
                            .auto_increment()
                            .primary_key(),
                    )
                    .col(ColumnDef::new(Users::Name).string().not_null())
                    .col(ColumnDef::new(Users::Email).string().not_null().unique_key())
                    .col(
                        ColumnDef::new(Users::CreatedAt)
                            .timestamp_with_time_zone()
                            .not_null()
                            .default(Expr::current_timestamp()),
                    )
                    .to_owned(),
            )
            .await
    }

    async fn down(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager
            .drop_table(Table::drop().table(Users::Table).to_owned())
            .await
    }
}

#[derive(Iden)]
enum Users {
    Table,
    Id,
    Name,
    Email,
    CreatedAt,
}
```

## 마이그레이션 베스트 프랙티스

### 1. 무중단 마이그레이션

```sql
-- 1단계: 새 컬럼 추가 (nullable)
ALTER TABLE users ADD COLUMN phone VARCHAR(50);

-- 2단계: 데이터 마이그레이션 (배치)
UPDATE users SET phone = 'unknown' WHERE phone IS NULL;

-- 3단계: NOT NULL 제약 추가
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;
```

### 2. 인덱스 동시 생성

```sql
-- CONCURRENTLY로 락 방지
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);
```

### 3. 대용량 테이블 변경

```sql
-- 새 테이블 생성 후 데이터 이동
CREATE TABLE users_new (LIKE users INCLUDING ALL);
ALTER TABLE users_new ADD COLUMN new_field VARCHAR(255);

-- 배치로 데이터 복사
INSERT INTO users_new
SELECT *, NULL as new_field FROM users
WHERE id BETWEEN 1 AND 10000;

-- 테이블 교체
ALTER TABLE users RENAME TO users_old;
ALTER TABLE users_new RENAME TO users;
DROP TABLE users_old;
```

### 4. 롤백 전략

```rust
pub async fn safe_migrate(pool: &PgPool) -> Result<(), Error> {
    let mut tx = pool.begin().await?;

    match sqlx::migrate!().run(&mut *tx).await {
        Ok(_) => {
            tx.commit().await?;
            Ok(())
        }
        Err(e) => {
            tx.rollback().await?;
            Err(e.into())
        }
    }
}
```

## 체크리스트

- [ ] 마이그레이션 파일에 타임스탬프 프리픽스
- [ ] up/down 양방향 마이그레이션 작성
- [ ] 대용량 테이블은 배치 처리
- [ ] 인덱스는 CONCURRENTLY 사용
- [ ] 프로덕션 전 스테이징에서 테스트
- [ ] 롤백 플랜 준비
- [ ] 마이그레이션 히스토리 문서화
