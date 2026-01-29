# Chain Composition

LangChain Rust에서 체인 구성 패턴.

## 기본 체인 구조

```rust
use langchain_rust::{
    chain::{Chain, LLMChain},
    llm::openai::OpenAI,
    prompt::PromptTemplate,
};

// 단순 LLM 체인
pub async fn create_simple_chain() -> Result<LLMChain, Error> {
    let llm = OpenAI::default();

    let prompt = PromptTemplate::new(
        "You are a helpful assistant. Answer the following question: {question}"
    );

    LLMChain::new(llm, prompt)
}

// 사용
let chain = create_simple_chain().await?;
let result = chain.invoke(hashmap! {
    "question" => "What is Rust?"
}).await?;
```

## Sequential Chain

여러 체인을 순차적으로 연결.

```rust
use langchain_rust::chain::SequentialChain;

pub async fn create_sequential_chain() -> Result<SequentialChain, Error> {
    let llm = OpenAI::default();

    // 1단계: 요약 생성
    let summarize_prompt = PromptTemplate::new(
        "Summarize the following text in one sentence: {text}"
    );
    let summarize_chain = LLMChain::new(llm.clone(), summarize_prompt)
        .with_output_key("summary");

    // 2단계: 요약을 번역
    let translate_prompt = PromptTemplate::new(
        "Translate the following to Korean: {summary}"
    );
    let translate_chain = LLMChain::new(llm, translate_prompt)
        .with_output_key("translation");

    // 순차 체인
    SequentialChain::new(vec![
        Box::new(summarize_chain),
        Box::new(translate_chain),
    ])
}
```

## Router Chain

조건에 따라 다른 체인으로 라우팅.

```rust
use langchain_rust::chain::{RouterChain, RouteConfig};

pub async fn create_router_chain() -> Result<RouterChain, Error> {
    let llm = OpenAI::default();

    // 기술 질문 체인
    let tech_chain = LLMChain::new(
        llm.clone(),
        PromptTemplate::new(
            "You are a technical expert. Answer: {input}"
        ),
    );

    // 일반 질문 체인
    let general_chain = LLMChain::new(
        llm.clone(),
        PromptTemplate::new(
            "You are a helpful assistant. Answer: {input}"
        ),
    );

    // 라우터 체인
    let router_prompt = PromptTemplate::new(
        r#"Given the input, classify it as 'tech' or 'general'.
        Input: {input}
        Classification:"#
    );

    RouterChain::new(
        llm,
        router_prompt,
        vec![
            RouteConfig::new("tech", Box::new(tech_chain)),
            RouteConfig::new("general", Box::new(general_chain)),
        ],
    )
}
```

## Transform Chain

입력/출력 변환.

```rust
use langchain_rust::chain::TransformChain;

pub fn create_transform_chain() -> TransformChain {
    TransformChain::new(|input: HashMap<String, String>| {
        let text = input.get("text").unwrap();

        // 전처리: 공백 정리, 소문자 변환
        let cleaned = text
            .trim()
            .to_lowercase()
            .replace("  ", " ");

        hashmap! {
            "cleaned_text" => cleaned
        }
    })
}

// 체인 조합
let preprocess = create_transform_chain();
let llm_chain = create_simple_chain().await?;

let full_chain = SequentialChain::new(vec![
    Box::new(preprocess),
    Box::new(llm_chain),
]);
```

## Conditional Chain

조건부 실행.

```rust
pub struct ConditionalChain {
    condition: Box<dyn Fn(&HashMap<String, String>) -> bool + Send + Sync>,
    if_true: Box<dyn Chain>,
    if_false: Box<dyn Chain>,
}

impl ConditionalChain {
    pub fn new(
        condition: impl Fn(&HashMap<String, String>) -> bool + Send + Sync + 'static,
        if_true: Box<dyn Chain>,
        if_false: Box<dyn Chain>,
    ) -> Self {
        Self {
            condition: Box::new(condition),
            if_true,
            if_false,
        }
    }
}

#[async_trait]
impl Chain for ConditionalChain {
    async fn invoke(&self, input: HashMap<String, String>) -> Result<String, Error> {
        if (self.condition)(&input) {
            self.if_true.invoke(input).await
        } else {
            self.if_false.invoke(input).await
        }
    }
}

// 사용
let chain = ConditionalChain::new(
    |input| input.get("language").map_or(false, |l| l == "korean"),
    Box::new(korean_chain),
    Box::new(english_chain),
);
```

## 체인 조합 패턴

### Builder 패턴

```rust
pub struct ChainBuilder {
    chains: Vec<Box<dyn Chain>>,
}

impl ChainBuilder {
    pub fn new() -> Self {
        Self { chains: vec![] }
    }

    pub fn add(mut self, chain: impl Chain + 'static) -> Self {
        self.chains.push(Box::new(chain));
        self
    }

    pub fn add_transform<F>(mut self, f: F) -> Self
    where
        F: Fn(HashMap<String, String>) -> HashMap<String, String> + Send + Sync + 'static,
    {
        self.chains.push(Box::new(TransformChain::new(f)));
        self
    }

    pub fn build(self) -> SequentialChain {
        SequentialChain::new(self.chains)
    }
}

// 사용
let chain = ChainBuilder::new()
    .add_transform(|mut input| {
        input.insert("timestamp".into(), Utc::now().to_rfc3339());
        input
    })
    .add(summarize_chain)
    .add(translate_chain)
    .build();
```

### Parallel 실행

```rust
use futures::future::join_all;

pub async fn parallel_chains(
    chains: Vec<Box<dyn Chain>>,
    input: HashMap<String, String>,
) -> Vec<Result<String, Error>> {
    let futures = chains.iter().map(|chain| {
        let input_clone = input.clone();
        async move { chain.invoke(input_clone).await }
    });

    join_all(futures).await
}
```

## 에러 처리

```rust
use langchain_rust::chain::FallbackChain;

// Fallback 체인
let chain = FallbackChain::new(
    primary_chain,
    vec![fallback_chain_1, fallback_chain_2],
);

// 또는 수동 fallback
pub async fn invoke_with_fallback(
    chains: &[Box<dyn Chain>],
    input: HashMap<String, String>,
) -> Result<String, Error> {
    for chain in chains {
        match chain.invoke(input.clone()).await {
            Ok(result) => return Ok(result),
            Err(e) => {
                tracing::warn!("Chain failed: {}, trying next", e);
                continue;
            }
        }
    }
    Err(Error::AllChainsFailed)
}
```

## 체크리스트

- [ ] 단일 책임 체인 설계
- [ ] Sequential vs Router 선택
- [ ] 입출력 키 명확히 정의
- [ ] 에러 핸들링 및 fallback
- [ ] 성능을 위한 병렬 실행 고려
- [ ] 테스트 가능한 체인 구조
