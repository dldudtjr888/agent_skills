---
name: rust-route-debugger
description: Axum 라우트 디버깅. tracing, tower 미들웨어를 활용한 요청/응답 분석.
model: opus
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Rust Route Debugger

Axum 라우트 문제를 진단하고 디버깅합니다.

**참조 스킬**: `rust-error-handling`, `axum-backend-pattern`

**관련 참조**: `common-backend/observability` (로깅, 트레이싱)

## 디버깅 도구

### Tracing 설정

```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

tracing_subscriber::registry()
    .with(tracing_subscriber::fmt::layer())
    .with(tracing_subscriber::EnvFilter::from_default_env())
    .init();
```

### 요청 로깅

```rust
use tower_http::trace::TraceLayer;

let app = Router::new()
    .route("/", get(handler))
    .layer(TraceLayer::new_for_http());
```

### 디버그 미들웨어

```rust
async fn debug_middleware<B>(
    request: Request<B>,
    next: Next<B>,
) -> Response {
    let method = request.method().clone();
    let uri = request.uri().clone();

    tracing::debug!(%method, %uri, "Request");

    let response = next.run(request).await;

    tracing::debug!(status = %response.status(), "Response");

    response
}
```

## 일반적인 문제

1. **404 Not Found** - 라우트 경로 확인
2. **422 Unprocessable** - JSON 스키마 확인
3. **500 Internal** - 로그에서 panic 확인
4. **인증 실패** - 토큰/헤더 확인

## 요청/응답 바디 로깅

```rust
use axum::body::{Body, Bytes};
use http_body_util::BodyExt;

async fn log_request_body<B>(
    request: Request<B>,
    next: Next<B>,
) -> Response
where
    B: axum::body::HttpBody<Data = Bytes>,
{
    let (parts, body) = request.into_parts();

    let bytes = body
        .collect()
        .await
        .map(|c| c.to_bytes())
        .unwrap_or_default();

    tracing::debug!(
        body = %String::from_utf8_lossy(&bytes),
        "Request body"
    );

    let request = Request::from_parts(parts, Body::from(bytes));
    next.run(request).await
}
```

## 라우트 목록 출력

```rust
// 개발 시 등록된 라우트 확인
fn print_routes(router: &Router) {
    // axum은 직접적인 라우트 목록 API 없음
    // 대신 문서화하거나 테스트로 확인
}

// 대안: OpenAPI 스펙 생성
use utoipa::OpenApi;

#[derive(OpenApi)]
#[openapi(paths(get_user, create_user, delete_user))]
struct ApiDoc;
```

## 에러 추적

```rust
use tracing::{instrument, error};

#[instrument(skip(pool))]
async fn get_user(
    State(pool): State<PgPool>,
    Path(id): Path<i64>,
) -> Result<Json<User>, AppError> {
    sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_optional(&pool)
        .await
        .map_err(|e| {
            error!(error = %e, "Database error");
            AppError::Database(e)
        })?
        .ok_or_else(|| {
            tracing::warn!(user_id = id, "User not found");
            AppError::NotFound
        })
        .map(Json)
}
```

## Panic 추적

```rust
use std::panic;

fn setup_panic_handler() {
    panic::set_hook(Box::new(|info| {
        let backtrace = std::backtrace::Backtrace::capture();
        tracing::error!(
            panic = %info,
            backtrace = %backtrace,
            "Panic occurred"
        );
    }));
}
```

## 명령어

```bash
# 기본 디버그
RUST_LOG=debug cargo run

# HTTP 트레이싱
RUST_LOG=tower_http=trace cargo run

# 특정 모듈만
RUST_LOG=my_app::handlers=debug cargo run

# JSON 포맷
RUST_LOG=debug cargo run 2>&1 | jq .

# 요청 테스트
curl -v http://localhost:3000/api/users/1
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

## 체크리스트

- [ ] tracing 설정 확인
- [ ] 로그 레벨 적절한지
- [ ] 에러 응답 메시지 확인
- [ ] 스택 트레이스 확인
- [ ] 요청/응답 헤더 확인
- [ ] 타임아웃 설정 확인
