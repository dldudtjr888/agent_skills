# Error Handling

Axum 에러 처리 패턴과 IntoResponse 구현.

## 통합 AppError 타입

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("not found")]
    NotFound,

    #[error("unauthorized")]
    Unauthorized,

    #[error("forbidden")]
    Forbidden,

    #[error("bad request: {0}")]
    BadRequest(String),

    #[error("validation error: {0}")]
    Validation(String),

    #[error("conflict: {0}")]
    Conflict(String),

    #[error("internal server error")]
    Internal(#[from] anyhow::Error),

    #[error("database error")]
    Database(#[from] sqlx::Error),

    #[error("serialization error")]
    Serialization(#[from] serde_json::Error),
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    details: Option<serde_json::Value>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_response) = match &self {
            AppError::NotFound => (
                StatusCode::NOT_FOUND,
                ErrorResponse {
                    error: "not_found".into(),
                    message: self.to_string(),
                    details: None,
                },
            ),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                ErrorResponse {
                    error: "unauthorized".into(),
                    message: self.to_string(),
                    details: None,
                },
            ),
            AppError::Forbidden => (
                StatusCode::FORBIDDEN,
                ErrorResponse {
                    error: "forbidden".into(),
                    message: self.to_string(),
                    details: None,
                },
            ),
            AppError::BadRequest(msg) => (
                StatusCode::BAD_REQUEST,
                ErrorResponse {
                    error: "bad_request".into(),
                    message: msg.clone(),
                    details: None,
                },
            ),
            AppError::Validation(msg) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                ErrorResponse {
                    error: "validation_error".into(),
                    message: msg.clone(),
                    details: None,
                },
            ),
            AppError::Conflict(msg) => (
                StatusCode::CONFLICT,
                ErrorResponse {
                    error: "conflict".into(),
                    message: msg.clone(),
                    details: None,
                },
            ),
            AppError::Internal(err) => {
                tracing::error!(?err, "internal server error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ErrorResponse {
                        error: "internal_error".into(),
                        message: "An internal error occurred".into(),
                        details: None,
                    },
                )
            }
            AppError::Database(err) => {
                tracing::error!(?err, "database error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ErrorResponse {
                        error: "database_error".into(),
                        message: "A database error occurred".into(),
                        details: None,
                    },
                )
            }
            AppError::Serialization(err) => {
                tracing::error!(?err, "serialization error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ErrorResponse {
                        error: "serialization_error".into(),
                        message: "Failed to process data".into(),
                        details: None,
                    },
                )
            }
        };

        (status, Json(error_response)).into_response()
    }
}
```

## 헬퍼 메서드

```rust
impl AppError {
    pub fn bad_request(msg: impl Into<String>) -> Self {
        Self::BadRequest(msg.into())
    }

    pub fn validation(msg: impl Into<String>) -> Self {
        Self::Validation(msg.into())
    }

    pub fn conflict(msg: impl Into<String>) -> Self {
        Self::Conflict(msg.into())
    }

    pub fn internal(err: impl Into<anyhow::Error>) -> Self {
        Self::Internal(err.into())
    }
}

// Result 타입 별칭
pub type AppResult<T> = Result<T, AppError>;
```

## Validation 에러

```rust
use validator::{Validate, ValidationErrors};

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUserRequest {
    #[validate(length(min = 1, max = 100))]
    name: String,

    #[validate(email)]
    email: String,

    #[validate(length(min = 8))]
    password: String,
}

impl From<ValidationErrors> for AppError {
    fn from(errors: ValidationErrors) -> Self {
        let messages: Vec<String> = errors
            .field_errors()
            .into_iter()
            .flat_map(|(field, errs)| {
                errs.iter().map(move |e| {
                    format!("{}: {}", field, e.message.as_deref().unwrap_or("invalid"))
                })
            })
            .collect();

        AppError::Validation(messages.join(", "))
    }
}

