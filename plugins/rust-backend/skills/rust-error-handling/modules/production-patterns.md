# Production Patterns

프로덕션 환경 에러 처리 패턴.

## 에러 응답 표준화

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;

#[derive(Serialize)]
pub struct ErrorResponse {
    pub error: ErrorBody,
}

#[derive(Serialize)]
pub struct ErrorBody {
    pub code: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub request_id: Option<String>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, code, message) = match &self {
            AppError::NotFound(id) => (
                StatusCode::NOT_FOUND,
                "NOT_FOUND",
                format!("Resource {} not found", id),
            ),
            AppError::Validation(msg) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                msg.clone(),
            ),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                "UNAUTHORIZED",
                "Authentication required".into(),
            ),
            AppError::Internal(e) => {
                // 내부 에러는 로깅만, 사용자에게는 일반 메시지
                tracing::error!(error = %e, "Internal error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "INTERNAL_ERROR",
                    "An unexpected error occurred".into(),
                )
            }
        };

        let body = ErrorResponse {
            error: ErrorBody {
                code: code.into(),
                message,
                details: None,
                request_id: None,
            },
        };

        (status, Json(body)).into_response()
    }
}
```

## 민감 정보 숨기기

```rust
#[derive(Debug)]
pub struct SanitizedError {
    /// 사용자에게 표시할 메시지
    pub user_message: String,
    /// 내부 로깅용 상세 정보
    internal_details: String,
}

impl SanitizedError {
    pub fn new(user_message: &str, internal: impl std::fmt::Display) -> Self {
        Self {
            user_message: user_message.into(),
            internal_details: internal.to_string(),
        }
    }

    pub fn log(&self) {
        tracing::error!(
            user_message = %self.user_message,
            internal_details = %self.internal_details,
            "Error occurred"
        );
    }
}

// 사용
fn handle_db_error(e: sqlx::Error) -> SanitizedError {
    SanitizedError::new(
        "Database operation failed",
        format!("SQLx error: {} (query: ...)", e),  // 쿼리 상세는 내부용
    )
}
```

## 구조화된 로깅

```rust
use tracing::{error, warn, info, instrument};

#[instrument(
    skip(pool),
    fields(
        user_id = %user_id,
        operation = "get_user",
    )
)]
pub async fn get_user(pool: &PgPool, user_id: i64) -> Result<User, AppError> {
    let result = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", user_id)
        .fetch_optional(pool)
        .await;

    match result {
        Ok(Some(user)) => {
            info!(user_name = %user.name, "User found");
            Ok(user)
        }
        Ok(None) => {
            warn!("User not found");
            Err(AppError::NotFound(user_id.to_string()))
        }
        Err(e) => {
            error!(
                error = %e,
                error_type = "database",
                "Failed to fetch user"
            );
            Err(AppError::Internal(e.into()))
        }
    }
}
```

## 메트릭스 연동

```rust
use metrics::{counter, histogram};
use std::time::Instant;

pub async fn monitored_operation<T, E>(
    operation_name: &str,
    operation: impl Future<Output = Result<T, E>>,
) -> Result<T, E>
where
    E: std::fmt::Display,
{
    let start = Instant::now();

    let result = operation.await;

    let duration = start.elapsed();
    let status = if result.is_ok() { "success" } else { "error" };

    // 메트릭스 기록
    counter!(
        "operation_total",
        "operation" => operation_name.to_string(),
        "status" => status.to_string()
    )
    .increment(1);

    histogram!(
        "operation_duration_seconds",
        "operation" => operation_name.to_string()
    )
    .record(duration.as_secs_f64());

    if let Err(ref e) = result {
        tracing::error!(
            operation = operation_name,
            error = %e,
            duration_ms = duration.as_millis() as u64,
            "Operation failed"
        );
    }

    result
}
```

## 에러 분류 및 알림

```rust
#[derive(Debug, Clone, Copy)]
pub enum ErrorSeverity {
    Low,      // 로깅만
    Medium,   // 로깅 + 대시보드
    High,     // + Slack 알림
    Critical, // + PagerDuty
}

pub trait ErrorClassifier {
    fn severity(&self) -> ErrorSeverity;
    fn should_alert(&self) -> bool {
        matches!(self.severity(), ErrorSeverity::High | ErrorSeverity::Critical)
    }
}

impl ErrorClassifier for AppError {
    fn severity(&self) -> ErrorSeverity {
        match self {
            AppError::NotFound(_) => ErrorSeverity::Low,
            AppError::Validation(_) => ErrorSeverity::Low,
            AppError::Unauthorized => ErrorSeverity::Medium,
            AppError::RateLimited => ErrorSeverity::Medium,
            AppError::Database(_) => ErrorSeverity::High,
            AppError::ExternalService(_) => ErrorSeverity::High,
            AppError::DataCorruption => ErrorSeverity::Critical,
        }
    }
}

pub async fn report_error(error: &impl ErrorClassifier) {
    match error.severity() {
        ErrorSeverity::Low => {
            tracing::warn!(error = ?error);
        }
        ErrorSeverity::Medium => {
            tracing::error!(error = ?error);
        }
        ErrorSeverity::High => {
            tracing::error!(error = ?error);
            notify_slack(error).await;
        }
        ErrorSeverity::Critical => {
            tracing::error!(error = ?error, "CRITICAL ERROR");
            notify_slack(error).await;
            notify_pagerduty(error).await;
        }
    }
}
```

## Health Check 에러 노출

```rust
#[derive(Serialize)]
pub struct HealthStatus {
    pub status: String,
    pub checks: HashMap<String, CheckResult>,
}

#[derive(Serialize)]
pub struct CheckResult {
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    pub latency_ms: u64,
}

pub async fn health_check(pool: &PgPool) -> HealthStatus {
    let mut checks = HashMap::new();

    // DB 체크
    let db_check = check_database(pool).await;
    checks.insert("database".into(), db_check);

    // Redis 체크
    let redis_check = check_redis().await;
    checks.insert("redis".into(), redis_check);

    let all_healthy = checks.values().all(|c| c.status == "healthy");

    HealthStatus {
        status: if all_healthy { "healthy" } else { "unhealthy" }.into(),
        checks,
    }
}

async fn check_database(pool: &PgPool) -> CheckResult {
    let start = Instant::now();

    match sqlx::query("SELECT 1").execute(pool).await {
        Ok(_) => CheckResult {
            status: "healthy".into(),
            error: None,
            latency_ms: start.elapsed().as_millis() as u64,
        },
        Err(e) => CheckResult {
            status: "unhealthy".into(),
            error: Some(e.to_string()),
            latency_ms: start.elapsed().as_millis() as u64,
        },
    }
}
```

## 체크리스트

- [ ] 에러 응답 표준 포맷 정의
- [ ] 민감 정보 필터링
- [ ] 구조화된 로깅 (tracing)
- [ ] 메트릭스 수집
- [ ] 에러 심각도 분류
- [ ] 알림 연동 (Slack, PagerDuty)
- [ ] Health check 에러 노출
- [ ] Request ID 추적
