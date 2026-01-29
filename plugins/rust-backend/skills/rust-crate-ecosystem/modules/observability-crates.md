# Observability Crates

tracing, metrics, opentelemetry 통합 패턴.

## tracing 기본 설정

```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

pub fn init_tracing() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| {
            "my_app=debug,tower_http=debug".into()
        }))
        .with(tracing_subscriber::fmt::layer())
        .init();
}

// JSON 포맷 (프로덕션)
pub fn init_json_tracing() {
    tracing_subscriber::registry()
        .with(EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer().json())
        .init();
}
```

## Span 및 Event

```rust
use tracing::{info, warn, error, instrument, Span};

#[instrument(skip(pool), fields(user_id = %user_id))]
pub async fn get_user(pool: &PgPool, user_id: i64) -> Result<User, Error> {
    info!("Fetching user");

    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", user_id)
        .fetch_optional(pool)
        .await?;

    match user {
        Some(u) => {
            Span::current().record("user_name", &u.name);
            info!(email = %u.email, "User found");
            Ok(u)
        }
        None => {
            warn!("User not found");
            Err(Error::NotFound)
        }
    }
}
```

## Axum + Tower HTTP

```rust
use axum::{Router, routing::get};
use tower_http::trace::{TraceLayer, DefaultMakeSpan, DefaultOnResponse};
use tracing::Level;

pub fn create_app() -> Router {
    Router::new()
        .route("/api/users", get(list_users))
        .layer(
            TraceLayer::new_for_http()
                .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                .on_response(DefaultOnResponse::new().level(Level::INFO)),
        )
}
```

## metrics 크레이트

```rust
use metrics::{counter, gauge, histogram, describe_counter, describe_histogram};

pub fn init_metrics() {
    describe_counter!("http_requests_total", "Total HTTP requests");
    describe_histogram!("http_request_duration_seconds", "HTTP request duration");
}

pub async fn track_request<F, T>(handler: F) -> T
where
    F: std::future::Future<Output = T>,
{
    let start = std::time::Instant::now();

    counter!("http_requests_total").increment(1);

    let result = handler.await;

    histogram!("http_request_duration_seconds")
        .record(start.elapsed().as_secs_f64());

    result
}
```

## metrics-exporter-prometheus

```rust
use axum::{routing::get, Router};
use metrics_exporter_prometheus::{Matcher, PrometheusBuilder, PrometheusHandle};

pub fn setup_metrics() -> PrometheusHandle {
    PrometheusBuilder::new()
        .set_buckets_for_metric(
            Matcher::Full("http_request_duration_seconds".to_string()),
            &[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
        .unwrap()
        .install_recorder()
        .unwrap()
}

pub fn metrics_router(handle: PrometheusHandle) -> Router {
    Router::new().route("/metrics", get(move || {
        std::future::ready(handle.render())
    }))
}
```

## OpenTelemetry 통합

```rust
use opentelemetry::sdk::trace::Tracer;
use opentelemetry_otlp::WithExportConfig;
use tracing_opentelemetry::OpenTelemetryLayer;

pub fn init_otel_tracing() -> Result<(), Box<dyn std::error::Error>> {
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://localhost:4317"),
        )
        .install_batch(opentelemetry::runtime::Tokio)?;

    tracing_subscriber::registry()
        .with(EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer())
        .with(OpenTelemetryLayer::new(tracer))
        .init();

    Ok(())
}
```

## Request ID 전파

```rust
use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};
use uuid::Uuid;

pub async fn request_id_middleware(mut request: Request, next: Next) -> Response {
    let request_id = request
        .headers()
        .get("x-request-id")
        .and_then(|v| v.to_str().ok())
        .map(String::from)
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    let span = tracing::info_span!("request", request_id = %request_id);
    let _guard = span.enter();

    request.headers_mut().insert(
        "x-request-id",
        request_id.parse().unwrap(),
    );

    next.run(request).await
}
```

## 에러 추적

```rust
pub fn log_error_with_context(error: &dyn std::error::Error) {
    let mut chain = vec![error.to_string()];
    let mut source = error.source();
    while let Some(err) = source {
        chain.push(err.to_string());
        source = err.source();
    }

    tracing::error!(
        error_chain = ?chain,
        "Error occurred"
    );
}
```

## 체크리스트

- [ ] tracing 초기화 (개발 vs 프로덕션)
- [ ] #[instrument] 주요 함수에 적용
- [ ] metrics 수집 설정
- [ ] Prometheus endpoint 노출
- [ ] Request ID 추적
- [ ] OpenTelemetry 연동 (선택)
- [ ] 에러 체인 로깅
