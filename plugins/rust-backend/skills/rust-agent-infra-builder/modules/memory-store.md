# Memory Store

Rust AI 에이전트의 메모리 관리 패턴.

## 대화 메모리

### 기본 구현

```rust
use std::collections::VecDeque;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Role {
    User,
    Assistant,
    System,
}

pub struct ConversationMemory {
    messages: VecDeque<Message>,
    max_messages: usize,
    max_tokens: usize,
}

impl ConversationMemory {
    pub fn new(max_messages: usize, max_tokens: usize) -> Self {
        Self {
            messages: VecDeque::new(),
            max_messages,
            max_tokens,
        }
    }

    pub fn add(&mut self, message: Message) {
        self.messages.push_back(message);
        self.trim();
    }

    fn trim(&mut self) {
        // 메시지 수 제한
        while self.messages.len() > self.max_messages {
            self.messages.pop_front();
        }

        // 토큰 수 제한 (근사치)
        let mut total_tokens = 0;
        let mut keep_from = 0;

        for (i, msg) in self.messages.iter().rev().enumerate() {
            total_tokens += estimate_tokens(&msg.content);
            if total_tokens > self.max_tokens {
                keep_from = self.messages.len() - i;
                break;
            }
        }

        if keep_from > 0 {
            self.messages = self.messages.split_off(keep_from);
        }
    }

    pub fn get_messages(&self) -> Vec<&Message> {
        self.messages.iter().collect()
    }

    pub fn clear(&mut self) {
        self.messages.clear();
    }
}

fn estimate_tokens(text: &str) -> usize {
    // 대략적인 토큰 추정 (실제로는 tokenizer 사용 권장)
    text.split_whitespace().count() * 4 / 3
}
```

### 세션 기반 메모리

```rust
use std::collections::HashMap;
use tokio::sync::RwLock;

pub struct SessionMemoryStore {
    sessions: RwLock<HashMap<String, ConversationMemory>>,
    max_messages: usize,
    max_tokens: usize,
}

impl SessionMemoryStore {
    pub fn new(max_messages: usize, max_tokens: usize) -> Self {
        Self {
            sessions: RwLock::new(HashMap::new()),
            max_messages,
            max_tokens,
        }
    }

    pub async fn get_or_create(&self, session_id: &str) -> ConversationMemory {
        let sessions = self.sessions.read().await;
        if let Some(memory) = sessions.get(session_id) {
            return memory.clone();
        }
        drop(sessions);

        let mut sessions = self.sessions.write().await;
        sessions
            .entry(session_id.to_string())
            .or_insert_with(|| ConversationMemory::new(self.max_messages, self.max_tokens))
            .clone()
    }

    pub async fn update(&self, session_id: &str, memory: ConversationMemory) {
        let mut sessions = self.sessions.write().await;
        sessions.insert(session_id.to_string(), memory);
    }

    pub async fn delete(&self, session_id: &str) {
        let mut sessions = self.sessions.write().await;
        sessions.remove(session_id);
    }
}
```

## 벡터 메모리

### 임베딩 기반 메모리

```rust
use ndarray::Array1;

#[derive(Debug, Clone)]
pub struct MemoryEntry {
    pub id: String,
    pub content: String,
    pub embedding: Array1<f32>,
    pub metadata: serde_json::Value,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

pub struct VectorMemory {
    entries: Vec<MemoryEntry>,
    embedding_dim: usize,
}

impl VectorMemory {
    pub fn new(embedding_dim: usize) -> Self {
        Self {
            entries: Vec::new(),
            embedding_dim,
        }
    }

    pub fn add(&mut self, entry: MemoryEntry) {
        self.entries.push(entry);
    }

    pub fn search(&self, query_embedding: &Array1<f32>, top_k: usize) -> Vec<&MemoryEntry> {
        let mut scored: Vec<_> = self.entries
            .iter()
            .map(|entry| {
                let score = cosine_similarity(query_embedding, &entry.embedding);
                (score, entry)
            })
            .collect();

        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());

        scored.into_iter()
            .take(top_k)
            .map(|(_, entry)| entry)
            .collect()
    }
}

fn cosine_similarity(a: &Array1<f32>, b: &Array1<f32>) -> f32 {
    let dot = a.dot(b);
    let norm_a = a.dot(a).sqrt();
    let norm_b = b.dot(b).sqrt();
    dot / (norm_a * norm_b)
}
```

### 임베딩 서비스 연동

```rust
use reqwest::Client;

pub struct EmbeddingService {
    client: Client,
    api_key: String,
    model: String,
}

impl EmbeddingService {
    pub fn new(api_key: &str, model: &str) -> Self {
        Self {
            client: Client::new(),
            api_key: api_key.to_string(),
            model: model.to_string(),
        }
    }

    pub async fn embed(&self, text: &str) -> anyhow::Result<Vec<f32>> {
        let response = self.client
            .post("https://api.openai.com/v1/embeddings")
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&serde_json::json!({
                "model": self.model,
                "input": text
            }))
            .send()
            .await?;

        let result: serde_json::Value = response.json().await?;
        let embedding = result["data"][0]["embedding"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_f64().unwrap() as f32)
            .collect();

        Ok(embedding)
    }
}
```

