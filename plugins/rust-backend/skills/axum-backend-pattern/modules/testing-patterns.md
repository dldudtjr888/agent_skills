# Testing Patterns

Axum 애플리케이션 테스트 패턴.

## 단위 테스트

### 핸들러 로직 테스트

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_create_user_validation() {
        let payload = CreateUserRequest {
            name: "".into(),  // 빈 이름 - 검증 실패 예상
            email: "invalid-email".into(),
            password: "123".into(),  // 너무 짧음
        };

        let result = payload.validate();
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn test_user_service_get() {
        let mut mock_repo = MockUserRepo::new();
        mock_repo
            .expect_find_by_id()
            .with(eq(1))
            .returning(|_| Ok(Some(User {
                id: 1,
                name: "Test User".into(),
                email: "test@example.com".into(),
            })));

        let service = UserService::new(mock_repo);
        let user = service.get_user(1).await.unwrap();

        assert_eq!(user.name, "Test User");
    }
}
```

## 통합 테스트 (axum-test)

### 기본 설정

```rust
// tests/api_tests.rs
use axum_test::TestServer;

async fn create_test_server() -> TestServer {
    let config = Config::test_config();
    let state = AppState::new(config).await.unwrap();
    let app = create_app(state);

    TestServer::new(app).unwrap()
}

#[tokio::test]
async fn test_health_check() {
    let server = create_test_server().await;

    let response = server.get("/health").await;

    response.assert_status_ok();
    response.assert_text("OK");
}
```

### CRUD 테스트

```rust
#[tokio::test]
async fn test_create_user() {
    let server = create_test_server().await;

    let response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepassword123"
        }))
        .await;

    response.assert_status(StatusCode::CREATED);

    let user: UserResponse = response.json();
    assert_eq!(user.name, "John Doe");
    assert_eq!(user.email, "john@example.com");
}

#[tokio::test]
async fn test_get_user() {
    let server = create_test_server().await;

    // 먼저 사용자 생성
    let create_response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123"
        }))
        .await;

    let created_user: UserResponse = create_response.json();

    // 조회
    let response = server
        .get(&format!("/api/v1/users/{}", created_user.id))
        .await;

    response.assert_status_ok();

    let user: UserResponse = response.json();
    assert_eq!(user.id, created_user.id);
}

#[tokio::test]
async fn test_list_users() {
    let server = create_test_server().await;

    let response = server
        .get("/api/v1/users")
        .add_query_param("page", 1)
        .add_query_param("per_page", 10)
        .await;

    response.assert_status_ok();

    let result: PaginatedResponse<UserResponse> = response.json();
    assert!(result.pagination.total >= 0);
}

#[tokio::test]
async fn test_update_user() {
    let server = create_test_server().await;

    // 생성
    let create_response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({
            "name": "Original Name",
            "email": "original@example.com",
            "password": "securepassword123"
        }))
        .await;

    let user: UserResponse = create_response.json();

    // 수정
    let response = server
        .patch(&format!("/api/v1/users/{}", user.id))
        .json(&serde_json::json!({
            "name": "Updated Name"
        }))
        .await;

    response.assert_status_ok();

    let updated: UserResponse = response.json();
    assert_eq!(updated.name, "Updated Name");
}

#[tokio::test]
async fn test_delete_user() {
    let server = create_test_server().await;

    // 생성
    let create_response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({
            "name": "To Delete",
            "email": "delete@example.com",
            "password": "securepassword123"
        }))
        .await;

    let user: UserResponse = create_response.json();

    // 삭제
    let response = server
        .delete(&format!("/api/v1/users/{}", user.id))
        .await;

    response.assert_status(StatusCode::NO_CONTENT);

    // 삭제 확인
    let get_response = server
        .get(&format!("/api/v1/users/{}", user.id))
        .await;

    get_response.assert_status(StatusCode::NOT_FOUND);
}
```

### 인증 테스트

```rust
#[tokio::test]
async fn test_protected_route_without_auth() {
    let server = create_test_server().await;

    let response = server.get("/api/v1/profile").await;

    response.assert_status(StatusCode::UNAUTHORIZED);
}

