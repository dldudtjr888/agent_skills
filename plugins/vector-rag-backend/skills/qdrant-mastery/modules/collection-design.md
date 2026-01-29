# Collection Design

Qdrant 컬렉션 설계 패턴 - 구조, 페이로드, 샤딩, 거리 메트릭

## 컬렉션 구조

### 기본 컬렉션 생성

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

# 기본 컬렉션
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=1536,              # OpenAI text-embedding-3-small
        distance=Distance.COSINE
    )
)
```

### 멀티벡터 컬렉션

하나의 포인트에 여러 벡터를 저장할 때 사용:

```python
# Named vectors - 다른 용도의 임베딩 저장
client.create_collection(
    collection_name="products",
    vectors_config={
        "title": VectorParams(size=384, distance=Distance.COSINE),
        "description": VectorParams(size=1536, distance=Distance.COSINE),
        "image": VectorParams(size=512, distance=Distance.COSINE),
    }
)

# 검색 시 특정 벡터 지정
results = client.search(
    collection_name="products",
    query_vector=("title", title_embedding),  # title 벡터로 검색
    limit=10
)
```

## 페이로드 설계

### 페이로드 인덱싱

자주 필터링하는 필드는 반드시 인덱싱:

```python
from qdrant_client.models import PayloadSchemaType

# 키워드 필드 인덱싱 (정확한 매칭)
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

# 정수 필드 인덱싱 (범위 쿼리)
client.create_payload_index(
    collection_name="documents",
    field_name="year",
    field_schema=PayloadSchemaType.INTEGER
)

# 텍스트 필드 인덱싱 (전문 검색)
client.create_payload_index(
    collection_name="documents",
    field_name="content",
    field_schema=PayloadSchemaType.TEXT
)
```

### 페이로드 모범 사례

```python
# GOOD: 경량 페이로드 + 참조
point = PointStruct(
    id=1,
    vector=embedding,
    payload={
        "doc_id": "doc_123",        # 외부 참조
        "category": "technology",    # 인덱싱된 필터 필드
        "year": 2024,               # 범위 쿼리용
        "chunk_index": 5,           # 메타데이터
        "title": "Introduction"     # 짧은 텍스트
    }
)

# BAD: 대용량 데이터 직접 저장
point = PointStruct(
    id=1,
    vector=embedding,
    payload={
        "full_content": "... 10KB 텍스트 ...",  # 너무 큼!
        "raw_html": "<html>...</html>",          # 불필요
    }
)
```

### 페이로드 크기 가이드라인

| 필드 타입 | 권장 크기 | 참고 |
|-----------|----------|------|
| ID/참조 | < 100 bytes | UUID, 외부 키 |
| 카테고리 | < 50 bytes | 인덱싱 필수 |
| 제목/요약 | < 500 bytes | 표시용 |
| 메타데이터 | < 1KB | JSON 객체 |
| **총 페이로드** | < 2KB | 성능 최적 |

## 거리 메트릭 선택

### Cosine Similarity (권장 기본값)

```python
# 텍스트 임베딩에 최적
VectorParams(size=1536, distance=Distance.COSINE)
```

- **사용**: 텍스트 임베딩, 문서 유사도
- **특징**: 벡터 방향만 비교, 크기 무시
- **범위**: -1 ~ 1 (1이 가장 유사)

### Euclidean Distance

```python
# 이미지, 좌표 데이터에 적합
VectorParams(size=512, distance=Distance.EUCLID)
```

- **사용**: 이미지 특징, 지리 좌표
- **특징**: 절대 거리 계산
- **범위**: 0 ~ ∞ (0이 가장 유사)

### Dot Product

```python
# 정규화된 벡터, 추천 시스템
VectorParams(size=768, distance=Distance.DOT)
```

- **사용**: 추천 시스템, 정규화된 임베딩
- **특징**: 계산 가장 빠름
- **주의**: 벡터가 정규화되어 있어야 함

## 샤딩 전략

### 자동 샤딩 (권장)

```python
from qdrant_client.models import OptimizersConfigDiff

