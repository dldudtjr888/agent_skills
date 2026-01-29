# State Design

rs-graph-llm에서 상태(State) 구조체 설계 패턴.

## 기본 State 구조

```rust
use rs_graph_llm::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentState {
    // 입력
    pub input: String,

    // 중간 결과
    pub messages: Vec<Message>,
    pub context: Option<String>,

    // 최종 출력
    pub output: Option<String>,

    // 메타데이터
    pub iteration: usize,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Role {
    User,
    Assistant,
    System,
}
```

## 타입 안전 State

### Enum 기반 상태

```rust
#[derive(Debug, Clone)]
pub enum WorkflowState {
    Initial { input: String },
    Processing { input: String, partial: Vec<String> },
    Completed { input: String, output: String },
    Failed { input: String, error: String },
}

impl WorkflowState {
    pub fn input(&self) -> &str {
        match self {
            Self::Initial { input } => input,
            Self::Processing { input, .. } => input,
            Self::Completed { input, .. } => input,
            Self::Failed { input, .. } => input,
        }
    }

    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Completed { .. } | Self::Failed { .. })
    }
}
```

### 제네릭 State

```rust
#[derive(Debug, Clone)]
pub struct TypedState<T, O> {
    pub input: T,
    pub output: Option<O>,
    pub steps: Vec<StepResult>,
    pub metadata: HashMap<String, Value>,
}

impl<T, O> TypedState<T, O> {
    pub fn new(input: T) -> Self {
        Self {
            input,
            output: None,
            steps: vec![],
            metadata: HashMap::new(),
        }
    }

    pub fn with_output(mut self, output: O) -> Self {
        self.output = Some(output);
        self
    }

    pub fn add_step(&mut self, result: StepResult) {
        self.steps.push(result);
    }
}
```

## State Reducer 패턴

```rust
pub trait StateReducer {
    type State;
    type Action;

    fn reduce(&self, state: Self::State, action: Self::Action) -> Self::State;
}

#[derive(Debug, Clone)]
pub enum AgentAction {
    AddMessage(Message),
    SetContext(String),
    SetOutput(String),
    SetError(String),
    IncrementIteration,
}

pub struct AgentReducer;

impl StateReducer for AgentReducer {
    type State = AgentState;
    type Action = AgentAction;

    fn reduce(&self, mut state: Self::State, action: Self::Action) -> Self::State {
        match action {
            AgentAction::AddMessage(msg) => {
                state.messages.push(msg);
            }
            AgentAction::SetContext(ctx) => {
                state.context = Some(ctx);
            }
            AgentAction::SetOutput(output) => {
                state.output = Some(output);
            }
            AgentAction::SetError(err) => {
                state.error = Some(err);
            }
            AgentAction::IncrementIteration => {
                state.iteration += 1;
            }
        }
        state
    }
}
```

## 불변성 패턴

```rust
use std::sync::Arc;

#[derive(Debug, Clone)]
pub struct ImmutableState {
    inner: Arc<StateInner>,
}

#[derive(Debug)]
struct StateInner {
    input: String,
    messages: Vec<Message>,
    output: Option<String>,
}

impl ImmutableState {
    pub fn new(input: String) -> Self {
        Self {
            inner: Arc::new(StateInner {
                input,
                messages: vec![],
                output: None,
            }),
        }
    }

    pub fn with_message(&self, msg: Message) -> Self {
        let mut messages = self.inner.messages.clone();
        messages.push(msg);

        Self {
            inner: Arc::new(StateInner {
                input: self.inner.input.clone(),
                messages,
                output: self.inner.output.clone(),
            }),
        }
    }

    pub fn with_output(&self, output: String) -> Self {
        Self {
            inner: Arc::new(StateInner {
                input: self.inner.input.clone(),
                messages: self.inner.messages.clone(),
                output: Some(output),
            }),
        }
    }

    // Getters
    pub fn input(&self) -> &str {
        &self.inner.input
    }

    pub fn messages(&self) -> &[Message] {
        &self.inner.messages
    }

    pub fn output(&self) -> Option<&String> {
        self.inner.output.as_ref()
    }
}
```

## 복잡한 워크플로우 State

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiAgentState {
    // 공유 컨텍스트
    pub shared_context: SharedContext,

    // 에이전트별 상태
    pub agents: HashMap<String, AgentStatus>,

    // 워크플로우 상태
    pub workflow: WorkflowProgress,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SharedContext {
    pub goal: String,
    pub documents: Vec<Document>,
    pub decisions: Vec<Decision>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentStatus {
    pub name: String,
    pub state: AgentPhase,
    pub last_output: Option<String>,
    pub error_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AgentPhase {
    Idle,
    Thinking,
    Acting,
    Waiting,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowProgress {
    pub current_step: String,
    pub completed_steps: Vec<String>,
    pub remaining_steps: Vec<String>,
    pub total_iterations: usize,
}
```

## State 검증

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum StateValidationError {
    #[error("Input is empty")]
    EmptyInput,
    #[error("Too many iterations: {0}")]
    MaxIterationsExceeded(usize),
    #[error("Invalid transition from {from} to {to}")]
    InvalidTransition { from: String, to: String },
}

impl AgentState {
    pub fn validate(&self) -> Result<(), StateValidationError> {
        if self.input.is_empty() {
            return Err(StateValidationError::EmptyInput);
        }

        if self.iteration > 100 {
            return Err(StateValidationError::MaxIterationsExceeded(self.iteration));
        }

        Ok(())
    }
}
```

## 체크리스트

- [ ] State에 필요한 모든 필드 정의
- [ ] Clone, Debug, Serialize derive
- [ ] 불변성 고려 (Arc 또는 with_* 패턴)
- [ ] 타입 안전성 확보 (enum, 제네릭)
- [ ] 검증 로직 구현
- [ ] 터미널 상태 명확히 정의
