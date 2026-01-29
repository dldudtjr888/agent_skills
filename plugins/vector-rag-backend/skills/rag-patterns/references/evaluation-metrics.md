# RAG Evaluation Metrics

RAG 시스템 품질 측정 메트릭 가이드

## 메트릭 분류

```
RAG Evaluation
├── Retrieval Metrics (검색 품질)
│   ├── Recall@K
│   ├── Precision@K
│   ├── MRR
│   └── NDCG
├── Generation Metrics (생성 품질)
│   ├── Faithfulness
│   ├── Answer Relevance
│   └── Fluency
└── End-to-End Metrics (전체 품질)
    ├── Answer Correctness
    └── Context Utilization
```

## Retrieval Metrics

### Recall@K

K개 검색 결과 중 관련 문서 비율.

```python
def recall_at_k(retrieved: list, relevant: set, k: int) -> float:
    """
    Recall@K = |relevant ∩ retrieved[:k]| / |relevant|
    """
    retrieved_k = set(retrieved[:k])
    return len(relevant & retrieved_k) / len(relevant)

# 예시
relevant_docs = {"doc1", "doc2", "doc3"}
retrieved_docs = ["doc1", "doc4", "doc2", "doc5", "doc3"]
print(recall_at_k(retrieved_docs, relevant_docs, k=3))  # 0.67
print(recall_at_k(retrieved_docs, relevant_docs, k=5))  # 1.0
```

**목표:**
- RAG 시스템: Recall@10 > 0.9

### Precision@K

K개 검색 결과의 정확도.

```python
def precision_at_k(retrieved: list, relevant: set, k: int) -> float:
    """
    Precision@K = |relevant ∩ retrieved[:k]| / k
    """
    retrieved_k = set(retrieved[:k])
    return len(relevant & retrieved_k) / k

# 예시
print(precision_at_k(retrieved_docs, relevant_docs, k=3))  # 0.67
print(precision_at_k(retrieved_docs, relevant_docs, k=5))  # 0.6
```

### MRR (Mean Reciprocal Rank)

첫 관련 문서의 순위 역수 평균.

```python
def reciprocal_rank(retrieved: list, relevant: set) -> float:
    """
    RR = 1 / rank_of_first_relevant
    """
    for i, doc in enumerate(retrieved, 1):
        if doc in relevant:
            return 1.0 / i
    return 0.0

def mean_reciprocal_rank(queries_results: list) -> float:
    """여러 쿼리의 평균 RR"""
    rrs = [reciprocal_rank(r["retrieved"], r["relevant"])
           for r in queries_results]
    return sum(rrs) / len(rrs)
```

**해석:**
- MRR = 1.0: 모든 쿼리에서 첫 번째 결과가 관련
- MRR = 0.5: 평균적으로 두 번째 결과가 관련

### NDCG (Normalized Discounted Cumulative Gain)

순위별 관련도 가중 평가.

```python
import numpy as np

def dcg_at_k(relevances: list, k: int) -> float:
    """DCG@K"""
    relevances = np.array(relevances[:k])
    gains = 2 ** relevances - 1
    discounts = np.log2(np.arange(2, len(relevances) + 2))
    return np.sum(gains / discounts)

def ndcg_at_k(retrieved_relevances: list, ideal_relevances: list, k: int) -> float:
    """NDCG@K = DCG@K / IDCG@K"""
    dcg = dcg_at_k(retrieved_relevances, k)
    idcg = dcg_at_k(sorted(ideal_relevances, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0

# 예시 (relevance: 0=무관, 1=관련, 2=매우 관련)
retrieved = [2, 0, 1, 1, 0]  # 실제 검색 결과 관련도
ideal = [2, 2, 1, 1, 0]       # 이상적 관련도 (정렬된)
print(ndcg_at_k(retrieved, ideal, k=5))  # ~0.87
```

## Generation Metrics

### Faithfulness (충실도)

답변이 검색된 컨텍스트에 기반하는지.

```python
from ragas.metrics import faithfulness
from ragas import evaluate

# RAGAS 사용
result = evaluate(
    dataset,
    metrics=[faithfulness]
)

# 수동 계산 (개념)
def check_faithfulness(answer: str, context: str, llm) -> float:
    """
    1. 답변에서 주장(claim) 추출
    2. 각 주장이 컨텍스트에서 뒷받침되는지 확인
    3. 뒷받침되는 주장 비율 계산
    """
    prompt = f"""
    Answer: {answer}
    Context: {context}

    List all claims in the answer, then for each claim,
    determine if it is supported by the context.
    Return the ratio of supported claims.
    """
    return llm.invoke(prompt)
```

**목표:**
- Faithfulness > 0.95 (환각 최소화)

### Answer Relevance (답변 관련성)

답변이 질문에 적절히 응답하는지.

```python
from ragas.metrics import answer_relevancy

# RAGAS 사용
result = evaluate(
    dataset,
    metrics=[answer_relevancy]
)

# 개념적 구현
def answer_relevance(question: str, answer: str, llm) -> float:
    """
    1. 답변에서 가상의 질문 생성
    2. 원본 질문과 생성된 질문 유사도 계산
    """
    generated_questions = llm.invoke(
        f"Generate questions that this answer would address: {answer}"
    )
    similarity = compute_similarity(question, generated_questions)
    return similarity
```

### Context Precision (컨텍스트 정밀도)

검색된 컨텍스트가 답변에 얼마나 활용되는지.