client.create_collection(
    collection_name="large_collection",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    # 자동 세그먼트 관리
    optimizers_config=OptimizersConfigDiff(
        indexing_threshold=20000,      # 인덱스 빌드 임계값
        memmap_threshold=50000,        # 디스크 저장 임계값
    )
)
```

### 수동 샤딩 (대규모)

```python
# 분산 환경에서 명시적 샤드 수 지정
client.create_collection(
    collection_name="distributed_collection",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    shard_number=6,           # CPU 코어 수에 맞춤
    replication_factor=2,     # HA를 위한 복제
)
```

### 스케일링 가이드

| 벡터 수 | 권장 구성 | 메모리 (1536d, float32) |
|---------|----------|------------------------|
| < 1M | 단일 노드 | ~6 GB |
| 1M - 10M | 단일 노드 + 양자화 | 6-15 GB (int8) |
| 10M - 100M | 분산 클러스터 2-4 노드 | 분산 |
| > 100M | 분산 클러스터 + 샤딩 | 분산 |

## 컬렉션 설정 예제

### RAG 문서 컬렉션

```python
from qdrant_client.models import (
    VectorParams, Distance, OptimizersConfigDiff,
    HnswConfigDiff, ScalarQuantization, ScalarQuantizationConfig
)

client.create_collection(
    collection_name="rag_documents",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=True,  # 대용량 시 디스크 저장
    ),
    hnsw_config=HnswConfigDiff(
        m=16,
        ef_construct=100,
        full_scan_threshold=10000,
    ),
    optimizers_config=OptimizersConfigDiff(
        default_segment_number=4,  # 병렬 처리
        indexing_threshold=20000,
    ),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            quantile=0.99,
            always_ram=True,  # 양자화 벡터는 RAM에
        )
    ),
)

# 필터 필드 인덱싱
for field, schema in [
    ("doc_id", PayloadSchemaType.KEYWORD),
    ("category", PayloadSchemaType.KEYWORD),
    ("created_at", PayloadSchemaType.DATETIME),
]:
    client.create_payload_index(
        collection_name="rag_documents",
        field_name=field,
        field_schema=schema
    )
```

### 멀티테넌트 컬렉션

```python
# tenant_id로 데이터 분리
client.create_collection(
    collection_name="multi_tenant",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# tenant_id 인덱싱 (필수!)
client.create_payload_index(
    collection_name="multi_tenant",
    field_name="tenant_id",
    field_schema=PayloadSchemaType.KEYWORD
)

# 검색 시 항상 tenant_id 필터
results = client.search(
    collection_name="multi_tenant",
    query_vector=embedding,
    query_filter=Filter(
        must=[FieldCondition(key="tenant_id", match=MatchValue(value="tenant_123"))]
    ),
    limit=10
)
```

## Anti-Patterns

### ❌ 인덱스 없이 필터링

```python
# BAD: category 인덱스 없이 필터링 → Full scan!
results = client.search(
    query_filter=Filter(must=[FieldCondition(key="category", ...)])
)

# GOOD: 먼저 인덱스 생성
client.create_payload_index(collection_name="docs", field_name="category", ...)
```

### ❌ 과도한 페이로드

```python
# BAD: 전체 문서 저장
payload = {"full_document": "... 100KB ..."}

# GOOD: 참조만 저장, 필요시 외부에서 조회
payload = {"doc_id": "123", "chunk_idx": 5}
```

### ❌ 잘못된 거리 메트릭

```python
# BAD: 텍스트 임베딩에 Euclidean
VectorParams(size=1536, distance=Distance.EUCLID)  # 부적절

# GOOD: 텍스트에는 Cosine
VectorParams(size=1536, distance=Distance.COSINE)
```
