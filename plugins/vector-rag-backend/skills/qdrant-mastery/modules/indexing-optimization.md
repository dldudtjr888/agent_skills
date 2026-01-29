# Indexing Optimization

HNSW 인덱스 파라미터 최적화 및 세그먼트 설정 가이드

## HNSW 알고리즘 이해

HNSW(Hierarchical Navigable Small World)는 Qdrant의 핵심 인덱싱 알고리즘입니다.

```
Layer 2:  o ─────────────── o (sparse, long links)
          │                 │
Layer 1:  o ── o ── o ── o ── o (medium density)
          │    │    │    │    │
Layer 0:  o─o─o─o─o─o─o─o─o─o─o (dense, short links)
```

### 핵심 파라미터

| 파라미터 | 영향 | 기본값 | 범위 |
|----------|------|--------|------|
| `m` | 노드당 연결 수, 메모리 사용 | 16 | 4-64 |
| `ef_construct` | 빌드 시 정확도 | 100 | 50-500 |
| `hnsw_ef` | 검색 시 정확도 | 64 | 16-512 |

## 시나리오별 최적화

### High Recall (99%+)

정확도가 가장 중요한 경우:

```python
from qdrant_client.models import HnswConfigDiff

client.create_collection(
    collection_name="high_recall",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(
        m=32,              # 높은 연결성
        ef_construct=200,  # 정확한 인덱스 빌드
    )
)

# 검색 시 높은 ef 사용
results = client.search(
    collection_name="high_recall",
    query_vector=embedding,
    search_params=SearchParams(hnsw_ef=128),  # 높은 정확도
    limit=10
)
```

### Balanced (권장 기본값)

대부분의 사용 사례에 적합:

```python
client.create_collection(
    collection_name="balanced",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(
        m=16,              # 적절한 연결성
        ef_construct=100,  # 적절한 빌드 품질
    )
)

# 기본 검색
results = client.search(
    collection_name="balanced",
    query_vector=embedding,
    search_params=SearchParams(hnsw_ef=64),
    limit=10
)
```

### Low Latency (<10ms)

응답 속도가 최우선인 경우:

```python
client.create_collection(
    collection_name="low_latency",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(
        m=8,               # 낮은 연결성 → 빠른 탐색
        ef_construct=50,   # 빠른 빌드
    )
)

results = client.search(
    collection_name="low_latency",
    query_vector=embedding,
    search_params=SearchParams(hnsw_ef=32),  # 빠른 검색
    limit=10
)
```

### Memory Constrained

메모리가 제한된 환경:

```python
client.create_collection(
    collection_name="memory_limited",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=True,  # 벡터를 디스크에 저장
    ),
    hnsw_config=HnswConfigDiff(
        m=8,               # 메모리 절약
        ef_construct=100,  # 정확도 유지
        on_disk=True,      # 인덱스도 디스크에
    )
)
```

## 세그먼트 설정

### 세그먼트 개념

컬렉션은 여러 세그먼트로 분할되어 병렬 처리됩니다.

```
Collection
├── Segment 1 (points 0-100K)    → CPU Core 1
├── Segment 2 (points 100K-200K) → CPU Core 2
├── Segment 3 (points 200K-300K) → CPU Core 3
└── Segment 4 (points 300K-400K) → CPU Core 4
```

### 세그먼트 최적화

```python
from qdrant_client.models import OptimizersConfigDiff

# Low Latency: 세그먼트 수 = CPU 코어 수
client.create_collection(
    collection_name="parallel_search",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    optimizers_config=OptimizersConfigDiff(
        default_segment_number=16,  # 16코어 머신
    )
)

# High Throughput: 적은 세그먼트, 큰 크기
client.create_collection(
    collection_name="high_throughput",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    optimizers_config=OptimizersConfigDiff(
        default_segment_number=2,
        max_segment_size=5000000,  # 500만 포인트/세그먼트
    )
)
```

### 인덱싱 임계값

```python
optimizers_config=OptimizersConfigDiff(
    indexing_threshold=20000,   # 20K 포인트 이상이면 HNSW 빌드
    memmap_threshold=50000,     # 50K 이상이면 memmap 사용
    flush_interval_sec=5,       # 5초마다 디스크 플러시
)
```

## 동적 파라미터 조정

### 검색 시 ef 조정

요청별로 정확도/속도 트레이드오프 조정:

```python
from qdrant_client.models import SearchParams

# 빠른 검색 (낮은 정확도)
fast_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(hnsw_ef=32),
    limit=10
)

# 정확한 검색 (느린 속도)
accurate_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(hnsw_ef=256),
    limit=10
)

# Exact 검색 (Ground Truth 비교용)
exact_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(exact=True),  # 완전 탐색
    limit=10
)
```

### 컬렉션 설정 업데이트

```python
# 기존 컬렉션의 HNSW 설정 변경
client.update_collection(
    collection_name="docs",
    hnsw_config=HnswConfigDiff(
        m=24,  # 연결성 증가
    )
)
# 주의: m 변경 시 인덱스 재빌드 필요
```

## 성능 벤치마크

### 파라미터별 성능 (1M vectors, 1536d)

| m | ef_construct | hnsw_ef | Recall@10 | Latency (ms) | Memory |
|---|--------------|---------|-----------|--------------|--------|
| 8 | 50 | 32 | 91% | 3 | 4.8 GB |
| 16 | 100 | 64 | 96% | 8 | 6.2 GB |
| 32 | 200 | 128 | 99% | 18 | 9.1 GB |

### 양자화 + HNSW

```python
# int8 양자화로 메모리 75% 절약
client.create_collection(
    collection_name="optimized",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(type="int8", always_ram=True)
    )
)
```

| 설정 | Recall@10 | Memory | Latency |
|------|-----------|--------|---------|
| float32 only | 96% | 6.2 GB | 8 ms |
| int8 + rescore | 95.5% | 1.6 GB | 10 ms |
| int8 no rescore | 94% | 1.6 GB | 6 ms |

## 모니터링 및 튜닝

### 컬렉션 상태 확인

```python
info = client.get_collection("docs")
print(f"Points: {info.points_count}")
print(f"Segments: {info.segments_count}")
print(f"Indexed: {info.indexed_vectors_count}")
print(f"Status: {info.status}")
```

### 성능 테스트

```python
import time
import numpy as np

def benchmark_search(client, collection, n_queries=100):
    dim = 1536
    latencies = []

    for _ in range(n_queries):
        query = np.random.rand(dim).tolist()
        start = time.perf_counter()
        client.search(collection, query_vector=query, limit=10)
        latencies.append((time.perf_counter() - start) * 1000)

    return {
        "p50": np.percentile(latencies, 50),
        "p95": np.percentile(latencies, 95),
        "p99": np.percentile(latencies, 99),
    }
```

## 권장 설정 매트릭스

| Use Case | m | ef_construct | hnsw_ef | on_disk | quantization |
|----------|---|--------------|---------|---------|--------------|
| RAG (정확도 중시) | 24 | 150 | 100 | False | int8 |
| 추천 (속도 중시) | 12 | 80 | 48 | False | int8 |
| 대규모 (>10M) | 16 | 100 | 64 | True | int8 |
| 실시간 (<5ms) | 8 | 50 | 32 | False | binary |
| 메모리 제한 | 8 | 100 | 64 | True | int8 |
