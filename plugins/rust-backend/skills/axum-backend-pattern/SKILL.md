---
name: axum-backend-pattern
description: "Axum 백엔드 패턴 가이드. 라우터 설계, 미들웨어, State 관리, 에러 핸들링, 테스트 패턴을 다룹니다."
version: 1.0.0
category: backend
user-invocable: true
triggers:
  keywords:
    - axum
    - router
    - 라우터
    - middleware
    - 미들웨어
    - tower
    - state
    - handler
    - 핸들러
    - into_response
    - extractor
  intentPatterns:
    - "(만들|생성|구현|설계).*(axum|API|백엔드|서버)"
    - "(axum|api).*(라우터|라우트|미들웨어|핸들러)"
---

# Axum Backend Pattern

Axum 웹 프레임워크를 사용한 백엔드 개발 패턴과 베스트 프랙티스.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Routing Patterns | [modules/routing-patterns.md](modules/routing-patterns.md) | 라우터 설계, Path/Query/Json 추출, 중첩 라우터 |
| 2 | Middleware Layers | [modules/middleware-layers.md](modules/middleware-layers.md) | Tower 미들웨어, 인증, 로깅, CORS, Rate Limiting |
| 3 | Error Handling | [modules/error-handling.md](modules/error-handling.md) | AppError, IntoResponse, thiserror 통합 |
| 4 | State Management | [modules/state-management.md](modules/state-management.md) | Arc<State>, Extension, 의존성 주입 |
| 5 | Testing Patterns | [modules/testing-patterns.md](modules/testing-patterns.md) | axum-test, TestClient, 통합 테스트 |

## 사용 시점

### When to Use
- Axum 기반 REST API 서버 구축
- 마이크로서비스 백엔드 개발
- Tower 미들웨어 스택 설계
- Tokio 기반 비동기 웹 서비스

### When NOT to Use
- 프론트엔드 전용 작업
- Actix-web 프로젝트 (별도 패턴 필요)
- 단순 CLI 도구 개발

## 핵심 아키텍처

```
                    Request
                       ↓
┌─────────────────────────────────────────────────────┐
│                    Tower Layers                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Tracing │→ │  CORS   │→ │  Auth   │→ │Compress │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                   Axum Router                        │
│  ┌─────────────────────────────────────────────────┐│
│  │ /api/v1                                         ││
│  │   ├── /users     → UsersRouter                  ││
│  │   ├── /products  → ProductsRouter               ││
│  │   └── /orders    → OrdersRouter                 ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                    Handler                           │
│  ┌─────────────────────────────────────────────────┐│
│  │ Extractors: Path, Query, Json, State, Extension ││
│  └─────────────────────────────────────────────────┘│
│                       ↓                              │
│  ┌─────────────────────────────────────────────────┐│
│  │ Business Logic (Service Layer)                  ││
│  └─────────────────────────────────────────────────┘│
│                       ↓                              │
│  ┌─────────────────────────────────────────────────┐│
│  │ Response: Json<T>, IntoResponse                 ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
                       ↓
                    Response
```

## Quick Start

### 기본 서버 설정

```rust
use axum::{Router, routing::get};
use std::net::SocketAddr;
use tokio::net::TcpListener;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 트레이싱 초기화
    tracing_subscriber::init();

    // 라우터 구성
    let app = Router::new()
        .route("/health", get(health_check))
        .nest("/api/v1", api_routes());

    // 서버 시작
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    let listener = TcpListener::bind(addr).await?;
    tracing::info!("listening on {}", addr);

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

async fn health_check() -> &'static str {
    "OK"
}

fn api_routes() -> Router {
    Router::new()
        .nest("/users", users::router())
        .nest("/products", products::router())
}
```

### 핸들러 예제

```rust
use axum::{
    extract::{Path, Query, State, Json},
    http::StatusCode,
    response::IntoResponse,
};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct ListParams {
    page: Option<u32>,
    per_page: Option<u32>,
}

#[derive(Serialize)]
pub struct UserResponse {
    id: i64,
    name: String,
    email: String,
}

// GET /users?page=1&per_page=10
pub async fn list_users(
    State(state): State<AppState>,
    Query(params): Query<ListParams>,
) -> Result<Json<Vec<UserResponse>>, AppError> {
    let page = params.page.unwrap_or(1);
    let per_page = params.per_page.unwrap_or(20);

    let users = state.user_service.list(page, per_page).await?;
    Ok(Json(users))
}

// GET /users/:id
pub async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<Json<UserResponse>, AppError> {
    let user = state.user_service.find_by_id(id).await?
        .ok_or(AppError::NotFound)?;
    Ok(Json(user))
}

// POST /users
pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUserRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user = state.user_service.create(payload).await?;
    Ok((StatusCode::CREATED, Json(user)))
}
```

### State 설정

```rust
use std::sync::Arc;

#[derive(Clone)]
pub struct AppState {
    pub db: sqlx::PgPool,
    pub user_service: Arc<UserService>,
    pub config: Arc<Config>,
}

impl AppState {
    pub async fn new(config: Config) -> anyhow::Result<Self> {
        let db = sqlx::PgPool::connect(&config.database_url).await?;
        let user_service = Arc::new(UserService::new(db.clone()));

        Ok(Self {
            db,
            user_service,
            config: Arc::new(config),
        })
    }
}

// 라우터에 State 추가
fn app(state: AppState) -> Router {
    Router::new()
        .route("/users", get(list_users).post(create_user))
        .route("/users/:id", get(get_user))
        .with_state(state)
}
```

## 체크리스트

### API 설계
- [ ] RESTful URL 구조 (/resources, /resources/:id)
- [ ] 적절한 HTTP 메서드 (GET/POST/PUT/PATCH/DELETE)
- [ ] 적절한 상태 코드 (201 Created, 204 No Content, 404 Not Found)
- [ ] JSON 스키마 분리 (CreateRequest/UpdateRequest/Response)
- [ ] 버저닝 전략 (/api/v1)

### 미들웨어
- [ ] 트레이싱/로깅 설정
- [ ] CORS 설정
- [ ] 인증 미들웨어
- [ ] Rate Limiting (필요시)
- [ ] 요청/응답 압축

### 에러 처리
- [ ] 통합 AppError 타입
- [ ] IntoResponse 구현
- [ ] 에러 로깅
- [ ] 클라이언트용 에러 응답 포맷

### 상태 관리
- [ ] Arc<State> 패턴
- [ ] 의존성 주입
- [ ] DB 커넥션 풀
- [ ] 설정 관리

### 테스트
- [ ] 단위 테스트 (핸들러 로직)
- [ ] 통합 테스트 (axum-test)
- [ ] API 엔드포인트 테스트

## common-backend 참조

이 스킬은 언어 무관 백엔드 패턴을 참조합니다:
- `common-backend/api-design` - REST/GraphQL 원칙
- `common-backend/auth-patterns` - 인증/인가 패턴
- `common-backend/observability` - 로깅/메트릭/트레이싱

## 관련 스킬

- `rust-patterns` - 기본 Rust 패턴
- `tokio-async-patterns` - Tokio 비동기 패턴
- `rust-db-patterns` - 데이터베이스 패턴
- `rust-error-handling` - 에러 처리 심화
