---
name: rig-builder
description: "Rig LLM 에이전트 빌더. Rust에서 LLM 애플리케이션을 구축하기 위한 패턴과 가이드."
version: 1.0.0
category: ai-agent
user-invocable: true
triggers:
  keywords:
    - rig
    - llm
    - agent
    - 에이전트
    - ai
    - openai
    - anthropic
    - rag
    - embedding
    - vector
  intentPatterns:
    - "(만들|생성|구현|빌드).*(에이전트|agent|llm|ai)"
    - "(rig|러스트).*(에이전트|llm)"
---

# Rig Builder

Rig을 사용한 Rust LLM 에이전트 개발 가이드.

Rig은 Rust에서 LLM 애플리케이션을 구축하기 위한 모듈화된 프레임워크입니다.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Agent Basics | [modules/agent-basics.md](modules/agent-basics.md) | 기본 에이전트 구축, Provider 설정, 프롬프트 |
| 2 | RAG Patterns | [modules/rag-patterns.md](modules/rag-patterns.md) | 벡터 스토어, 임베딩, 컨텍스트 검색 |
| 3 | Tool Use | [modules/tool-use.md](modules/tool-use.md) | 도구 정의, 함수 호출, MCP 통합 |

## 사용 시점

### When to Use
- Rust에서 LLM 기반 에이전트 구축
- RAG(Retrieval-Augmented Generation) 시스템 구현
- 도구 사용 에이전트 개발
- 고성능 LLM 애플리케이션 필요시

### When NOT to Use
- Python 에이전트 개발 (→ python-agent-backend)
- 단순 HTTP API 클라이언트
- LLM 없는 일반 백엔드

## 핵심 개념

### Rig 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    Rig Agent                         │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐│
│  │              LLM Provider                        ││
│  │  (OpenAI, Anthropic, Cohere, Local)             ││
│  └─────────────────────────────────────────────────┘│
│                        ↓                             │
│  ┌─────────────────────────────────────────────────┐│
│  │              Completion Model                    ││
│  │  (gpt-4, claude-3, command-r)                   ││
│  └─────────────────────────────────────────────────┘│
│                        ↓                             │
│  ┌─────────────────────────────────────────────────┐│
│  │                 Agent                            ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         ││
│  │  │ Preamble│  │ Context │  │  Tools  │         ││
│  │  └─────────┘  └─────────┘  └─────────┘         ││
│  └─────────────────────────────────────────────────┘│
│                        ↓                             │
│  ┌─────────────────────────────────────────────────┐│
│  │              Vector Store (RAG)                  ││
│  │  (In-Memory, MongoDB, PostgreSQL)               ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

## Quick Start

### 의존성 추가

```toml
# Cargo.toml
[dependencies]
rig-core = "0.5"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"

# Provider별 선택
# OpenAI
rig-core = { version = "0.5", features = ["openai"] }
# Anthropic
rig-core = { version = "0.5", features = ["anthropic"] }
```

### 기본 에이전트

```rust
use rig::providers::openai;
use rig::completion::Prompt;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // OpenAI 클라이언트 생성
    let client = openai::Client::from_env();

    // GPT-4 모델로 에이전트 생성
    let agent = client
        .agent("gpt-4")
        .preamble("You are a helpful assistant specialized in Rust programming.")
        .build();

    // 프롬프트 실행
    let response = agent
        .prompt("How do I handle errors in Rust?")
        .await?;

    println!("{}", response);

    Ok(())
}
```

### Anthropic 사용

```rust
use rig::providers::anthropic;

let client = anthropic::Client::from_env();

let agent = client
    .agent("claude-3-5-sonnet-20241022")
    .preamble("You are an expert Rust developer.")
    .max_tokens(4096)
    .build();
```

## 에이전트 패턴

### 시스템 프롬프트 설정

```rust
let agent = client
    .agent("gpt-4")
    .preamble(r#"
        You are a helpful coding assistant specialized in Rust.

        Guidelines:
        - Always provide idiomatic Rust code
        - Explain your reasoning
        - Include error handling
        - Add appropriate comments
    "#)
    .build();
```

### 동적 컨텍스트

