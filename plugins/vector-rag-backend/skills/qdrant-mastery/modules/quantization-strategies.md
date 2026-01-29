# Quantization Strategies

벡터 양자화를 통한 메모리 최적화 및 성능 향상 가이드

## 양자화 개요

양자화는 벡터를 압축하여 메모리 사용량을 줄이고 검색 속도를 높입니다.

| 방식 | 압축률 | 정확도 손실 | 사용 시점 |
|------|--------|------------|----------|
| **Scalar (int8)** | 4x | ~1% | 대부분의 경우 (권장) |
| **Binary** | 32x | ~5% | 대규모, 고차원 |
| **Product** | 가변 | ~2-3% | 고급 최적화 |

## Scalar Quantization (권장)

float32 벡터를 int8로 압축 (4x 메모리 절약)

### 기본 설정

```python
from qdrant_client.models import (
    ScalarQuantization, ScalarQuantizationConfig
)

client.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            quantile=0.99,      # 이상치 제외
            always_ram=True,    # 양자화 벡터는 RAM에
        )
    )
)
```

### 하이브리드 저장 (권장)

양자화 벡터는 RAM에, 원본은 디스크에:

```python
client.create_collection(
    collection_name="hybrid_storage",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=True,           # 원본 벡터 → 디스크
    ),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            always_ram=True,    # 양자화 벡터 → RAM
        )
    )
)
```

**메모리 계산:**
```
10M vectors × 1536d:
- float32 only (RAM): 61.4 GB
- int8 + float32 disk: 15.4 GB RAM + 61.4 GB disk
- int8 only: 15.4 GB
```

### Rescoring 설정

양자화된 벡터로 후보를 찾고, 원본으로 재점수화:

```python
from qdrant_client.models import SearchParams, QuantizationSearchParams

# Rescoring 활성화 (기본값, 권장)
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(
        quantization=QuantizationSearchParams(
            rescore=True,       # 원본 벡터로 재점수화
            oversampling=2.0,   # 2배 후보 검색 후 리랭킹
        )
    ),
    limit=10
)

# Rescoring 비활성화 (속도 우선)
fast_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(
        quantization=QuantizationSearchParams(
            rescore=False,      # 양자화 점수만 사용
        )
    ),
    limit=10
)
```

### Oversampling 가이드

| oversampling | Recall 보정 | 지연시간 증가 | 권장 상황 |
|--------------|------------|--------------|----------|
| 1.0 | 없음 | 없음 | 속도 최우선 |
| 1.5 | ~0.5% | ~20% | 균형 |
| 2.0 | ~1% | ~40% | 정확도 중시 (권장) |
| 3.0 | ~1.5% | ~80% | 높은 정확도 필요 |

## Binary Quantization

벡터를 비트로 압축 (32x 메모리 절약)

### 적합한 상황

- 고차원 임베딩 (1536+)
- 대규모 데이터셋 (100M+)
- 메모리가 매우 제한적인 환경

### 기본 설정

```python
from qdrant_client.models import (
    BinaryQuantization, BinaryQuantizationConfig
)

client.create_collection(
    collection_name="large_scale",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    quantization_config=BinaryQuantization(
        binary=BinaryQuantizationConfig(
            always_ram=True,
        )
    )
)
```

### Binary + Rescoring (필수)

Binary 양자화는 정확도 손실이 크므로 rescoring 필수:

```python
results = client.search(
    collection_name="large_scale",
    query_vector=embedding,
    search_params=SearchParams(
        quantization=QuantizationSearchParams(
            rescore=True,
            oversampling=3.0,   # Binary는 높은 oversampling 필요
        )
    ),
    limit=10
)
```

### Inline Storage

HNSW 그래프 내에 양자화 벡터 저장으로 캐시 효율 향상:

```python
from qdrant_client.models import HnswConfigDiff

client.create_collection(
    collection_name="inline_binary",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(
        m=16,
        ef_construct=100,
        # 인덱스 파일에 양자화 벡터 포함
    ),
    quantization_config=BinaryQuantization(
        binary=BinaryQuantizationConfig(
            always_ram=True,
        )
    )
)
```

## Product Quantization

벡터를 서브벡터로 분할하여 압축 (가변 압축률)

### 적합한 상황

- Scalar와 Binary 사이의 트레이드오프 필요
- 특정 압축률 목표가 있을 때

### 설정 예시

```python
from qdrant_client.models import (
    ProductQuantization, ProductQuantizationConfig
)

client.create_collection(
    collection_name="product_quantized",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    quantization_config=ProductQuantization(
        product=ProductQuantizationConfig(
            compression="x16",  # x4, x8, x16, x32, x64
            always_ram=True,
        )
    )
)
```

| compression | 압축률 | 정확도 손실 | 서브벡터 수 |
|-------------|--------|------------|------------|
| x4 | 4x | ~1% | 많음 |
| x8 | 8x | ~2% | 중간 |
| x16 | 16x | ~3% | 적음 |
| x32 | 32x | ~5% | 매우 적음 |

## 기존 컬렉션에 양자화 추가

```python
# 이미 데이터가 있는 컬렉션에 양자화 적용
client.update_collection(
    collection_name="existing_collection",
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            quantile=0.99,
            always_ram=True,
        )
    )
)
# 참고: 백그라운드에서 양자화 인덱스 빌드됨
```

## 양자화 전략 선택 가이드

```
메모리 충분 & 최고 정확도?
    → 양자화 없음 (float32)

메모리 제한 & 정확도 중요?
    → Scalar (int8) + rescoring

대규모 (100M+) & 메모리 심각 제한?
    → Binary + 높은 oversampling

중간 압축 & 세밀한 제어?
    → Product Quantization
```

### 시나리오별 권장 설정

```python
# RAG 시스템 (정확도 우선)
rag_config = ScalarQuantization(
    scalar=ScalarQuantizationConfig(
        type="int8",
        quantile=0.99,
        always_ram=True,
    )
)
# 검색: oversampling=2.0, rescore=True

# 추천 시스템 (속도 우선)
rec_config = ScalarQuantization(
    scalar=ScalarQuantizationConfig(
        type="int8",
        always_ram=True,
    )
)
# 검색: oversampling=1.5, rescore=True

# 대규모 시맨틱 검색 (100M+)
large_config = BinaryQuantization(
    binary=BinaryQuantizationConfig(
        always_ram=True,
    )
)
# 검색: oversampling=3.0, rescore=True
```

## 성능 비교

### 1M vectors, 1536d, Cosine

| 설정 | Memory | Recall@10 | Latency (p50) |
|------|--------|-----------|---------------|
| float32 | 6.2 GB | 96% | 8 ms |
| int8 + rescore | 1.6 GB | 95.5% | 10 ms |
| int8 no rescore | 1.6 GB | 94% | 6 ms |
| binary + rescore | 0.2 GB | 93% | 12 ms |
| binary no rescore | 0.2 GB | 85% | 4 ms |

### 메모리 계산 공식

```
float32: vectors × dimensions × 4 bytes
int8:    vectors × dimensions × 1 byte
binary:  vectors × dimensions / 8 bytes

예시 (10M vectors, 1536d):
- float32: 10M × 1536 × 4 = 61.4 GB
- int8:    10M × 1536 × 1 = 15.4 GB
- binary:  10M × 1536 / 8 = 1.9 GB
```

## 양자화 모니터링

```python
# 컬렉션 정보에서 양자화 상태 확인
info = client.get_collection("docs")
print(f"Quantization: {info.config.quantization_config}")
print(f"Vectors indexed: {info.indexed_vectors_count}")
print(f"Points count: {info.points_count}")
```
