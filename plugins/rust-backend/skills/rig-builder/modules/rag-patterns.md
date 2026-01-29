# RAG Patterns

Rig을 사용한 RAG(Retrieval-Augmented Generation) 구현 패턴.

## 기본 RAG 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    RAG Pipeline                      │
├─────────────────────────────────────────────────────┤
│  1. Document Ingestion                               │
│     ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│     │Documents│ →  │ Chunking│ →  │Embedding│      │
│     └─────────┘    └─────────┘    └─────────┘      │
│                                         ↓           │
│  2. Storage                                          │
│     ┌─────────────────────────────────────┐         │
│     │        Vector Store                  │         │
│     │  (InMemory, MongoDB, PostgreSQL)    │         │
│     └─────────────────────────────────────┘         │
│                         ↓                            │
│  3. Retrieval                                        │
│     ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│     │  Query  │ →  │Embedding│ →  │ Search  │      │
│     └─────────┘    └─────────┘    └─────────┘      │
│                                         ↓           │
│  4. Generation                                       │
│     ┌─────────────────────────────────────┐         │
│     │     LLM + Retrieved Context         │         │
│     └─────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

## 임베딩 설정

### OpenAI 임베딩

```rust
use rig::providers::openai;
use rig::embeddings::EmbeddingModel;

let client = openai::Client::from_env();

// 임베딩 모델 선택
let embedding_model = client.embedding_model("text-embedding-3-small");
// 또는 더 큰 모델
let embedding_model = client.embedding_model("text-embedding-3-large");
```

### Cohere 임베딩

```rust
use rig::providers::cohere;

let client = cohere::Client::from_env();
let embedding_model = client.embedding_model("embed-english-v3.0");
```

## 문서 임베딩

### 기본 문서 임베딩

```rust
use rig::embeddings::EmbeddingsBuilder;

let embeddings = EmbeddingsBuilder::new(embedding_model.clone())
    .document("Rust ownership rules ensure memory safety...")?
    .document("Borrowing allows references without ownership...")?
    .document("Lifetimes prevent dangling references...")?
    .build()
    .await?;
```

### 메타데이터 포함

```rust
use rig::embeddings::{EmbeddingsBuilder, DocumentBuilder};

let doc1 = DocumentBuilder::new("Rust ownership rules...")
    .with_metadata("source", "rust-book")
    .with_metadata("chapter", "4")
    .build();

let doc2 = DocumentBuilder::new("Borrowing in Rust...")
    .with_metadata("source", "rust-book")
    .with_metadata("chapter", "4")
    .build();

let embeddings = EmbeddingsBuilder::new(embedding_model.clone())
    .documents(vec![doc1, doc2])
    .build()
    .await?;
```

### 파일에서 문서 로드

```rust
use std::fs;

async fn load_documents_from_dir(
    dir: &str,
    embedding_model: impl EmbeddingModel,
) -> anyhow::Result<Vec<Embedding>> {
    let mut builder = EmbeddingsBuilder::new(embedding_model);

    for entry in fs::read_dir(dir)? {
        let path = entry?.path();
        if path.extension().map_or(false, |ext| ext == "md") {
            let content = fs::read_to_string(&path)?;
            let filename = path.file_name().unwrap().to_string_lossy();

            builder = builder.document_with_metadata(
                &content,
                vec![("filename".into(), filename.into())],
            )?;
        }
    }

    builder.build().await
}
```

## 벡터 스토어

### InMemory 벡터 스토어

```rust
use rig::vector_store::InMemoryVectorStore;

// 임베딩으로 벡터 스토어 생성
let vector_store = InMemoryVectorStore::from_documents(embeddings);

// 인덱스 생성
let index = vector_store.index(embedding_model.clone());
```

### MongoDB 벡터 스토어

```rust
use rig::vector_store::mongodb::MongoDbVectorStore;

let mongo_client = mongodb::Client::with_uri_str("mongodb://localhost:27017").await?;
let db = mongo_client.database("rag_db");
let collection = db.collection("documents");

// MongoDB 벡터 스토어 생성
let vector_store = MongoDbVectorStore::new(collection, embedding_model.clone());

// 문서 추가
vector_store.add_documents(embeddings).await?;

// 인덱스 생성 (MongoDB Atlas Search 필요)
let index = vector_store.index();
```

### PostgreSQL (pgvector)

```rust
use rig::vector_store::pgvector::PgVectorStore;
use sqlx::PgPool;

let pool = PgPool::connect("postgres://localhost/rag_db").await?;

// 테이블 생성 (pgvector extension 필요)
sqlx::query(r#"
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(1536),
        metadata JSONB
    )
"#)
.execute(&pool)
.await?;

let vector_store = PgVectorStore::new(pool, embedding_model.clone());
vector_store.add_documents(embeddings).await?;
```

## 검색 패턴

### 기본 유사도 검색

