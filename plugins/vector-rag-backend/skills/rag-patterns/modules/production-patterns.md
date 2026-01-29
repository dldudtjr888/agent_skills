# Production Patterns

프로덕션 RAG 시스템을 위한 에러 핸들링, 복원력, 안정성 패턴

## 핵심 원칙

```
프로덕션 RAG = 기본 RAG + 복원력 계층

┌─────────────────────────────────────────┐
│           Rate Limiting                  │
├─────────────────────────────────────────┤
│         Circuit Breaker                  │
├─────────────────────────────────────────┤
│      Retry with Backoff                  │
├─────────────────────────────────────────┤
│          Fallbacks                       │
├─────────────────────────────────────────┤
│        Core RAG Pipeline                 │
└─────────────────────────────────────────┘
```

---

## 1. 에러 핸들링 전략

### 예외 분류

| 예외 유형 | 예시 | 전략 |
|----------|------|------|
| **Transient** | 5xx, 타임아웃, 네트워크 오류 | 재시도 |
| **Rate Limit** | 429 Too Many Requests | Backoff 후 재시도 |
| **Client Error** | 400, 401, 403 | 즉시 실패 |
| **Resource** | OOM, 디스크 풀 | 알림 + 폴백 |

### LangChain 에러 핸들링

```python
from langchain_core.runnables import RunnableConfig
from langchain.callbacks import get_openai_callback

def handle_rag_query(query: str, chain, config: RunnableConfig = None):
    """구조화된 에러 핸들링으로 RAG 쿼리 실행"""
    try:
        with get_openai_callback() as cb:
            result = chain.invoke(query, config=config)
            return {
                "success": True,
                "result": result,
                "tokens": cb.total_tokens,
                "cost": cb.total_cost
            }
    except openai.RateLimitError as e:
        # 429 - 백오프 후 재시도 권장
        return {"success": False, "error": "rate_limit", "retry_after": 60}
    except openai.APIConnectionError as e:
        # 네트워크 오류 - 재시도 가능
        return {"success": False, "error": "connection", "retryable": True}
    except openai.BadRequestError as e:
        # 400 - 입력 문제, 재시도 불가
        return {"success": False, "error": "bad_request", "retryable": False}
    except Exception as e:
        # 예상치 못한 오류
        return {"success": False, "error": "unknown", "message": str(e)}
```

---

## 2. Retry 패턴

### Tenacity 라이브러리

```bash
pip install tenacity
```

### 기본 재시도

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def embed_documents(texts: list[str], embeddings):
    """재시도 로직이 포함된 임베딩 함수"""
    return embeddings.embed_documents(texts)
```

### Jitter 추가 (권장)

```python
from tenacity import wait_exponential_jitter

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
)
def query_vector_db(query_vector, collection):
    """Jitter로 동시 재시도 폭주 방지"""
    return collection.search(query_vector, limit=10)
```

### LangChain RunnableRetry

```python
from langchain_core.runnables.retry import RunnableRetry

# Runnable에 재시도 추가
retriever_with_retry = RunnableRetry(
    bound=retriever,
    retry_exception_types=(ConnectionError, TimeoutError),
    max_attempt_number=3,
    wait_exponential_jitter=True
)

# 또는 .with_retry() 메서드 사용
chain_with_retry = chain.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True
)
```

### 재시도 범위 최소화

```python
# BAD: 전체 체인 재시도
@retry(stop=stop_after_attempt(3))
def full_rag_pipeline(query):
    docs = retriever.get_relevant_documents(query)  # 이미 성공했을 수 있음
    reranked = reranker.rerank(query, docs)         # 이미 성공했을 수 있음
    return llm.generate(query, reranked)            # 여기서만 실패

# GOOD: 실패 가능 부분만 재시도
def full_rag_pipeline(query):
    docs = retriever_with_retry.get_relevant_documents(query)
    reranked = reranker_with_retry.rerank(query, docs)
    return llm_with_retry.generate(query, reranked)
```

---

## 3. Circuit Breaker 패턴

### 개념

```
Closed (정상) ──[실패 임계치 도달]──▶ Open (차단)
     ▲                                    │
     │                            [복구 타임아웃]
     │                                    ▼
     └────[테스트 성공]───── Half-Open (테스트)
```

### circuitbreaker 라이브러리

```bash
pip install circuitbreaker
```

```python
from circuitbreaker import circuit, CircuitBreakerError

