# Context Engineering

컨텍스트 엔지니어링 - 리패킹, 압축, 롱컨텍스트 전략

## 컨텍스트 엔지니어링이란?

검색된 문서를 LLM에 최적화된 형태로 구성하는 기술.

```
Retrieved Docs → [Repack] → [Compress] → [Format] → LLM Context
                    ↓           ↓           ↓
                순서 최적화   중복 제거    프롬프트 구조화
```

## Repacking 전략

### Lost in the Middle 문제

LLM은 컨텍스트 중간 정보를 잘 활용하지 못함.

```
Position Effect on Attention:
╔════════════════════════════════════════╗
║ ██████ Start: High Attention           ║
║ ████                                   ║
║ ██                                     ║
║ █    Middle: Low Attention ← 문제!    ║
║ ██                                     ║
║ ████                                   ║
║ ██████ End: High Attention             ║
╚════════════════════════════════════════╝
```

### Repacking 전략 구현

```python
def repack_documents(
    documents: list,
    strategy: str = "sides"
) -> list:
    """
    Repacking strategies:
    - forward: 관련도 높은 것 먼저 (기본)
    - reverse: 관련도 높은 것 마지막
    - sides: 관련도 높은 것 처음과 끝 (권장)
    """

    if strategy == "forward":
        # 이미 관련도순 정렬됨
        return documents

    elif strategy == "reverse":
        # 역순 (마지막이 가장 관련)
        return list(reversed(documents))

    elif strategy == "sides":
        # 홀수 인덱스는 앞, 짝수 인덱스는 뒤
        n = len(documents)
        reordered = [None] * n

        left, right = 0, n - 1
        for i, doc in enumerate(documents):
            if i % 2 == 0:
                reordered[left] = doc
                left += 1
            else:
                reordered[right] = doc
                right -= 1

        return reordered

    return documents
```

### 전략별 효과

| 전략 | 적합한 상황 | 효과 |
|------|------------|------|
| **forward** | 짧은 컨텍스트 | 기본 |
| **reverse** | 요약 태스크 | 결론 강조 |
| **sides** | 긴 컨텍스트 | **최적** (lost in middle 완화) |

## 컨텍스트 압축

### LLM Chain Extractor

LLM으로 관련 부분만 추출.

```python
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever

# Compressor 생성
compressor = LLMChainExtractor.from_llm(llm)

# 압축 Retriever
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever,
)

# 사용
docs = compression_retriever.get_relevant_documents(query)
# 각 문서가 쿼리와 관련된 부분만 추출됨
```

### Embeddings Filter

임베딩 유사도 기반 필터링.

```python
from langchain.retrievers.document_compressors import EmbeddingsFilter

embeddings_filter = EmbeddingsFilter(
    embeddings=embeddings,
    similarity_threshold=0.76  # 최소 유사도
)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=embeddings_filter,
    base_retriever=base_retriever,
)
```

### 커스텀 압축기

```python
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.document_transformers import (
    EmbeddingsRedundantFilter,
    LongContextReorder,
)

# 파이프라인 구성
compressor_pipeline = DocumentCompressorPipeline(
    transformers=[
        EmbeddingsRedundantFilter(embeddings=embeddings),  # 중복 제거
        EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.75),
        LongContextReorder(),  # 순서 최적화
    ]
)
```

## 중복 제거

### Semantic Deduplication

의미적으로 유사한 문서 제거.

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def semantic_deduplicate(
    documents: list,
    embeddings,
    threshold: float = 0.95
) -> list:
    """유사도 threshold 이상인 문서 제거"""

    # 임베딩 계산
    doc_embeddings = embeddings.embed_documents(
        [doc.page_content for doc in documents]
    )

    # 유사도 행렬
    similarity_matrix = cosine_similarity(doc_embeddings)

    # 중복 마킹
    keep_indices = []
    for i in range(len(documents)):
        is_duplicate = False
        for j in keep_indices:
            if similarity_matrix[i][j] >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            keep_indices.append(i)

    return [documents[i] for i in keep_indices]
```

### MMR (Maximal Marginal Relevance)

다양성과 관련성의 균형.

```python
# LangChain의 MMR 검색
docs = vectorstore.max_marginal_relevance_search(
    query,
    k=10,
    fetch_k=50,  # 후보 수
    lambda_mult=0.5  # 0=다양성, 1=관련성
)
```

## 롱컨텍스트 전략

### 언제 긴 컨텍스트를 사용할까?

| 상황 | 권장 전략 |
|------|----------|
| 단일 문서 전체 이해 | 전체 문서 포함 |
| 여러 문서 종합 | 청킹 + 검색 |
| 코드 분석 | 관련 파일 전체 |
| 법률/계약서 | 전체 문서 |

### 청킹 vs 전체 문서

```python
def decide_context_strategy(
    document_length: int,
    context_window: int,
    task_type: str
) -> str:
    """컨텍스트 전략 결정"""

    if document_length < context_window * 0.5:
        return "full_document"

    if task_type in ["summarization", "legal_review"]:
        return "full_document"

    if task_type in ["qa", "search"]:
        return "chunked_retrieval"

    return "hybrid"
