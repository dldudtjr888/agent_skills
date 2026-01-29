# Retrieval Optimization

검색 최적화 - 쿼리 변환, 하이브리드 검색, 다단계 검색

## 검색 최적화 개요

```
Query → [Transform] → [Retrieve] → [Filter] → Results
           ↓              ↓           ↓
        HyDE          Hybrid      Metadata
        Multi-Query   Multi-Stage  Score Threshold
        Step-back     Dense+Sparse Re-fetch
```

## 쿼리 변환 (Query Transformation)

### HyDE (Hypothetical Document Embeddings)

쿼리 대신 가상의 답변을 생성하여 검색.

```python
from langchain.chains import HypotheticalDocumentEmbedder
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# HyDE 설정
llm = ChatOpenAI(model="gpt-3.5-turbo")
base_embeddings = OpenAIEmbeddings()

hyde = HypotheticalDocumentEmbedder.from_llm(
    llm=llm,
    base_embeddings=base_embeddings,
    prompt_key="web_search"  # 또는 커스텀 프롬프트
)

# 검색
# 내부적으로: query → 가상 문서 생성 → 임베딩 → 검색
docs = vectorstore.similarity_search_by_vector(
    hyde.embed_query("What is machine learning?")
)
```

**작동 원리:**
```
Query: "What is machine learning?"
        ↓
LLM generates hypothetical answer:
"Machine learning is a subset of AI that enables
 systems to learn from data..."
        ↓
Embed this hypothetical answer
        ↓
Search with this embedding
```

### Multi-Query Retrieval

다양한 관점의 쿼리로 검색 후 결과 통합.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=0)

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=llm,
    include_original=True,  # 원본 쿼리도 포함
)

# 내부적으로 여러 쿼리 생성 후 검색
docs = retriever.get_relevant_documents(
    "What are the effects of climate change on agriculture?"
)
```

**생성되는 쿼리 예시:**
```
Original: "What are the effects of climate change on agriculture?"

Generated:
1. "How does global warming impact crop yields?"
2. "Climate change agricultural consequences"
3. "Farming challenges due to temperature rise"
```

### Step-Back Prompting

구체적 질문을 추상화하여 검색.

```python
from langchain.prompts import ChatPromptTemplate

step_back_prompt = ChatPromptTemplate.from_template("""
You are an expert at converting specific questions into more general questions.
Given a specific question, generate a broader question that would help answer it.

Specific question: {question}
Broader question:
""")

def step_back_retrieval(question: str, retriever, llm):
    # 1. 추상화된 질문 생성
    broader_question = llm.invoke(
        step_back_prompt.format(question=question)
    ).content

    # 2. 원본 + 추상화 질문으로 검색
    original_docs = retriever.get_relevant_documents(question)
    broader_docs = retriever.get_relevant_documents(broader_question)

    # 3. 결과 병합 (중복 제거)
    all_docs = list({doc.page_content: doc for doc in original_docs + broader_docs}.values())

    return all_docs
```

**예시:**
```
Specific: "What is the boiling point of water at 2000m altitude?"
Step-back: "What factors affect the boiling point of water?"
```

## 하이브리드 검색 (Hybrid Search)

### BM25 + Vector Search

키워드 검색과 시맨틱 검색 결합.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma

# BM25 Retriever (키워드 검색)
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 5

# Vector Retriever (시맨틱 검색)
vectorstore = Chroma.from_documents(documents, embeddings)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 앙상블 Retriever
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6]  # BM25 40%, Vector 60%
)

docs = ensemble_retriever.get_relevant_documents("query")
```

### Reciprocal Rank Fusion (RRF)

여러 검색 결과를 순위 기반으로 융합.

```python
def reciprocal_rank_fusion(
    results_lists: list[list],
    k: int = 60
) -> list:
    """
    RRF Score = sum(1 / (k + rank))

    k=60은 연구에서 제안된 기본값
    """
    scores = {}

    for results in results_lists:
        for rank, doc in enumerate(results):
            doc_id = doc.metadata.get("id", hash(doc.page_content))

            if doc_id not in scores:
                scores[doc_id] = {"doc": doc, "score": 0}

            scores[doc_id]["score"] += 1 / (k + rank + 1)

    # 점수순 정렬
    sorted_docs = sorted(
        scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return [item["doc"] for item in sorted_docs]

# 사용
bm25_results = bm25_retriever.get_relevant_documents(query)
vector_results = vector_retriever.get_relevant_documents(query)
fused_results = reciprocal_rank_fusion([bm25_results, vector_results])
```

### Convex Combination

점수를 정규화하여 가중 합산.