#[tokio::test]
async fn test_protected_route_with_auth() {
    let server = create_test_server().await;

    // 로그인
    let login_response = server
        .post("/api/v1/auth/login")
        .json(&serde_json::json!({
            "email": "test@example.com",
            "password": "testpassword123"
        }))
        .await;

    let tokens: TokenResponse = login_response.json();

    // 보호된 라우트 접근
    let response = server
        .get("/api/v1/profile")
        .add_header("Authorization", format!("Bearer {}", tokens.access_token))
        .await;

    response.assert_status_ok();
}

#[tokio::test]
async fn test_invalid_token() {
    let server = create_test_server().await;

    let response = server
        .get("/api/v1/profile")
        .add_header("Authorization", "Bearer invalid-token")
        .await;

    response.assert_status(StatusCode::UNAUTHORIZED);
}
```

### 에러 응답 테스트

```rust
#[tokio::test]
async fn test_not_found() {
    let server = create_test_server().await;

    let response = server.get("/api/v1/users/999999").await;

    response.assert_status(StatusCode::NOT_FOUND);

    let error: ErrorResponse = response.json();
    assert_eq!(error.error, "not_found");
}

#[tokio::test]
async fn test_validation_error() {
    let server = create_test_server().await;

    let response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({
            "name": "",  // 빈 이름
            "email": "invalid-email",  // 잘못된 이메일
            "password": "123"  // 너무 짧음
        }))
        .await;

    response.assert_status(StatusCode::UNPROCESSABLE_ENTITY);

    let error: ErrorResponse = response.json();
    assert_eq!(error.error, "validation_error");
}
```

## 테스트 픽스처

```rust
// tests/fixtures.rs
pub struct TestFixtures {
    pub server: TestServer,
    pub test_user: UserResponse,
    pub auth_token: String,
}

impl TestFixtures {
    pub async fn setup() -> Self {
        let server = create_test_server().await;

        // 테스트 사용자 생성
        let create_response = server
            .post("/api/v1/users")
            .json(&serde_json::json!({
                "name": "Test User",
                "email": format!("test-{}@example.com", uuid::Uuid::new_v4()),
                "password": "testpassword123"
            }))
            .await;

        let test_user: UserResponse = create_response.json();

        // 로그인
        let login_response = server
            .post("/api/v1/auth/login")
            .json(&serde_json::json!({
                "email": test_user.email,
                "password": "testpassword123"
            }))
            .await;

        let tokens: TokenResponse = login_response.json();

        Self {
            server,
            test_user,
            auth_token: tokens.access_token,
        }
    }

    pub fn auth_header(&self) -> (&str, String) {
        ("Authorization", format!("Bearer {}", self.auth_token))
    }
}

// 사용
#[tokio::test]
async fn test_with_fixtures() {
    let fixtures = TestFixtures::setup().await;

    let response = fixtures.server
        .get("/api/v1/profile")
        .add_header(fixtures.auth_header().0, fixtures.auth_header().1)
        .await;

    response.assert_status_ok();
}
```

## 데이터베이스 테스트

```rust
// 테스트용 트랜잭션 롤백
use sqlx::PgPool;

async fn with_test_db<F, Fut>(f: F)
where
    F: FnOnce(PgPool) -> Fut,
    Fut: std::future::Future<Output = ()>,
{
    let pool = PgPool::connect(&std::env::var("TEST_DATABASE_URL").unwrap())
        .await
        .unwrap();

    // 트랜잭션 시작
    let mut tx = pool.begin().await.unwrap();

    // 테스트 실행 (트랜잭션 내에서)
    // ...

    // 롤백 (테스트 데이터 정리)
    tx.rollback().await.unwrap();
}
```

## 체크리스트

- [ ] 단위 테스트 (서비스 로직)
- [ ] 통합 테스트 (axum-test)
- [ ] CRUD 엔드포인트 테스트
- [ ] 인증/인가 테스트
- [ ] 에러 응답 테스트
- [ ] 테스트 픽스처 설정
- [ ] 테스트 데이터 정리 (트랜잭션 롤백)
