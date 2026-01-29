# Tutorial 02: Advanced RAG with Reranking

리랭킹으로 검색 품질 향상시키기

## 목표

- Cross-encoder 리랭킹 적용
- Cohere Rerank API 사용
- 검색 품질 비교

## 사전 요구사항

```bash
pip install sentence-transformers  # Cross-encoder용
pip install cohere  # Cohere Rerank용
pip install langchain-cohere
```

## Step 1: 기본 설정 (Tutorial 01 기반)

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

# 벡터 저장소
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(
    chunks, embeddings,
    location=":memory:",
    collection_name="docs"
)

# 기본 Retriever (과다 검색)
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
```

## Step 2: Cross-Encoder Reranking

### 2.1 Cross-Encoder 직접 사용

```python
from sentence_transformers import CrossEncoder

# 리랭커 로드
reranker = CrossEncoder("BAAI/bge-reranker-base")  # 빠름
# reranker = CrossEncoder("BAAI/bge-reranker-large")  # 더 정확

def rerank_documents(query: str, docs: list, top_k: int = 5) -> list:
    """Cross-encoder로 문서 리랭킹"""
    if not docs:
        return []

    # 쿼리-문서 쌍 생성
    pairs = [[query, doc.page_content] for doc in docs]

    # 점수 계산
    scores = reranker.predict(pairs)

    # 점수순 정렬
    doc_score_pairs = list(zip(docs, scores))
    doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

    # 상위 K개 반환
    return [doc for doc, score in doc_score_pairs[:top_k]]

# 테스트
query = "What is machine learning?"
initial_docs = base_retriever.get_relevant_documents(query)
reranked_docs = rerank_documents(query, initial_docs, top_k=5)

print("After reranking:")
for i, doc in enumerate(reranked_docs, 1):
    print(f"[{i}] {doc.page_content[:100]}...")
```

### 2.2 LangChain 통합

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# Cross-encoder 모델
model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")

# Compressor로 래핑
compressor = CrossEncoderReranker(model=model, top_n=5)

# Compression Retriever
reranking_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever  # k=20으로 설정한 retriever
)

# 사용
docs = reranking_retriever.get_relevant_documents("What is machine learning?")
```

## Step 3: Cohere Rerank API

### 3.1 Cohere 직접 사용

```python
import cohere

os.environ["COHERE_API_KEY"] = "your-cohere-key"
co = cohere.Client(os.environ["COHERE_API_KEY"])

def cohere_rerank(query: str, docs: list, top_k: int = 5) -> list:
    """Cohere API로 리랭킹"""
    if not docs:
        return []

    # API 호출
    response = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=[doc.page_content for doc in docs],
        top_n=top_k,
        return_documents=False
    )

    # 결과 매핑
    reranked = []
    for result in response.results:
        reranked.append({
            "doc": docs[result.index],
            "score": result.relevance_score
        })

    return [item["doc"] for item in reranked]

# 테스트
docs = cohere_rerank(query, initial_docs, top_k=5)
```

### 3.2 LangChain + Cohere

```python
from langchain_cohere import CohereRerank

# Cohere Reranker
cohere_reranker = CohereRerank(
    model="rerank-english-v3.0",
    top_n=5
)

# Compression Retriever
cohere_retriever = ContextualCompressionRetriever(
    base_compressor=cohere_reranker,
    base_retriever=base_retriever
)

# 사용
docs = cohere_retriever.get_relevant_documents("What is machine learning?")
```

## Step 4: RAG 체인에 통합

```python
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt = ChatPromptTemplate.from_template("""
Answer based on the context. Cite sources using [1], [2], etc.

Context:
{context}

Question: {question}

Answer:
""")

def format_docs_with_index(docs):
    return "\n\n".join(
        f"[{i+1}] {doc.page_content}"
        for i, doc in enumerate(docs)
    )

# 리랭킹 포함 RAG 체인
advanced_rag_chain = (
    {
        "context": reranking_retriever | format_docs_with_index,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# 질문
answer = advanced_rag_chain.invoke("What is machine learning?")
print(answer)
```

## Step 5: 성능 비교

```python
def compare_retrieval(query: str, base_ret, rerank_ret):
    """기본 vs 리랭킹 비교"""
    print(f"Query: {query}\n")

    # 기본 검색
    print("=== Without Reranking ===")
    base_docs = base_ret.get_relevant_documents(query)[:5]
    for i, doc in enumerate(base_docs, 1):
        print(f"[{i}] {doc.page_content[:80]}...")

    print("\n=== With Reranking ===")
    rerank_docs = rerank_ret.get_relevant_documents(query)
    for i, doc in enumerate(rerank_docs, 1):
        print(f"[{i}] {doc.page_content[:80]}...")

# 비교
compare_retrieval(
    "What are the benefits of machine learning?",
    vectorstore.as_retriever(search_kwargs={"k": 5}),
    reranking_retriever
)
```

## Step 6: Oversampling 최적화

```python
def test_oversampling(query: str, factors: list = [2, 3, 5, 10]):
    """Oversampling factor 테스트"""
    results = {}

    for factor in factors:
        # 과다 검색
        base_ret = vectorstore.as_retriever(search_kwargs={"k": 5 * factor})

        # 리랭킹
        ret = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_ret
        )

        docs = ret.get_relevant_documents(query)
        results[factor] = docs

        print(f"\nFactor {factor}x (fetch {5*factor}, return 5):")
        print(f"Top result: {docs[0].page_content[:80]}...")

    return results

# 테스트
test_oversampling("What is deep learning?")
```

## 전체 코드

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
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

# 벡터 저장소
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(chunks, embeddings, location=":memory:", collection_name="docs")

# 리랭킹 Retriever
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})  # Oversample
model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
compressor = CrossEncoderReranker(model=model, top_n=5)
retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base_retriever)

# RAG 체인
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
prompt = ChatPromptTemplate.from_template("""
Answer based on context. Cite using [1], [2], etc.
Context: {context}
Question: {question}
Answer:
""")

def format_docs(docs):
    return "\n\n".join(f"[{i+1}] {d.page_content}" for i, d in enumerate(docs))

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# 사용
print(chain.invoke("What is machine learning?"))
```

## 다음 단계

- [Tutorial 03: 하이브리드 검색](03-hybrid-search.md)

## 체크리스트

- [ ] Cross-encoder 리랭킹 동작
- [ ] Cohere Rerank 연동 (선택)
- [ ] Oversampling 최적화
- [ ] RAG 체인 통합
- [ ] 품질 개선 확인
