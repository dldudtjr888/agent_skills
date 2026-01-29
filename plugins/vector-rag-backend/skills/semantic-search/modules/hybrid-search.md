# Hybrid Search

하이브리드 검색 - BM25 + Vector, RRF 융합

## 왜 하이브리드 검색인가?

| 검색 방식 | 강점 | 약점 |
|----------|------|------|
| **Keyword (BM25)** | 정확한 용어, 코드, ID | 동의어, 의미 이해 못함 |
| **Semantic (Vector)** | 의미 이해, 동의어 | 정확한 매칭 어려움 |
| **Hybrid** | 두 장점 결합 | 구현 복잡도 |

**예시:**
```
Query: "Python ML tutorial"

BM25 찾음: "Python ML 101", "Python Machine Learning"
Vector 찾음: "Deep Learning with PyTorch", "AI Programming Guide"
Hybrid: 모두 포함 (순위 조정)
```

## 기본 구현

### LangChain EnsembleRetriever

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma

# 문서 준비
documents = [...]  # Document 객체 리스트

# BM25 Retriever
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 10

# Vector Retriever
vectorstore = Chroma.from_documents(documents, embeddings)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# 앙상블 (Hybrid)
hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7]  # BM25 30%, Vector 70%
)

# 검색
docs = hybrid_retriever.get_relevant_documents("Python ML tutorial")
```

### 가중치 튜닝

| 시나리오 | BM25 비중 | Vector 비중 |
|----------|----------|------------|
| 기술 문서 (정확한 용어) | 0.4 | 0.6 |
| 일반 Q&A | 0.3 | 0.7 |
| 코드 검색 | 0.5 | 0.5 |
| 자연어 질문 | 0.2 | 0.8 |

## Reciprocal Rank Fusion (RRF)

여러 검색 결과를 순위 기반으로 융합.

### 알고리즘

```
RRF Score = Σ 1 / (k + rank)

