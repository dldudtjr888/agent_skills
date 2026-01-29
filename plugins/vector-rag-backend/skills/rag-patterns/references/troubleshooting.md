# RAG Troubleshooting Guide

RAG 시스템 문제 해결 가이드

## 빠른 진단 체크리스트

```
문제 발생 시 확인 순서:
1. 검색 결과 확인 → 검색 품질 문제?
2. 컨텍스트 확인 → 관련 정보 포함?
3. 프롬프트 확인 → LLM에 올바르게 전달?
4. 응답 확인 → 환각? 누락?
```

---

## 검색 품질 문제

### 증상: 관련 없는 문서가 검색됨

**원인 1: 잘못된 청킹**
```python
# 진단
for chunk in chunks[:5]:
    print(f"Length: {len(chunk)}, Preview: {chunk[:100]}")

# 해결: 시맨틱 청킹 적용
from langchain_experimental.text_splitter import SemanticChunker
chunker = SemanticChunker(embeddings, breakpoint_threshold_amount=95)
```

**원인 2: 임베딩 모델 불일치**
```python
# 진단: 쿼리와 문서의 임베딩 모델이 같은지 확인
# 쿼리: OpenAI embeddings
# 문서: Local BGE embeddings  ← 불일치!

# 해결: 동일한 모델 사용
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
# 쿼리와 문서 모두 같은 embeddings 객체 사용
```

**원인 3: 거리 메트릭 불일치**
```python
# 진단
collection_info = client.get_collection("docs")
print(f"Distance: {collection_info.config.params.vectors.distance}")

# 텍스트 임베딩에 Euclidean 사용 중이면 문제
# 해결: Cosine으로 재생성
client.recreate_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)
```

### 증상: 검색 결과가 0개

**원인 1: 필터 조건 너무 엄격**
```python
# 진단: 필터 없이 검색
results_no_filter = client.search(query_vector=emb, limit=10)
print(f"Without filter: {len(results_no_filter)}")

results_with_filter = client.search(query_vector=emb, query_filter=filter, limit=10)
print(f"With filter: {len(results_with_filter)}")

# 해결: 필터 조건 완화 또는 제거
```

**원인 2: 인덱스 미완성**
```python
# 진단
info = client.get_collection("docs")
print(f"Points: {info.points_count}")
print(f"Indexed: {info.indexed_vectors_count}")

# indexed_vectors_count < points_count 면 인덱싱 진행 중
# 해결: 인덱싱 완료 대기 또는 force indexing
```

**원인 3: 컬렉션이 비어있음**
```python
# 진단
info = client.get_collection("docs")
if info.points_count == 0:
    print("Collection is empty!")
    # 데이터 로딩 확인
```

### 증상: 검색 속도가 느림

**원인 1: 양자화 미적용**
```python
# 진단
info = client.get_collection("docs")
print(f"Quantization: {info.config.quantization_config}")

# 해결: 양자화 적용
client.update_collection(
    collection_name="docs",
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(type="int8", always_ram=True)
    )
)
```

**원인 2: 필터 인덱스 없음**
```python
# 진단: 필터 쿼리 시간 측정
import time
start = time.time()
results = client.search(..., query_filter=filter)
print(f"Time: {time.time() - start:.3f}s")

# 1초 이상이면 인덱스 없을 가능성
# 해결: 필터 필드 인덱싱
client.create_payload_index(
    collection_name="docs",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)
```

**원인 3: hnsw_ef가 너무 높음**
```python
# 해결: 검색 시 ef 낮추기
results = client.search(
    ...,
    search_params=SearchParams(hnsw_ef=64)  # 기본 128 → 64
)
```

---

## 생성 품질 문제

### 증상: 환각 (Hallucination)

**원인 1: 컨텍스트에 정보 없음**
```python
# 진단: 검색된 컨텍스트 확인
docs = retriever.get_relevant_documents(question)
for doc in docs:
    print(f"Content: {doc.page_content[:200]}")
    print(f"Source: {doc.metadata.get('source')}")
    print("---")

# 해결: 검색 개선 (리랭킹, 하이브리드)
```

**원인 2: 프롬프트에 컨텍스트 강조 부족**
```python
# BAD
prompt = f"Answer: {question}\nContext: {context}"

# GOOD
prompt = f"""Answer the question based ONLY on the following context.
If the answer is not in the context, say "I don't know."

Context:
{context}

Question: {question}

Answer:"""
```

**원인 3: Temperature 너무 높음**
```python
# 해결: 팩트 기반 응답은 낮은 temperature
llm = ChatOpenAI(model="gpt-4", temperature=0)  # 0 또는 0.1
```

### 증상: 답변이 너무 짧거나 불완전

**원인 1: 컨텍스트 부족**
```python
# 해결: 검색 수 증가
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})  # 5 → 10
```

