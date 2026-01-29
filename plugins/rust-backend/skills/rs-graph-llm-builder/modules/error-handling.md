# Error Handling

rs-graph-llm에서 에러 처리 및 재시도 전략.

## 노드 에러 타입

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum NodeError {
    #[error("LLM API error: {0}")]
    LlmError(String),

    #[error("Parsing error: {0}")]
    ParseError(String),

    #[error("Validation error: {0}")]
    ValidationError(String),

    #[error("Timeout after {0}s")]
    Timeout(u64),

    #[error("Max retries exceeded")]
    MaxRetriesExceeded,

    #[error("External service error: {0}")]
    ExternalService(String),
}

impl NodeError {
    pub fn is_retryable(&self) -> bool {
        matches!(
            self,
            NodeError::LlmError(_) |
            NodeError::Timeout(_) |
            NodeError::ExternalService(_)
        )
    }
}
```

## 노드 레벨 에러 처리

```rust
async fn robust_node(state: AgentState) -> Result<AgentState, NodeError> {
    // 입력 검증
    if state.input.is_empty() {
        return Err(NodeError::ValidationError("Empty input".into()));
    }

    // LLM 호출 with 에러 처리
    let response = call_llm(&state.input)
        .await
        .map_err(|e| NodeError::LlmError(e.to_string()))?;

    // 응답 파싱
    let parsed = parse_response(&response)
        .map_err(|e| NodeError::ParseError(e.to_string()))?;

    Ok(AgentState {
        output: Some(parsed),
        ..state
    })
}

// 그래프에서 사용
graph.add_node_with_error_handler(
    "processor",
    robust_node,
    |state, error| {
        // 에러 발생 시 상태 업데이트
        AgentState {
            error: Some(error.to_string()),
            ..state
        }
    },
);
```

## 재시도 패턴

### 지수 백오프

```rust
use tokio::time::{sleep, Duration};

pub async fn with_retry<T, E, F, Fut>(
    operation: F,
    max_retries: u32,
    base_delay_ms: u64,
) -> Result<T, E>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
    E: std::fmt::Display,
{
    let mut attempts = 0;

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts < max_retries => {
                attempts += 1;
                let delay = Duration::from_millis(
                    base_delay_ms * 2_u64.pow(attempts - 1)
                );
                tracing::warn!(
                    "Attempt {} failed: {}. Retrying in {:?}",
                    attempts, e, delay
                );
                sleep(delay).await;
            }
            Err(e) => return Err(e),
        }
    }
}

// 노드에서 사용
async fn retrying_node(state: AgentState) -> AgentState {
    let result = with_retry(
        || async { call_llm(&state.input).await },
        3,
        100,
    ).await;

    match result {
        Ok(output) => AgentState {
            output: Some(output),
            ..state
        },
        Err(e) => AgentState {
            error: Some(e.to_string()),
            ..state
        },
    }
}
```

### 재시도 정책

```rust
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub base_delay: Duration,
    pub max_delay: Duration,
    pub jitter: bool,
}

impl RetryPolicy {
    pub fn default_llm() -> Self {
        Self {
            max_attempts: 3,
            base_delay: Duration::from_millis(100),
            max_delay: Duration::from_secs(10),
            jitter: true,
        }
    }

    pub fn delay_for_attempt(&self, attempt: u32) -> Duration {
        let delay = self.base_delay.saturating_mul(2_u32.pow(attempt));
        let delay = delay.min(self.max_delay);

        if self.jitter {
            let jitter = rand::random::<f64>() * 0.3;
            Duration::from_secs_f64(delay.as_secs_f64() * (1.0 + jitter))
        } else {
            delay
        }
    }
}
```

## 폴백 노드

```rust
pub fn build_graph_with_fallback() -> Graph<AgentState> {
    let mut graph = Graph::new();

    graph.add_node("primary", primary_node);
    graph.add_node("fallback", fallback_node);
    graph.add_node("output", output_node);

    // 에러 시 폴백으로 라우팅
    graph.add_conditional_edge(
        "primary",
        |state: &AgentState| {
            if state.error.is_some() {
                "fallback"
            } else {
                "output"
            }
        },
        vec!["fallback", "output"],
    );

    graph.add_edge("fallback", "output");

    graph.set_entry_point("primary");
    graph.set_finish_point("output");

    graph
}

async fn fallback_node(mut state: AgentState) -> AgentState {
    tracing::warn!("Using fallback for error: {:?}", state.error);

    // 간단한 폴백 로직
    state.output = Some("I couldn't process your request. Please try again.".into());
    state.error = None;  // 에러 클리어

    state
}
```

## 에러 복구 그래프

```rust
pub fn build_resilient_graph() -> Graph<AgentState> {
    let mut graph = Graph::new();

    graph.add_node("process", process_node);
    graph.add_node("validate", validate_node);
    graph.add_node("repair", repair_node);
    graph.add_node("finish", finish_node);

    graph.add_edge("process", "validate");

    // 검증 실패 시 수리 시도
    graph.add_conditional_edge(
        "validate",
        |state: &AgentState| {
            match state.validation_status {
                ValidationStatus::Valid => "finish",
                ValidationStatus::Repairable => "repair",
                ValidationStatus::Invalid => "finish",  // 포기
            }
        },
        vec!["finish", "repair"],
    );

    // 수리 후 재검증
    graph.add_edge("repair", "validate");

    graph.set_entry_point("process");
    graph.set_finish_point("finish");

    graph
}
```

## 에러 전파 vs 격리

### 전파 (fail fast)

```rust
async fn fail_fast_node(state: AgentState) -> Result<AgentState, NodeError> {
    let result = risky_operation(&state).await?;  // ? 로 전파
    Ok(AgentState { output: Some(result), ..state })
}
```

### 격리 (continue on error)

```rust
async fn isolated_node(mut state: AgentState) -> AgentState {
    match risky_operation(&state).await {
        Ok(result) => {
            state.output = Some(result);
        }
        Err(e) => {
            state.partial_errors.push(e.to_string());
            // 계속 진행
        }
    }
    state
}
```

## 타임아웃 처리

```rust
use tokio::time::timeout;

async fn node_with_timeout(state: AgentState) -> AgentState {
    let timeout_duration = Duration::from_secs(30);

    match timeout(timeout_duration, long_running_operation(&state)).await {
        Ok(Ok(result)) => AgentState {
            output: Some(result),
            ..state
        },
        Ok(Err(e)) => AgentState {
            error: Some(format!("Operation error: {}", e)),
            ..state
        },
        Err(_) => AgentState {
            error: Some(format!("Timeout after {}s", timeout_duration.as_secs())),
            ..state
        },
    }
}
```

## 에러 로깅

```rust
async fn logged_node(state: AgentState) -> AgentState {
    let span = tracing::info_span!(
        "node_execution",
        input = %state.input,
        iteration = state.iteration,
    );
    let _guard = span.enter();

    match process(&state).await {
        Ok(result) => {
            tracing::info!(output = %result, "Node completed successfully");
            AgentState { output: Some(result), ..state }
        }
        Err(e) => {
            tracing::error!(error = %e, "Node failed");
            AgentState { error: Some(e.to_string()), ..state }
        }
    }
}
```

## 체크리스트

- [ ] 모든 에러 타입 정의
- [ ] 재시도 가능 에러 분류
- [ ] 적절한 재시도 정책 설정
- [ ] 폴백 경로 구현
- [ ] 타임아웃 설정
- [ ] 에러 로깅
- [ ] 무한 루프 방지 (최대 반복)
- [ ] 에러 전파 vs 격리 결정