k: 상수 (기본 60)
rank: 각 검색 결과에서의 순위 (1부터 시작)
```

### 구현

```python
def reciprocal_rank_fusion(
    results_lists: list[list],
    k: int = 60
) -> list:
    """
    RRF로 여러 검색 결과 융합

    Args:
        results_lists: 각 retriever의 결과 리스트들
        k: RRF 상수 (기본 60, 연구 권장값)

    Returns:
        융합된 결과 리스트
    """
    scores = {}

    for results in results_lists:
        for rank, doc in enumerate(results, 1):
            # 문서 식별자 (내용 해시 또는 ID)
            doc_id = hash(doc.page_content)

            if doc_id not in scores:
                scores[doc_id] = {"doc": doc, "score": 0}

            # RRF 점수 누적
            scores[doc_id]["score"] += 1 / (k + rank)

    # 점수순 정렬
    sorted_results = sorted(
        scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return [item["doc"] for item in sorted_results]

# 사용
bm25_results = bm25_retriever.get_relevant_documents(query)
vector_results = vector_retriever.get_relevant_documents(query)
hybrid_results = reciprocal_rank_fusion([bm25_results, vector_results])
```

### RRF k 값 선택

| k 값 | 효과 |
|------|------|
| 20 | 상위 순위에 더 큰 가중치 |
| 60 | 균형 (기본값) |
| 100 | 하위 순위도 영향력 있음 |

## Convex Combination

점수를 정규화하여 선형 결합.

```python
def convex_combination(
    results1: list[tuple],  # [(doc, score), ...]
    results2: list[tuple],
    alpha: float = 0.5     # 0=첫번째만, 1=두번째만
) -> list:
    """
    점수 기반 선형 결합

    Final Score = alpha * norm_score1 + (1-alpha) * norm_score2
    """
    def normalize(scores: list) -> list:
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return [0.5] * len(scores)
        return [(s - min_s) / (max_s - min_s) for s in scores]

    # 점수 정규화
    scores1 = normalize([s for _, s in results1])
    scores2 = normalize([s for _, s in results2])

    # 문서별 점수 매핑
    combined = {}
    for (doc, _), norm_score in zip(results1, scores1):
        doc_id = hash(doc.page_content)
        combined[doc_id] = {"doc": doc, "score": (1 - alpha) * norm_score}

    for (doc, _), norm_score in zip(results2, scores2):
        doc_id = hash(doc.page_content)
        if doc_id in combined:
            combined[doc_id]["score"] += alpha * norm_score
        else:
            combined[doc_id] = {"doc": doc, "score": alpha * norm_score}

    # 정렬
    sorted_results = sorted(
        combined.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return [item["doc"] for item in sorted_results]
```

## Qdrant Hybrid Search

Qdrant의 내장 하이브리드 검색.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    SparseVector, NamedSparseVector, NamedVector,
    SearchRequest, Prefetch, Query
)

client = QdrantClient("localhost", port=6333)

# Dense + Sparse 하이브리드 컬렉션 생성
client.create_collection(
    collection_name="hybrid_docs",
    vectors_config={
        "dense": VectorParams(size=1536, distance=Distance.COSINE),
    },
    sparse_vectors_config={
        "sparse": SparseVectorParams(),  # BM25 스타일
    },
)

# 포인트 추가
client.upsert(
    collection_name="hybrid_docs",
    points=[
        PointStruct(
            id=1,
            vector={
                "dense": dense_embedding,
                "sparse": SparseVector(indices=[1, 5, 100], values=[0.5, 0.3, 0.8])
            },
            payload={"text": "..."}
        )
    ]
)

# 하이브리드 검색
results = client.query_points(
    collection_name="hybrid_docs",
    prefetch=[
        Prefetch(query=dense_query, using="dense", limit=20),
        Prefetch(query=sparse_query, using="sparse", limit=20),
    ],
    query=Query.rrf(limit=10),  # RRF 융합
)
```

## 완전한 하이브리드 파이프라인

```python
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import numpy as np

class HybridSearcher:
    def __init__(
        self,
        documents: list,
        embedding_model: str = "BAAI/bge-base-en-v1.5"
    ):
        self.documents = documents
        self.texts = [doc.page_content for doc in documents]

        # BM25 인덱스
        tokenized = [text.lower().split() for text in self.texts]
        self.bm25 = BM25Okapi(tokenized)

        # Vector 인덱스
        self.embed_model = SentenceTransformer(embedding_model)
        self.doc_embeddings = self.embed_model.encode(self.texts)

    def search(
        self,
        query: str,
        k: int = 10,
        alpha: float = 0.5,  # 0=BM25, 1=Vector
        fusion: str = "rrf"  # "rrf" or "linear"
    ) -> list:
        # BM25 검색
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top = np.argsort(bm25_scores)[::-1][:k*2]

        # Vector 검색
        query_embedding = self.embed_model.encode([query])[0]
        similarities = np.dot(self.doc_embeddings, query_embedding)
        vector_top = np.argsort(similarities)[::-1][:k*2]

        # 융합
        if fusion == "rrf":
            return self._rrf_fusion(bm25_top, vector_top, k)
        else:
            return self._linear_fusion(
                bm25_scores, similarities, alpha, k
            )

    def _rrf_fusion(self, bm25_ranks, vector_ranks, k, rrf_k=60):
        scores = {}

        for rank, idx in enumerate(bm25_ranks, 1):
            scores[idx] = scores.get(idx, 0) + 1 / (rrf_k + rank)

        for rank, idx in enumerate(vector_ranks, 1):
            scores[idx] = scores.get(idx, 0) + 1 / (rrf_k + rank)

        top_indices = sorted(scores, key=scores.get, reverse=True)[:k]
        return [self.documents[i] for i in top_indices]

    def _linear_fusion(self, bm25_scores, vector_scores, alpha, k):
        # Min-Max 정규화
        bm25_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-6)
        vector_norm = (vector_scores - vector_scores.min()) / (vector_scores.max() - vector_scores.min() + 1e-6)

        # 선형 결합
        combined = (1 - alpha) * bm25_norm + alpha * vector_norm

        top_indices = np.argsort(combined)[::-1][:k]
        return [self.documents[i] for i in top_indices]

# 사용
searcher = HybridSearcher(documents)
results = searcher.search("Python machine learning", k=10, alpha=0.7)
```

## 성능 비교

### 벤치마크 (MS MARCO)

| 방식 | MRR@10 | Recall@100 |
|------|--------|------------|
| BM25 only | 0.184 | 0.857 |
| Vector only | 0.330 | 0.923 |
| Hybrid (RRF) | **0.358** | **0.948** |
| Hybrid (Linear) | 0.352 | 0.942 |

### 결론

- 하이브리드 > Vector only > BM25 only
- RRF와 Linear 융합은 비슷한 성능
- RRF가 구현 더 간단
