# Embedding Selection

임베딩 모델 선택 가이드 - 모델 비교, 차원, 성능

## 임베딩 모델 카테고리

### 1. API 기반 (Closed-source)

| 모델 | 차원 | MTEB | 비용 | 특징 |
|------|------|------|------|------|
| `text-embedding-3-small` | 1536 | 62.3 | $0.02/1M | 비용 효율적 |
| `text-embedding-3-large` | 3072 | 64.6 | $0.13/1M | 최고 품질 |
| `text-embedding-ada-002` | 1536 | 61.0 | $0.10/1M | Legacy |
| Cohere `embed-english-v3.0` | 1024 | 64.5 | $0.10/1M | 검색 최적화 |
| Voyage `voyage-2` | 1024 | 65.3 | $0.10/1M | RAG 특화 |

### 2. 오픈소스 (Self-hosted)

| 모델 | 차원 | MTEB | 크기 | 특징 |
|------|------|------|------|------|
| `bge-large-en-v1.5` | 1024 | 64.2 | 1.3GB | 최고 성능 |
| `bge-base-en-v1.5` | 768 | 63.6 | 438MB | 균형 |
| `e5-large-v2` | 1024 | 62.0 | 1.3GB | MS Research |
| `all-MiniLM-L6-v2` | 384 | 56.3 | 91MB | 경량/빠름 |
| `multilingual-e5-large` | 1024 | 61.5 | 2.2GB | 다국어 |

### 3. 특수 목적

| 모델 | 용도 | 특징 |
|------|------|------|
| `nomic-embed-text-v1.5` | 긴 텍스트 | 8K 컨텍스트 |
| `jina-embeddings-v2` | 긴 텍스트 | 8K 컨텍스트 |
| `CodeBERT` | 코드 | 코드 검색 특화 |
| `clip-ViT-B-32` | 이미지+텍스트 | 멀티모달 |

## 모델 선택 가이드

```
시작
  │
  ├─ 예산 제한 없음?
  │   ├─ Yes → text-embedding-3-large
  │   └─ No ─┐
  │          │
  ├─ 로컬 실행 필요?
  │   ├─ Yes ─┬─ 고품질 → bge-large-en-v1.5
  │   │       ├─ 균형 → bge-base-en-v1.5
  │   │       └─ 경량 → all-MiniLM-L6-v2
  │   └─ No ─┐
  │          │
  ├─ 다국어 필요?
  │   ├─ Yes → multilingual-e5-large
  │   └─ No ─┐
  │          │
  └─ 기본 선택 → text-embedding-3-small
```

## OpenAI Embeddings

```python
from langchain_openai import OpenAIEmbeddings

# 기본 (권장)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 고품질
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# 차원 축소 (비용 절감)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1024  # 3072 → 1024로 축소
)

# 사용
vector = embeddings.embed_query("Hello world")
vectors = embeddings.embed_documents(["doc1", "doc2"])
```

## 로컬 임베딩

### Sentence Transformers

```python
from sentence_transformers import SentenceTransformer

# 모델 로드
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# 임베딩
embeddings = model.encode(["Hello world", "Another text"])

# 쿼리/문서 구분 (일부 모델)
query_embedding = model.encode("search query", prompt_name="query")
doc_embedding = model.encode("document text", prompt_name="passage")
```

### HuggingFace + LangChain

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cuda"},  # GPU 사용
    encode_kwargs={"normalize_embeddings": True}  # 정규화
)
```

### Ollama (로컬 실행)

```python
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

## 차원 선택

### 차원별 트레이드오프

| 차원 | 메모리 | 검색 속도 | 정확도 |
|------|--------|----------|--------|
| 384 | 낮음 | 빠름 | 보통 |
| 768 | 중간 | 중간 | 좋음 |
| 1024 | 중간 | 중간 | 좋음 |
| 1536 | 높음 | 느림 | 매우 좋음 |
| 3072 | 매우 높음 | 느림 | 최고 |

### 메모리 계산

```
Memory = num_vectors × dimensions × bytes_per_value

예: 10M 벡터, 1536차원, float32
= 10,000,000 × 1536 × 4 = 61.4 GB

예: 10M 벡터, 384차원, float32
= 10,000,000 × 384 × 4 = 15.4 GB
```

### 차원 축소

```python
# OpenAI는 API에서 지원
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1024  # 원래 3072
)

# 또는 PCA로 축소
from sklearn.decomposition import PCA

pca = PCA(n_components=512)
reduced_embeddings = pca.fit_transform(original_embeddings)
```

## 배치 처리

```python
from langchain_openai import OpenAIEmbeddings
import asyncio

embeddings = OpenAIEmbeddings()

# 동기 배치
texts = ["text1", "text2", ..., "text1000"]
vectors = embeddings.embed_documents(texts)  # 자동 배치 처리

# 비동기 배치 (더 빠름)
async def embed_async(texts: list):
    return await embeddings.aembed_documents(texts)

vectors = asyncio.run(embed_async(texts))
```

## 캐싱

```python
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

# 파일 기반 캐시
store = LocalFileStore("./embedding_cache")
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    embeddings,
    store,
    namespace="my_embeddings"
)

# 동일 텍스트는 캐시에서 반환
vector = cached_embeddings.embed_query("Hello")  # 첫 번째: API 호출
vector = cached_embeddings.embed_query("Hello")  # 두 번째: 캐시
```

## 성능 테스트

```python
import time
import numpy as np

def benchmark_embedding_model(model, texts: list, n_runs: int = 5):
    """임베딩 모델 벤치마크"""
    latencies = []

    for _ in range(n_runs):
        start = time.perf_counter()
        embeddings = model.encode(texts)
        latencies.append(time.perf_counter() - start)

    return {
        "avg_latency": np.mean(latencies),
        "p95_latency": np.percentile(latencies, 95),
        "texts_per_sec": len(texts) / np.mean(latencies),
        "embedding_dim": len(embeddings[0]),
    }

# 테스트
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
results = benchmark_embedding_model(model, sample_texts)
```

## 모델 비교 실험

```python
from sklearn.metrics.pairwise import cosine_similarity

def compare_models(models: dict, query: str, documents: list):
    """여러 모델 비교"""
    results = {}

    for name, model in models.items():
        query_emb = model.encode([query])
        doc_embs = model.encode(documents)

        similarities = cosine_similarity(query_emb, doc_embs)[0]
        rankings = np.argsort(similarities)[::-1]

        results[name] = {
            "rankings": rankings.tolist(),
            "top_similarity": similarities[rankings[0]],
        }

    return results
```
