---
name: langchain-rust-builder
description: "LangChain Rust 빌더. 체인, 메모리, 에이전트 패턴을 Rust에서 구현."
version: 1.0.0
category: ai-agent
user-invocable: true
triggers:
  keywords:
    - langchain
    - langchain-rust
    - chain
    - 체인
  intentPatterns:
    - "(만들|구현).*(langchain|체인)"
    - "(langchain).*(rust|러스트)"
---

# LangChain Rust Builder

langchain-rust를 사용한 LLM 체인 및 에이전트 개발 가이드.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Chain Composition | [modules/chain-composition.md](modules/chain-composition.md) | Sequential, Router, Transform chains |
| 2 | Memory Integration | [modules/memory-integration.md](modules/memory-integration.md) | 대화 메모리, 벡터 메모리, 커스텀 메모리 |
| 3 | Agent Patterns | [modules/agent-patterns.md](modules/agent-patterns.md) | ReAct, Plan-and-Execute 에이전트 |

## 의존성

```toml
[dependencies]
langchain-rust = "4"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
```

## Quick Start

### LLM 설정

```rust
use langchain_rust::llm::openai::OpenAI;

let llm = OpenAI::default()
    .with_model("gpt-4o")
    .with_api_key(std::env::var("OPENAI_API_KEY")?);
```

### 프롬프트 템플릿

```rust
use langchain_rust::prompt::PromptTemplate;

let template = PromptTemplate::new(
    "Answer the following question: {question}"
);

let prompt = template.format(&[("question", "What is Rust?")])?;
```

### 체인

```rust
use langchain_rust::chain::{Chain, LLMChain};

let chain = LLMChain::new(llm, template);
let result = chain.call(&[("question", "What is Rust?")]).await?;
```

### 메모리

```rust
use langchain_rust::memory::ConversationBufferMemory;

let memory = ConversationBufferMemory::new();
memory.save_context("user", "Hello");
memory.save_context("assistant", "Hi there!");

let history = memory.load_memory_variables()?;
```

## 참고

- [langchain-rust GitHub](https://github.com/Abraxas-365/langchain-rust)
