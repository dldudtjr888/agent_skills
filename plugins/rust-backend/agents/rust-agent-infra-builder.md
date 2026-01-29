---
name: rust-agent-infra-builder
description: Rust AI 에이전트 인프라 설계. 메모리 스토어, 프롬프트 관리, MCP 통합 구현.
model: opus
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Rust Agent Infrastructure Builder

Rust AI 에이전트의 인프라를 설계하고 구현합니다.

**참조 스킬**: `rust-agent-infra-builder`, `rig-builder`, `langchain-rust-builder`

**관련 참조**:
- `common-backend/caching-strategies` (메모리 캐싱)
- `common-backend/message-queue-patterns` (비동기 처리)

## Core Responsibilities

1. **메모리 설계** - 대화 메모리, 벡터 메모리, 지속성
2. **프롬프트 관리** - 템플릿, 버전 관리
3. **MCP 통합** - 서버 연결, 도구 디스커버리

## 메모리 아키텍처

```rust
pub struct AgentMemory {
    conversation: ConversationMemory,
    vector: VectorMemory,
    persistence: Box<dyn MemoryStore>,
}
```

## 프롬프트 관리

```rust
pub struct PromptManager {
    templates: HashMap<String, String>,
    handlebars: Handlebars<'static>,
}
```

## MCP 클라이언트

```rust
pub struct McpClient {
    // JSON-RPC over stdio
}

impl McpClient {
    pub async fn list_tools(&mut self) -> Vec<ToolInfo>;
    pub async fn call_tool(&mut self, name: &str, args: Value) -> Value;
}
```

## 벡터 메모리 (RAG)

```rust
use rig::embeddings::{EmbeddingModel, EmbeddingsBuilder};
use rig::vector_store::{InMemoryVectorStore, VectorStoreIndex};

pub struct VectorMemory {
    store: InMemoryVectorStore<Document>,
    model: EmbeddingModel,
}

impl VectorMemory {
    pub async fn add_documents(&mut self, docs: Vec<Document>) -> Result<()> {
        let embeddings = EmbeddingsBuilder::new(self.model.clone())
            .documents(docs)?
            .build()
            .await?;

        self.store.add_documents(embeddings).await?;
        Ok(())
    }

    pub async fn search(&self, query: &str, top_k: usize) -> Vec<Document> {
        let index = self.store.index(self.model.clone());
        index.top_n(query, top_k).await.unwrap_or_default()
    }
}
```

## 프롬프트 템플릿 상세

```rust
use handlebars::Handlebars;

pub struct PromptManager {
    handlebars: Handlebars<'static>,
}

impl PromptManager {
    pub fn new() -> Self {
        let mut hb = Handlebars::new();

        // 시스템 프롬프트
        hb.register_template_string("system", r#"
You are a helpful assistant.
{{#if context}}
Context:
{{context}}
{{/if}}
        "#).unwrap();

        // RAG 프롬프트
        hb.register_template_string("rag", r#"
Answer based on the following documents:
{{#each documents}}
---
{{this.content}}
---
{{/each}}

Question: {{question}}
        "#).unwrap();

        Self { handlebars: hb }
    }

    pub fn render(&self, template: &str, data: &Value) -> Result<String> {
        self.handlebars.render(template, data)
            .map_err(|e| Error::Template(e.to_string()))
    }
}
```

## MCP 클라이언트 상세

```rust
use tokio::process::{Command, Child};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

pub struct McpClient {
    child: Child,
    request_id: AtomicU64,
}

impl McpClient {
    pub async fn spawn(command: &str, args: &[&str]) -> Result<Self> {
        let child = Command::new(command)
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()?;

        Ok(Self {
            child,
            request_id: AtomicU64::new(1),
        })
    }

    pub async fn initialize(&mut self) -> Result<ServerInfo> {
        self.request("initialize", json!({
            "protocolVersion": "2024-11-05",
            "clientInfo": { "name": "rust-agent", "version": "1.0.0" }
        })).await
    }

    pub async fn list_tools(&mut self) -> Result<Vec<ToolInfo>> {
        self.request("tools/list", json!({})).await
    }

    pub async fn call_tool(&mut self, name: &str, args: Value) -> Result<Value> {
        self.request("tools/call", json!({
            "name": name,
            "arguments": args
        })).await
    }

    async fn request<T: DeserializeOwned>(&mut self, method: &str, params: Value) -> Result<T> {
        let id = self.request_id.fetch_add(1, Ordering::SeqCst);
        let request = json!({
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params
        });

        // Send request
        let stdin = self.child.stdin.as_mut().unwrap();
        stdin.write_all(request.to_string().as_bytes()).await?;
        stdin.write_all(b"\n").await?;

        // Read response
        let stdout = self.child.stdout.as_mut().unwrap();
        let mut reader = BufReader::new(stdout);
        let mut line = String::new();
        reader.read_line(&mut line).await?;

        let response: JsonRpcResponse<T> = serde_json::from_str(&line)?;
        response.result.ok_or(Error::RpcError(response.error))
    }
}
```

## 체크리스트

- [ ] 메모리 구조 설계
- [ ] 지속성 백엔드 선택 (SQLite, Redis)
- [ ] 프롬프트 템플릿 작성
- [ ] MCP 서버 연동
- [ ] 에러 처리
- [ ] 벡터 검색 구현
- [ ] 세션 관리
