# Similarity Metrics

유사도 메트릭 - Cosine, Euclidean, Dot Product

## 메트릭 비교

| 메트릭 | 수식 | 범위 | 해석 |
|--------|------|------|------|
| **Cosine** | cos(θ) = A·B / (‖A‖‖B‖) | [-1, 1] | 1 = 같은 방향 |
| **Euclidean** | √Σ(aᵢ-bᵢ)² | [0, ∞) | 0 = 동일 |
| **Dot Product** | Σ(aᵢ×bᵢ) | (-∞, ∞) | 높을수록 유사 |

## Cosine Similarity

가장 널리 사용되는 텍스트 임베딩 유사도.

### 특징

- **방향만 비교**: 벡터 크기 무시
- **정규화 효과**: 문서 길이에 무관
- **텍스트에 최적**: 대부분의 임베딩 모델과 호환

### 수식

```
Cosine Similarity = (A · B) / (||A|| × ||B||)

A = [1, 2, 3], B = [2, 4, 6]
Cosine = (1×2 + 2×4 + 3×6) / (√14 × √56) = 28 / 28 = 1.0

두 벡터가 방향이 같으면 1.0 (크기 달라도)
```

### 구현

```python
import numpy as np
from numpy.linalg import norm

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (norm(a) * norm(b))

# 또는 scikit-learn
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity([vec_a], [vec_b])[0][0]
```

### 사용 시점

- ✅ 텍스트 임베딩 (대부분의 경우)
- ✅ 문서 유사도
- ✅ 정규화되지 않은 벡터

### Qdrant 설정

```python
from qdrant_client.models import Distance, VectorParams

client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE  # 코사인 유사도
    )
)
```

## Euclidean Distance

절대적 거리 측정.

### 특징

- **절대 거리**: 벡터 크기 영향
- **기하학적 의미**: 실제 공간에서의 거리
- **이미지/좌표에 적합**: 절대 위치 중요할 때

### 수식

```
Euclidean Distance = √Σ(aᵢ - bᵢ)²

A = [1, 2], B = [4, 6]
Distance = √((4-1)² + (6-2)²) = √(9 + 16) = 5.0

거리가 0이면 동일한 벡터
```

### 구현

```python
import numpy as np
from numpy.linalg import norm

def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return norm(a - b)

# 또는
from scipy.spatial.distance import euclidean
distance = euclidean(vec_a, vec_b)
```

### 사용 시점

- ✅ 이미지 특징 벡터
- ✅ 지리적 좌표
- ✅ 절대적 거리가 의미 있을 때
- ❌ 텍스트 임베딩 (크기 변동 큼)

### Qdrant 설정

```python
client.create_collection(
    collection_name="images",
    vectors_config=VectorParams(
        size=512,
        distance=Distance.EUCLID  # 유클리드 거리
    )
)
```

## Dot Product (Inner Product)

정규화된 벡터에 최적.

### 특징

- **가장 빠름**: 단순 곱셈과 덧셈
- **정규화 필요**: 벡터 길이 = 1이어야 함
- **정규화 시 = Cosine**: 정규화되면 코사인과 동일

### 수식

```
Dot Product = Σ(aᵢ × bᵢ)

A = [0.6, 0.8], B = [0.8, 0.6] (정규화된 벡터)
Dot = 0.6×0.8 + 0.8×0.6 = 0.96

정규화된 벡터에서 높을수록 유사
```

### 구현

```python
import numpy as np

def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b)

# 정규화
def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)

# 정규화 후 내적
a_norm = normalize(vec_a)
b_norm = normalize(vec_b)
similarity = np.dot(a_norm, b_norm)  # == cosine_similarity
```

### 사용 시점

- ✅ 미리 정규화된 벡터
- ✅ 추천 시스템 (사용자-아이템 내적)
- ✅ 속도가 중요할 때
- ❌ 정규화되지 않은 벡터

### Qdrant 설정

```python
client.create_collection(
    collection_name="recommendations",
    vectors_config=VectorParams(
        size=256,
        distance=Distance.DOT  # 내적
    )
)
```

## 메트릭 선택 가이드

```
텍스트 임베딩?
  │
  ├─ Yes → Cosine Similarity
  │
  └─ No ──┬─ 이미지/좌표? → Euclidean Distance
          │
          └─ 정규화된 벡터? → Dot Product
```

### 일반 권장

| 데이터 타입 | 권장 메트릭 |
|-------------|------------|
| 텍스트 임베딩 | Cosine |
| OpenAI/Cohere 임베딩 | Cosine |
| 이미지 특징 | Euclidean 또는 Cosine |
| 추천 (정규화) | Dot Product |
| 지리 좌표 | Euclidean |

## 성능 비교

### 계산 복잡도

| 메트릭 | 연산 | 복잡도 |
|--------|------|--------|
| Dot Product | d 곱셈 + d 덧셈 | O(d) |
| Cosine | Dot + 2 norm | O(d) |
| Euclidean | d 뺄셈 + d 곱셈 + sqrt | O(d) |

### 벤치마크 (1536차원, 1M 벡터)

| 메트릭 | 검색 시간 | 상대 속도 |
|--------|----------|----------|
| Dot Product | 8ms | 1.0x |
| Cosine | 10ms | 0.8x |
| Euclidean | 12ms | 0.67x |

## 변환 관계

### 정규화된 벡터에서

```python
# 정규화된 벡터에서 세 메트릭의 관계

# Cosine = Dot Product (정규화 시)
cosine = dot_product(a_normalized, b_normalized)

# Euclidean² = 2 - 2 × Cosine
euclidean_squared = 2 - 2 * cosine
euclidean = np.sqrt(euclidean_squared)

# 변환 예시
cosine = 0.9
euclidean = np.sqrt(2 - 2 * 0.9)  # ≈ 0.447
```

### 임베딩 정규화

```python
# 대부분의 임베딩 모델 출력은 정규화되어 있음
# 확인 방법:
embedding = model.encode("text")
norm = np.linalg.norm(embedding)
print(f"Norm: {norm}")  # 1.0에 가까우면 정규화됨

# 명시적 정규화
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
embeddings = model.encode(
    texts,
    normalize_embeddings=True  # 정규화 옵션
)
```

## 임계값 설정

### Cosine Similarity 임계값

| 임계값 | 의미 | 용도 |
|--------|------|------|
| > 0.9 | 매우 유사 | 중복 탐지 |
| > 0.8 | 유사 | 관련 문서 |
| > 0.7 | 관련 있음 | 검색 결과 |
| < 0.5 | 관련 적음 | 필터링 |

```python
# 검색 시 임계값 적용
results = client.search(
    collection_name="documents",
    query_vector=embedding,
    score_threshold=0.7,  # 0.7 이상만
    limit=10
)
```

### Euclidean Distance 임계값

```python
# 유사도로 변환 (선택적)
def euclidean_to_similarity(distance: float) -> float:
    return 1 / (1 + distance)

# 또는 최대 거리 기반 정규화
max_distance = 2.0  # 정규화된 벡터의 최대 거리
similarity = 1 - (distance / max_distance)
```
