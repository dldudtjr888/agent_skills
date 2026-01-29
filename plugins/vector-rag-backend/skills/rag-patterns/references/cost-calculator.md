# RAG Cost Calculator

RAG 시스템 운영 비용 계산 가이드 및 최적화 전략

## 비용 구성 요소

```
Total RAG Cost = Embedding + Retrieval + Reranking + Generation + Storage

┌─────────────────────────────────────────────────────────────┐
│                    Query Processing                          │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Embedding   │  Retrieval   │  Reranking   │  Generation   │
│  $0.00008    │  $0.00012    │  $0.0003     │  $0.002-0.06  │
│  /query      │  /query      │  /query      │  /query       │
└──────────────┴──────────────┴──────────────┴───────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│                      Storage (Monthly)                       │
├─────────────────────────────────────────────────────────────┤
│  Vector DB: $0.05-0.20/GB    │   Object Storage: $0.02/GB   │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. 비용 상세 분석

### Embedding 비용

| Provider | Model | 비용/1M tokens | 차원 | 비용/쿼리* |
|----------|-------|---------------|------|----------|
| OpenAI | text-embedding-3-small | $0.02 | 1536 | $0.00002 |
| OpenAI | text-embedding-3-large | $0.13 | 3072 | $0.00013 |
| Cohere | embed-english-v3.0 | $0.10 | 1024 | $0.00010 |
| Voyage | voyage-2 | $0.10 | 1024 | $0.00010 |
| **로컬** | bge-large-en-v1.5 | $0 (GPU 비용) | 1024 | ~$0.00001 |

*평균 쿼리 1000 토큰 기준

### Vector DB 비용

| Provider | 요금 모델 | 비용/쿼리 | 비용/GB/월 |
|----------|----------|----------|-----------|
| Pinecone Serverless | 읽기 단위 | $0.00008-0.0002 | - |
| Qdrant Cloud | 용량 기반 | - | $0.05 |
| Weaviate Cloud | 용량 기반 | - | $0.08 |
| Self-hosted | 인프라 비용 | - | ~$0.02 |

### Reranking 비용

| Provider | Model | 비용/1K 검색 | 비용/쿼리 (100 candidates) |
|----------|-------|-------------|---------------------------|
| Cohere | rerank-english-v3.0 | $2.00 | $0.0003 |
| Voyage | rerank-2 | $2.00 | $0.0003 |
| **로컬** | bge-reranker-base | $0 | ~$0.00005 |

### LLM Generation 비용

| Provider | Model | Input/1M | Output/1M | 비용/쿼리* |
|----------|-------|----------|-----------|----------|
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | $0.002 |
| OpenAI | gpt-4o | $2.50 | $10.00 | $0.03 |
| Anthropic | claude-3-haiku | $0.25 | $1.25 | $0.003 |
| Anthropic | claude-3.5-sonnet | $3.00 | $15.00 | $0.04 |
| **로컬** | llama-3.1-8b | $0 | $0 | ~$0.001 |

*평균 2000 input + 500 output 토큰 기준

---

## 2. 월간 비용 계산 공식

### 기본 공식

```
Monthly Cost = Queries/Month × Cost Per Query

Cost Per Query =
    Embedding Cost +
    Retrieval Cost +
    Reranking Cost +
    Generation Cost
```

### 예시 시나리오

#### 시나리오 1: 스타트업 (10K queries/month)

```
Config:
- Embedding: text-embedding-3-small ($0.00002/query)
- Retrieval: Qdrant Cloud ($0.00012/query)
- Reranking: 없음 ($0)
- Generation: gpt-4o-mini ($0.002/query)

Cost = 10,000 × ($0.00002 + $0.00012 + $0 + $0.002)
     = 10,000 × $0.00214
     = $21.40/month
```

#### 시나리오 2: 중견기업 (100K queries/month)

```
Config:
- Embedding: text-embedding-3-small ($0.00002/query)
- Retrieval: Qdrant Cloud ($0.00012/query)
- Reranking: Cohere ($0.0003/query)
- Generation: gpt-4o-mini ($0.002/query)

Cost = 100,000 × ($0.00002 + $0.00012 + $0.0003 + $0.002)
     = 100,000 × $0.00244
     = $244/month
```

#### 시나리오 3: 엔터프라이즈 (1M queries/month)

```
Config:
- Embedding: text-embedding-3-small ($0.00002/query)
- Retrieval: Self-hosted Qdrant ($0.00005/query)
- Reranking: Cohere ($0.0003/query)
- Generation: gpt-4o ($0.03/query)

Cost = 1,000,000 × ($0.00002 + $0.00005 + $0.0003 + $0.03)
     = 1,000,000 × $0.03037
     = $30,370/month
