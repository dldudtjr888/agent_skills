---
name: rust-crate-ecosystem
description: "Rust 주요 크레이트 가이드. serde, tracing, tower, reqwest 등 필수 크레이트."
version: 1.0.0
category: ecosystem
user-invocable: true
triggers:
  keywords:
    - crate
    - 크레이트
    - serde
    - tracing
    - tower
    - reqwest
  intentPatterns:
    - "(추천|사용).*(크레이트|crate)"
    - "(serde|tracing|tower).*(사용법|패턴)"
---

# Rust Crate Ecosystem

필수 Rust 크레이트 가이드.

## 관련 참조

- **common-backend/api-design**: RESTful API 설계 원칙
- **common-backend/observability**: 모니터링 및 트레이싱 통합

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Serialization | [modules/serialization.md](modules/serialization.md) | serde 심화, custom deserialize |
| 2 | Observability Crates | [modules/observability-crates.md](modules/observability-crates.md) | tracing, metrics, opentelemetry |
| 3 | Web Crates | [modules/web-crates.md](modules/web-crates.md) | tower middleware, reqwest, hyper |

## Serialization: serde

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct User {
    id: i64,
    name: String,
    #[serde(default)]
    active: bool,
}

// JSON
let json = serde_json::to_string(&user)?;
let user: User = serde_json::from_str(&json)?;
```

## Logging: tracing

```rust
use tracing::{info, warn, error, instrument};

#[instrument(skip(password))]
async fn login(email: &str, password: &str) -> Result<User> {
    info!(%email, "Login attempt");

    let user = find_user(email).await?;
    if !verify_password(password, &user.hash) {
        warn!(%email, "Invalid password");
        return Err(AuthError::InvalidPassword);
    }

    info!(%email, user_id = %user.id, "Login successful");
    Ok(user)
}
```

## HTTP Client: reqwest

```rust
use reqwest::Client;

let client = Client::new();
let response = client
    .get("https://api.example.com/data")
    .header("Authorization", format!("Bearer {}", token))
    .send()
    .await?;

let data: ApiResponse = response.json().await?;
```

## Middleware: tower

```rust
use tower::{ServiceBuilder, timeout::TimeoutLayer};

let service = ServiceBuilder::new()
    .layer(TimeoutLayer::new(Duration::from_secs(30)))
    .service(inner_service);
```

## 주요 크레이트

| 분야 | 크레이트 |
|------|---------|
| 직렬화 | serde, serde_json |
| 로깅 | tracing, tracing-subscriber |
| HTTP 클라이언트 | reqwest |
| HTTP 서버 | axum, actix-web |
| 데이터베이스 | sqlx, diesel |
| 비동기 | tokio |
| CLI | clap |
| 에러 | thiserror, anyhow |
| 날짜/시간 | chrono |
| UUID | uuid |
