# RAG Benchmark Scripts

RAG 시스템 품질 및 성능 측정을 위한 벤치마크 스크립트

## 개요

```
RAG 평가 = Retrieval 품질 + Generation 품질 + 성능 메트릭

┌─────────────────────────────────────────────────────────────┐
│                    Retrieval Metrics                         │
├─────────────────────────────────────────────────────────────┤
│  Recall@K  │  Precision@K  │  MRR  │  NDCG  │  Hit Rate    │
└─────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│                   Generation Metrics                         │
├─────────────────────────────────────────────────────────────┤
│  Faithfulness  │  Answer Relevancy  │  Context Recall       │
└─────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│                   Performance Metrics                        │
├─────────────────────────────────────────────────────────────┤
│  Latency (P50/P95/P99)  │  Throughput  │  Error Rate        │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Retrieval 메트릭 구현

### 설치

```bash
pip install numpy pandas
```

### 기본 메트릭 함수

```python
import numpy as np
from typing import List, Set, Dict

def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Recall@K: 상위 K개 중 관련 문서 비율

    Args:
        retrieved_ids: 검색된 문서 ID 리스트 (순서대로)
        relevant_ids: 정답 문서 ID 집합
        k: 상위 K개

    Returns:
        0.0 ~ 1.0
    """
    if not relevant_ids:
        return 0.0

    retrieved_at_k = set(retrieved_ids[:k])
    hits = len(retrieved_at_k & relevant_ids)
    return hits / len(relevant_ids)


def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Precision@K: 상위 K개 중 정확히 관련된 비율
    """
    if k == 0:
        return 0.0

    retrieved_at_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in retrieved_at_k if doc_id in relevant_ids)
    return hits / k


def mean_reciprocal_rank(results: List[Dict]) -> float:
    """
    MRR: 첫 번째 관련 문서의 순위 역수 평균

    Args:
        results: [{"retrieved": [...], "relevant_ids": {...}}, ...]
    """
    reciprocal_ranks = []

    for result in results:
        retrieved = result["retrieved"]
        relevant = set(result["relevant_ids"])

        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                reciprocal_ranks.append(1 / (i + 1))
                break
        else:
            reciprocal_ranks.append(0.0)

    return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0


