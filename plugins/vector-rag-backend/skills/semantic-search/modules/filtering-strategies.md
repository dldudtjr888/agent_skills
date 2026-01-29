# Filtering Strategies

검색 필터링 전략 - Pre/Post 필터링, 메타데이터 활용

## Pre-filtering vs Post-filtering

```
Pre-filtering (권장):
┌────────┐     ┌────────┐     ┌────────┐
│ Query  │────▶│ Filter │────▶│ Search │────▶ Results
└────────┘     └────────┘     └────────┘
                   ↓
              인덱스 활용
              빠름, 효율적

Post-filtering:
┌────────┐     ┌────────┐     ┌────────┐
│ Query  │────▶│ Search │────▶│ Filter │────▶ Results
└────────┘     └────────┘     └────────┘
                                  ↓
                            결과 수 부족 가능
                            느림
```

## Pre-filtering

검색 전에 조건 적용.

### Qdrant 예시

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# 단일 조건
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[FieldCondition(key="category", match=MatchValue(value="tech"))]
    ),
    limit=10
)

# 복합 조건
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="year", range=Range(gte=2023)),
        ],
        must_not=[
            FieldCondition(key="status", match=MatchValue(value="draft"))
        ]
    ),
    limit=10
)
```

### Chroma 예시

```python
# 메타데이터 필터
results = vectorstore.similarity_search(
    query,
    k=10,
    filter={"category": "tech"}
)

# 복합 필터
results = vectorstore.similarity_search(
    query,
    k=10,
    filter={
        "$and": [
            {"category": {"$eq": "tech"}},
            {"year": {"$gte": 2023}}
        ]
    }
)
```

## 메타데이터 설계

### 권장 필드

```python
metadata = {
    # 필수 필드
    "doc_id": "unique_identifier",
    "source": "filename.pdf",

    # 필터링용
    "category": "technology",
    "subcategory": "machine-learning",
    "language": "en",

    # 시간 기반
    "created_at": "2024-01-15",
    "updated_at": "2024-03-20",

    # 권한/테넌트
    "tenant_id": "company_123",
    "access_level": "public",

    # 청크 정보
    "chunk_index": 5,
    "total_chunks": 20,
    "parent_doc_id": "doc_001",
}
```

### 인덱싱 필수 필드

자주 필터링하는 필드는 반드시 인덱싱:

```python
# Qdrant
from qdrant_client.models import PayloadSchemaType

for field, schema in [
    ("category", PayloadSchemaType.KEYWORD),
    ("tenant_id", PayloadSchemaType.KEYWORD),
    ("created_at", PayloadSchemaType.DATETIME),
    ("year", PayloadSchemaType.INTEGER),
]:
    client.create_payload_index(
        collection_name="documents",
        field_name=field,
        field_schema=schema
    )
```

## 멀티테넌트 패턴

### 테넌트별 필터링

```python
class MultiTenantRetriever:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def search(
        self,
        query: str,
        tenant_id: str,
        k: int = 10
    ) -> list:
        # 항상 tenant_id 필터 적용
        return self.vectorstore.similarity_search(
            query,
            k=k,
            filter={"tenant_id": tenant_id}
        )
```

### 테넌트별 컬렉션 vs 필터링

| 방식 | 장점 | 단점 |
|------|------|------|
| 컬렉션 분리 | 완전 격리, 독립 스케일링 | 관리 복잡 |
| 필터링 | 단순 구현, 통합 관리 | 필터 성능 의존 |

**권장:**
- 테넌트 수 < 100: 필터링
- 테넌트 수 > 100 또는 데이터 격리 필수: 컬렉션 분리

## 시간 기반 필터링

```python
from datetime import datetime, timedelta

# 최근 N일 문서만
recent_date = datetime.now() - timedelta(days=30)

results = client.search(
    collection_name="documents",
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="created_at",
                range=DatetimeRange(gte=recent_date)
            )
        ]
    ),
    limit=10
)
```

## 계층적 필터링

```python
def hierarchical_filter(
    category: str,
    subcategory: str = None
) -> Filter:
    """계층적 카테고리 필터"""
    conditions = [
        FieldCondition(key="category", match=MatchValue(value=category))
    ]

    if subcategory:
        conditions.append(
            FieldCondition(key="subcategory", match=MatchValue(value=subcategory))
        )

    return Filter(must=conditions)

# 사용
filter = hierarchical_filter("technology", "ml")
```

## Self-Query Retrieval

쿼리에서 자동으로 필터 추출.

```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

# 메타데이터 필드 정의
metadata_field_info = [
    AttributeInfo(
        name="category",
        description="Document category: tech, science, business",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="Publication year",
        type="integer",
    ),
    AttributeInfo(
        name="author",
        description="Author name",
        type="string",
    ),
]

# Self-Query Retriever
retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="Technical articles and tutorials",
    metadata_field_info=metadata_field_info,
)

# 자동 필터 추출
# "Python tutorials from 2024 by John" →
# filter: {category: "tech", year: 2024, author: "John"}
docs = retriever.get_relevant_documents("Python tutorials from 2024 by John")
```

## 필터 최적화

### 선택도 고려

```python
# 높은 선택도 필터 먼저 (결과 수 많이 줄이는 것)
filter = Filter(
    must=[
        # 선택도 높음: tenant_id (특정 테넌트만)
        FieldCondition(key="tenant_id", match=MatchValue(value="tenant_123")),
        # 선택도 낮음: status (대부분 active)
        FieldCondition(key="status", match=MatchValue(value="active")),
    ]
)
```

### 복합 인덱스 활용

```python
# 자주 함께 사용되는 필드는 복합 인덱스
client.create_payload_index(
    collection_name="documents",
    field_name="tenant_id",
    field_schema=PayloadSchemaType.KEYWORD
)
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)
```

## Post-filtering 사용 시점

Pre-filtering이 어려울 때만 사용:

```python
def search_with_post_filter(
    query: str,
    custom_filter_fn,
    k: int = 10,
    oversample: int = 3
) -> list:
    """
    Post-filtering이 필요한 경우
    - 복잡한 조건 (함수 기반)
    - 외부 데이터 참조 필요
    """
    # 과다 검색
    candidates = vectorstore.similarity_search(query, k=k * oversample)

    # Post-filter
    filtered = [doc for doc in candidates if custom_filter_fn(doc)]

    return filtered[:k]

# 사용
def is_accessible(doc):
    # 외부 권한 시스템 확인
    return permission_service.check(doc.metadata["doc_id"])

results = search_with_post_filter(query, is_accessible, k=10)
```

## Anti-Patterns

### ❌ Post-filtering으로 대량 필터링

```python
# BAD: 90%가 필터링됨
results = vectorstore.similarity_search(query, k=1000)
filtered = [r for r in results if r.metadata["category"] == "rare_category"][:10]
```

### ❌ 인덱스 없는 필터링

```python
# BAD: Full scan 발생
results = client.search(
    query_vector=embedding,
    query_filter=Filter(must=[
        FieldCondition(key="unindexed_field", ...)  # 인덱스 없음!
    ])
)
```

### ✅ 권장 패턴

```python
# GOOD: 인덱싱 후 Pre-filtering
client.create_payload_index(collection, "category", PayloadSchemaType.KEYWORD)

results = client.search(
    query_vector=embedding,
    query_filter=Filter(must=[
        FieldCondition(key="category", match=MatchValue(value="rare_category"))
    ]),
    limit=10
)
```
