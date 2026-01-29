# Memory Integration

LangChain Rust에서 메모리 시스템 통합.

## 메모리 타입

| 타입 | 설명 | 사용 사례 |
|------|------|----------|
| ConversationBufferMemory | 전체 대화 저장 | 짧은 대화 |
| ConversationSummaryMemory | 요약 저장 | 긴 대화 |
| ConversationBufferWindowMemory | 최근 N개 저장 | 중간 길이 대화 |
| VectorStoreMemory | 벡터 검색 기반 | 대용량, 검색 필요 |

## ConversationBufferMemory

```rust
use langchain_rust::memory::{ConversationBufferMemory, BaseMemory};

pub struct ChatBot {
    chain: LLMChain,
    memory: ConversationBufferMemory,
}

impl ChatBot {
    pub fn new(llm: OpenAI) -> Self {
        let prompt = PromptTemplate::new(
            "Current conversation:\n{history}\n\nHuman: {input}\nAI:"
        );

        Self {
            chain: LLMChain::new(llm, prompt),
            memory: ConversationBufferMemory::new(),
        }
    }

    pub async fn chat(&mut self, input: &str) -> Result<String, Error> {
        // 히스토리 로드
        let history = self.memory.load_memory_variables().await?;

        // LLM 호출
        let response = self.chain.invoke(hashmap! {
            "history" => history.get("history").unwrap_or(&String::new()),
            "input" => input,
        }).await?;

        // 메모리에 저장
        self.memory.save_context(
            hashmap! { "input" => input.to_string() },
            hashmap! { "output" => response.clone() },
        ).await?;

        Ok(response)
    }

    pub async fn clear_memory(&mut self) {
        self.memory.clear().await;
    }
}
```

## ConversationBufferWindowMemory

최근 N개의 대화만 유지.

```rust
use langchain_rust::memory::ConversationBufferWindowMemory;

pub struct WindowedChatBot {
    chain: LLMChain,
    memory: ConversationBufferWindowMemory,
}

impl WindowedChatBot {
    pub fn new(llm: OpenAI, window_size: usize) -> Self {
        Self {
            chain: LLMChain::new(llm, prompt),
            memory: ConversationBufferWindowMemory::new(window_size),
        }
    }
}
```

## ConversationSummaryMemory

대화를 요약하여 저장.

```rust
use langchain_rust::memory::ConversationSummaryMemory;

pub struct SummarizingChatBot {
    chain: LLMChain,
    memory: ConversationSummaryMemory,
}

impl SummarizingChatBot {
    pub fn new(llm: OpenAI) -> Self {
        // 요약용 LLM도 같이 사용
        let summary_llm = llm.clone();

        Self {
            chain: LLMChain::new(llm, prompt),
            memory: ConversationSummaryMemory::new(summary_llm),
        }
    }

    pub async fn chat(&mut self, input: &str) -> Result<String, Error> {
        let summary = self.memory.load_memory_variables().await?;

        let response = self.chain.invoke(hashmap! {
            "summary" => summary.get("summary").unwrap_or(&String::new()),
            "input" => input,
        }).await?;

        // 새 대화로 요약 업데이트
        self.memory.save_context(
            hashmap! { "input" => input.to_string() },
            hashmap! { "output" => response.clone() },
        ).await?;

        Ok(response)
    }
}
```

## VectorStoreMemory

벡터 검색 기반 메모리.

```rust
use langchain_rust::memory::VectorStoreMemory;
use langchain_rust::vectorstore::Qdrant;
use langchain_rust::embeddings::OpenAIEmbeddings;

pub struct SemanticChatBot {
    chain: LLMChain,
    memory: VectorStoreMemory<Qdrant>,
}

impl SemanticChatBot {
    pub async fn new(llm: OpenAI) -> Result<Self, Error> {
        let embeddings = OpenAIEmbeddings::default();
        let vectorstore = Qdrant::new("http://localhost:6333", "memories", embeddings).await?;

        Ok(Self {
            chain: LLMChain::new(llm, prompt),
            memory: VectorStoreMemory::new(vectorstore, 5), // top 5 relevant
        })
    }

    pub async fn chat(&mut self, input: &str) -> Result<String, Error> {
        // 관련 대화 검색
        let relevant = self.memory.search(input).await?;

        let response = self.chain.invoke(hashmap! {
            "context" => relevant.join("\n"),
            "input" => input,
        }).await?;

        // 새 대화 저장
        self.memory.add(format!("Human: {}\nAI: {}", input, response)).await?;

        Ok(response)
    }
}
```

## 커스텀 메모리

```rust
use async_trait::async_trait;
use langchain_rust::memory::BaseMemory;

pub struct RedisMemory {
    client: redis::Client,
    session_id: String,
}

#[async_trait]
impl BaseMemory for RedisMemory {
    async fn load_memory_variables(&self) -> Result<HashMap<String, String>, Error> {
        let mut conn = self.client.get_async_connection().await?;
        let history: Vec<String> = redis::cmd("LRANGE")
            .arg(&self.session_id)
            .arg(0)
            .arg(-1)
            .query_async(&mut conn)
            .await?;

        Ok(hashmap! {
            "history" => history.join("\n")
        })
    }

    async fn save_context(
        &mut self,
        inputs: HashMap<String, String>,
        outputs: HashMap<String, String>,
    ) -> Result<(), Error> {
        let mut conn = self.client.get_async_connection().await?;

        let human = inputs.get("input").unwrap();
        let ai = outputs.get("output").unwrap();

        redis::cmd("RPUSH")
            .arg(&self.session_id)
            .arg(format!("Human: {}", human))
            .arg(format!("AI: {}", ai))
            .query_async(&mut conn)
            .await?;

        // TTL 설정 (24시간)
        redis::cmd("EXPIRE")
            .arg(&self.session_id)
            .arg(86400)
            .query_async(&mut conn)
            .await?;

        Ok(())
    }

    async fn clear(&mut self) -> Result<(), Error> {
        let mut conn = self.client.get_async_connection().await?;
        redis::cmd("DEL")
            .arg(&self.session_id)
            .query_async(&mut conn)
            .await?;
        Ok(())
    }
}
```

## 메모리 선택 가이드

```
Q: 대화 길이?
├── 짧음 (< 10턴) → ConversationBufferMemory
├── 중간 (10-50턴) → ConversationBufferWindowMemory
└── 긺 (> 50턴) → ConversationSummaryMemory

Q: 검색 필요?
├── 예 → VectorStoreMemory
└── 아니오 → 위 선택

Q: 지속성 필요?
├── 예 → 커스텀 (Redis, DB)
└── 아니오 → 인메모리
```

## 체크리스트

- [ ] 적절한 메모리 타입 선택
- [ ] 메모리 크기 제한 설정
- [ ] 세션 관리 (멀티 유저)
- [ ] 지속성 필요 시 외부 저장소
- [ ] TTL 설정으로 메모리 정리
- [ ] 에러 핸들링