def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    NDCG@K: Normalized Discounted Cumulative Gain

    관련성 점수를 순위에 따라 할인하여 계산
    """
    def dcg(relevances: List[int], k: int) -> float:
        relevances = relevances[:k]
        return sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances))

    # 실제 순위의 관련성 (0 또는 1)
    actual_relevances = [1 if doc_id in relevant_ids else 0 for doc_id in retrieved_ids[:k]]

    # 이상적인 순위 (모든 관련 문서가 먼저)
    ideal_relevances = sorted(actual_relevances, reverse=True)

    actual_dcg = dcg(actual_relevances, k)
    ideal_dcg = dcg(ideal_relevances, k)

    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def hit_rate(results: List[Dict], k: int = 10) -> float:
    """
    Hit Rate: 최소 1개의 관련 문서가 검색된 쿼리 비율
    """
    hits = 0
    for result in results:
        retrieved_at_k = set(result["retrieved"][:k])
        relevant = set(result["relevant_ids"])
        if retrieved_at_k & relevant:
            hits += 1
    return hits / len(results) if results else 0.0
```

### 종합 평가 클래스

```python
from dataclasses import dataclass
from typing import List, Dict, Set
import json

@dataclass
class RetrievalBenchmark:
    """Retrieval 평가 벤치마크"""

    def __init__(self, retriever, test_dataset: List[Dict]):
        """
        Args:
            retriever: 검색기 (get_relevant_documents 메서드 필요)
            test_dataset: [{"query": "...", "relevant_doc_ids": [...]}]
        """
        self.retriever = retriever
        self.test_dataset = test_dataset

    def run(self, k_values: List[int] = [1, 5, 10, 20]) -> Dict:
        """벤치마크 실행"""
        results = []

        for item in self.test_dataset:
            query = item["query"]
            relevant_ids = set(item["relevant_doc_ids"])

            # 검색 실행
            docs = self.retriever.get_relevant_documents(query)
            retrieved_ids = [doc.metadata.get("id", str(i)) for i, doc in enumerate(docs)]

            results.append({
                "query": query,
                "retrieved": retrieved_ids,
                "relevant_ids": relevant_ids
            })

        # 메트릭 계산
        metrics = {}
        for k in k_values:
            metrics[f"recall@{k}"] = np.mean([
                recall_at_k(r["retrieved"], r["relevant_ids"], k) for r in results
            ])
            metrics[f"precision@{k}"] = np.mean([
                precision_at_k(r["retrieved"], r["relevant_ids"], k) for r in results
            ])
            metrics[f"ndcg@{k}"] = np.mean([
                ndcg_at_k(r["retrieved"], r["relevant_ids"], k) for r in results
            ])

        metrics["mrr"] = mean_reciprocal_rank(results)
        metrics["hit_rate@10"] = hit_rate(results, k=10)

        return {
            "metrics": metrics,
            "num_queries": len(results),
            "detailed_results": results
        }


# 사용 예시
if __name__ == "__main__":
    # 테스트 데이터셋
    test_data = [
        {"query": "What is machine learning?", "relevant_doc_ids": ["doc1", "doc5", "doc12"]},
        {"query": "How does RAG work?", "relevant_doc_ids": ["doc3", "doc7"]},
        # ...
    ]

    benchmark = RetrievalBenchmark(retriever, test_data)
    results = benchmark.run()

    print("=== Retrieval Metrics ===")
    for metric, value in results["metrics"].items():
        print(f"  {metric}: {value:.4f}")
```

---

## 2. RAGAS 평가

### 설치

```bash
pip install ragas datasets
```

### RAGAS 평가 실행

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
    answer_correctness
)
from datasets import Dataset

def prepare_ragas_dataset(test_cases: List[Dict]) -> Dataset:
    """
    RAGAS 데이터셋 준비

    Args:
        test_cases: [{
            "question": "...",
            "answer": "...",  # RAG 시스템 응답
            "contexts": ["...", "..."],  # 검색된 컨텍스트
            "ground_truth": "..."  # 정답 (선택)
        }]
    """
    return Dataset.from_dict({
        "question": [tc["question"] for tc in test_cases],
        "answer": [tc["answer"] for tc in test_cases],
        "contexts": [tc["contexts"] for tc in test_cases],
        "ground_truth": [tc.get("ground_truth", "") for tc in test_cases]
    })


def run_ragas_evaluation(rag_chain, test_questions: List[Dict]) -> Dict:
    """
    RAGAS 평가 실행

    Args:
        rag_chain: RAG 체인
        test_questions: [{"question": "...", "ground_truth": "..."}]
    """
    test_cases = []

    for item in test_questions:
        question = item["question"]

        # RAG 실행
        result = rag_chain.invoke(question)

        # 결과 수집
        test_cases.append({
            "question": question,
            "answer": result["answer"],
            "contexts": [doc.page_content for doc in result["source_documents"]],
            "ground_truth": item.get("ground_truth", "")
        })

    # 데이터셋 준비
    dataset = prepare_ragas_dataset(test_cases)

    # 평가 실행
    metrics = [
        faithfulness,      # 답변이 컨텍스트에 기반하는지
        answer_relevancy,  # 답변이 질문에 관련되는지
        context_recall,    # 필요한 정보가 검색되었는지
        context_precision  # 검색된 정보가 관련 있는지
    ]

    # ground_truth가 있으면 correctness도 평가
    if all(tc.get("ground_truth") for tc in test_cases):
        metrics.append(answer_correctness)

    results = evaluate(dataset, metrics=metrics)

    return {
        "faithfulness": results["faithfulness"],
        "answer_relevancy": results["answer_relevancy"],
        "context_recall": results["context_recall"],
        "context_precision": results["context_precision"],
        "answer_correctness": results.get("answer_correctness", None)
    }


# 사용 예시
test_questions = [
    {
        "question": "What is the capital of France?",
        "ground_truth": "Paris is the capital of France."
    },
    {
        "question": "How does photosynthesis work?",
        "ground_truth": "Photosynthesis converts light energy into chemical energy."
    }
]

ragas_results = run_ragas_evaluation(rag_chain, test_questions)
print("=== RAGAS Metrics ===")
for metric, score in ragas_results.items():
    if score is not None:
        print(f"  {metric}: {score:.4f}")
```

---

## 3. 지연시간 벤치마크

```python
import time
import statistics
from typing import Callable, List, Dict
from dataclasses import dataclass
import asyncio

@dataclass
class LatencyBenchmark:
    """지연시간 벤치마크"""

    def __init__(self):
        self.results = {
            "embedding": [],
            "retrieval": [],
            "reranking": [],
            "generation": [],
            "total": []
        }

    def measure(self, func: Callable, component: str):
        """단일 호출 측정"""
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        self.results[component].append(elapsed * 1000)  # ms
        return result

    def calculate_percentiles(self, data: List[float]) -> Dict:
        """백분위수 계산"""
        if not data:
            return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "min": 0, "max": 0}

        sorted_data = sorted(data)
        n = len(sorted_data)

        return {
            "p50": sorted_data[int(n * 0.5)],
            "p95": sorted_data[int(n * 0.95)] if n >= 20 else sorted_data[-1],
            "p99": sorted_data[int(n * 0.99)] if n >= 100 else sorted_data[-1],
            "mean": statistics.mean(data),
            "min": min(data),
            "max": max(data)
        }

    def report(self) -> Dict:
        """벤치마크 결과 리포트"""
        report = {}
        for component, latencies in self.results.items():
            if latencies:
                report[component] = self.calculate_percentiles(latencies)
        return report


def run_latency_benchmark(
    rag_pipeline,
    test_queries: List[str],
    num_iterations: int = 100
) -> Dict:
    """
    RAG 파이프라인 지연시간 벤치마크

    Args:
        rag_pipeline: RAG 파이프라인 (embed, retrieve, rerank, generate 메서드)
        test_queries: 테스트 쿼리 목록
        num_iterations: 반복 횟수
    """
    benchmark = LatencyBenchmark()

    for _ in range(num_iterations):
        query = test_queries[_ % len(test_queries)]

        total_start = time.perf_counter()

        # 1. Embedding
        query_vector = benchmark.measure(
            lambda: rag_pipeline.embed(query),
            "embedding"
        )

        # 2. Retrieval
        docs = benchmark.measure(
            lambda: rag_pipeline.retrieve(query_vector),
            "retrieval"
        )

        # 3. Reranking (optional)
        if hasattr(rag_pipeline, 'rerank'):
            reranked = benchmark.measure(
                lambda: rag_pipeline.rerank(query, docs),
                "reranking"
            )
        else:
            reranked = docs

        # 4. Generation
        answer = benchmark.measure(
            lambda: rag_pipeline.generate(query, reranked),
            "generation"
        )

        total_elapsed = (time.perf_counter() - total_start) * 1000
        benchmark.results["total"].append(total_elapsed)

    return benchmark.report()


# 사용 예시
class RAGPipeline:
    def embed(self, query):
        return embeddings.embed_query(query)

    def retrieve(self, vector):
        return vectorstore.similarity_search_by_vector(vector, k=10)

    def rerank(self, query, docs):
        return reranker.rerank(query, docs)[:5]

    def generate(self, query, docs):
        context = "\n".join(d.page_content for d in docs)
        return llm.invoke(f"Context: {context}\nQuestion: {query}")


pipeline = RAGPipeline()
test_queries = ["What is AI?", "How does ML work?", "Explain RAG"]

latency_report = run_latency_benchmark(pipeline, test_queries, num_iterations=50)

print("=== Latency Benchmark (ms) ===")
for component, stats in latency_report.items():
    print(f"\n{component}:")
    print(f"  P50: {stats['p50']:.2f}ms")
    print(f"  P95: {stats['p95']:.2f}ms")
    print(f"  P99: {stats['p99']:.2f}ms")
```

---

## 4. 부하 테스트 (Locust)

### 설치

```bash
pip install locust
```

### locustfile.py

```python
from locust import HttpUser, task, between
import json

class RAGUser(HttpUser):
    """RAG API 부하 테스트 사용자"""

    wait_time = between(1, 3)  # 요청 간 대기 시간

    test_queries = [
        "What is machine learning?",
        "How does deep learning work?",
        "Explain neural networks",
        "What is RAG?",
        "How to optimize vector search?"
    ]

    @task(10)
    def query_rag(self):
        """일반 RAG 쿼리"""
        query = self.test_queries[self.environment.runner.user_count % len(self.test_queries)]

        response = self.client.post(
            "/api/query",
            json={"question": query},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            # 응답 검증
            assert "answer" in data

    @task(1)
    def health_check(self):
        """헬스 체크"""
        self.client.get("/health")


# 실행:
# locust -f locustfile.py --host=http://localhost:8000
```

### 커스텀 리포터

```python
import time
from collections import defaultdict

class LoadTestReporter:
    """부하 테스트 결과 수집"""

    def __init__(self):
        self.requests = []
        self.errors = defaultdict(int)

    def record(self, endpoint: str, latency_ms: float, success: bool, error: str = None):
        self.requests.append({
            "timestamp": time.time(),
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "success": success
        })
        if not success:
            self.errors[error or "unknown"] += 1

    def summary(self) -> Dict:
        if not self.requests:
            return {}

        latencies = [r["latency_ms"] for r in self.requests]
        successes = [r for r in self.requests if r["success"]]

        return {
            "total_requests": len(self.requests),
            "successful_requests": len(successes),
            "error_rate": 1 - len(successes) / len(self.requests),
            "throughput_rps": len(self.requests) / (self.requests[-1]["timestamp"] - self.requests[0]["timestamp"]),
            "latency": {
                "p50": sorted(latencies)[len(latencies) // 2],
                "p95": sorted(latencies)[int(len(latencies) * 0.95)],
                "p99": sorted(latencies)[int(len(latencies) * 0.99)],
                "mean": sum(latencies) / len(latencies)
            },
            "errors": dict(self.errors)
        }
```

---

## 5. 종합 벤치마크 스크립트

```python
#!/usr/bin/env python3
"""RAG 시스템 종합 벤치마크"""

import argparse
import json
from datetime import datetime

def run_full_benchmark(
    rag_chain,
    retriever,
    test_dataset_path: str,
    output_path: str
):
    """종합 벤치마크 실행"""

    # 테스트 데이터 로드
    with open(test_dataset_path) as f:
        test_data = json.load(f)

    results = {
        "timestamp": datetime.now().isoformat(),
        "num_test_cases": len(test_data),
        "metrics": {}
    }

    # 1. Retrieval 메트릭
    print("Running retrieval benchmark...")
    retrieval_benchmark = RetrievalBenchmark(retriever, test_data)
    retrieval_results = retrieval_benchmark.run()
    results["metrics"]["retrieval"] = retrieval_results["metrics"]

    # 2. RAGAS 평가
    print("Running RAGAS evaluation...")
    ragas_results = run_ragas_evaluation(rag_chain, test_data[:20])  # 샘플
    results["metrics"]["ragas"] = ragas_results

    # 3. 지연시간 벤치마크
    print("Running latency benchmark...")
    latency_results = run_latency_benchmark(
        pipeline,
        [item["query"] for item in test_data],
        num_iterations=50
    )
    results["metrics"]["latency"] = latency_results

    # 결과 저장
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")

    # 요약 출력
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)

    print("\nRetrieval:")
    print(f"  Recall@10: {results['metrics']['retrieval']['recall@10']:.4f}")
    print(f"  MRR: {results['metrics']['retrieval']['mrr']:.4f}")

    print("\nRAGAS:")
    print(f"  Faithfulness: {results['metrics']['ragas']['faithfulness']:.4f}")
    print(f"  Answer Relevancy: {results['metrics']['ragas']['answer_relevancy']:.4f}")

    print("\nLatency (total):")
    print(f"  P50: {results['metrics']['latency']['total']['p50']:.0f}ms")
    print(f"  P95: {results['metrics']['latency']['total']['p95']:.0f}ms")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Benchmark")
    parser.add_argument("--test-data", required=True, help="Test dataset JSON file")
    parser.add_argument("--output", default="benchmark_results.json", help="Output file")
    args = parser.parse_args()

    # RAG 컴포넌트 초기화
    # rag_chain = ...
    # retriever = ...
    # pipeline = ...

    run_full_benchmark(rag_chain, retriever, args.test_data, args.output)
```

---

## 테스트 데이터셋 예시

```json
[
  {
    "query": "What is machine learning?",
    "relevant_doc_ids": ["ml_intro_1", "ml_basics_3"],
    "ground_truth": "Machine learning is a subset of AI that enables systems to learn from data."
  },
  {
    "query": "How does RAG improve LLM responses?",
    "relevant_doc_ids": ["rag_overview", "rag_benefits"],
    "ground_truth": "RAG improves LLM responses by grounding them in retrieved relevant documents."
  }
]
```

---

## 메트릭 해석 가이드

| 메트릭 | 좋음 | 보통 | 개선 필요 |
|--------|-----|------|---------|
| Recall@10 | > 0.9 | 0.7-0.9 | < 0.7 |
| MRR | > 0.8 | 0.5-0.8 | < 0.5 |
| Faithfulness | > 0.9 | 0.7-0.9 | < 0.7 |
| Answer Relevancy | > 0.85 | 0.7-0.85 | < 0.7 |
| P95 Latency | < 2s | 2-5s | > 5s |
| Error Rate | < 1% | 1-5% | > 5% |
