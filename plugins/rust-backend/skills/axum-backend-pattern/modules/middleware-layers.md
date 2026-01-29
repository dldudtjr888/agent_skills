# Middleware Layers

Tower 기반 미들웨어와 Axum 레이어 패턴.

## Tower ServiceBuilder

```rust
use axum::{Router, middleware};
use tower::ServiceBuilder;
use tower_http::{
    cors::CorsLayer,
    trace::TraceLayer,
    compression::CompressionLayer,
    timeout::TimeoutLayer,
};
use std::time::Duration;

fn app(state: AppState) -> Router {
    Router::new()
        .nest("/api", api_routes())
        .layer(
            ServiceBuilder::new()
                // 순서 중요: 아래에서 위로 실행됨
                .layer(TraceLayer::new_for_http())
                .layer(CompressionLayer::new())
                .layer(TimeoutLayer::new(Duration::from_secs(30)))
                .layer(CorsLayer::permissive())
        )
        .with_state(state)
}
```

## 트레이싱/로깅

```rust
use tower_http::trace::{TraceLayer, DefaultMakeSpan, DefaultOnResponse};
use tracing::Level;

fn tracing_layer() -> TraceLayer<
    tower_http::classify::SharedClassifier<tower_http::classify::ServerErrorsAsFailures>,
> {
    TraceLayer::new_for_http()
        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
        .on_response(DefaultOnResponse::new().level(Level::INFO))
}

// 커스텀 트레이싱
use tower_http::trace::{MakeSpan, OnRequest, OnResponse};

#[derive(Clone)]
struct CustomMakeSpan;

impl<B> MakeSpan<B> for CustomMakeSpan {
    fn make_span(&mut self, request: &axum::http::Request<B>) -> tracing::Span {
        tracing::info_span!(
            "http_request",
            method = %request.method(),
            uri = %request.uri(),
            version = ?request.version(),
        )
    }
}
```

## CORS

```rust
use tower_http::cors::{CorsLayer, Any};
use axum::http::{HeaderValue, Method};

// 개발용: 모든 오리진 허용
fn cors_dev() -> CorsLayer {
    CorsLayer::permissive()
}

// 프로덕션용: 특정 오리진만 허용
fn cors_prod() -> CorsLayer {
    CorsLayer::new()
        .allow_origin([
            "https://example.com".parse::<HeaderValue>().unwrap(),
            "https://app.example.com".parse::<HeaderValue>().unwrap(),
        ])
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_headers(Any)
        .allow_credentials(true)
        .max_age(Duration::from_secs(3600))
}
```

## 인증 미들웨어

### from_fn 미들웨어

```rust
use axum::{
    middleware::{self, Next},
    http::Request,
    response::Response,
};

async fn auth_middleware<B>(
    State(state): State<AppState>,
    request: Request<B>,
    next: Next<B>,
) -> Result<Response, AppError> {
    let auth_header = request
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .ok_or(AppError::Unauthorized)?;

    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or(AppError::Unauthorized)?;

    // 토큰 검증
    let claims = state.auth_service.verify_token(token).await?;

    // 요청에 사용자 정보 추가
    let mut request = request;
    request.extensions_mut().insert(claims);

    Ok(next.run(request).await)
}

// 특정 라우트에만 적용
fn protected_routes() -> Router<AppState> {
    Router::new()
        .route("/profile", get(get_profile))
        .route("/settings", get(get_settings).put(update_settings))
        .layer(middleware::from_fn_with_state(state.clone(), auth_middleware))
}
```

### 선택적 인증

```rust
async fn optional_auth_middleware<B>(
    State(state): State<AppState>,
    mut request: Request<B>,
    next: Next<B>,
) -> Response {
    if let Some(auth_header) = request
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
    {
        if let Some(token) = auth_header.strip_prefix("Bearer ") {
            if let Ok(claims) = state.auth_service.verify_token(token).await {
                request.extensions_mut().insert(claims);
            }
        }
    }

    next.run(request).await
}
```

## Rate Limiting

