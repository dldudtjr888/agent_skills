# Routing Patterns

Axum 라우터 설계와 경로 추출 패턴.

## 기본 라우팅

### 라우터 구성

```rust
use axum::{
    Router,
    routing::{get, post, put, patch, delete},
};

pub fn router() -> Router<AppState> {
    Router::new()
        // 기본 CRUD
        .route("/", get(list).post(create))
        .route("/:id", get(show).put(update).patch(partial_update).delete(destroy))
        // 중첩 리소스
        .route("/:id/comments", get(list_comments).post(create_comment))
}
```

### HTTP 메서드 매핑

| 메서드 | 경로 | 핸들러 | 설명 |
|--------|------|--------|------|
| GET | /resources | list | 목록 조회 |
| POST | /resources | create | 생성 |
| GET | /resources/:id | show | 단건 조회 |
| PUT | /resources/:id | update | 전체 수정 |
| PATCH | /resources/:id | partial_update | 부분 수정 |
| DELETE | /resources/:id | destroy | 삭제 |

## Extractors

### Path - 경로 파라미터

```rust
use axum::extract::Path;

// 단일 파라미터
async fn get_user(Path(id): Path<i64>) -> impl IntoResponse {
    // ...
}

// 다중 파라미터
async fn get_comment(
    Path((user_id, comment_id)): Path<(i64, i64)>,
) -> impl IntoResponse {
    // ...
}

// 구조체로 추출
#[derive(Deserialize)]
struct PathParams {
    user_id: i64,
    post_id: i64,
}

async fn get_post(Path(params): Path<PathParams>) -> impl IntoResponse {
    // params.user_id, params.post_id
}
```

### Query - 쿼리 파라미터

```rust
use axum::extract::Query;

#[derive(Deserialize)]
struct ListParams {
    page: Option<u32>,
    per_page: Option<u32>,
    sort: Option<String>,
    order: Option<SortOrder>,
}

#[derive(Deserialize)]
#[serde(rename_all = "lowercase")]
enum SortOrder {
    Asc,
    Desc,
}

async fn list_users(Query(params): Query<ListParams>) -> impl IntoResponse {
    let page = params.page.unwrap_or(1);
    let per_page = params.per_page.unwrap_or(20).min(100);
    // ...
}
```

### Json - 요청 바디

```rust
use axum::Json;

#[derive(Deserialize)]
struct CreateUserRequest {
    name: String,
    email: String,
    #[serde(default)]
    role: UserRole,
}

#[derive(Deserialize, Default)]
#[serde(rename_all = "lowercase")]
enum UserRole {
    #[default]
    User,
    Admin,
}

async fn create_user(Json(payload): Json<CreateUserRequest>) -> impl IntoResponse {
    // ...
}
```

### 커스텀 Extractor

```rust
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::request::Parts,
};

pub struct CurrentUser {
    pub id: i64,
    pub email: String,
}

#[async_trait]
impl<S> FromRequestParts<S> for CurrentUser
where
    S: Send + Sync,
{
    type Rejection = AppError;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        // Authorization 헤더에서 토큰 추출
        let auth_header = parts
            .headers
            .get("Authorization")
            .and_then(|v| v.to_str().ok())
            .ok_or(AppError::Unauthorized)?;

        let token = auth_header
            .strip_prefix("Bearer ")
            .ok_or(AppError::Unauthorized)?;

        // 토큰 검증 및 사용자 정보 추출
        let claims = verify_token(token)?;

        Ok(CurrentUser {
            id: claims.sub,
            email: claims.email,
        })
    }
}

// 사용
async fn get_profile(user: CurrentUser) -> impl IntoResponse {
    // user.id, user.email 사용 가능
}
```

## 중첩 라우터

### 모듈별 라우터 분리

```rust
// src/routes/mod.rs
pub mod users;
pub mod products;
pub mod orders;

pub fn api_routes() -> Router<AppState> {
    Router::new()
        .nest("/users", users::router())
        .nest("/products", products::router())
        .nest("/orders", orders::router())
}

// src/routes/users.rs
pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(list).post(create))
        .route("/:id", get(show).put(update).delete(destroy))
        .route("/:id/avatar", post(upload_avatar))
}
```

### 버저닝

```rust
fn app() -> Router<AppState> {
    Router::new()
        .nest("/api/v1", v1::routes())
        .nest("/api/v2", v2::routes())
        .route("/health", get(health_check))
}
```

## 응답 패턴

### 다양한 응답 타입

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response, Json},
};

// 단순 상태 코드
async fn delete_user() -> StatusCode {
    StatusCode::NO_CONTENT
}

// JSON 응답
async fn get_user() -> Json<UserResponse> {
    Json(UserResponse { /* ... */ })
}

// 상태 코드 + JSON
async fn create_user() -> (StatusCode, Json<UserResponse>) {
    (StatusCode::CREATED, Json(UserResponse { /* ... */ }))
}

// 헤더 포함
async fn create_with_location() -> impl IntoResponse {
    (
        StatusCode::CREATED,
        [("Location", "/users/123")],
        Json(UserResponse { /* ... */ }),
    )
}

// Result 반환
async fn get_user_result() -> Result<Json<UserResponse>, AppError> {
    let user = find_user().await?;
    Ok(Json(user))
}
```

### 페이지네이션 응답

```rust
#[derive(Serialize)]
struct PaginatedResponse<T> {
    data: Vec<T>,
    pagination: Pagination,
}

#[derive(Serialize)]
struct Pagination {
    page: u32,
    per_page: u32,
    total: u64,
    total_pages: u32,
}

async fn list_users(
    Query(params): Query<ListParams>,
) -> Result<Json<PaginatedResponse<UserResponse>>, AppError> {
    let (users, total) = user_service.list_paginated(params.page, params.per_page).await?;

    Ok(Json(PaginatedResponse {
        data: users,
        pagination: Pagination {
            page: params.page,
            per_page: params.per_page,
            total,
            total_pages: (total as f64 / params.per_page as f64).ceil() as u32,
        },
    }))
}
```

## Fallback 핸들러

```rust
async fn fallback(uri: axum::http::Uri) -> impl IntoResponse {
    (
        StatusCode::NOT_FOUND,
        Json(serde_json::json!({
            "error": "not_found",
            "message": format!("No route for {}", uri)
        })),
    )
}

fn app() -> Router<AppState> {
    Router::new()
        .nest("/api", api_routes())
        .fallback(fallback)
}
```
