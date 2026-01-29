# Agent Basics

Rig 에이전트 기본 구축 패턴.

## Provider 설정

### OpenAI

```rust
use rig::providers::openai;

// 환경변수에서 API 키 로드
let client = openai::Client::from_env();

// 직접 API 키 지정
let client = openai::Client::new("sk-...");

// 커스텀 설정
let client = openai::Client::builder()
    .api_key("sk-...")
    .base_url("https://api.openai.com/v1")  // 또는 프록시 URL
    .build()?;
```

### Anthropic

```rust
use rig::providers::anthropic;

let client = anthropic::Client::from_env();

// 직접 지정
let client = anthropic::Client::new("sk-ant-...");
```

### Cohere

```rust
use rig::providers::cohere;

let client = cohere::Client::from_env();
```

### 로컬 모델 (Ollama)

```rust
use rig::providers::ollama;

let client = ollama::Client::new("http://localhost:11434");

let agent = client
    .agent("llama3.2")
    .preamble("You are a helpful assistant.")
    .build();
```

## 에이전트 빌더

### 기본 에이전트

```rust
let agent = client
    .agent("gpt-4o")
    .preamble("You are a helpful assistant.")
    .build();

let response = agent.prompt("Hello!").await?;
```

### 상세 설정

```rust
let agent = client
    .agent("gpt-4o")
    .preamble(SYSTEM_PROMPT)
    .max_tokens(4096)
    .temperature(0.7)
    .top_p(0.9)
    .build();
```

### 모델별 설정

```rust
// OpenAI
let agent = client
    .agent("gpt-4o")
    .preamble("...")
    .max_tokens(4096)
    .temperature(0.7)
    .presence_penalty(0.1)
    .frequency_penalty(0.1)
    .build();

// Anthropic
let agent = client
    .agent("claude-3-5-sonnet-20241022")
    .preamble("...")
    .max_tokens(8192)
    .temperature(0.7)
    .build();
```

## 프롬프트 패턴

### 단순 프롬프트

```rust
let response = agent.prompt("What is Rust?").await?;
println!("{}", response);
```

### 대화 히스토리

```rust
use rig::completion::{Chat, Message};

let mut chat = Chat::new(agent);

// 사용자 메시지 추가
chat.add_user_message("Hello!");
let response = chat.send().await?;
println!("Assistant: {}", response);

// 대화 계속
chat.add_user_message("Tell me about Rust.");
let response = chat.send().await?;
println!("Assistant: {}", response);

// 전체 히스토리 확인
for message in chat.history() {
    println!("{:?}: {}", message.role, message.content);
}
```

### 컨텍스트 주입

```rust
use rig::completion::PromptContext;

// 정적 컨텍스트
let context = PromptContext::new()
    .with_context("user_name", "John")
    .with_context("user_role", "developer");

let response = agent
    .prompt_with_context("Greet the user", context)
    .await?;
```

## 시스템 프롬프트 설계

### 기본 구조

```rust
const SYSTEM_PROMPT: &str = r#"
# Role
You are an expert Rust developer assistant.

# Capabilities
- Code review and suggestions
- Debugging assistance
- Best practices guidance
- Documentation help

# Guidelines
1. Always provide idiomatic Rust code
2. Include error handling with Result/Option
3. Add meaningful comments
4. Consider performance implications

# Output Format
- Use markdown for code blocks
- Explain your reasoning
- Suggest alternatives when appropriate
"#;
```

### 도메인별 프롬프트

```rust
// 코드 리뷰어
const CODE_REVIEWER_PROMPT: &str = r#"
You are a senior Rust code reviewer. Your task is to:

1. Identify potential bugs and issues
2. Suggest performance improvements
3. Check for idiomatic Rust patterns
4. Verify error handling
5. Assess code readability

Be constructive and explain the reasoning behind each suggestion.
"#;

// 문서 작성자
const DOC_WRITER_PROMPT: &str = r#"
You are a technical documentation writer specializing in Rust.

Guidelines:
- Write clear, concise documentation
- Include usage examples
- Document edge cases and errors
- Use proper rustdoc format
"#;
```

## 응답 처리

### 기본 응답

```rust
let response: String = agent.prompt("...").await?;
```

### 구조화된 응답

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct CodeReview {
    issues: Vec<Issue>,
    suggestions: Vec<String>,
    overall_rating: u8,
}

#[derive(Deserialize)]
struct Issue {
    line: u32,
    severity: String,
    message: String,
}

// JSON 응답 요청
let prompt = r#"
Review this code and respond in JSON format:
```rust
fn main() {
    let x = vec![1, 2, 3];
    println!("{:?}", x.get(10).unwrap());
}
```

Response format:
{
    "issues": [{"line": 3, "severity": "high", "message": "..."}],
    "suggestions": ["..."],
    "overall_rating": 5
}
"#;

let response = agent.prompt(prompt).await?;
let review: CodeReview = serde_json::from_str(&response)?;
```

### 스트리밍 응답

```rust
use rig::completion::StreamingPrompt;
use futures::StreamExt;

let mut stream = agent.stream_prompt("Explain ownership in Rust").await?;

while let Some(chunk) = stream.next().await {
    match chunk {
        Ok(text) => {
            print!("{}", text);
            std::io::stdout().flush()?;
        }
        Err(e) => eprintln!("Stream error: {}", e),
    }
}
println!(); // 줄바꿈
```

## 에러 처리

```rust
use rig::completion::CompletionError;

async fn safe_prompt(agent: &Agent, prompt: &str) -> anyhow::Result<String> {
    match agent.prompt(prompt).await {
        Ok(response) => Ok(response),
        Err(CompletionError::RateLimit) => {
            tracing::warn!("Rate limited, retrying...");
            tokio::time::sleep(Duration::from_secs(1)).await;
            agent.prompt(prompt).await.map_err(Into::into)
        }
        Err(CompletionError::InvalidRequest(msg)) => {
            tracing::error!("Invalid request: {}", msg);
            Err(anyhow::anyhow!("Invalid request: {}", msg))
        }
        Err(e) => {
            tracing::error!("Completion error: {:?}", e);
            Err(e.into())
        }
    }
}
```

## 재시도 로직

```rust
use tokio_retry::{strategy::ExponentialBackoff, Retry};

async fn prompt_with_retry(agent: &Agent, prompt: &str) -> anyhow::Result<String> {
    let retry_strategy = ExponentialBackoff::from_millis(100)
        .max_delay(Duration::from_secs(10))
        .take(3);

    Retry::spawn(retry_strategy, || async {
        agent.prompt(prompt).await
    })
    .await
    .map_err(Into::into)
}
```

## 체크리스트

- [ ] Provider 선택 및 설정
- [ ] 환경변수로 API 키 관리
- [ ] 시스템 프롬프트 설계
- [ ] 적절한 모델 파라미터 설정
- [ ] 에러 처리 구현
- [ ] 재시도 로직 (필요시)
- [ ] 스트리밍 지원 (필요시)
