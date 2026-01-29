# Rust Observability Cheatsheet

## Tracing

```rust
use tracing::{info, warn, error, instrument, span, Level};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// Setup
tracing_subscriber::registry()
    .with(tracing_subscriber::fmt::layer().json())
    .init();

// Logging
info!(user_id = "123", "User logged in");
warn!(order_id = order_id, "Order processing delayed");
error!(error = ?e, "Failed to process");

// Spans
#[instrument(skip(db))]
async fn get_user(db: &Database, user_id: i64) -> User {
    info!("Fetching user");
    db.get_user(user_id).await
}
```

## Metrics (prometheus)

```rust
use prometheus::{Counter, Histogram, Registry, Encoder, TextEncoder};

lazy_static! {
    static ref REQUEST_COUNTER: Counter = Counter::new(
        "http_requests_total", "Total HTTP requests"
    ).unwrap();

    static ref REQUEST_DURATION: Histogram = Histogram::with_opts(
        HistogramOpts::new("http_request_duration_seconds", "Request duration")
    ).unwrap();
}

// Axum middleware
async fn metrics_middleware<B>(request: Request<B>, next: Next<B>) -> Response {
    let start = Instant::now();
    let response = next.run(request).await;

    REQUEST_COUNTER.inc();
    REQUEST_DURATION.observe(start.elapsed().as_secs_f64());

    response
}

// Expose metrics
async fn metrics() -> String {
    let encoder = TextEncoder::new();
    let metric_families = prometheus::gather();
    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer).unwrap();
    String::from_utf8(buffer).unwrap()
}
```

## OpenTelemetry

```rust
use opentelemetry::global;
use opentelemetry_sdk::trace::TracerProvider;
use tracing_opentelemetry::OpenTelemetryLayer;

// Setup
let tracer = opentelemetry_otlp::new_pipeline()
    .tracing()
    .with_exporter(opentelemetry_otlp::new_exporter().tonic())
    .install_batch(opentelemetry_sdk::runtime::Tokio)?;

tracing_subscriber::registry()
    .with(OpenTelemetryLayer::new(tracer))
    .init();

// Usage with #[instrument]
#[instrument]
async fn process_order(order_id: i64) {
    // Automatically creates span
}
```

## Axum with Tracing

```rust
use axum::{Router, middleware};
use tower_http::trace::TraceLayer;

let app = Router::new()
    .route("/", get(handler))
    .layer(TraceLayer::new_for_http());
```
