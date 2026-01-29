# Qdrant Quick Reference

자주 사용하는 설정 및 명령어 빠른 참조

## 설치 및 실행

### Docker

```bash
# 단일 노드 실행
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# 환경 변수 설정
docker run -p 6333:6333 \
    -e QDRANT__SERVICE__GRPC_PORT=6334 \
    -e QDRANT__STORAGE__STORAGE_PATH=/qdrant/storage \
    qdrant/qdrant
```

### Python Client

```bash
pip install qdrant-client
```

## 클라이언트 초기화

```python
from qdrant_client import QdrantClient

# 로컬
client = QdrantClient(host="localhost", port=6333)

# Cloud
client = QdrantClient(
    url="https://xxx.us-east-1-0.aws.cloud.qdrant.io",
    api_key="your-api-key"
)

# 메모리 (테스트용)
client = QdrantClient(":memory:")

# 파일 기반
client = QdrantClient(path="./local_qdrant")
```

## HNSW 파라미터 가이드

| 시나리오 | m | ef_construct | hnsw_ef | 메모리 | Recall |
|----------|---|--------------|---------|--------|--------|
| High Recall | 32 | 200 | 128 | High | 99%+ |
| Balanced | 16 | 100 | 64 | Medium | 95%+ |
| Low Latency | 8 | 50 | 32 | Low | 90%+ |

## 거리 메트릭

| 메트릭 | 사용 | 범위 |
|--------|------|------|
| `Distance.COSINE` | 텍스트 임베딩 | -1 ~ 1 |
| `Distance.EUCLID` | 이미지, 좌표 | 0 ~ ∞ |
| `Distance.DOT` | 정규화 벡터 | -∞ ~ ∞ |

## 양자화 설정

### Scalar (int8) - 권장

```python
ScalarQuantization(
    scalar=ScalarQuantizationConfig(
        type="int8",
        quantile=0.99,
        always_ram=True,
    )
)
```

### Binary - 대규모

```python
BinaryQuantization(
    binary=BinaryQuantizationConfig(
        always_ram=True,
    )
)
```

## 필터 문법

```python
# 단일 조건
Filter(must=[FieldCondition(key="field", match=MatchValue(value="x"))])

# 범위
Filter(must=[FieldCondition(key="price", range=Range(gte=10, lte=100))])

# OR 조건
Filter(should=[...])

# NOT 조건
Filter(must_not=[...])

# 배열 포함
Filter(must=[FieldCondition(key="tags", match=MatchAny(any=["a", "b"]))])
```

## 메모리 계산

```
float32: vectors × dimensions × 4 bytes
int8:    vectors × dimensions × 1 byte
binary:  vectors × dimensions / 8 bytes

예: 10M vectors, 1536d
- float32: 61.4 GB
- int8: 15.4 GB
- binary: 1.9 GB
```

## 페이로드 인덱스 타입

| 타입 | 용도 |
|------|------|
| `KEYWORD` | 정확한 매칭 |
| `INTEGER` | 숫자 범위 |
| `FLOAT` | 실수 범위 |
| `TEXT` | 전문 검색 |
| `DATETIME` | 날짜 범위 |
| `GEO` | 지리 좌표 |

## 자주 쓰는 패턴

### 컬렉션 생성 (RAG용)

```python
client.create_collection(
    collection_name="rag_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(type="int8", always_ram=True)
    ),
)
```

### 포인트 추가

```python
client.upsert(
    collection_name="docs",
    points=[
        PointStruct(id=1, vector=emb, payload={"title": "...", "category": "tech"})
    ]
)
```

### 검색

```python
client.search(
    collection_name="docs",
    query_vector=embedding,
    query_filter=Filter(must=[...]),
    limit=10,
    with_payload=True,
)
```

### 배치 검색

```python
client.search_batch(
    collection_name="docs",
    requests=[SearchRequest(vector=emb, limit=10) for emb in embeddings]
)
```

## API 엔드포인트

| 작업 | 엔드포인트 |
|------|-----------|
| 컬렉션 목록 | `GET /collections` |
| 컬렉션 정보 | `GET /collections/{name}` |
| 검색 | `POST /collections/{name}/points/search` |
| 추가 | `PUT /collections/{name}/points` |
| 삭제 | `POST /collections/{name}/points/delete` |
| 스크롤 | `POST /collections/{name}/points/scroll` |

## 환경 변수

```bash
QDRANT__SERVICE__HTTP_PORT=6333
QDRANT__SERVICE__GRPC_PORT=6334
QDRANT__STORAGE__STORAGE_PATH=/qdrant/storage
QDRANT__CLUSTER__ENABLED=true
```
