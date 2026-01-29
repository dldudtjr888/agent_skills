# Context Propagation

에러 컨텍스트 전파 및 스택 트레이스 패턴.

## anyhow Context

```rust
use anyhow::{Context, Result};

pub fn load_config(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read config file: {}", path))?;

    let config: Config = toml::from_str(&content)
        .with_context(|| "Failed to parse TOML config")?;

    validate_config(&config)
        .with_context(|| "Config validation failed")?;

    Ok(config)
}

// 출력 예:
// Error: Config validation failed
// Caused by:
//     0: Failed to parse TOML config
//     1: expected string, found integer at line 5
```

## 체인된 Context

```rust
pub async fn process_order(order_id: i64) -> Result<Receipt> {
    let order = fetch_order(order_id)
        .await
        .with_context(|| format!("Failed to fetch order {}", order_id))?;

    let items = fetch_items(&order)
        .await
        .with_context(|| format!("Failed to fetch items for order {}", order_id))?;

    let total = calculate_total(&items)
        .with_context(|| "Failed to calculate total")?;

    let receipt = generate_receipt(&order, total)
        .with_context(|| format!("Failed to generate receipt for order {}", order_id))?;

    Ok(receipt)
}
```

## thiserror + Source

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ServiceError {
    #[error("Database operation failed")]
    Database(#[source] sqlx::Error),

    #[error("External API call failed")]
    ExternalApi(#[source] reqwest::Error),

    #[error("Validation failed: {message}")]
    Validation {
        message: String,
        #[source]
        source: ValidationError,
    },
}

// source() 체인 접근
fn log_error_chain(error: &dyn std::error::Error) {
    tracing::error!("Error: {}", error);

    let mut source = error.source();
    let mut depth = 1;

    while let Some(err) = source {
        tracing::error!("  Caused by [{}]: {}", depth, err);
        source = err.source();
        depth += 1;
    }
}
```

## 커스텀 Context 타입

```rust
#[derive(Debug)]
pub struct ErrorContext {
    pub operation: String,
    pub resource_id: Option<String>,
    pub user_id: Option<i64>,
    pub request_id: Option<String>,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl ErrorContext {
    pub fn new(operation: &str) -> Self {
        Self {
            operation: operation.to_string(),
            resource_id: None,
            user_id: None,
            request_id: None,
            timestamp: chrono::Utc::now(),
        }
    }

    pub fn with_resource(mut self, id: impl ToString) -> Self {
        self.resource_id = Some(id.to_string());
        self
    }

    pub fn with_user(mut self, id: i64) -> Self {
        self.user_id = Some(id);
        self
    }
}

#[derive(Debug, Error)]
#[error("{context.operation} failed")]
pub struct ContextualError {
    pub context: ErrorContext,
    #[source]
    pub source: anyhow::Error,
}

// 사용
fn process(user_id: i64, resource_id: &str) -> Result<(), ContextualError> {
    let ctx = ErrorContext::new("process_resource")
        .with_user(user_id)
        .with_resource(resource_id);

    do_work(resource_id).map_err(|e| ContextualError {
        context: ctx,
        source: e.into(),
    })
}
```

## Backtrace 캡처

```rust
use std::backtrace::Backtrace;

#[derive(Debug)]
pub struct DetailedError {
    pub message: String,
    pub backtrace: Backtrace,
}

impl DetailedError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            backtrace: Backtrace::capture(),
        }
    }
}

impl std::fmt::Display for DetailedError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}\n\nBacktrace:\n{}", self.message, self.backtrace)
    }
}

// RUST_BACKTRACE=1 환경변수 필요
```

## Span 기반 Context (tracing)

```rust
use tracing::{instrument, Span};

#[instrument(skip(pool), fields(user_id = %user_id))]
pub async fn get_user(pool: &PgPool, user_id: i64) -> Result<User, Error> {
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| {
            tracing::error!(error = %e, "Database query failed");
            Error::Database(e)
        })?
        .ok_or_else(|| {
            tracing::warn!("User not found");
            Error::NotFound
        })?;

    Span::current().record("user_name", &user.name);

    Ok(user)
}
```

## 에러 리포팅 통합

```rust
pub fn report_error(error: &anyhow::Error) {
    // 로깅
    tracing::error!(
        error = %error,
        "Operation failed"
    );

    // 전체 체인 로깅
    let mut current = error.source();
    while let Some(cause) = current {
        tracing::error!(cause = %cause, "Caused by");
        current = cause.source();
    }

    // 외부 리포팅 (Sentry 등)
    #[cfg(feature = "sentry")]
    {
        sentry::capture_error(error);
    }
}
```

## Context Extension Trait

```rust
pub trait ResultExt<T, E> {
    fn with_operation(self, op: &str) -> Result<T, ContextualError>
    where
        E: Into<anyhow::Error>;

    fn log_error(self) -> Self
    where
        E: std::fmt::Display;
}

impl<T, E> ResultExt<T, E> for Result<T, E> {
    fn with_operation(self, op: &str) -> Result<T, ContextualError>
    where
        E: Into<anyhow::Error>,
    {
        self.map_err(|e| ContextualError {
            context: ErrorContext::new(op),
            source: e.into(),
        })
    }

    fn log_error(self) -> Self
    where
        E: std::fmt::Display,
    {
        if let Err(ref e) = self {
            tracing::error!(error = %e);
        }
        self
    }
}

// 사용
let result = fetch_data()
    .log_error()
    .with_operation("fetch_data")?;
```

## 체크리스트

- [ ] anyhow::Context로 컨텍스트 추가
- [ ] thiserror에 #[source] 사용
- [ ] 에러 체인 로깅
- [ ] Backtrace 캡처 (개발 환경)
- [ ] tracing span 활용
- [ ] 외부 에러 리포팅 연동