```rust
use tower_governor::{
    governor::GovernorConfigBuilder,
    GovernorLayer,
};

fn rate_limit_layer() -> GovernorLayer<'static, (), impl tower_governor::key_extractor::KeyExtractor> {
    let config = GovernorConfigBuilder::default()
        .per_second(10)  // 초당 10개 요청
        .burst_size(20)  // 버스트 허용량
        .finish()
        .unwrap();

    GovernorLayer::new(&config)
}

// IP 기반 Rate Limiting
use tower_governor::key_extractor::SmartIpKeyExtractor;

fn rate_limit_by_ip() -> GovernorLayer<'static, (), SmartIpKeyExtractor> {
    let config = GovernorConfigBuilder::default()
        .per_second(10)
        .burst_size(20)
        .key_extractor(SmartIpKeyExtractor)
        .finish()
        .unwrap();

    GovernorLayer::new(&config)
}
```

## 요청 ID

```rust
use tower_http::request_id::{
    MakeRequestId, RequestId, SetRequestIdLayer, PropagateRequestIdLayer,
};
use uuid::Uuid;

#[derive(Clone)]
struct MakeRequestUuid;

impl MakeRequestId for MakeRequestUuid {
    fn make_request_id<B>(&mut self, _request: &Request<B>) -> Option<RequestId> {
        let id = Uuid::new_v4().to_string();
        Some(RequestId::new(id.parse().unwrap()))
    }
}

fn request_id_layers() -> (SetRequestIdLayer<MakeRequestUuid>, PropagateRequestIdLayer) {
    (
        SetRequestIdLayer::new(MakeRequestUuid),
        PropagateRequestIdLayer::new(HeaderName::from_static("x-request-id")),
    )
}
```

## 타임아웃

```rust
use tower_http::timeout::TimeoutLayer;
use std::time::Duration;

// 전역 타임아웃
fn timeout_layer() -> TimeoutLayer {
    TimeoutLayer::new(Duration::from_secs(30))
}

// 라우트별 타임아웃
fn routes_with_timeout() -> Router<AppState> {
    Router::new()
        .route("/quick", get(quick_handler))
        .route(
            "/slow",
            get(slow_handler).layer(TimeoutLayer::new(Duration::from_secs(120)))
        )
}
```

## 압축

```rust
use tower_http::compression::{CompressionLayer, predicate::SizeAbove};

fn compression_layer() -> CompressionLayer {
    CompressionLayer::new()
        .quality(tower_http::compression::CompressionLevel::Default)
}

// 최소 크기 이상만 압축
fn compression_with_predicate() -> CompressionLayer<SizeAbove> {
    CompressionLayer::new()
        .compress_when(SizeAbove::new(1024))  // 1KB 이상만 압축
}
```

## 커스텀 미들웨어

```rust
use std::task::{Context, Poll};
use tower::{Layer, Service};

// Layer 정의
#[derive(Clone)]
pub struct TimingLayer;

impl<S> Layer<S> for TimingLayer {
    type Service = TimingService<S>;

    fn layer(&self, inner: S) -> Self::Service {
        TimingService { inner }
    }
}

// Service 정의
#[derive(Clone)]
pub struct TimingService<S> {
    inner: S,
}

impl<S, B> Service<Request<B>> for TimingService<S>
where
    S: Service<Request<B>, Response = Response> + Clone + Send + 'static,
    S::Future: Send,
    B: Send + 'static,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = std::pin::Pin<Box<dyn std::future::Future<Output = Result<Self::Response, Self::Error>> + Send>>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, request: Request<B>) -> Self::Future {
        let mut inner = self.inner.clone();

        Box::pin(async move {
            let start = std::time::Instant::now();
            let response = inner.call(request).await?;
            let elapsed = start.elapsed();

            tracing::info!(elapsed_ms = elapsed.as_millis(), "request completed");

            Ok(response)
        })
    }
}
```

## 레이어 순서

```rust
// 실행 순서: 아래에서 위로 (요청), 위에서 아래로 (응답)
Router::new()
    .layer(
        ServiceBuilder::new()
            // 5. 가장 바깥쪽: 트레이싱 (모든 요청/응답 기록)
            .layer(TraceLayer::new_for_http())
            // 4. 압축 (응답 압축)
            .layer(CompressionLayer::new())
            // 3. 타임아웃 (최대 요청 시간)
            .layer(TimeoutLayer::new(Duration::from_secs(30)))
            // 2. CORS (프리플라이트 처리)
            .layer(cors_layer())
            // 1. 가장 안쪽: 인증 (보호된 리소스 접근)
            .layer(middleware::from_fn(auth_middleware))
    )
```
