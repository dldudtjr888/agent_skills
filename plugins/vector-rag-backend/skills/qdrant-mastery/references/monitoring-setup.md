# Qdrant Monitoring Setup

Prometheus와 Grafana를 사용한 Qdrant 및 RAG 파이프라인 모니터링

## 개요

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Qdrant    │────▶│ Prometheus  │────▶│   Grafana   │
│  /metrics   │     │  (scrape)   │     │ (visualize) │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ RAG Pipeline│
│  (custom)   │
└─────────────┘
```

---

## 1. Qdrant 메트릭 엔드포인트

### 기본 메트릭

Qdrant는 `/metrics` 엔드포인트에서 Prometheus 형식 메트릭을 노출합니다.

```bash
# 메트릭 확인
curl http://localhost:6333/metrics
```

### 핵심 메트릭

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `rest_responses_total` | Counter | REST API 응답 수 |
| `grpc_responses_total` | Counter | gRPC 응답 수 |
| `collections_total` | Gauge | 컬렉션 수 |
| `app_info` | Info | 버전 정보 |
| `rest_responses_duration_seconds` | Histogram | REST 응답 지연시간 |

### Cloud 전용 메트릭 (/sys_metrics)

Qdrant Cloud에서는 추가 인프라 메트릭 제공:

```bash
# Cloud 클러스터 메트릭
curl -H "api-key: YOUR_API_KEY" \
  https://your-cluster.cloud.qdrant.io/sys_metrics
```

---

## 2. Prometheus 설정

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Qdrant 단일 노드
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: /metrics

  # Qdrant 클러스터 (여러 노드)
  - job_name: 'qdrant-cluster'
    static_configs:
      - targets:
        - 'qdrant-node-1:6333'
        - 'qdrant-node-2:6333'
        - 'qdrant-node-3:6333'

  # RAG 애플리케이션 커스텀 메트릭
  - job_name: 'rag-pipeline'
    static_configs:
      - targets: ['rag-app:8000']
    metrics_path: /metrics
```

### Kubernetes ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: qdrant-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: qdrant
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
  namespaceSelector:
    matchNames:
      - qdrant
```

---

## 3. Grafana 대시보드

### 공식 Qdrant 대시보드

**Dashboard ID: 24074**

```bash
# Grafana에서 Import
Dashboard → Import → ID: 24074 → Load
```

### 핵심 패널 구성

#### QPS (Queries Per Second)

```promql
# REST API QPS
rate(rest_responses_total[5m])

# gRPC QPS
rate(grpc_responses_total[5m])
```

#### 응답 지연시간 (P99)

```promql
# P99 Latency
histogram_quantile(0.99,
  rate(rest_responses_duration_seconds_bucket[5m])
)

# P95 Latency
histogram_quantile(0.95,
  rate(rest_responses_duration_seconds_bucket[5m])
)
```

#### 에러율

```promql
# 5xx 에러율
sum(rate(rest_responses_total{status=~"5.."}[5m]))
/ sum(rate(rest_responses_total[5m])) * 100
```

#### 컬렉션 크기

```promql
# 컬렉션별 포인트 수 (커스텀 메트릭 필요)
qdrant_collection_points_total{collection="documents"}
```

---

## 4. RAG 파이프라인 커스텀 메트릭

### Python 메트릭 서버

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# === 메트릭 정의 ===

# Counters
rag_queries_total = Counter(
    'rag_queries_total',
    'Total RAG queries',
    ['status']  # success, error
)

retrieval_requests_total = Counter(
    'retrieval_requests_total',
    'Total retrieval requests',
    ['source']  # vector, bm25, cache
)

# Histograms
retrieval_latency = Histogram(
    'rag_retrieval_latency_seconds',
    'Retrieval latency',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

rerank_latency = Histogram(
    'rag_rerank_latency_seconds',
    'Reranking latency',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

generation_latency = Histogram(
    'rag_generation_latency_seconds',
    'LLM generation latency',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

# Gauges
active_requests = Gauge(
    'rag_active_requests',
    'Currently processing requests'
)

circuit_breaker_state = Gauge(
    'rag_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half-open, 2=open)',
    ['component']
)

# === 메트릭 수집 데코레이터 ===

def track_latency(histogram):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                histogram.observe(time.time() - start)
        return wrapper
    return decorator

# === 사용 예시 ===

@track_latency(retrieval_latency)
def retrieve_documents(query: str):
    retrieval_requests_total.labels(source='vector').inc()
    return retriever.get_relevant_documents(query)

@track_latency(rerank_latency)
def rerank_documents(query: str, docs: list):
    return reranker.rerank(query, docs)

@track_latency(generation_latency)
def generate_answer(query: str, context: str):
    return llm.generate(query, context)

def rag_query(query: str):
    active_requests.inc()
    try:
        docs = retrieve_documents(query)
        reranked = rerank_documents(query, docs)
        answer = generate_answer(query, reranked)
        rag_queries_total.labels(status='success').inc()
        return answer
    except Exception as e:
        rag_queries_total.labels(status='error').inc()
        raise
    finally:
        active_requests.dec()

# === 메트릭 서버 시작 ===
if __name__ == '__main__':
    start_http_server(8000)  # /metrics 엔드포인트
    # 애플리케이션 실행...
```