```python
from ragas.metrics import context_precision

result = evaluate(
    dataset,
    metrics=[context_precision]
)
```

### Context Recall (컨텍스트 재현율)

정답에 필요한 정보가 컨텍스트에 있는지.

```python
from ragas.metrics import context_recall

result = evaluate(
    dataset,
    metrics=[context_recall]
)
```

## RAGAS 프레임워크

### 설치 및 사용

```python
pip install ragas

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# 평가 데이터셋 준비
data = {
    "question": ["What is machine learning?"],
    "answer": ["Machine learning is a subset of AI..."],
    "contexts": [["ML is a type of artificial intelligence...", "..."]],
    "ground_truth": ["Machine learning is a subset of AI that..."],
}
dataset = Dataset.from_dict(data)

# 평가 실행
result = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]
)

print(result)
```

### RAGAS 메트릭 요약

| 메트릭 | 측정 대상 | 범위 | 목표 |
|--------|----------|------|------|
| Faithfulness | 환각 없음 | 0-1 | > 0.95 |
| Answer Relevancy | 답변 관련성 | 0-1 | > 0.9 |
| Context Precision | 검색 정확도 | 0-1 | > 0.8 |
| Context Recall | 검색 재현율 | 0-1 | > 0.9 |

## TruLens 프레임워크

### 설치 및 사용

```python
pip install trulens-eval

from trulens_eval import Feedback, TruLlama, Tru
from trulens_eval.feedback.provider import OpenAI

# Provider 설정
provider = OpenAI()

# Feedback 함수 정의
f_groundedness = Feedback(provider.groundedness_measure_with_cot_reasons)
f_relevance = Feedback(provider.relevance)
f_coherence = Feedback(provider.coherence)

# 앱 래핑
tru_app = TruLlama(
    app,
    feedbacks=[f_groundedness, f_relevance, f_coherence]
)

# 실행 및 평가
with tru_app:
    response = app.query("What is RAG?")

# 결과 확인
Tru().get_leaderboard()
```

## 커스텀 평가 파이프라인

```python
class RAGEvaluator:
    def __init__(self, llm, embeddings):
        self.llm = llm
        self.embeddings = embeddings

    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: list,
        ground_truth: str = None
    ) -> dict:
        """종합 평가"""

        results = {
            "faithfulness": self._eval_faithfulness(answer, contexts),
            "relevance": self._eval_relevance(question, answer),
            "context_utilization": self._eval_context_use(answer, contexts),
        }

        if ground_truth:
            results["correctness"] = self._eval_correctness(
                answer, ground_truth
            )

        return results

    def _eval_faithfulness(self, answer: str, contexts: list) -> float:
        # 답변의 각 주장이 컨텍스트에 근거하는지
        prompt = f"""
        Rate the faithfulness of the answer to the given context.
        Score 0-1, where 1 means all claims are supported.

        Context: {' '.join([c.page_content for c in contexts])}
        Answer: {answer}

        Score (0-1):
        """
        score = float(self.llm.invoke(prompt).content.strip())
        return score

    def _eval_relevance(self, question: str, answer: str) -> float:
        # 답변이 질문에 관련되는지
        prompt = f"""
        Rate how well the answer addresses the question.
        Score 0-1, where 1 means perfectly relevant.

        Question: {question}
        Answer: {answer}

        Score (0-1):
        """
        return float(self.llm.invoke(prompt).content.strip())

    def _eval_context_use(self, answer: str, contexts: list) -> float:
        # 컨텍스트 활용도
        context_text = ' '.join([c.page_content for c in contexts])
        answer_emb = self.embeddings.embed_query(answer)
        context_emb = self.embeddings.embed_query(context_text)
        # 코사인 유사도 계산
        return cosine_similarity([answer_emb], [context_emb])[0][0]

    def _eval_correctness(self, answer: str, ground_truth: str) -> float:
        # 정답과 비교
        prompt = f"""
        Compare the answer to the ground truth.
        Score 0-1, where 1 means factually equivalent.

        Ground Truth: {ground_truth}
        Answer: {answer}

        Score (0-1):
        """
        return float(self.llm.invoke(prompt).content.strip())
```

## 벤치마크 데이터셋

| 데이터셋 | 도메인 | 크기 | 링크 |
|---------|--------|------|------|
| MS MARCO | 웹 검색 | 8.8M | Microsoft |
| Natural Questions | Wikipedia | 300K | Google |
| HotpotQA | 멀티홉 | 113K | Stanford |
| SQuAD 2.0 | 독해 | 150K | Stanford |
| TriviaQA | 일반 지식 | 95K | UW |

## 평가 주기 및 베이스라인

### 평가 주기

| 상황 | 주기 |
|------|------|
| 개발 중 | 매 변경 |
| 프로덕션 | 주간 |
| 새 데이터 추가 | 즉시 |

### 베이스라인 설정

```python
# 베이스라인 성능 기록
baseline = {
    "recall_at_10": 0.85,
    "mrr": 0.72,
    "faithfulness": 0.92,
    "answer_relevance": 0.88,
}

# 새 평가 결과와 비교
def compare_to_baseline(results: dict, baseline: dict) -> dict:
    comparison = {}
    for metric, value in results.items():
        if metric in baseline:
            diff = value - baseline[metric]
            comparison[metric] = {
                "current": value,
                "baseline": baseline[metric],
                "diff": diff,
                "improved": diff > 0
            }
    return comparison
```
