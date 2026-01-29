# Web Crates

tower, hyper, reqwest 통합 패턴.

## Tower 미들웨어

```rust
use tower::{ServiceBuilder, ServiceExt, timeout::TimeoutLayer};
use tower_http::{
    cors::CorsLayer,
    compression::CompressionLayer,
    limit::RequestBodyLimitLayer,
    trace::TraceLayer,
};
use std::time::Duration;

pub fn create_service_stack() -> ServiceBuilder<...> {
    ServiceBuilder::new()
        .layer(TraceLayer::new_for_http())
        .layer(TimeoutLayer::new(Duration::from_secs(30)))
        .layer(CompressionLayer::new())
        .layer(CorsLayer::permissive())
        .layer(RequestBodyLimitLayer::new(1024 * 1024))  // 1MB
}
```

## 커스텀 Tower Layer

```rust
use tower::{Layer, Service};
use std::task::{Context, Poll};
use pin_project::pin_project;

#[derive(Clone)]
pub struct TimingLayer;

impl<S> Layer<S> for TimingLayer {
    type Service = TimingService<S>;

    fn layer(&self, inner: S) -> Self::Service {
        TimingService { inner }
    }
}

#[derive(Clone)]
pub struct TimingService<S> {
    inner: S,
}

impl<S, Request> Service<Request> for TimingService<S>
where
    S: Service<Request>,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = TimingFuture<S::Future>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, request: Request) -> Self::Future {
        let start = std::time::Instant::now();
        TimingFuture {
            inner: self.inner.call(request),
            start,
        }
    }
}

#[pin_project]
pub struct TimingFuture<F> {
    #[pin]
    inner: F,
    start: std::time::Instant,
}

impl<F, T, E> Future for TimingFuture<F>
where
    F: Future<Output = Result<T, E>>,
{
    type Output = Result<T, E>;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let this = self.project();
        let result = this.inner.poll(cx);

        if result.is_ready() {
            tracing::info!(
                duration_ms = this.start.elapsed().as_millis() as u64,
                "Request completed"
            );
        }

        result
    }
}
```

## reqwest HTTP 클라이언트

```rust
use reqwest::{Client, ClientBuilder};
use std::time::Duration;

pub fn create_http_client() -> Client {
    ClientBuilder::new()
        .timeout(Duration::from_secs(30))
        .connect_timeout(Duration::from_secs(10))
        .pool_max_idle_per_host(10)
        .pool_idle_timeout(Duration::from_secs(60))
        .user_agent("my-app/1.0")
        .build()
        .unwrap()
}

pub async fn fetch_json<T: serde::de::DeserializeOwned>(
    client: &Client,
    url: &str,
) -> Result<T, reqwest::Error> {
    client
        .get(url)
        .header("Accept", "application/json")
        .send()
        .await?
        .error_for_status()?
        .json()
        .await
}
```

## reqwest 재시도 패턴

```rust
use reqwest_middleware::{ClientBuilder, ClientWithMiddleware};
use reqwest_retry::{RetryTransientMiddleware, policies::ExponentialBackoff};

pub fn create_resilient_client() -> ClientWithMiddleware {
    let retry_policy = ExponentialBackoff::builder()
        .retry_bounds(
            Duration::from_millis(100),
            Duration::from_secs(10),
        )
        .build_with_max_retries(3);

    ClientBuilder::new(reqwest::Client::new())
        .with(RetryTransientMiddleware::new_with_policy(retry_policy))
        .build()
}
```

## hyper 직접 사용

```rust
use hyper::{Body, Request, Response, Server};
use hyper::service::{make_service_fn, service_fn};

async fn handle_request(req: Request<Body>) -> Result<Response<Body>, hyper::Error> {
    match (req.method(), req.uri().path()) {
        (&hyper::Method::GET, "/health") => {
            Ok(Response::new(Body::from("OK")))
        }
        _ => {
            let mut response = Response::new(Body::from("Not Found"));
            *response.status_mut() = hyper::StatusCode::NOT_FOUND;
            Ok(response)
        }
    }
}

pub async fn run_server(addr: std::net::SocketAddr) {
    let make_svc = make_service_fn(|_conn| async {
        Ok::<_, hyper::Error>(service_fn(handle_request))
    });

    Server::bind(&addr)
        .serve(make_svc)
        .await
        .unwrap();
}
```

## Connection Pool 관리

```rust
use reqwest::Client;
use std::sync::Arc;

pub struct ApiClient {
    client: Client,
    base_url: String,
}

impl ApiClient {
    pub fn new(base_url: &str) -> Self {
        let client = Client::builder()
            .pool_max_idle_per_host(20)
            .pool_idle_timeout(Duration::from_secs(90))
            .build()
            .unwrap();

        Self {
            client,
            base_url: base_url.to_string(),
        }
    }

    pub async fn get<T: serde::de::DeserializeOwned>(
        &self,
        path: &str,
    ) -> Result<T, ApiError> {
        let url = format!("{}{}", self.base_url, path);

        self.client
            .get(&url)
            .send()
            .await?
            .error_for_status()?
            .json()
            .await
            .map_err(Into::into)
    }
}

// Axum State로 공유
pub type SharedApiClient = Arc<ApiClient>;
```

## 스트리밍 응답

```rust
use axum::{
    body::Body,
    response::Response,
};
use tokio_stream::StreamExt;
use futures::stream;

pub async fn stream_response() -> Response<Body> {
    let stream = stream::iter(vec!["Hello, ", "World!"])
        .map(|s| Ok::<_, std::io::Error>(s.to_string()));

    Response::new(Body::wrap_stream(stream))
}
```

## 체크리스트

- [ ] Tower 미들웨어 스택 구성
- [ ] 타임아웃 설정
- [ ] Connection pool 최적화
- [ ] 재시도 정책 설정
- [ ] 요청/응답 로깅
- [ ] 에러 핸들링 통합
