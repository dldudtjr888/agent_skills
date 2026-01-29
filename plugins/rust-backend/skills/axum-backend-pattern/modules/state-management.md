# State Management

Axum State 관리와 의존성 주입 패턴.

## AppState 설계

```rust
use std::sync::Arc;
use sqlx::PgPool;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub config: Arc<Config>,
    pub user_service: Arc<UserService>,
    pub auth_service: Arc<AuthService>,
    pub cache: Arc<dyn CacheService>,
}

impl AppState {
    pub async fn new(config: Config) -> anyhow::Result<Self> {
        // 데이터베이스 연결
        let db = PgPool::connect(&config.database_url).await?;

        // 레포지토리 생성
        let user_repo = Arc::new(UserRepository::new(db.clone()));

        // 서비스 생성 (의존성 주입)
        let user_service = Arc::new(UserService::new(user_repo.clone()));
        let auth_service = Arc::new(AuthService::new(
            config.jwt_secret.clone(),
            user_repo,
        ));

        // 캐시 서비스
        let cache: Arc<dyn CacheService> = if config.redis_url.is_some() {
            Arc::new(RedisCache::new(&config.redis_url.unwrap()).await?)
        } else {
            Arc::new(InMemoryCache::new())
        };

        Ok(Self {
            db,
            config: Arc::new(config),
            user_service,
            auth_service,
            cache,
        })
    }
}
```

## State Extractor

```rust
use axum::extract::State;

// 전체 State 추출
async fn handler(State(state): State<AppState>) -> impl IntoResponse {
    let users = state.user_service.list().await?;
    // ...
}

// 부분 State 추출 (FromRef 사용)
use axum::extract::FromRef;

impl FromRef<AppState> for PgPool {
    fn from_ref(state: &AppState) -> Self {
        state.db.clone()
    }
}

impl FromRef<AppState> for Arc<UserService> {
    fn from_ref(state: &AppState) -> Self {
        state.user_service.clone()
    }
}

// 이제 부분 추출 가능
async fn list_users(
    State(user_service): State<Arc<UserService>>,
) -> Result<Json<Vec<User>>, AppError> {
    let users = user_service.list().await?;
    Ok(Json(users))
}
```

## Extension 사용

```rust
use axum::Extension;

// 미들웨어에서 Extension 추가
async fn auth_middleware<B>(
    State(state): State<AppState>,
    mut request: Request<B>,
    next: Next<B>,
) -> Result<Response, AppError> {
    let claims = validate_token(&request, &state)?;

    // Extension으로 추가
    request.extensions_mut().insert(CurrentUser {
        id: claims.sub,
        email: claims.email,
    });

    Ok(next.run(request).await)
}

// 핸들러에서 Extension 추출
async fn get_profile(
    Extension(user): Extension<CurrentUser>,
) -> Result<Json<ProfileResponse>, AppError> {
    // user.id, user.email 사용 가능
}
```

## 의존성 주입 패턴

### Trait 기반 의존성

```rust
// 인터페이스 정의
#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: i64) -> Result<Option<User>, DbError>;
    async fn find_by_email(&self, email: &str) -> Result<Option<User>, DbError>;
    async fn create(&self, user: &NewUser) -> Result<User, DbError>;
}

// 실제 구현
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

// 서비스에서 trait 사용
pub struct UserService<R: UserRepository> {
    repo: R,
}

impl<R: UserRepository> UserService<R> {
    pub fn new(repo: R) -> Self {
        Self { repo }
    }

    pub async fn get_user(&self, id: i64) -> Result<User, AppError> {
        self.repo
            .find_by_id(id)
            .await?
            .ok_or(AppError::NotFound)
    }
}
```

### 테스트용 Mock

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use mockall::mock;

    mock! {
        UserRepo {}

        #[async_trait]
        impl UserRepository for UserRepo {
            async fn find_by_id(&self, id: i64) -> Result<Option<User>, DbError>;
            async fn find_by_email(&self, email: &str) -> Result<Option<User>, DbError>;
            async fn create(&self, user: &NewUser) -> Result<User, DbError>;
        }
    }

    #[tokio::test]
    async fn test_get_user() {
        let mut mock_repo = MockUserRepo::new();
        mock_repo
            .expect_find_by_id()
            .with(eq(1))
            .returning(|_| Ok(Some(User { id: 1, name: "Test".into() })));

        let service = UserService::new(mock_repo);
        let user = service.get_user(1).await.unwrap();

        assert_eq!(user.id, 1);
    }
}
```

## 설정 관리

```rust
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    #[serde(default = "default_host")]
    pub host: String,

    #[serde(default = "default_port")]
    pub port: u16,

    pub database_url: String,

    pub jwt_secret: String,

    #[serde(default)]
    pub redis_url: Option<String>,

    #[serde(default = "default_log_level")]
    pub log_level: String,
}

fn default_host() -> String {
    "0.0.0.0".into()
}

fn default_port() -> u16 {
    3000
}

fn default_log_level() -> String {
    "info".into()
}

impl Config {
    pub fn load() -> anyhow::Result<Self> {
        // 환경변수에서 로드
        let config = envy::from_env::<Config>()?;
        Ok(config)
    }

    pub fn from_file(path: &str) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }
}
```

## 리소스 정리

```rust
impl AppState {
    pub async fn shutdown(&self) {
        tracing::info!("Shutting down application...");

        // DB 커넥션 풀 닫기
        self.db.close().await;

        // 캐시 연결 닫기
        if let Some(cache) = Arc::get_mut(&mut self.cache.clone()) {
            cache.close().await;
        }

        tracing::info!("Shutdown complete");
    }
}

// main에서 사용
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::load()?;
    let state = AppState::new(config).await?;

    let app = create_app(state.clone());

    let listener = TcpListener::bind("0.0.0.0:3000").await?;

    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            shutdown_signal().await;
            state.shutdown().await;
        })
        .await?;

    Ok(())
}
```

## 체크리스트

- [ ] AppState 구조체 설계
- [ ] Arc로 공유 리소스 래핑
- [ ] FromRef 구현 (부분 State 추출)
- [ ] Trait 기반 의존성 주입
- [ ] Config 환경변수/파일 로드
- [ ] 리소스 정리 (graceful shutdown)
- [ ] 테스트용 Mock 지원