## 지속성

### Redis 백엔드

```rust
use redis::{AsyncCommands, Client};

pub struct RedisMemoryStore {
    client: Client,
    prefix: String,
    ttl: usize,
}

impl RedisMemoryStore {
    pub fn new(redis_url: &str, prefix: &str, ttl: usize) -> anyhow::Result<Self> {
        let client = Client::open(redis_url)?;
        Ok(Self {
            client,
            prefix: prefix.to_string(),
            ttl,
        })
    }

    pub async fn save(&self, session_id: &str, memory: &ConversationMemory) -> anyhow::Result<()> {
        let mut conn = self.client.get_async_connection().await?;
        let key = format!("{}:{}", self.prefix, session_id);
        let value = serde_json::to_string(memory)?;

        conn.set_ex(&key, &value, self.ttl).await?;
        Ok(())
    }

    pub async fn load(&self, session_id: &str) -> anyhow::Result<Option<ConversationMemory>> {
        let mut conn = self.client.get_async_connection().await?;
        let key = format!("{}:{}", self.prefix, session_id);

        let value: Option<String> = conn.get(&key).await?;
        match value {
            Some(v) => Ok(Some(serde_json::from_str(&v)?)),
            None => Ok(None),
        }
    }

    pub async fn delete(&self, session_id: &str) -> anyhow::Result<()> {
        let mut conn = self.client.get_async_connection().await?;
        let key = format!("{}:{}", self.prefix, session_id);
        conn.del(&key).await?;
        Ok(())
    }
}
```

### PostgreSQL 백엔드

```rust
use sqlx::PgPool;

pub struct PgMemoryStore {
    pool: PgPool,
}

impl PgMemoryStore {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn init(&self) -> anyhow::Result<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS conversation_memory (
                session_id VARCHAR(255) PRIMARY KEY,
                messages JSONB NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        "#)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    pub async fn save(&self, session_id: &str, memory: &ConversationMemory) -> anyhow::Result<()> {
        let messages = serde_json::to_value(&memory.get_messages())?;

        sqlx::query(r#"
            INSERT INTO conversation_memory (session_id, messages, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (session_id) DO UPDATE
            SET messages = $2, updated_at = NOW()
        "#)
        .bind(session_id)
        .bind(&messages)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    pub async fn load(&self, session_id: &str) -> anyhow::Result<Option<Vec<Message>>> {
        let row: Option<(serde_json::Value,)> = sqlx::query_as(r#"
            SELECT messages FROM conversation_memory WHERE session_id = $1
        "#)
        .bind(session_id)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some((messages,)) => Ok(Some(serde_json::from_value(messages)?)),
            None => Ok(None),
        }
    }
}
```

## 요약 메모리

```rust
pub struct SummaryMemory {
    summary: Option<String>,
    recent_messages: VecDeque<Message>,
    max_recent: usize,
    summarizer: Box<dyn Summarizer>,
}

#[async_trait::async_trait]
pub trait Summarizer: Send + Sync {
    async fn summarize(&self, messages: &[Message]) -> anyhow::Result<String>;
}

impl SummaryMemory {
    pub fn new(max_recent: usize, summarizer: impl Summarizer + 'static) -> Self {
        Self {
            summary: None,
            recent_messages: VecDeque::new(),
            max_recent,
            summarizer: Box::new(summarizer),
        }
    }

    pub async fn add(&mut self, message: Message) -> anyhow::Result<()> {
        self.recent_messages.push_back(message);

        if self.recent_messages.len() > self.max_recent * 2 {
            // 오래된 메시지 요약
            let to_summarize: Vec<_> = self.recent_messages
                .drain(..self.max_recent)
                .collect();

            let new_summary = self.summarizer.summarize(&to_summarize).await?;

            self.summary = Some(match &self.summary {
                Some(existing) => format!("{}\n{}", existing, new_summary),
                None => new_summary,
            });
        }

        Ok(())
    }

    pub fn get_context(&self) -> (Option<&str>, Vec<&Message>) {
        (
            self.summary.as_deref(),
            self.recent_messages.iter().collect(),
        )
    }
}
```

## 체크리스트

- [ ] 대화 메모리 크기 제한 설정
- [ ] 토큰 수 기반 트리밍
- [ ] 세션 관리 구현
- [ ] 벡터 메모리 (RAG용) 고려
- [ ] 지속성 백엔드 선택 (Redis/PostgreSQL)
- [ ] TTL 설정
- [ ] 요약 메모리 (긴 대화용) 고려
