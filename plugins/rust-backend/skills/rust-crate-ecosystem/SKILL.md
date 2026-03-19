---
name: rust-crate-ecosystem
description: >-
  Rust 핵심 크레이트 에코시스템 가이드. serde/serde_json 직렬화, tracing/tracing-subscriber 구조화 로깅,
  tower/tower-http 미들웨어, reqwest HTTP 클라이언트, moka 캐시, rdkafka Kafka 클라이언트,
  lapin RabbitMQ AMQP, tonic gRPC, prost protobuf, config-rs 설정 관리, clap CLI 파서,
  chrono/time 시간 처리, uuid, base64, regex 유틸리티 크레이트 사용법과 조합 패턴.
  MUST USE: Rust 크레이트 선택, serde 직렬화 패턴, tracing 설정, reqwest 사용, 메시지 큐(rdkafka/lapin)
  연동, 캐시(moka) 설정, gRPC(tonic) 서비스 구축 시 반드시 사용.
  러스트 크레이트 추천, 필수 라이브러리 선택, 직렬화/로깅/HTTP/메시지큐 설정 시 반드시 활성화.
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
