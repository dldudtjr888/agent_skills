# Reranking Patterns

리랭킹 패턴 - Cross-encoder, Cohere, LLM 리랭커

## 리랭킹의 중요성

> "Reranking is one of the highest ROI upgrades in RAG"

| 항목 | Before Reranking | After Reranking |
|------|-----------------|-----------------|
| Recall@10 | 75% | 90%+ |
| MRR | 0.6 | 0.8+ |
| 구현 복잡도 | - | 낮음 |
| 추가 지연 | - | 100-300ms |

## 리랭킹 아키텍처

```
Query → Retriever → [Top 100 docs] → Reranker → [Top 10 docs] → LLM
           ↑              ↑              ↑
        빠름          근사치        정밀 점수
        O(log n)      ANN          Cross-attention
```

## Cross-Encoder Reranking

가장 정확하고 빠른 방법.

### Sentence Transformers

```python
from sentence_transformers import CrossEncoder

# 모델 로드
reranker = CrossEncoder("BAAI/bge-reranker-large")

def rerank_with_cross_encoder(
    query: str,
    documents: list,
    top_k: int = 10
) -> list:
    """Cross-encoder로 문서 리랭킹"""

    # 쿼리-문서 쌍 생성
    pairs = [[query, doc.page_content] for doc in documents]

    # 점수 계산
    scores = reranker.predict(pairs)

    # 점수순 정렬
    doc_score_pairs = list(zip(documents, scores))
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, score in doc_score_pairs[:top_k]]
```

### 인기 Cross-Encoder 모델

| 모델 | 크기 | 속도 | 정확도 |
|------|------|------|--------|
| `BAAI/bge-reranker-base` | 278M | 빠름 | 좋음 |
| `BAAI/bge-reranker-large` | 560M | 중간 | 매우 좋음 |
| `BAAI/bge-reranker-v2-m3` | 568M | 중간 | 최고 |
| `ms-marco-MiniLM-L-6-v2` | 22M | 매우 빠름 | 적당 |

### 배치 처리 최적화

```python
import torch
from sentence_transformers import CrossEncoder

class BatchedReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        self.model = CrossEncoder(model_name)
        self.batch_size = 32

    def rerank(
        self,
        query: str,
        documents: list,
        top_k: int = 10
    ) -> list:
        pairs = [[query, doc.page_content] for doc in documents]

        # 배치 처리
        all_scores = []
        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i:i + self.batch_size]
            scores = self.model.predict(
                batch,
                batch_size=self.batch_size,
                show_progress_bar=False
            )
            all_scores.extend(scores)

        # 정렬
        sorted_pairs = sorted(
            zip(documents, all_scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"doc": doc, "score": score}
            for doc, score in sorted_pairs[:top_k]
        ]
```

## Cohere Rerank API

상용 서비스로 간편하게 사용.

```python
import cohere

co = cohere.Client("your-api-key")

def rerank_with_cohere(
    query: str,
    documents: list,
    top_k: int = 10
) -> list:
    """Cohere Rerank API 사용"""

    # API 호출
    response = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=[doc.page_content for doc in documents],
        top_n=top_k,
        return_documents=True
    )

    # 결과 매핑
    reranked = []
    for result in response.results:
        reranked.append({
            "doc": documents[result.index],
            "score": result.relevance_score,
        })

    return reranked
```

### LangChain 통합

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

# Cohere Reranker
compressor = CohereRerank(
    model="rerank-english-v3.0",
    top_n=10
)

# Compression Retriever
retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 50})
)

docs = retriever.get_relevant_documents("query")
```

## LLM-Based Reranking

LLM을 사용한 리랭킹 (비용 높음, 정확도 최고).

### Listwise Reranking

전체 목록을 한 번에 정렬.

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4", temperature=0)

listwise_prompt = ChatPromptTemplate.from_template("""
Given the question and a list of documents, rank them by relevance.
Return only the document numbers in order of relevance (most relevant first).

Question: {question}

Documents:
{documents}

Ranking (comma-separated numbers):
""")

def llm_listwise_rerank(
    query: str,
    documents: list,
    top_k: int = 10
) -> list:
    # 문서 포맷팅
    docs_text = "\n".join([
        f"{i+1}. {doc.page_content[:500]}"
        for i, doc in enumerate(documents)
    ])

    # LLM 호출
    response = llm.invoke(
        listwise_prompt.format(
            question=query,
            documents=docs_text
        )
    )

    # 순위 파싱
    ranking = [int(x.strip()) - 1 for x in response.content.split(",")]

    # 순서대로 반환
    return [documents[i] for i in ranking[:top_k] if i < len(documents)]
```

### Pointwise Scoring

각 문서에 개별 점수 부여.