```python
def convex_combination(
    results_with_scores: list[tuple],  # [(doc, score), ...]
    alpha: float = 0.5  # 0=첫번째만, 1=두번째만
) -> list:
    """
    Final Score = alpha * normalized_score1 + (1-alpha) * normalized_score2
    """
    # Min-Max 정규화
    def normalize(scores):
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return [0.5] * len(scores)
        return [(s - min_s) / (max_s - min_s) for s in scores]

    # ... 구현
```

## 다단계 검색 (Multi-Stage Retrieval)

### Coarse-to-Fine Retrieval

넓게 검색 후 좁혀가기.

```python
def coarse_to_fine_retrieval(
    query: str,
    vectorstore,
    reranker,
    coarse_k: int = 50,
    fine_k: int = 10
) -> list:
    """
    1단계: 많은 후보 검색 (coarse)
    2단계: 리랭킹으로 정제 (fine)
    """
    # Coarse: 빠른 ANN 검색
    candidates = vectorstore.similarity_search(query, k=coarse_k)

    # Fine: 정밀 리랭킹
    reranked = reranker.rerank(query, candidates)

    return reranked[:fine_k]
```

### Iterative Retrieval

검색 → 평가 → 재검색 반복.

```python
def iterative_retrieval(
    query: str,
    retriever,
    evaluator,
    max_iterations: int = 3
) -> list:
    """검색 결과가 충분할 때까지 반복"""
    all_docs = []

    for i in range(max_iterations):
        # 검색
        docs = retriever.get_relevant_documents(query)
        all_docs.extend(docs)

        # 평가
        is_sufficient = evaluator.evaluate(query, all_docs)
        if is_sufficient:
            break

        # 쿼리 수정 (다음 반복용)
        query = evaluator.suggest_refined_query(query, all_docs)

    return all_docs
```

## 필터링 전략

### Pre-Filtering (권장)

검색 전에 필터 적용.

```python
# Qdrant 예시
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="docs",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="year", range=Range(gte=2023)),
        ]
    ),
    limit=10
)
```

### Self-Query Retrieval

쿼리에서 자동으로 필터 추출.

```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

metadata_field_info = [
    AttributeInfo(
        name="category",
        description="The category of the document",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="The year the document was published",
        type="integer",
    ),
]

retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="Technical documentation about software",
    metadata_field_info=metadata_field_info,
)

# 자동으로 필터 추출
# "Python tutorials from 2023" → filter: {category: "python", year: 2023}
docs = retriever.get_relevant_documents("Python tutorials from 2023")
```

### Score Threshold

최소 점수 이하 결과 제외.

```python
# 점수 임계값 설정
results = vectorstore.similarity_search_with_score(query, k=20)
filtered = [(doc, score) for doc, score in results if score >= 0.7]
```

## Contextual Compression

검색 후 관련 부분만 추출.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# LLM 기반 압축
compressor = LLMChainExtractor.from_llm(llm)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)

# 검색 후 관련 부분만 추출하여 반환
docs = compression_retriever.get_relevant_documents(query)
```

## Time-Weighted Retrieval

최신 문서에 가중치 부여.

```python
from langchain.retrievers import TimeWeightedVectorStoreRetriever

retriever = TimeWeightedVectorStoreRetriever(
    vectorstore=vectorstore,
    decay_rate=0.01,  # 시간 감쇠율
    k=5,
)

# 최신 문서가 더 높은 점수
docs = retriever.get_relevant_documents(query)
```

## 검색 파이프라인 예시

```python
class OptimizedRetriever:
    def __init__(self, vectorstore, bm25_retriever, reranker, llm):
        self.vectorstore = vectorstore
        self.bm25 = bm25_retriever
        self.reranker = reranker
        self.llm = llm

    def retrieve(
        self,
        query: str,
        filters: dict = None,
        top_k: int = 10
    ) -> list:
        # 1. 쿼리 변환 (Multi-Query)
        queries = self._generate_queries(query)

        # 2. 하이브리드 검색
        all_results = []
        for q in queries:
            vector_results = self.vectorstore.similarity_search(
                q, k=20, filter=filters
            )
            bm25_results = self.bm25.get_relevant_documents(q)[:20]
            all_results.extend(vector_results + bm25_results)

        # 3. 중복 제거 및 RRF
        unique_results = self._deduplicate(all_results)

        # 4. 리랭킹
        reranked = self.reranker.rerank(query, unique_results)

        return reranked[:top_k]

    def _generate_queries(self, query: str) -> list:
        # Multi-query 생성
        prompt = f"Generate 3 different versions of: {query}"
        variations = self.llm.invoke(prompt).content.split("\n")
        return [query] + variations[:2]

    def _deduplicate(self, docs: list) -> list:
        seen = set()
        unique = []
        for doc in docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(doc)
        return unique
```
