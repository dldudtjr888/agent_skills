# Query Patterns

Qdrant 검색, 필터링, 배치 처리, 추천 쿼리 패턴

## 기본 벡터 검색

### 단순 검색

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

results = client.search(
    collection_name="documents",
    query_vector=embedding,  # [0.1, 0.2, ..., 0.n]
    limit=10,
)

for result in results:
    print(f"ID: {result.id}, Score: {result.score}")
    print(f"Payload: {result.payload}")
```

### Named Vector 검색

```python
# 멀티벡터 컬렉션에서 특정 벡터로 검색
results = client.search(
    collection_name="products",
    query_vector=("title", title_embedding),  # (vector_name, vector)
    limit=10,
)
```

## 필터링 검색

### 기본 필터

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# 단일 조건 필터
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="technology")
            )
        ]
    ),
    limit=10
)
```

### 복합 필터

```python
# AND 조건 (must)
filter_and = Filter(
    must=[
        FieldCondition(key="category", match=MatchValue(value="tech")),
        FieldCondition(key="year", range=Range(gte=2023)),
    ]
)

# OR 조건 (should)
filter_or = Filter(
    should=[
        FieldCondition(key="category", match=MatchValue(value="tech")),
        FieldCondition(key="category", match=MatchValue(value="science")),
    ]
)

# NOT 조건 (must_not)
filter_not = Filter(
    must_not=[
        FieldCondition(key="status", match=MatchValue(value="deleted"))
    ]
)

# 복합 조건
complex_filter = Filter(
    must=[
        FieldCondition(key="tenant_id", match=MatchValue(value="tenant_123")),
    ],
    should=[
        FieldCondition(key="priority", match=MatchValue(value="high")),
        FieldCondition(key="priority", match=MatchValue(value="critical")),
    ],
    must_not=[
        FieldCondition(key="archived", match=MatchValue(value=True))
    ]
)
```

### 범위 필터

```python
from qdrant_client.models import Range, DatetimeRange
from datetime import datetime

# 숫자 범위
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="price",
                range=Range(gte=100, lte=500)
            ),
            FieldCondition(
                key="rating",
                range=Range(gt=4.0)
            )
        ]
    ),
    limit=10
)

# 날짜 범위
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="created_at",
                range=DatetimeRange(
                    gte=datetime(2024, 1, 1),
                    lt=datetime(2025, 1, 1)
                )
            )
        ]
    ),
    limit=10
)
```

### 텍스트 검색 (Full-Text)

```python
from qdrant_client.models import FieldCondition, MatchText

# 전문 검색 (인덱스 필요)
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="content",
                match=MatchText(text="machine learning")
            )
        ]
    ),
    limit=10
)
```

### 배열 필터

```python
from qdrant_client.models import MatchAny, MatchExcept

# 배열 내 값 포함 (any)
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="tags",
                match=MatchAny(any=["python", "ml", "ai"])
            )
        ]
    ),
    limit=10
)

# 배열 내 값 제외 (except)
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="tags",
                match=MatchExcept(except_=["deprecated", "draft"])
            )
        ]
    ),
    limit=10
)
```

## 배치 검색

### 여러 쿼리 동시 처리

```python
from qdrant_client.models import SearchRequest

# 배치 검색 (병렬 처리)
queries = [
    SearchRequest(vector=emb1, limit=5),
    SearchRequest(vector=emb2, limit=5),
    SearchRequest(vector=emb3, limit=5),
]

batch_results = client.search_batch(
    collection_name="documents",
    requests=queries,
)

for i, results in enumerate(batch_results):
    print(f"Query {i}: {len(results)} results")
```

### 배치 검색 with 필터

```python
requests = [
    SearchRequest(
        vector=embedding,
        filter=Filter(must=[FieldCondition(key="category", match=MatchValue(value="tech"))]),
        limit=10,
    ),
    SearchRequest(
        vector=embedding,
        filter=Filter(must=[FieldCondition(key="category", match=MatchValue(value="science"))]),
        limit=10,
    ),
]

batch_results = client.search_batch(
    collection_name="documents",
    requests=requests,
)
```

## Scroll API (대량 조회)