```

---

## 3. Python 비용 계산기

### 설치

```bash
pip install tokencost
```

### 계산기 코드

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class RAGCostConfig:
    """RAG 비용 설정"""
    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_cost_per_1m_tokens: float = 0.02
    avg_query_tokens: int = 500
    avg_doc_tokens: int = 500  # 인덱싱용

    # Retrieval
    retrieval_cost_per_query: float = 0.00012

    # Reranking
    use_reranking: bool = True
    rerank_cost_per_query: float = 0.0003
    rerank_candidates: int = 100

    # Generation
    llm_model: str = "gpt-4o-mini"
    llm_input_cost_per_1m: float = 0.15
    llm_output_cost_per_1m: float = 0.60
    avg_input_tokens: int = 2000  # query + context
    avg_output_tokens: int = 500

    # Storage
    storage_cost_per_gb_month: float = 0.05
    vector_dimensions: int = 1536
    bytes_per_dimension: int = 4  # float32


class RAGCostCalculator:
    """RAG 시스템 비용 계산기"""

    def __init__(self, config: RAGCostConfig):
        self.config = config

    def calculate_embedding_cost(self, tokens: int) -> float:
        """임베딩 비용 계산"""
        return (tokens / 1_000_000) * self.config.embedding_cost_per_1m_tokens

    def calculate_query_embedding_cost(self) -> float:
        """쿼리 임베딩 비용"""
        return self.calculate_embedding_cost(self.config.avg_query_tokens)

    def calculate_retrieval_cost(self) -> float:
        """검색 비용"""
        return self.config.retrieval_cost_per_query

    def calculate_rerank_cost(self) -> float:
        """리랭킹 비용"""
        if not self.config.use_reranking:
            return 0
        return self.config.rerank_cost_per_query

    def calculate_generation_cost(self) -> float:
        """LLM 생성 비용"""
        input_cost = (self.config.avg_input_tokens / 1_000_000) * self.config.llm_input_cost_per_1m
        output_cost = (self.config.avg_output_tokens / 1_000_000) * self.config.llm_output_cost_per_1m
        return input_cost + output_cost

    def calculate_cost_per_query(self) -> dict:
        """쿼리당 비용 상세"""
        embedding = self.calculate_query_embedding_cost()
        retrieval = self.calculate_retrieval_cost()
        reranking = self.calculate_rerank_cost()
        generation = self.calculate_generation_cost()

        return {
            "embedding": embedding,
            "retrieval": retrieval,
            "reranking": reranking,
            "generation": generation,
            "total": embedding + retrieval + reranking + generation
        }

    def calculate_monthly_cost(self, queries_per_month: int) -> dict:
        """월간 비용 계산"""
        per_query = self.calculate_cost_per_query()

        return {
            "queries_per_month": queries_per_month,
            "cost_per_query": per_query,
            "monthly_breakdown": {
                "embedding": per_query["embedding"] * queries_per_month,
                "retrieval": per_query["retrieval"] * queries_per_month,
                "reranking": per_query["reranking"] * queries_per_month,
                "generation": per_query["generation"] * queries_per_month,
            },
            "total_monthly": per_query["total"] * queries_per_month
        }

    def calculate_indexing_cost(self, num_documents: int, avg_chunks_per_doc: int = 10) -> dict:
        """인덱싱 비용 계산 (1회성)"""
        total_chunks = num_documents * avg_chunks_per_doc
        total_tokens = total_chunks * self.config.avg_doc_tokens
        embedding_cost = self.calculate_embedding_cost(total_tokens)

        # 스토리지 계산
        vector_size_bytes = self.config.vector_dimensions * self.config.bytes_per_dimension
        total_storage_gb = (total_chunks * vector_size_bytes) / (1024 ** 3)

        return {
            "num_documents": num_documents,
            "total_chunks": total_chunks,
            "embedding_cost": embedding_cost,
            "storage_gb": total_storage_gb,
            "storage_cost_monthly": total_storage_gb * self.config.storage_cost_per_gb_month
        }


# === 사용 예시 ===

if __name__ == "__main__":
    # 기본 설정
    config = RAGCostConfig(
        embedding_model="text-embedding-3-small",
        llm_model="gpt-4o-mini",
        use_reranking=True
    )

    calculator = RAGCostCalculator(config)

    # 쿼리당 비용
    print("=== Cost Per Query ===")
    per_query = calculator.calculate_cost_per_query()
    for k, v in per_query.items():
        print(f"  {k}: ${v:.6f}")

    # 월간 비용 (100K queries)
    print("\n=== Monthly Cost (100K queries) ===")
    monthly = calculator.calculate_monthly_cost(100_000)
    print(f"  Total: ${monthly['total_monthly']:.2f}")
    for k, v in monthly['monthly_breakdown'].items():
        print(f"    {k}: ${v:.2f}")

    # 인덱싱 비용 (10K documents)
    print("\n=== Indexing Cost (10K docs) ===")
    indexing = calculator.calculate_indexing_cost(10_000)
    print(f"  Embedding: ${indexing['embedding_cost']:.2f}")
    print(f"  Storage: {indexing['storage_gb']:.2f} GB")
    print(f"  Storage/month: ${indexing['storage_cost_monthly']:.2f}")
```

