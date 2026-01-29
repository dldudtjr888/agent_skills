# Tutorial 03: Hybrid Search 구현

BM25 + Vector 하이브리드 검색으로 검색 품질 향상

## 목표

- BM25 키워드 검색 추가
- Vector + BM25 결합
- Reciprocal Rank Fusion (RRF) 적용

## 사전 요구사항

```bash
pip install rank-bm25  # BM25 구현
pip install langchain langchain-openai langchain-community
pip install qdrant-client
```

## Step 1: 기본 설정

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant

os.environ["OPENAI_API_KEY"] = "your-api-key"

# 문서 로드 및 청킹
loader = PyPDFLoader("document.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks")
```

## Step 2: BM25 Retriever 설정

```python
from langchain_community.retrievers import BM25Retriever

# BM25 Retriever 생성
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 10  # 검색 결과 수

# 테스트
query = "machine learning algorithms"
bm25_docs = bm25_retriever.get_relevant_documents(query)

print(f"BM25 found {len(bm25_docs)} documents")
for i, doc in enumerate(bm25_docs[:3], 1):
    print(f"[{i}] {doc.page_content[:100]}...")
```

## Step 3: Vector Retriever 설정

```python
# 벡터 저장소
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(
    chunks, embeddings,
    location=":memory:",
    collection_name="docs"
)

# Vector Retriever
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# 테스트
vector_docs = vector_retriever.get_relevant_documents(query)

print(f"Vector found {len(vector_docs)} documents")
for i, doc in enumerate(vector_docs[:3], 1):
    print(f"[{i}] {doc.page_content[:100]}...")
```

## Step 4: Ensemble Retriever (LangChain 내장)

```python
from langchain.retrievers import EnsembleRetriever

# 앙상블 Retriever 생성
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7]  # BM25 30%, Vector 70%
)

# 테스트
ensemble_docs = ensemble_retriever.get_relevant_documents(query)

print(f"Ensemble found {len(ensemble_docs)} documents")
for i, doc in enumerate(ensemble_docs[:5], 1):
    print(f"[{i}] {doc.page_content[:100]}...")
```

## Step 5: 커스텀 RRF 구현

더 세밀한 제어를 위한 직접 구현:

```python
def reciprocal_rank_fusion(
    results_lists: list,
    k: int = 60
) -> list:
    """
    Reciprocal Rank Fusion (RRF)

    Score = Σ 1/(k + rank)

    Args:
        results_lists: 각 retriever의 결과 리스트들
        k: RRF 상수 (기본 60)

    Returns:
        융합된 결과 리스트
    """
    scores = {}

    for results in results_lists:
        for rank, doc in enumerate(results, 1):
            # 문서 식별자 (내용 해시)
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

print(f"RRF Hybrid found {len(hybrid_results)} documents")
for i, doc in enumerate(hybrid_results[:5], 1):
    print(f"[{i}] {doc.page_content[:100]}...")
```

## Step 6: 가중 하이브리드 검색

```python
class WeightedHybridRetriever:
    """가중치 기반 하이브리드 검색"""

    def __init__(
        self,
        bm25_retriever,
        vector_retriever,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7
    ):
        self.bm25 = bm25_retriever
        self.vector = vector_retriever
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    def get_relevant_documents(self, query: str, k: int = 10) -> list:
        # 각 retriever에서 검색
        bm25_docs = self.bm25.get_relevant_documents(query)
        vector_docs = self.vector.get_relevant_documents(query)

        # RRF 융합
        hybrid_docs = reciprocal_rank_fusion([bm25_docs, vector_docs])

        return hybrid_docs[:k]

# 사용
hybrid_retriever = WeightedHybridRetriever(
    bm25_retriever,
    vector_retriever,
    bm25_weight=0.4,
    vector_weight=0.6
)

docs = hybrid_retriever.get_relevant_documents("machine learning", k=5)
```

## Step 7: RAG 체인에 통합

```python
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt = ChatPromptTemplate.from_template("""
Answer based on the context. If unsure, say "I don't know."

Context:
{context}

Question: {question}

Answer:
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 하이브리드 RAG 체인
hybrid_rag_chain = (
    {
        "context": ensemble_retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# 질문
answer = hybrid_rag_chain.invoke("What is machine learning?")
print(answer)
```

## Step 8: 성능 비교

```python
def compare_search_methods(query: str, queries_count: int = 1):
    """검색 방법 비교"""
    print(f"Query: {query}\n")

    # BM25
    print("=== BM25 Only ===")
    bm25_docs = bm25_retriever.get_relevant_documents(query)[:5]
    for i, doc in enumerate(bm25_docs, 1):
        print(f"[{i}] {doc.page_content[:60]}...")

    # Vector
    print("\n=== Vector Only ===")
    vector_docs = vector_retriever.get_relevant_documents(query)[:5]
    for i, doc in enumerate(vector_docs, 1):
        print(f"[{i}] {doc.page_content[:60]}...")

    # Hybrid
    print("\n=== Hybrid (BM25 + Vector) ===")
    hybrid_docs = ensemble_retriever.get_relevant_documents(query)[:5]
    for i, doc in enumerate(hybrid_docs, 1):
        print(f"[{i}] {doc.page_content[:60]}...")

# 비교 테스트
compare_search_methods("Python programming tutorial")
compare_search_methods("ML algorithm performance")  # 약어 테스트
```

## Step 9: 가중치 튜닝

```python
def tune_weights(query: str, ground_truth_ids: set):
    """최적 가중치 찾기"""
    best_weight = 0
    best_recall = 0

    for bm25_w in [0.1, 0.2, 0.3, 0.4, 0.5]:
        vector_w = 1 - bm25_w

        ensemble = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[bm25_w, vector_w]
        )

        docs = ensemble.get_relevant_documents(query)[:10]
        doc_ids = {hash(d.page_content) for d in docs}

        recall = len(doc_ids & ground_truth_ids) / len(ground_truth_ids)

        print(f"BM25={bm25_w}, Vector={vector_w}: Recall={recall:.2f}")

        if recall > best_recall:
            best_recall = recall
            best_weight = bm25_w

    print(f"\nBest: BM25={best_weight}, Vector={1-best_weight}")
    return best_weight
```

## 전체 코드

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# 설정
os.environ["OPENAI_API_KEY"] = "your-key"

# 문서 준비
loader = PyPDFLoader("document.pdf")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# BM25 Retriever
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 10

# Vector Retriever
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(chunks, embeddings, location=":memory:", collection_name="docs")
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# Hybrid Retriever
hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7]
)

# RAG 체인
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
prompt = ChatPromptTemplate.from_template("""
Answer based on context. If unsure, say "I don't know."
Context: {context}
Question: {question}
Answer:
""")

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

chain = (
    {"context": hybrid_retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# 사용
print(chain.invoke("What is machine learning?"))
```

## 언제 하이브리드를 사용할까?

| 시나리오 | BM25 | Vector | Hybrid |
|----------|------|--------|--------|
| 정확한 용어 검색 | ✅ | ❌ | ✅ |
| 동의어/관련어 | ❌ | ✅ | ✅ |
| 약어 (ML, AI) | ✅ | ❌ | ✅ |
| 자연어 질문 | ❌ | ✅ | ✅ |
| 코드/ID | ✅ | ❌ | ✅ |

**결론**: 대부분의 RAG 시스템에서 하이브리드 검색이 최적

## 체크리스트

- [ ] BM25 Retriever 동작
- [ ] Vector Retriever 동작
- [ ] Ensemble/RRF 융합
- [ ] 가중치 튜닝
- [ ] RAG 체인 통합
- [ ] 품질 비교 완료
