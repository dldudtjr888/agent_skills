# Qdrant Python Cheatsheet

qdrant-client 라이브러리 코드 예제 모음

## 설치

```bash
pip install qdrant-client
pip install qdrant-client[fastembed]  # FastEmbed 포함
```

## 클라이언트 초기화

```python
from qdrant_client import QdrantClient, AsyncQdrantClient

# 동기 클라이언트
client = QdrantClient(host="localhost", port=6333)

# 비동기 클라이언트
async_client = AsyncQdrantClient(host="localhost", port=6333)

# Cloud 연결
client = QdrantClient(
    url="https://xxx.cloud.qdrant.io",
    api_key="your-api-key",
    timeout=60,
)

# 로컬 파일 기반
client = QdrantClient(path="./qdrant_data")

# 메모리 (테스트용)
client = QdrantClient(":memory:")
```

## 컬렉션 관리

```python
from qdrant_client.models import (
    Distance, VectorParams, HnswConfigDiff,
    OptimizersConfigDiff, ScalarQuantization,
    ScalarQuantizationConfig, PayloadSchemaType
)

# 생성
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        on_disk=False,
    ),
    hnsw_config=HnswConfigDiff(
        m=16,
        ef_construct=100,
    ),
    optimizers_config=OptimizersConfigDiff(
        default_segment_number=4,
        indexing_threshold=20000,
    ),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            always_ram=True,
        )
    ),
)

# 목록 조회
collections = client.get_collections()

# 정보 조회
info = client.get_collection("documents")
print(f"Points: {info.points_count}")
print(f"Segments: {info.segments_count}")

# 삭제
client.delete_collection("documents")

# 업데이트
client.update_collection(
    collection_name="documents",
    hnsw_config=HnswConfigDiff(m=24),
)
```

## 포인트 CRUD

```python
from qdrant_client.models import PointStruct, PointIdsList

# 단일 추가
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],
            payload={"title": "Doc 1", "category": "tech"}
        )
    ]
)

# 배치 추가
points = [
    PointStruct(id=i, vector=embeddings[i], payload=payloads[i])
    for i in range(len(embeddings))
]
client.upsert(
    collection_name="documents",
    points=points,
    wait=True,  # 완료까지 대기
)

# 조회
point = client.retrieve(
    collection_name="documents",
    ids=[1, 2, 3],
    with_payload=True,
    with_vectors=True,
)

# 삭제 (ID)
client.delete(
    collection_name="documents",
    points_selector=PointIdsList(points=[1, 2, 3])
)

# 삭제 (필터)
from qdrant_client.models import FilterSelector, Filter, FieldCondition, MatchValue
client.delete(
    collection_name="documents",
    points_selector=FilterSelector(
        filter=Filter(
            must=[FieldCondition(key="category", match=MatchValue(value="old"))]
        )
    )
)
```

## 검색

```python
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, Range,
    SearchParams, QuantizationSearchParams
)

# 기본 검색
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    limit=10,
)

# 필터 검색
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="year", range=Range(gte=2023)),
        ]
    ),
    limit=10,
)

# 검색 파라미터 튜닝
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    search_params=SearchParams(
        hnsw_ef=128,
        quantization=QuantizationSearchParams(
            rescore=True,
            oversampling=2.0,
        )
    ),
    limit=10,
    score_threshold=0.7,
    with_payload=True,
    with_vectors=False,
)

# 배치 검색
from qdrant_client.models import SearchRequest
batch_results = client.search_batch(
    collection_name="documents",
    requests=[
        SearchRequest(vector=emb1, limit=5),
        SearchRequest(vector=emb2, limit=5, filter=Filter(...)),
    ]
)
```

## 필터 예제

```python
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, MatchAny, MatchExcept,
    MatchText, Range, DatetimeRange, GeoBoundingBox, GeoRadius
)
from datetime import datetime

# 정확한 매칭
f1 = FieldCondition(key="status", match=MatchValue(value="active"))

# 배열 내 값 (OR)
f2 = FieldCondition(key="tags", match=MatchAny(any=["python", "ml"]))

# 배열 제외
f3 = FieldCondition(key="tags", match=MatchExcept(except_=["deprecated"]))

# 텍스트 검색
f4 = FieldCondition(key="content", match=MatchText(text="machine learning"))

# 숫자 범위
f5 = FieldCondition(key="price", range=Range(gte=10, lte=100))

# 날짜 범위
f6 = FieldCondition(
    key="created_at",
    range=DatetimeRange(gte=datetime(2024, 1, 1))
)

# 지리 검색 (원형)
f7 = FieldCondition(
    key="location",
    geo_radius=GeoRadius(center={"lat": 37.5, "lon": 127.0}, radius=1000)
)

# 복합 필터
complex_filter = Filter(
    must=[f1, f5],
    should=[f2],
    must_not=[f3]
)
```

## 페이로드 인덱스

```python
# 키워드 인덱스
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

# 숫자 인덱스
client.create_payload_index(
    collection_name="documents",
    field_name="price",
    field_schema=PayloadSchemaType.INTEGER
)

# 텍스트 인덱스
client.create_payload_index(
    collection_name="documents",
    field_name="content",
    field_schema=PayloadSchemaType.TEXT
)

# 날짜 인덱스
client.create_payload_index(
    collection_name="documents",
    field_name="created_at",
    field_schema=PayloadSchemaType.DATETIME
)
```

## 스크롤 (페이지네이션)

```python
# 전체 데이터 순회
offset = None
all_points = []

while True:
    results, offset = client.scroll(
        collection_name="documents",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )
    all_points.extend(results)
    if offset is None:
        break
```

## 추천

```python
# ID 기반 추천
results = client.recommend(
    collection_name="products",
    positive=[1, 2, 3],
    negative=[10],
    limit=10,
)

# 벡터 기반 추천
results = client.recommend(
    collection_name="products",
    positive=[embedding1, embedding2],
    negative=[neg_embedding],
    query_filter=Filter(...),
    limit=10,
)
```

## 비동기 사용

```python
import asyncio
from qdrant_client import AsyncQdrantClient

async def main():
    client = AsyncQdrantClient(host="localhost", port=6333)

    # 비동기 검색
    results = await client.search(
        collection_name="documents",
        query_vector=embedding,
        limit=10,
    )

    # 비동기 배치
    batch_results = await client.search_batch(
        collection_name="documents",
        requests=[...]
    )

    await client.close()

asyncio.run(main())
```

## 에러 처리

```python
from qdrant_client.http.exceptions import (
    UnexpectedResponse,
    ResponseHandlingException,
)

try:
    results = client.search(...)
except UnexpectedResponse as e:
    print(f"API Error: {e.status_code} - {e.content}")
except ResponseHandlingException as e:
    print(f"Response Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
```

## FastEmbed 통합

```python
from qdrant_client import QdrantClient

# FastEmbed 자동 사용
client = QdrantClient(":memory:")

# 텍스트로 직접 추가
client.add(
    collection_name="documents",
    documents=["doc1 text", "doc2 text"],
    metadata=[{"source": "a"}, {"source": "b"}],
    ids=[1, 2],
)

# 텍스트로 검색
results = client.query(
    collection_name="documents",
    query_text="search query",
    limit=5,
)
```

## 스냅샷

```python
# 스냅샷 생성
snapshot = client.create_snapshot(collection_name="documents")

# 스냅샷 목록
snapshots = client.list_snapshots(collection_name="documents")

# 스냅샷 복원
client.recover_snapshot(
    collection_name="documents",
    location=snapshot.name,
)
```