```rust
// top-k 검색
let results = index.search("How does borrowing work?", 5).await?;

for result in results {
    println!("Score: {:.4}", result.score);
    println!("Content: {}", result.document.content);
    println!("---");
}
```

### 메타데이터 필터링

```rust
use rig::vector_store::Filter;

// 특정 소스만 검색
let filter = Filter::eq("source", "rust-book");
let results = index.search_with_filter("ownership", 5, filter).await?;

// 복합 필터
let filter = Filter::and(vec![
    Filter::eq("source", "rust-book"),
    Filter::gte("chapter", 4),
]);
```

### 하이브리드 검색 (키워드 + 시맨틱)

```rust
async fn hybrid_search(
    index: &impl VectorIndex,
    query: &str,
    k: usize,
) -> anyhow::Result<Vec<SearchResult>> {
    // 시맨틱 검색
    let semantic_results = index.search(query, k * 2).await?;

    // 키워드 기반 점수 부스트
    let keywords: Vec<&str> = query.split_whitespace().collect();

    let mut scored_results: Vec<_> = semantic_results
        .into_iter()
        .map(|result| {
            let keyword_boost = keywords
                .iter()
                .filter(|kw| result.document.content.to_lowercase().contains(&kw.to_lowercase()))
                .count() as f64 * 0.1;

            (result.score + keyword_boost, result)
        })
        .collect();

    // 재정렬
    scored_results.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());

    Ok(scored_results.into_iter().take(k).map(|(_, r)| r).collect())
}
```

## RAG 에이전트

### 기본 RAG 에이전트

```rust
let rag_agent = client
    .agent("gpt-4o")
    .preamble(r#"
        You are a helpful assistant that answers questions based on the provided context.

        Guidelines:
        - Only use information from the context to answer
        - If the context doesn't contain relevant information, say so
        - Cite specific parts of the context when answering
    "#)
    .dynamic_context(4, index)  // top-4 문서 검색
    .build();

let response = rag_agent
    .prompt("How does Rust prevent memory leaks?")
    .await?;
```

### 컨텍스트 크기 조절

```rust
// 짧은 컨텍스트 (빠른 응답)
let fast_agent = client
    .agent("gpt-4o-mini")
    .dynamic_context(2, index.clone())
    .build();

// 긴 컨텍스트 (자세한 응답)
let detailed_agent = client
    .agent("gpt-4o")
    .dynamic_context(8, index.clone())
    .build();
```

## 문서 청킹

### 고정 크기 청킹

```rust
fn chunk_by_size(text: &str, chunk_size: usize, overlap: usize) -> Vec<String> {
    let words: Vec<&str> = text.split_whitespace().collect();
    let mut chunks = Vec::new();

    let mut i = 0;
    while i < words.len() {
        let end = (i + chunk_size).min(words.len());
        let chunk = words[i..end].join(" ");
        chunks.push(chunk);

        if end >= words.len() {
            break;
        }
        i += chunk_size - overlap;
    }

    chunks
}
```

### 문단 기반 청킹

```rust
fn chunk_by_paragraph(text: &str, max_chunk_size: usize) -> Vec<String> {
    let paragraphs: Vec<&str> = text.split("\n\n").collect();
    let mut chunks = Vec::new();
    let mut current_chunk = String::new();

    for para in paragraphs {
        if current_chunk.len() + para.len() > max_chunk_size && !current_chunk.is_empty() {
            chunks.push(current_chunk.trim().to_string());
            current_chunk = String::new();
        }
        current_chunk.push_str(para);
        current_chunk.push_str("\n\n");
    }

    if !current_chunk.trim().is_empty() {
        chunks.push(current_chunk.trim().to_string());
    }

    chunks
}
```

### 시맨틱 청킹

```rust
fn chunk_by_headers(markdown: &str) -> Vec<(String, String)> {
    let mut chunks = Vec::new();
    let mut current_header = String::new();
    let mut current_content = String::new();

    for line in markdown.lines() {
        if line.starts_with('#') {
            if !current_content.trim().is_empty() {
                chunks.push((current_header.clone(), current_content.trim().to_string()));
            }
            current_header = line.to_string();
            current_content = String::new();
        } else {
            current_content.push_str(line);
            current_content.push('\n');
        }
    }

    if !current_content.trim().is_empty() {
        chunks.push((current_header, current_content.trim().to_string()));
    }

    chunks
}
```

## 체크리스트

- [ ] 임베딩 모델 선택 (차원, 비용, 성능)
- [ ] 문서 청킹 전략 선택
- [ ] 벡터 스토어 선택 (InMemory/MongoDB/PostgreSQL)
- [ ] 적절한 검색 결과 개수 (k) 설정
- [ ] 메타데이터 설계
- [ ] 하이브리드 검색 고려 (필요시)
- [ ] 프롬프트에 컨텍스트 사용 지침 포함