**원인 2: 컨텍스트 잘림**
```python
# 진단: 토큰 수 확인
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")
context_tokens = len(enc.encode(context))
print(f"Context tokens: {context_tokens}")

# 해결: 토큰 한도 내로 조정
MAX_CONTEXT_TOKENS = 6000
if context_tokens > MAX_CONTEXT_TOKENS:
    # 컨텍스트 압축 또는 청크 수 줄이기
```

**원인 3: 프롬프트에 상세 응답 요청 없음**
```python
# 해결: 명시적 요청
prompt = """...
Provide a detailed answer with examples if available.
Include relevant quotes from the context.
"""
```

### 증상: 답변이 컨텍스트를 인용하지 않음

**원인: Citation 지시 없음**
```python
# 해결: Citation 명시
prompt = """Answer using ONLY the provided sources.
Cite sources using [1], [2], etc.

Sources:
[1] {source1}
[2] {source2}

Question: {question}

Answer (with citations):"""
```

---

## 성능 문제

### 증상: 메모리 부족 (OOM)

**원인 1: 벡터가 모두 RAM에**
```python
# 해결: 디스크 저장
client.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=True  # 벡터 디스크 저장
    ),
    hnsw_config=HnswConfigDiff(on_disk=True)  # 인덱스도 디스크
)
```

**원인 2: 양자화 미적용**
```python
# 해결: int8 양자화 (메모리 75% 절감)
quantization_config=ScalarQuantization(
    scalar=ScalarQuantizationConfig(type="int8", always_ram=True)
)
```

**원인 3: 배치 크기 너무 큼**
```python
# BAD: 한 번에 10만 개
client.upsert(collection_name="docs", points=all_100k_points)

# GOOD: 배치로 나눠서
BATCH_SIZE = 1000
for i in range(0, len(points), BATCH_SIZE):
    batch = points[i:i+BATCH_SIZE]
    client.upsert(collection_name="docs", points=batch)
```

### 증상: API 비용이 너무 높음

**원인 1: 임베딩 재계산**
```python
# 해결: 캐싱 적용
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

store = LocalFileStore("./embedding_cache")
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    embeddings, store, namespace="docs"
)
```

**원인 2: 불필요한 LLM 호출**
```python
# 해결: 응답 캐싱
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_rag_query(question: str) -> str:
    return rag_chain.invoke(question)
```

**원인 3: 로컬 모델로 대체 가능**
```python
# 해결: 로컬 임베딩
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-base-en-v1.5")  # 무료

# 해결: 로컬 리랭커
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-base")  # 무료
```

---

## 디버깅 도구

### 검색 결과 시각화

```python
def debug_retrieval(query: str, retriever, top_k: int = 5):
    """검색 결과 디버깅"""
    docs = retriever.get_relevant_documents(query)[:top_k]

    print(f"Query: {query}")
    print(f"Results: {len(docs)}")
    print("-" * 50)

    for i, doc in enumerate(docs, 1):
        print(f"\n[{i}] Score: {doc.metadata.get('score', 'N/A')}")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content: {doc.page_content[:200]}...")
```

### RAG 파이프라인 프로파일링

```python
import time

def profile_rag(query: str, rag_chain) -> dict:
    """RAG 파이프라인 시간 측정"""
    timings = {}

    # Retrieval
    start = time.perf_counter()
    docs = retriever.get_relevant_documents(query)
    timings["retrieval"] = time.perf_counter() - start

    # Generation
    start = time.perf_counter()
    response = rag_chain.invoke(query)
    timings["generation"] = time.perf_counter() - start

    timings["total"] = sum(timings.values())

    print(f"Retrieval: {timings['retrieval']:.3f}s")
    print(f"Generation: {timings['generation']:.3f}s")
    print(f"Total: {timings['total']:.3f}s")

    return timings
```

### 컨텍스트 품질 검증

```python
def validate_context(question: str, contexts: list, llm) -> dict:
    """컨텍스트가 질문에 답할 수 있는지 검증"""
    prompt = f"""
    Question: {question}

    Contexts:
    {chr(10).join([f'[{i+1}] {c}' for i, c in enumerate(contexts)])}

    Can these contexts answer the question? Rate 1-5.
    Which context is most relevant? (number)

    Response format:
    Score: X/5
    Most relevant: [number]
    Reason: ...
    """

    response = llm.invoke(prompt)
    return {"validation": response.content}
```

---

## 에러 메시지별 해결

| 에러 | 원인 | 해결 |
|------|------|------|
| `Collection not found` | 컬렉션 미생성 | `client.create_collection(...)` |
| `Vector dimension mismatch` | 임베딩 차원 불일치 | 모델 확인, 컬렉션 재생성 |
| `Rate limit exceeded` | API 한도 초과 | 배치 크기 줄이기, 딜레이 추가 |
| `Context length exceeded` | 토큰 초과 | 청크 크기 줄이기, 요약 |
| `Out of memory` | RAM 부족 | 양자화, 디스크 저장 |
| `Timeout` | 쿼리 너무 느림 | 인덱스 확인, k 줄이기 |
