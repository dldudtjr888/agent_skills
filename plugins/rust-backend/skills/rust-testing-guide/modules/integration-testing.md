# Integration Testing

Rust 통합 테스트 패턴.

## 통합 테스트 구조

```
my-crate/
├── src/
│   └── lib.rs
├── tests/
│   ├── common/
│   │   └── mod.rs    # 공유 유틸리티
│   ├── api_tests.rs
│   └── db_tests.rs
└── Cargo.toml
```

## 테스트 설정

```rust
// tests/common/mod.rs
use my_crate::AppState;
use sqlx::PgPool;

pub struct TestContext {
    pub pool: PgPool,
    pub state: AppState,
}

impl TestContext {
    pub async fn new() -> Self {
        let database_url = std::env::var("TEST_DATABASE_URL")
            .unwrap_or_else(|_| "postgres://localhost/test_db".into());

        let pool = PgPool::connect(&database_url).await.unwrap();

        // 마이그레이션 실행
        sqlx::migrate!().run(&pool).await.unwrap();

        let state = AppState::new(pool.clone());

        Self { pool, state }
    }

    pub async fn cleanup(&self) {
        // 테스트 데이터 정리
        sqlx::query("TRUNCATE users, posts CASCADE")
            .execute(&self.pool)
            .await
            .unwrap();
    }
}

impl Drop for TestContext {
    fn drop(&mut self) {
        // 동기 정리 (필요시)
    }
}
```

## API 통합 테스트

```rust
// tests/api_tests.rs
mod common;

use axum_test::TestServer;
use my_crate::create_app;

async fn create_test_server() -> TestServer {
    let ctx = common::TestContext::new().await;
    let app = create_app(ctx.state);
    TestServer::new(app).unwrap()
}

#[tokio::test]
async fn test_create_user_flow() {
    let server = create_test_server().await;

    // 1. 사용자 생성
    let response = server
        .post("/api/users")
        .json(&serde_json::json!({
            "name": "Test User",
            "email": "test@example.com"
        }))
        .await;

    response.assert_status(StatusCode::CREATED);
    let user: User = response.json();
    assert_eq!(user.name, "Test User");

    // 2. 생성된 사용자 조회
    let response = server
        .get(&format!("/api/users/{}", user.id))
        .await;

    response.assert_status_ok();
    let fetched: User = response.json();
    assert_eq!(fetched.email, "test@example.com");

    // 3. 사용자 업데이트
    let response = server
        .put(&format!("/api/users/{}", user.id))
        .json(&serde_json::json!({
            "name": "Updated Name"
        }))
        .await;

    response.assert_status_ok();

    // 4. 업데이트 확인
    let response = server
        .get(&format!("/api/users/{}", user.id))
        .await;

    let updated: User = response.json();
    assert_eq!(updated.name, "Updated Name");
}
```

## 데이터베이스 통합 테스트

```rust
// tests/db_tests.rs
mod common;

use my_crate::repositories::UserRepository;

#[tokio::test]
async fn test_user_crud_operations() {
    let ctx = common::TestContext::new().await;
    ctx.cleanup().await;

    let repo = UserRepository::new(ctx.pool.clone());

    // Create
    let user = repo.create(&NewUser {
        name: "Test".into(),
        email: "test@example.com".into(),
    }).await.unwrap();

    assert!(user.id > 0);

    // Read
    let found = repo.find_by_id(user.id).await.unwrap();
    assert!(found.is_some());
    assert_eq!(found.unwrap().name, "Test");

    // Update
    let updated = repo.update(user.id, &UpdateUser {
        name: Some("Updated".into()),
        email: None,
    }).await.unwrap();

    assert_eq!(updated.name, "Updated");

    // Delete
    repo.delete(user.id).await.unwrap();
    let deleted = repo.find_by_id(user.id).await.unwrap();
    assert!(deleted.is_none());
}
```

## 테스트 격리

### 트랜잭션 롤백

```rust
#[tokio::test]
async fn test_with_transaction_rollback() {
    let ctx = common::TestContext::new().await;

    // 트랜잭션 시작
    let mut tx = ctx.pool.begin().await.unwrap();

    // 테스트 작업
    sqlx::query!("INSERT INTO users (name) VALUES ($1)", "test")
        .execute(&mut *tx)
        .await
        .unwrap();

    // 검증
    let count: i64 = sqlx::query_scalar!("SELECT COUNT(*) FROM users")
        .fetch_one(&mut *tx)
        .await
        .unwrap()
        .unwrap();

    assert_eq!(count, 1);

    // 롤백 (tx drop 시 자동)
    // tx.rollback().await.unwrap();
}
```

### 테스트별 데이터베이스

```rust
use uuid::Uuid;

pub async fn create_test_database() -> PgPool {
    let base_url = std::env::var("DATABASE_URL").unwrap();
    let db_name = format!("test_{}", Uuid::new_v4().to_string().replace("-", ""));

    // 관리자 연결로 DB 생성
    let admin_pool = PgPool::connect(&base_url).await.unwrap();
    sqlx::query(&format!("CREATE DATABASE {}", db_name))
        .execute(&admin_pool)
        .await
        .unwrap();

    // 새 DB에 연결
    let test_url = format!("{}/{}", base_url.rsplit_once('/').unwrap().0, db_name);
    let pool = PgPool::connect(&test_url).await.unwrap();

    // 마이그레이션
    sqlx::migrate!().run(&pool).await.unwrap();

    pool
}
```

## 병렬 테스트 제어

```bash
# 순차 실행 (DB 테스트)
cargo test -- --test-threads=1

# 특정 테스트만 순차
cargo test db_ -- --test-threads=1

# 나머지는 병렬
cargo test --test api_tests
```

```rust
// 테스트 내에서 직렬화
use serial_test::serial;

#[tokio::test]
#[serial]
async fn test_requires_isolation() {
    // 다른 #[serial] 테스트와 순차 실행
}
```

## Fixtures

```rust
pub mod fixtures {
    use crate::models::*;

    pub fn user() -> User {
        User {
            id: 1,
            name: "Test User".into(),
            email: "test@example.com".into(),
            created_at: chrono::Utc::now(),
        }
    }

    pub fn users(count: usize) -> Vec<User> {
        (0..count)
            .map(|i| User {
                id: i as i64 + 1,
                name: format!("User {}", i),
                email: format!("user{}@example.com", i),
                created_at: chrono::Utc::now(),
            })
            .collect()
    }
}
```

## 체크리스트

- [ ] tests/ 디렉토리 구조 설정
- [ ] 공유 유틸리티 (common/mod.rs)
- [ ] 테스트 격리 전략 선택
- [ ] DB 정리 로직 구현
- [ ] 병렬 실행 vs 순차 실행 결정
- [ ] Fixtures 준비
