# Error Recovery

에러 복구 전략 및 fallback 패턴.

## 복구 가능 vs 불가능 에러

```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    // 복구 가능
    #[error("Resource temporarily unavailable")]
    TemporarilyUnavailable,

    #[error("Rate limited, retry after {retry_after}s")]
    RateLimited { retry_after: u64 },

    #[error("Connection lost")]
    ConnectionLost,

    // 복구 불가능
    #[error("Invalid configuration: {0}")]
    InvalidConfig(String),

    #[error("Data corruption detected")]
    DataCorruption,
}

impl AppError {
    pub fn is_recoverable(&self) -> bool {
        matches!(
            self,
            Self::TemporarilyUnavailable |
            Self::RateLimited { .. } |
            Self::ConnectionLost
        )
    }

    pub fn retry_delay(&self) -> Option<Duration> {
        match self {
            Self::RateLimited { retry_after } => {
                Some(Duration::from_secs(*retry_after))
            }
            Self::TemporarilyUnavailable => {
                Some(Duration::from_secs(1))
            }
            Self::ConnectionLost => {
                Some(Duration::from_millis(100))
            }
            _ => None,
        }
    }
}
```

## 재시도 패턴

### 단순 재시도

```rust
pub async fn with_retry<T, E, F, Fut>(
    operation: F,
    max_retries: u32,
) -> Result<T, E>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
{
    let mut attempts = 0;

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts < max_retries => {
                attempts += 1;
                tokio::time::sleep(Duration::from_millis(100 * attempts as u64)).await;
            }
            Err(e) => return Err(e),
        }
    }
}
```

### 조건부 재시도

```rust
pub async fn retry_if_recoverable<T, F, Fut>(
    operation: F,
    max_retries: u32,
) -> Result<T, AppError>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, AppError>>,
{
    let mut attempts = 0;

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if e.is_recoverable() && attempts < max_retries => {
                attempts += 1;
                if let Some(delay) = e.retry_delay() {
                    tracing::warn!(
                        error = %e,
                        attempt = attempts,
                        "Retrying after {:?}",
                        delay
                    );
                    tokio::time::sleep(delay).await;
                }
            }
            Err(e) => return Err(e),
        }
    }
}
```

## Fallback 패턴

### 기본값 Fallback

```rust
pub async fn get_config_with_fallback() -> Config {
    match load_remote_config().await {
        Ok(config) => config,
        Err(e) => {
            tracing::warn!(error = %e, "Using default config");
            Config::default()
        }
    }
}
```

### 체인 Fallback

```rust
pub async fn get_data(id: i64) -> Result<Data, Error> {
    // 1차: 캐시
    if let Some(data) = cache.get(id).await {
        return Ok(data);
    }

    // 2차: 주 DB
    match primary_db.find(id).await {
        Ok(Some(data)) => {
            cache.set(id, &data).await;
            return Ok(data);
        }
        Ok(None) => {}
        Err(e) => {
            tracing::warn!(error = %e, "Primary DB failed");
        }
    }

    // 3차: 복제 DB
    match replica_db.find(id).await {
        Ok(Some(data)) => return Ok(data),
        Ok(None) => return Err(Error::NotFound),
        Err(e) => {
            tracing::error!(error = %e, "All sources failed");
            return Err(Error::ServiceUnavailable);
        }
    }
}
```

## Circuit Breaker

```rust
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::Arc;

pub struct CircuitBreaker {
    failure_count: AtomicU32,
    last_failure: AtomicU64,
    threshold: u32,
    reset_timeout: Duration,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CircuitState {
    Closed,      // 정상
    Open,        // 차단
    HalfOpen,    // 테스트 중
}

impl CircuitBreaker {
    pub fn new(threshold: u32, reset_timeout: Duration) -> Self {
        Self {
            failure_count: AtomicU32::new(0),
            last_failure: AtomicU64::new(0),
            threshold,
            reset_timeout,
        }
    }

    pub fn state(&self) -> CircuitState {
        let failures = self.failure_count.load(Ordering::SeqCst);
        if failures < self.threshold {
            return CircuitState::Closed;
        }

        let last = self.last_failure.load(Ordering::SeqCst);
        let elapsed = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() - last;

        if elapsed > self.reset_timeout.as_secs() {
            CircuitState::HalfOpen
        } else {
            CircuitState::Open
        }
    }

    pub fn record_success(&self) {
        self.failure_count.store(0, Ordering::SeqCst);
    }

    pub fn record_failure(&self) {
        self.failure_count.fetch_add(1, Ordering::SeqCst);
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        self.last_failure.store(now, Ordering::SeqCst);
    }

    pub async fn call<T, E, F, Fut>(&self, operation: F) -> Result<T, CircuitError<E>>
    where
        F: FnOnce() -> Fut,
        Fut: std::future::Future<Output = Result<T, E>>,
    {
        match self.state() {
            CircuitState::Open => {
                return Err(CircuitError::CircuitOpen);
            }
            CircuitState::HalfOpen | CircuitState::Closed => {
                match operation().await {
                    Ok(result) => {
                        self.record_success();
                        Ok(result)
                    }
                    Err(e) => {
                        self.record_failure();
                        Err(CircuitError::Inner(e))
                    }
                }
            }
        }
    }
}
```

## Graceful Degradation

```rust
pub async fn get_user_profile(id: i64) -> UserProfile {
    let user = users_service.get(id).await
        .unwrap_or_else(|_| User::anonymous());

    let preferences = preferences_service.get(id).await
        .unwrap_or_default();

    let recommendations = recommendations_service.get(id).await
        .unwrap_or_else(|_| vec![]);  // 추천 없이도 동작

    UserProfile {
        user,
        preferences,
        recommendations,
    }
}
```

## 보상 트랜잭션 (Saga)

```rust
pub async fn process_order(order: Order) -> Result<(), OrderError> {
    // 1. 재고 차감
    let inventory_result = inventory_service.reserve(&order).await;
    if let Err(e) = inventory_result {
        return Err(OrderError::InventoryFailed(e));
    }

    // 2. 결제 처리
    let payment_result = payment_service.charge(&order).await;
    if let Err(e) = payment_result {
        // 보상: 재고 복구
        inventory_service.release(&order).await.ok();
        return Err(OrderError::PaymentFailed(e));
    }

    // 3. 배송 요청
    let shipping_result = shipping_service.schedule(&order).await;
    if let Err(e) = shipping_result {
        // 보상: 결제 취소, 재고 복구
        payment_service.refund(&order).await.ok();
        inventory_service.release(&order).await.ok();
        return Err(OrderError::ShippingFailed(e));
    }

    Ok(())
}
```

## 체크리스트

- [ ] 복구 가능/불가능 에러 분류
- [ ] 적절한 재시도 전략 선택
- [ ] Fallback 체인 구현
- [ ] Circuit breaker 적용 (외부 서비스)
- [ ] Graceful degradation 구현
- [ ] 보상 트랜잭션 로직 (분산 시스템)