### FastAPI 통합

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# 자동 메트릭 수집
Instrumentator().instrument(app).expose(app)

@app.post("/query")
async def query_rag(question: str):
    with retrieval_latency.time():
        docs = await retrieve_documents(question)

    with generation_latency.time():
        answer = await generate_answer(question, docs)

    return {"answer": answer}
```

---

## 5. OpenTelemetry 통합

### 설정

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

# Tracer 설정
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# OTLP Exporter (Jaeger, Tempo 등)
otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4317")
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# LangChain 자동 계측
LangchainInstrumentor().instrument()
```

### 수동 트레이싱

```python
@tracer.start_as_current_span("rag_query")
def rag_query(query: str):
    span = trace.get_current_span()
    span.set_attribute("query.length", len(query))

    with tracer.start_as_current_span("retrieval"):
        docs = retrieve_documents(query)
        span.set_attribute("docs.count", len(docs))

    with tracer.start_as_current_span("reranking"):
        reranked = rerank_documents(query, docs)

    with tracer.start_as_current_span("generation"):
        answer = generate_answer(query, reranked)
        span.set_attribute("answer.length", len(answer))

    return answer
```

---

## 6. Langfuse 통합 (RAG 특화)

```python
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

# Langfuse 클라이언트
langfuse = Langfuse(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com"
)

# LangChain 콜백 핸들러
langfuse_handler = CallbackHandler()

# RAG 체인에 연결
result = rag_chain.invoke(
    "What is machine learning?",
    config={"callbacks": [langfuse_handler]}
)

# 수동 트레이스
trace = langfuse.trace(name="rag_query")

# Retrieval span
retrieval_span = trace.span(name="retrieval")
docs = retriever.get_relevant_documents(query)
retrieval_span.end(output={"doc_count": len(docs)})

# Generation span
generation_span = trace.span(name="generation")
answer = llm.generate(query, docs)
generation_span.end(output={"answer_length": len(answer)})

# 평가 점수 기록
trace.score(name="relevance", value=0.9)
trace.score(name="faithfulness", value=0.85)
```

---

## 7. 알림 규칙

### Prometheus Alerting Rules

```yaml
groups:
  - name: qdrant_alerts
    rules:
      # 높은 에러율
      - alert: QdrantHighErrorRate
        expr: |
          sum(rate(rest_responses_total{status=~"5.."}[5m]))
          / sum(rate(rest_responses_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Qdrant error rate > 5%"

      # 높은 지연시간
      - alert: QdrantHighLatency
        expr: |
          histogram_quantile(0.99,
            rate(rest_responses_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Qdrant P99 latency > 2s"

  - name: rag_alerts
    rules:
      # RAG 지연시간
      - alert: RAGHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(rag_generation_latency_seconds_bucket[5m])
          ) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RAG generation P95 > 10s"

      # Circuit Breaker Open
      - alert: CircuitBreakerOpen
        expr: rag_circuit_breaker_state > 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker is open"
```

---

## 8. 대시보드 JSON 예시

```json
{
  "title": "RAG Pipeline Dashboard",
  "panels": [
    {
      "title": "QPS",
      "type": "stat",
      "targets": [
        {
          "expr": "sum(rate(rag_queries_total[5m]))"
        }
      ]
    },
    {
      "title": "Latency Distribution",
      "type": "heatmap",
      "targets": [
        {
          "expr": "sum(rate(rag_generation_latency_seconds_bucket[5m])) by (le)"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "gauge",
      "targets": [
        {
          "expr": "sum(rate(rag_queries_total{status='error'}[5m])) / sum(rate(rag_queries_total[5m])) * 100"
        }
      ]
    },
    {
      "title": "Component Latency",
      "type": "timeseries",
      "targets": [
        {"expr": "histogram_quantile(0.95, rate(rag_retrieval_latency_seconds_bucket[5m]))", "legendFormat": "Retrieval P95"},
        {"expr": "histogram_quantile(0.95, rate(rag_rerank_latency_seconds_bucket[5m]))", "legendFormat": "Rerank P95"},
        {"expr": "histogram_quantile(0.95, rate(rag_generation_latency_seconds_bucket[5m]))", "legendFormat": "Generation P95"}
      ]
    }
  ]
}
```

---

## 체크리스트

- [ ] Qdrant `/metrics` 엔드포인트 접근 확인
- [ ] Prometheus scrape 설정 완료
- [ ] Grafana 대시보드 Import (ID: 24074)
- [ ] RAG 애플리케이션 커스텀 메트릭 추가
- [ ] 알림 규칙 설정
- [ ] Langfuse/Phoenix 연동 (선택)