```

### 계층적 요약

긴 문서를 계층적으로 요약.

```python
from langchain.chains.summarize import load_summarize_chain

def hierarchical_summarize(
    documents: list,
    llm,
    max_context: int = 8000
) -> str:
    """
    Map-Reduce 방식 요약:
    1. 각 청크 요약 (Map)
    2. 요약들을 합쳐 최종 요약 (Reduce)
    """

    # Map: 각 문서 요약
    map_chain = load_summarize_chain(llm, chain_type="map_reduce")
    summary = map_chain.run(documents)

    return summary
```

## 프롬프트 포맷팅

### 구조화된 컨텍스트

```python
def format_context(
    documents: list,
    include_metadata: bool = True,
    include_source: bool = True
) -> str:
    """구조화된 컨텍스트 포맷"""

    formatted_parts = []

    for i, doc in enumerate(documents, 1):
        parts = [f"[Document {i}]"]

        if include_source and doc.metadata.get("source"):
            parts.append(f"Source: {doc.metadata['source']}")

        if include_metadata:
            meta = {k: v for k, v in doc.metadata.items()
                   if k not in ["source", "embedding"]}
            if meta:
                parts.append(f"Metadata: {meta}")

        parts.append(f"Content:\n{doc.page_content}")

        formatted_parts.append("\n".join(parts))

    return "\n\n---\n\n".join(formatted_parts)
```

### Citation 지원

```python
def format_with_citations(documents: list) -> tuple[str, dict]:
    """Citation 참조가 포함된 컨텍스트"""

    citation_map = {}
    formatted_parts = []

    for i, doc in enumerate(documents, 1):
        citation_key = f"[{i}]"
        citation_map[citation_key] = {
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page"),
            "url": doc.metadata.get("url"),
        }

        formatted_parts.append(
            f"{citation_key}\n{doc.page_content}"
        )

    context = "\n\n".join(formatted_parts)

    return context, citation_map

# 프롬프트에서 사용
context, citations = format_with_citations(documents)
prompt = f"""
Based on the following sources, answer the question.
Cite sources using [1], [2], etc.

Sources:
{context}

Question: {query}
"""
```

## 토큰 최적화

### 토큰 카운팅

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """토큰 수 계산"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def fit_to_context(
    documents: list,
    max_tokens: int,
    model: str = "gpt-4"
) -> list:
    """토큰 한도 내에서 최대한 많은 문서 포함"""

    selected = []
    current_tokens = 0

    for doc in documents:
        doc_tokens = count_tokens(doc.page_content, model)

        if current_tokens + doc_tokens <= max_tokens:
            selected.append(doc)
            current_tokens += doc_tokens
        else:
            break

    return selected
```

### 동적 컨텍스트 크기

```python
def dynamic_context_size(
    query: str,
    base_context_tokens: int = 4000,
    query_complexity_factor: float = 1.0
) -> int:
    """쿼리 복잡도에 따른 동적 컨텍스트 크기"""

    # 쿼리 길이 기반 조정
    query_tokens = count_tokens(query)

    if query_tokens > 100:
        complexity_factor = 1.5  # 복잡한 쿼리
    elif query_tokens > 50:
        complexity_factor = 1.2
    else:
        complexity_factor = 1.0

    return int(base_context_tokens * complexity_factor)
```

## 완성된 파이프라인

```python
class ContextEngineer:
    def __init__(
        self,
        embeddings,
        llm,
        max_context_tokens: int = 8000
    ):
        self.embeddings = embeddings
        self.llm = llm
        self.max_tokens = max_context_tokens

    def prepare_context(
        self,
        documents: list,
        query: str,
        strategy: str = "optimal"
    ) -> str:
        # 1. 중복 제거
        docs = semantic_deduplicate(
            documents, self.embeddings, threshold=0.9
        )

        # 2. 토큰 한도 적용
        docs = fit_to_context(docs, self.max_tokens)

        # 3. 리패킹 (sides 전략)
        docs = repack_documents(docs, strategy="sides")

        # 4. 포맷팅
        context = format_with_citations(docs)

        return context
```