```python
pointwise_prompt = ChatPromptTemplate.from_template("""
Rate the relevance of the following document to the question on a scale of 1-10.
Return only the number.

Question: {question}
Document: {document}

Relevance score (1-10):
""")

def llm_pointwise_rerank(
    query: str,
    documents: list,
    top_k: int = 10
) -> list:
    scored_docs = []

    for doc in documents:
        response = llm.invoke(
            pointwise_prompt.format(
                question=query,
                document=doc.page_content[:1000]
            )
        )

        try:
            score = float(response.content.strip())
        except:
            score = 0

        scored_docs.append({"doc": doc, "score": score})

    # 점수순 정렬
    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    return scored_docs[:top_k]
```

### Pairwise Comparison

문서 쌍 비교로 상대적 순위 결정.

```python
pairwise_prompt = ChatPromptTemplate.from_template("""
Given the question, which document is more relevant: A or B?
Return only 'A' or 'B'.

Question: {question}
Document A: {doc_a}
Document B: {doc_b}

More relevant:
""")

def llm_pairwise_rerank(
    query: str,
    documents: list,
    top_k: int = 10
) -> list:
    """버블 정렬 방식의 페어와이즈 비교"""

    docs = documents.copy()

    # 버블 정렬
    for i in range(min(top_k, len(docs))):
        for j in range(len(docs) - i - 1):
            response = llm.invoke(
                pairwise_prompt.format(
                    question=query,
                    doc_a=docs[j].page_content[:500],
                    doc_b=docs[j+1].page_content[:500]
                )
            )

            if response.content.strip().upper() == "B":
                docs[j], docs[j+1] = docs[j+1], docs[j]

    return docs[:top_k]
```

## 하이브리드 리랭킹

여러 리랭커 조합.

```python
class HybridReranker:
    def __init__(self):
        self.cross_encoder = CrossEncoder("BAAI/bge-reranker-base")
        self.llm = ChatOpenAI(model="gpt-3.5-turbo")

    def rerank(
        self,
        query: str,
        documents: list,
        top_k: int = 10
    ) -> list:
        # 1. Cross-encoder로 1차 필터링 (빠름)
        pairs = [[query, doc.page_content] for doc in documents]
        ce_scores = self.cross_encoder.predict(pairs)

        # 상위 20개만 선별
        top_indices = sorted(
            range(len(ce_scores)),
            key=lambda i: ce_scores[i],
            reverse=True
        )[:20]
        filtered_docs = [documents[i] for i in top_indices]

        # 2. LLM으로 최종 리랭킹 (정밀)
        final_ranking = self.llm_listwise_rerank(query, filtered_docs)

        return final_ranking[:top_k]
```

## Oversampling 전략

리랭킹 효과 극대화를 위한 과다 검색.

```python
def retrieval_with_oversampling(
    query: str,
    retriever,
    reranker,
    final_k: int = 10,
    oversample_factor: float = 3.0
) -> list:
    """
    Oversample: final_k * factor만큼 검색 후 리랭킹
    """
    # 과다 검색
    oversample_k = int(final_k * oversample_factor)
    candidates = retriever.get_relevant_documents(query)[:oversample_k]

    # 리랭킹
    reranked = reranker.rerank(query, candidates, top_k=final_k)

    return reranked
```

### Oversample Factor 가이드

| Factor | 검색 수 | 리랭킹 시간 | 정확도 향상 |
|--------|--------|------------|------------|
| 2.0 | 20 | ~100ms | +5% |
| 3.0 | 30 | ~150ms | +8% |
| 5.0 | 50 | ~250ms | +10% |
| 10.0 | 100 | ~500ms | +12% |

## 리랭커 선택 가이드

| 상황 | 권장 리랭커 | 이유 |
|------|------------|------|
| 비용 민감, 빠른 속도 | Cross-Encoder (bge-base) | 무료, 빠름 |
| 높은 정확도, 영어 | Cross-Encoder (bge-large) | 정확도 최고 |
| 다국어 | Cross-Encoder (bge-m3) | 다국어 지원 |
| 간편한 통합 | Cohere Rerank | API 호출만 |
| 최고 품질 | LLM Reranking | 가장 정확 |

## 성능 비교

### 1000개 문서, Top-10 리랭킹

| 리랭커 | 지연시간 | NDCG@10 | 비용 |
|--------|---------|---------|------|
| None (baseline) | 0ms | 0.45 | $0 |
| bge-reranker-base | 120ms | 0.62 | $0 |
| bge-reranker-large | 280ms | 0.68 | $0 |
| Cohere Rerank | 150ms | 0.65 | ~$0.001 |
| GPT-3.5 Listwise | 2s | 0.70 | ~$0.01 |
| GPT-4 Listwise | 4s | 0.75 | ~$0.10 |