### 출력 예시

```
=== Cost Per Query ===
  embedding: $0.000010
  retrieval: $0.000120
  reranking: $0.000300
  generation: $0.000600
  total: $0.001030

=== Monthly Cost (100K queries) ===
  Total: $103.00
    embedding: $1.00
    retrieval: $12.00
    reranking: $30.00
    generation: $60.00

=== Indexing Cost (10K docs) ===
  Embedding: $1.00
  Storage: 0.06 GB
  Storage/month: $0.00
```

---

## 4. 비용 최적화 전략

### 캐싱 (30-50% 절감)

```python
import hashlib
from functools import lru_cache

class CachedRAG:
    def __init__(self, rag_chain, cache):
        self.chain = rag_chain
        self.cache = cache

    def query(self, question: str):
        cache_key = hashlib.md5(question.encode()).hexdigest()

        # 캐시 히트
        cached = self.cache.get(cache_key)
        if cached:
            return cached  # 비용 $0

        # 캐시 미스 - RAG 실행
        result = self.chain.invoke(question)
        self.cache.set(cache_key, result, ttl=3600)
        return result
```

**예상 절감:**
- 반복 쿼리 비율 40% 가정
- $103/month → $61.80/month (40% 절감)

### 로컬 임베딩 (95% 절감)

```python
from sentence_transformers import SentenceTransformer

# API 대신 로컬 모델
local_embeddings = SentenceTransformer("BAAI/bge-large-en-v1.5")

# GPU 인스턴스 비용: ~$0.50/hour
# 10K queries/hour 처리 가능
# 비용: $0.00005/query vs $0.00002/query (API)
```

### 배치 처리 (20-30% 절감)

```python
async def batch_queries(questions: list[str], batch_size: int = 10):
    """배치 처리로 API 오버헤드 감소"""
    results = []

    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        # 배치 임베딩 (더 효율적)
        embeddings = await embeddings_model.aembed_documents(batch)
        # 배치 검색
        all_docs = await vectorstore.asimilarity_search_by_vector_batch(embeddings)
        results.extend(all_docs)

    return results
```

### 양자화 (스토리지 75% 절감)

```python
# int8 양자화 적용
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig

client.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            always_ram=True
        )
    )
)

# 스토리지: 6.14GB → 1.54GB (75% 절감)
```

### 모델 티어링

```python
# 간단한 쿼리 → 저렴한 모델
# 복잡한 쿼리 → 고품질 모델

def select_model(query: str, retrieved_docs: list):
    # 복잡도 휴리스틱
    is_complex = (
        len(query) > 200 or
        "compare" in query.lower() or
        "explain" in query.lower() or
        len(retrieved_docs) > 5
    )

    if is_complex:
        return "gpt-4o"  # $0.03/query
    else:
        return "gpt-4o-mini"  # $0.002/query
```

---

## 5. 비용 모니터링

### 실시간 비용 추적

```python
from prometheus_client import Counter, Gauge

# 비용 메트릭
rag_cost_total = Counter(
    'rag_cost_dollars_total',
    'Total RAG cost in dollars',
    ['component']  # embedding, retrieval, reranking, generation
)

daily_budget_remaining = Gauge(
    'rag_daily_budget_remaining',
    'Remaining daily budget in dollars'
)

def track_cost(component: str, cost: float):
    rag_cost_total.labels(component=component).inc(cost)

    # 일일 예산 체크
    daily_spent = get_daily_cost()
    daily_budget_remaining.set(DAILY_BUDGET - daily_spent)

    if daily_spent > DAILY_BUDGET * 0.8:
        send_alert("80% of daily budget consumed")
```

### 비용 알림

```yaml
# Prometheus Alert Rule
groups:
  - name: cost_alerts
    rules:
      - alert: HighDailyCost
        expr: sum(increase(rag_cost_dollars_total[24h])) > 100
        labels:
          severity: warning
        annotations:
          summary: "Daily RAG cost exceeded $100"

      - alert: BudgetExhausted
        expr: rag_daily_budget_remaining < 10
        labels:
          severity: critical
        annotations:
          summary: "Daily budget nearly exhausted"
```

---

## 요약: 비용 대비표

| 시나리오 | Queries/Month | Config | 월 비용 |
|---------|---------------|--------|--------|
| 개인 프로젝트 | 1K | mini + no rerank | $2 |
| 스타트업 | 10K | mini + rerank | $24 |
| 중견기업 | 100K | mini + rerank | $244 |
| 엔터프라이즈 | 1M | gpt-4o + rerank | $30,370 |
| 최적화된 엔터프라이즈 | 1M | 캐싱+로컬+티어링 | $8,000 |