```rust
use rig::completion::PromptContext;

// 컨텍스트 추가
let context = PromptContext::new()
    .with_context("user_info", &user)
    .with_context("project_context", &project);

let response = agent
    .prompt_with_context("Review this code", context)
    .await?;
```

### 스트리밍 응답

```rust
use rig::completion::StreamingPrompt;
use futures::StreamExt;

let mut stream = agent
    .stream_prompt("Explain Rust's ownership system")
    .await?;

while let Some(chunk) = stream.next().await {
    match chunk {
        Ok(text) => print!("{}", text),
        Err(e) => eprintln!("Error: {}", e),
    }
}
```

## RAG (Retrieval-Augmented Generation)

### 벡터 스토어 설정

```rust
use rig::vector_store::InMemoryVectorStore;
use rig::embeddings::EmbeddingsBuilder;

// 임베딩 모델 설정
let embedding_model = client.embedding_model("text-embedding-3-small");

// 문서 임베딩 생성
let embeddings = EmbeddingsBuilder::new(embedding_model.clone())
    .document("Rust ownership rules...")?
    .document("Borrowing in Rust...")?
    .document("Lifetimes explained...")?
    .build()
    .await?;

// 벡터 스토어에 저장
let vector_store = InMemoryVectorStore::from_documents(embeddings);
```

### RAG 에이전트

```rust
use rig::agent::AgentBuilder;

let rag_agent = client
    .agent("gpt-4")
    .preamble("Answer questions using the provided context.")
    .dynamic_context(4, vector_store.index(embedding_model))  // top-4 검색
    .build();

let response = rag_agent
    .prompt("How does borrowing work in Rust?")
    .await?;
```

## 도구 사용

### 도구 정의

```rust
use rig::tool::{Tool, ToolDescription};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct CalculatorInput {
    operation: String,
    a: f64,
    b: f64,
}

#[derive(Serialize)]
struct CalculatorOutput {
    result: f64,
}

struct Calculator;

impl Tool for Calculator {
    const NAME: &'static str = "calculator";

    type Input = CalculatorInput;
    type Output = CalculatorOutput;
    type Error = anyhow::Error;

    fn description(&self) -> ToolDescription {
        ToolDescription {
            name: Self::NAME.into(),
            description: "Performs basic arithmetic operations".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "a": { "type": "number" },
                    "b": { "type": "number" }
                },
                "required": ["operation", "a", "b"]
            }),
        }
    }

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        let result = match input.operation.as_str() {
            "add" => input.a + input.b,
            "subtract" => input.a - input.b,
            "multiply" => input.a * input.b,
            "divide" => input.a / input.b,
            _ => anyhow::bail!("Unknown operation"),
        };

        Ok(CalculatorOutput { result })
    }
}
```

### 도구 사용 에이전트

```rust
let agent = client
    .agent("gpt-4")
    .preamble("You are a helpful assistant with access to tools.")
    .tool(Calculator)
    .build();

// 도구가 필요한 질문
let response = agent
    .prompt("What is 123 * 456?")
    .await?;
```

## 체크리스트

### 기본 설정
- [ ] Cargo.toml에 rig-core 추가
- [ ] Provider 선택 (OpenAI/Anthropic/etc)
- [ ] 환경변수 설정 (API 키)

### 에이전트 구현
- [ ] 적절한 모델 선택
- [ ] 시스템 프롬프트 설계
- [ ] 에러 처리 구현
- [ ] 스트리밍 지원 (필요시)

### RAG 구현
- [ ] 임베딩 모델 선택
- [ ] 벡터 스토어 설정
- [ ] 문서 청킹 전략
- [ ] 검색 결과 개수 조정

### 도구 사용
- [ ] Tool trait 구현
- [ ] 입출력 타입 정의
- [ ] 에러 처리
- [ ] 도구 설명 작성

## 관련 스킬

- `rust-agent-infra-builder` - 에이전트 인프라 (메모리, MCP)
- `langchain-rust-builder` - LangChain Rust 버전
- `rs-graph-llm-builder` - 워크플로우 기반 에이전트

## 참고 자료

- [Rig Documentation](https://rig.rs/)
- [Rig GitHub](https://github.com/0xPlaygrounds/rig)
- [Rig Examples](https://github.com/0xPlaygrounds/rig/tree/main/examples)