### 전체 데이터 순회

```python
from qdrant_client.models import ScrollRequest

# 페이지네이션으로 전체 데이터 조회
offset = None
all_points = []

while True:
    results, offset = client.scroll(
        collection_name="documents",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False,  # 벡터 제외로 속도 향상
    )

    all_points.extend(results)

    if offset is None:
        break

print(f"Total points: {len(all_points)}")
```

### 필터와 함께 Scroll

```python
# 특정 조건의 모든 데이터 조회
offset = None
filtered_points = []

while True:
    results, offset = client.scroll(
        collection_name="documents",
        scroll_filter=Filter(
            must=[FieldCondition(key="category", match=MatchValue(value="tech"))]
        ),
        limit=100,
        offset=offset,
    )

    filtered_points.extend(results)

    if offset is None:
        break
```

## 추천 쿼리

### 긍정/부정 예시 기반 추천

```python
from qdrant_client.models import RecommendRequest

# 포인트 ID 기반 추천
results = client.recommend(
    collection_name="products",
    positive=[1, 2, 3],      # 이것과 비슷한 것
    negative=[10, 11],        # 이것과 다른 것
    limit=10,
)

# 벡터 기반 추천
results = client.recommend(
    collection_name="products",
    positive=[embedding1, embedding2],
    negative=[negative_embedding],
    limit=10,
)
```

### 추천 with 필터

```python
results = client.recommend(
    collection_name="products",
    positive=[user_liked_item_id],
    query_filter=Filter(
        must=[
            FieldCondition(key="in_stock", match=MatchValue(value=True)),
            FieldCondition(key="price", range=Range(lte=100)),
        ],
        must_not=[
            FieldCondition(key="category", match=MatchValue(value="adult"))
        ]
    ),
    limit=10,
)
```

## 검색 파라미터 튜닝

### HNSW 검색 파라미터

```python
from qdrant_client.models import SearchParams

# 빠른 검색
fast_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(
        hnsw_ef=32,    # 낮은 ef = 빠른 검색
        exact=False,
    ),
    limit=10
)

# 정확한 검색
accurate_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(
        hnsw_ef=256,   # 높은 ef = 정확한 검색
    ),
    limit=10
)

# Exact 검색 (Ground Truth)
exact_results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(exact=True),
    limit=10
)
```

### 양자화 검색 파라미터

```python
from qdrant_client.models import QuantizationSearchParams

results = client.search(
    collection_name="docs",
    query_vector=embedding,
    search_params=SearchParams(
        quantization=QuantizationSearchParams(
            rescore=True,        # 원본 벡터로 재점수화
            oversampling=2.0,    # 2배 후보 검색
            ignore=False,        # 양자화 사용 (True면 무시)
        )
    ),
    limit=10
)
```

## 그룹 검색

### 필드별 그룹화

```python
from qdrant_client.models import SearchGroups

# category별로 그룹화하여 검색
results = client.search_groups(
    collection_name="documents",
    query_vector=embedding,
    group_by="category",
    limit=3,           # 그룹당 결과 수
    group_size=5,      # 최대 그룹 수
)

for group in results.groups:
    print(f"Category: {group.id}")
    for hit in group.hits:
        print(f"  - {hit.id}: {hit.score}")
```

## 쿼리 최적화 팁

### Pre-filtering vs Post-filtering

```python
# GOOD: Pre-filtering (인덱스 활용)
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    query_filter=Filter(
        must=[FieldCondition(key="category", match=MatchValue(value="tech"))]
    ),
    limit=10
)

# BAD: Post-filtering (비효율)
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    limit=1000,  # 과다 검색
)
filtered = [r for r in results if r.payload["category"] == "tech"][:10]
```

### 페이로드 선택적 반환

```python
from qdrant_client.models import PayloadSelector

# 필요한 필드만 반환
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    with_payload=PayloadSelector(include=["title", "category"]),
    limit=10
)

# 벡터 제외 (속도 향상)
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    with_vectors=False,
    limit=10
)
```

### Score Threshold

```python
# 최소 점수 이상만 반환
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    score_threshold=0.7,  # 0.7 이상만
    limit=10
)
```