@circuit(
    failure_threshold=5,      # 5회 실패 시 차단
    recovery_timeout=30,      # 30초 후 Half-Open
    expected_exception=Exception
)
def call_embedding_api(texts: list[str]):
    """Circuit Breaker가 적용된 임베딩 호출"""
    return openai_embeddings.embed_documents(texts)

# 사용
try:
    embeddings = call_embedding_api(texts)
except CircuitBreakerError:
    # 서킷이 열림 - 폴백 사용
    embeddings = local_embeddings.embed_documents(texts)
```

### PyBreaker (고급)

```bash
pip install pybreaker
```

```python
import pybreaker

# 서킷 브레이커 인스턴스 (공유 가능)
embedding_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    state_storage=pybreaker.CircuitRedisStorage(
        pybreaker.CircuitBreakerState.CLOSED,
        redis_object,
        namespace='embedding_api'
    )  # 분산 환경에서 상태 공유
)

@embedding_breaker
def call_embedding_api(texts):
    return openai_embeddings.embed_documents(texts)

# 리스너로 모니터링
class CircuitBreakerMonitor(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        logger.warning(f"Circuit {cb.name}: {old_state.name} -> {new_state.name}")
        metrics.circuit_state_change(cb.name, new_state.name)

embedding_breaker.add_listener(CircuitBreakerMonitor())
```

### Circuit Breaker + Retry 조합

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from circuitbreaker import circuit

# Circuit Breaker를 바깥에 배치
@circuit(failure_threshold=5, recovery_timeout=30)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def resilient_embedding(texts: list[str]):
    """
    동작 순서:
    1. Circuit이 Closed면 진행
    2. 실패 시 최대 3회 재시도 (exponential backoff)
    3. 3회 모두 실패하면 Circuit에 실패 기록
    4. 5회 실패 누적 시 Circuit Open
    """
    return embeddings.embed_documents(texts)
```

---

## 4. Fallback 패턴

### LangChain Fallbacks

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama

# LLM 폴백 체인
primary_llm = ChatOpenAI(model="gpt-4o", timeout=30)
backup_llm = ChatAnthropic(model="claude-3-sonnet-20240229")
local_llm = Ollama(model="llama3.1")

llm_with_fallbacks = primary_llm.with_fallbacks([backup_llm, local_llm])

# Retriever 폴백
from langchain_community.retrievers import BM25Retriever

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
bm25_retriever = BM25Retriever.from_documents(documents, k=10)

retriever_with_fallback = vector_retriever.with_fallbacks([bm25_retriever])
```

### 커스텀 폴백 로직

```python
from typing import Optional, List
from langchain.schema import Document

class ResilientRetriever:
    def __init__(self, primary, fallbacks: List, cache=None):
        self.primary = primary
        self.fallbacks = fallbacks
        self.cache = cache

    def get_relevant_documents(self, query: str) -> List[Document]:
        # 1. 캐시 확인
        if self.cache:
            cached = self.cache.get(query)
            if cached:
                return cached

        # 2. Primary 시도
        try:
            docs = self.primary.get_relevant_documents(query)
            if docs:
                if self.cache:
                    self.cache.set(query, docs)
                return docs
        except Exception as e:
            logger.warning(f"Primary retriever failed: {e}")

        # 3. Fallbacks 순차 시도
        for i, fallback in enumerate(self.fallbacks):
            try:
                docs = fallback.get_relevant_documents(query)
                if docs:
                    logger.info(f"Fallback {i} succeeded")
                    return docs
            except Exception as e:
                logger.warning(f"Fallback {i} failed: {e}")

        # 4. 모두 실패
        logger.error("All retrievers failed")
        return []
```

### 검색 실패 시 응답 전략

```python
def generate_with_fallback(query: str, retriever, llm):
    """검색 실패 시에도 적절한 응답 생성"""
    docs = retriever.get_relevant_documents(query)

    if not docs:
        # 검색 결과 없음 - 솔직하게 응답
        return {
            "answer": "죄송합니다. 관련 정보를 찾지 못했습니다. "
                      "다른 방식으로 질문해 주시거나, 더 구체적인 키워드를 사용해 주세요.",
            "source": "no_retrieval",
            "confidence": 0.0
        }

    # 정상 RAG 응답
    answer = llm.generate(query, docs)
    return {
        "answer": answer,
        "source": "rag",
        "confidence": 0.9,
        "sources": [doc.metadata.get("source") for doc in docs]
    }
```

---

## 5. Rate Limiting

### 클라이언트 측 Rate Limiting

```python
import asyncio
from asyncio import Semaphore
from collections import deque
import time

class RateLimiter:
    """토큰 버킷 기반 Rate Limiter"""

    def __init__(self, rate: float, burst: int = 1):
        self.rate = rate  # 초당 요청 수
        self.burst = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            wait_time = (1 - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self.tokens = 0
            return True

# 사용
rate_limiter = RateLimiter(rate=10, burst=20)  # 초당 10요청, 버스트 20

async def rate_limited_embed(texts):
    await rate_limiter.acquire()
    return await embeddings.aembed_documents(texts)
```

### Semaphore로 동시성 제한

```python
from asyncio import Semaphore

# 동시 요청 제한
embedding_semaphore = Semaphore(5)  # 최대 5개 동시 요청
llm_semaphore = Semaphore(3)        # 최대 3개 동시 요청

async def controlled_embed(texts):
    async with embedding_semaphore:
        return await embeddings.aembed_documents(texts)

async def controlled_generate(prompt):
    async with llm_semaphore:
        return await llm.agenerate(prompt)
```

### 배치 처리로 Rate Limit 회피

```python
import asyncio
from typing import List

async def batch_embed_with_delay(
    texts: List[str],
    batch_size: int = 100,
    delay_between_batches: float = 1.0
):
    """배치 처리로 Rate Limit 회피"""
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = await embeddings.aembed_documents(batch)
        all_embeddings.extend(embeddings)

        # 마지막 배치가 아니면 대기
        if i + batch_size < len(texts):
            await asyncio.sleep(delay_between_batches)

    return all_embeddings
```

---

## 6. 통합 예제: 프로덕션 RAG 체인

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from circuitbreaker import circuit
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Qdrant
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
import logging

logger = logging.getLogger(__name__)

# === 복원력 레이어 ===

@circuit(failure_threshold=5, recovery_timeout=30)
@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=30))
def resilient_search(retriever, query: str):
    return retriever.get_relevant_documents(query)

# === 컴포넌트 설정 ===

# Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    timeout=30,
    max_retries=2  # 내장 재시도
)

# Vector Store
vectorstore = Qdrant.from_documents(
    documents, embeddings,
    url="http://localhost:6333",
    collection_name="production_docs"
)

# Retriever with retry
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# LLM with fallbacks
primary_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    timeout=60,
    max_retries=2
)
backup_llm = ChatAnthropic(model="claude-3-haiku-20240307")
llm = primary_llm.with_fallbacks([backup_llm])

# === RAG 체인 ===

prompt = ChatPromptTemplate.from_template("""
Answer based on the context. If unsure, say "I don't know."

Context: {context}
Question: {question}
Answer:
""")

def safe_retrieve(query: str):
    try:
        docs = resilient_search(base_retriever, query)
        return "\n\n".join(doc.page_content for doc in docs)
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return "No context available."

production_rag_chain = (
    {"context": safe_retrieve, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# === 사용 ===

def query_with_monitoring(question: str):
    """모니터링 포함 쿼리"""
    import time

    start = time.time()
    try:
        answer = production_rag_chain.invoke(question)
        latency = time.time() - start

        # 메트릭 기록
        logger.info(f"Query succeeded in {latency:.2f}s")

        return {
            "success": True,
            "answer": answer,
            "latency_ms": latency * 1000
        }
    except Exception as e:
        latency = time.time() - start
        logger.error(f"Query failed after {latency:.2f}s: {e}")

        return {
            "success": False,
            "error": str(e),
            "latency_ms": latency * 1000
        }

# 실행
result = query_with_monitoring("What is machine learning?")
print(result)
```

---

## 체크리스트

### 필수
- [ ] 모든 외부 API 호출에 타임아웃 설정
- [ ] Transient 에러에 재시도 로직 적용
- [ ] Critical 컴포넌트에 Circuit Breaker 적용
- [ ] 검색 실패 시 적절한 폴백 응답

### 권장
- [ ] Rate Limiter로 API 비용 제어
- [ ] 배치 처리로 처리량 최적화
- [ ] 에러 로깅 및 알림 설정
- [ ] 메트릭 수집 (latency, error rate, circuit state)

### 고급
- [ ] 분산 환경 Circuit Breaker (Redis 상태 공유)
- [ ] 적응형 Rate Limiting
- [ ] Chaos Engineering 테스트