// 핸들러에서 사용
async fn create_user(
    Json(payload): Json<CreateUserRequest>,
) -> Result<Json<UserResponse>, AppError> {
    payload.validate()?;  // ValidationErrors -> AppError 자동 변환
    // ...
}
```

## 도메인 에러 통합

```rust
// 도메인별 에러
#[derive(Debug, Error)]
pub enum UserError {
    #[error("user not found: {0}")]
    NotFound(i64),

    #[error("email already exists: {0}")]
    EmailExists(String),

    #[error("invalid password")]
    InvalidPassword,
}

// AppError로 변환
impl From<UserError> for AppError {
    fn from(err: UserError) -> Self {
        match err {
            UserError::NotFound(_) => AppError::NotFound,
            UserError::EmailExists(email) => {
                AppError::Conflict(format!("Email {} already exists", email))
            }
            UserError::InvalidPassword => AppError::Unauthorized,
        }
    }
}

// 서비스에서 사용
impl UserService {
    pub async fn authenticate(
        &self,
        email: &str,
        password: &str,
    ) -> Result<User, UserError> {
        let user = self.repo.find_by_email(email).await?
            .ok_or(UserError::NotFound(0))?;

        if !verify_password(password, &user.password_hash) {
            return Err(UserError::InvalidPassword);
        }

        Ok(user)
    }
}

// 핸들러에서 사용
async fn login(
    State(state): State<AppState>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<TokenResponse>, AppError> {
    let user = state.user_service
        .authenticate(&payload.email, &payload.password)
        .await?;  // UserError -> AppError 자동 변환

    let token = state.auth_service.create_token(&user)?;
    Ok(Json(TokenResponse { token }))
}
```

## Extractor 에러 처리

```rust
use axum::extract::rejection::{JsonRejection, PathRejection, QueryRejection};

impl From<JsonRejection> for AppError {
    fn from(rejection: JsonRejection) -> Self {
        AppError::BadRequest(rejection.body_text())
    }
}

impl From<PathRejection> for AppError {
    fn from(rejection: PathRejection) -> Self {
        AppError::BadRequest(rejection.body_text())
    }
}

impl From<QueryRejection> for AppError {
    fn from(rejection: QueryRejection) -> Self {
        AppError::BadRequest(rejection.body_text())
    }
}
```

## 에러 로깅

```rust
impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        // 에러 심각도에 따른 로깅
        match &self {
            AppError::Internal(err) => {
                tracing::error!(
                    error = ?err,
                    error_type = "internal",
                    "Internal server error"
                );
            }
            AppError::Database(err) => {
                tracing::error!(
                    error = ?err,
                    error_type = "database",
                    "Database error"
                );
            }
            AppError::Unauthorized | AppError::Forbidden => {
                tracing::warn!(
                    error_type = %self,
                    "Authentication/Authorization error"
                );
            }
            _ => {
                tracing::debug!(
                    error_type = %self,
                    "Client error"
                );
            }
        }

        // 응답 생성...
    }
}
```

## 에러 응답 포맷

### 단순 포맷

```json
{
  "error": "not_found",
  "message": "User not found"
}
```

### 상세 포맷 (개발 환경)

```json
{
  "error": "validation_error",
  "message": "Validation failed",
  "details": {
    "fields": {
      "email": ["Invalid email format"],
      "password": ["Must be at least 8 characters"]
    }
  }
}
```

### 환경별 에러 상세 표시

```rust
impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let show_details = std::env::var("RUST_ENV")
            .map(|v| v != "production")
            .unwrap_or(true);

        let details = if show_details {
            match &self {
                AppError::Internal(err) => Some(serde_json::json!({
                    "source": format!("{:?}", err)
                })),
                _ => None,
            }
        } else {
            None
        };

        // 응답 생성에 details 포함
    }
}
```

## 체크리스트

- [ ] 통합 AppError 타입 정의
- [ ] IntoResponse 구현
- [ ] 도메인 에러 -> AppError 변환
- [ ] Extractor 에러 처리
- [ ] 에러 로깅 (심각도별)
- [ ] 프로덕션에서 내부 에러 숨기기
- [ ] 일관된 에러 응답 포맷
