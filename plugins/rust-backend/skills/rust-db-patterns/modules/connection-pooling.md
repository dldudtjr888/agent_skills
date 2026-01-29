# Connection Pooling

데이터베이스 연결 풀 설정 및 최적화 패턴.

## SQLx 풀 설정

### 기본 설정

```rust
use sqlx::postgres::{PgPoolOptions, PgConnectOptions};
use std::time::Duration;

pub async fn create_pool(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(20)
        .min_connections(5)
        .acquire_timeout(Duration::from_secs(3))
        .idle_timeout(Duration::from_secs(600))
        .max_lifetime(Duration::from_secs(1800))
        .connect(database_url)
        .await
}
```

### 상세 옵션 설정

```rust
use sqlx::postgres::{PgConnectOptions, PgSslMode};

pub async fn create_production_pool() -> Result<PgPool, sqlx::Error> {
    let options = PgConnectOptions::new()
        .host("localhost")
        .port(5432)
        .database("myapp")
        .username("app_user")
        .password("secret")
        .ssl_mode(PgSslMode::Require)
        .application_name("my-rust-app")
        .statement_cache_capacity(100);

    PgPoolOptions::new()
        .max_connections(50)
        .min_connections(10)
        .acquire_timeout(Duration::from_secs(5))
        .test_before_acquire(true)  // 연결 유효성 검사
        .connect_with(options)
        .await
}
```

## Diesel 풀 설정

### r2d2 매니저

```rust
use diesel::pg::PgConnection;
use diesel::r2d2::{self, ConnectionManager, Pool};

pub type DbPool = Pool<ConnectionManager<PgConnection>>;

pub fn create_pool(database_url: &str) -> DbPool {
    let manager = ConnectionManager::<PgConnection>::new(database_url);

    r2d2::Pool::builder()
        .max_size(20)
        .min_idle(Some(5))
        .connection_timeout(Duration::from_secs(3))
        .idle_timeout(Some(Duration::from_secs(600)))
        .max_lifetime(Some(Duration::from_secs(1800)))
        .build(manager)
        .expect("Failed to create pool")
}
```

### deadpool-diesel (async)

```rust
use deadpool_diesel::postgres::{Manager, Pool, Runtime};

pub fn create_async_pool(database_url: &str) -> Pool {
    let manager = Manager::new(database_url, Runtime::Tokio1);

    Pool::builder(manager)
        .max_size(20)
        .build()
        .expect("Failed to create pool")
}

// 사용
async fn get_users(pool: &Pool) -> Result<Vec<User>, Error> {
    let conn = pool.get().await?;
    conn.interact(|conn| {
        users::table.load::<User>(conn)
    }).await??
}
```

## SeaORM 풀 설정

```rust
use sea_orm::{Database, ConnectOptions, DatabaseConnection};
use std::time::Duration;

pub async fn create_pool(database_url: &str) -> Result<DatabaseConnection, DbErr> {
    let mut opt = ConnectOptions::new(database_url);
    opt.max_connections(100)
       .min_connections(10)
       .connect_timeout(Duration::from_secs(5))
       .acquire_timeout(Duration::from_secs(5))
       .idle_timeout(Duration::from_secs(600))
       .max_lifetime(Duration::from_secs(1800))
       .sqlx_logging(true)
       .sqlx_logging_level(log::LevelFilter::Debug);

    Database::connect(opt).await
}
```

## 풀 크기 계산

### 권장 공식

```
max_connections = (core_count * 2) + effective_spindle_count
```

- **core_count**: CPU 코어 수
- **effective_spindle_count**: SSD는 1, HDD는 디스크 수

### 환경별 권장값

| 환경 | max | min | idle_timeout |
|------|-----|-----|--------------|
| 개발 | 5 | 1 | 60s |
| 스테이징 | 20 | 5 | 300s |
| 프로덕션 | 50-100 | 10 | 600s |

## Health Check

### SQLx

```rust
pub async fn health_check(pool: &PgPool) -> Result<(), sqlx::Error> {
    sqlx::query("SELECT 1")
        .fetch_one(pool)
        .await?;
    Ok(())
}

// Axum 핸들러
async fn health(State(pool): State<PgPool>) -> impl IntoResponse {
    match health_check(&pool).await {
        Ok(_) => (StatusCode::OK, "healthy"),
        Err(_) => (StatusCode::SERVICE_UNAVAILABLE, "unhealthy"),
    }
}
```

### 풀 메트릭스

```rust
pub fn pool_metrics(pool: &PgPool) -> PoolMetrics {
    PoolMetrics {
        size: pool.size(),
        idle: pool.num_idle(),
        // SQLx는 내부 메트릭 제한적
    }
}
```

## 재연결 패턴

```rust
use tokio::time::{sleep, Duration};

pub async fn with_retry<T, F, Fut>(
    pool: &PgPool,
    max_retries: u32,
    operation: F,
) -> Result<T, sqlx::Error>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, sqlx::Error>>,
{
    let mut attempts = 0;

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts < max_retries => {
                attempts += 1;
                let delay = Duration::from_millis(100 * 2_u64.pow(attempts));
                tracing::warn!(
                    error = %e,
                    attempt = attempts,
                    "Database operation failed, retrying"
                );
                sleep(delay).await;
            }
            Err(e) => return Err(e),
        }
    }
}
```

## 체크리스트

- [ ] 적절한 max_connections 설정
- [ ] min_connections로 워밍업
- [ ] acquire_timeout 설정
- [ ] idle_timeout으로 리소스 관리
- [ ] max_lifetime으로 연결 순환
- [ ] health check 구현
- [ ] 재연결 로직 구현
