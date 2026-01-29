# Library Compatibility Guide

라이브러리 버전 및 호환성 가이드

## 권장 버전 (2024-2025)

### Core Libraries

| 라이브러리 | 권장 버전 | 최소 버전 | 비고 |
|-----------|----------|----------|------|
| Python | 3.10+ | 3.9 | 3.12 권장 |
| langchain | 0.2.x | 0.1.0 | 0.3.x 준비 중 |
| langchain-openai | 0.1.x | 0.1.0 | langchain 0.2+ 필수 |
| langchain-community | 0.2.x | 0.0.1 | |
| openai | 1.x | 1.0.0 | v0.x와 호환 안됨 |
| qdrant-client | 1.9+ | 1.6.0 | |
| sentence-transformers | 2.7+ | 2.2.0 | |

### Vector Databases

| DB | Python Client | Docker Image | 비고 |
|----|--------------|--------------|------|
| Qdrant | `qdrant-client>=1.9` | `qdrant/qdrant:v1.9.0` | |
| Chroma | `chromadb>=0.4` | `chromadb/chroma:0.4` | |
| Pinecone | `pinecone-client>=3.0` | - | Cloud only |
| FalkorDB | `falkordb>=1.0` | `falkordb/falkordb` | |

### Embedding Models

| Provider | Library | 권장 버전 |
|----------|---------|----------|
| OpenAI | `openai>=1.0` | 1.30+ |
| Cohere | `cohere>=5.0` | 5.0+ |
| HuggingFace | `sentence-transformers>=2.7` | 2.7+ |
| Voyage | `voyageai>=0.2` | 0.2+ |

### Rerankers

| Reranker | Library | 권장 버전 |
|----------|---------|----------|
| Cohere | `cohere>=5.0` | 5.0+ |
| Cross-Encoder | `sentence-transformers>=2.7` | 2.7+ |
| BGE Reranker | `FlagEmbedding>=1.2` | 1.2+ |

---

## 설치 명령어

### 기본 RAG 스택

```bash
# Core
pip install langchain>=0.2.0 langchain-openai>=0.1.0 langchain-community>=0.2.0

# Vector DB (택 1)
pip install qdrant-client>=1.9.0
pip install chromadb>=0.4.0
pip install pinecone-client>=3.0.0

# Embeddings
pip install openai>=1.30.0
pip install sentence-transformers>=2.7.0

# Reranking
pip install cohere>=5.0.0
# 또는 sentence-transformers (위에서 설치됨)
```

### requirements.txt 예시

```txt
# Core
langchain>=0.2.0,<0.3.0
langchain-openai>=0.1.0
langchain-community>=0.2.0
langchain-experimental>=0.0.50

# OpenAI
openai>=1.30.0

# Vector DB
qdrant-client>=1.9.0

# Embeddings & Reranking
sentence-transformers>=2.7.0
cohere>=5.0.0

# Evaluation
ragas>=0.1.0
datasets>=2.14.0

# Utils
tiktoken>=0.5.0
python-dotenv>=1.0.0
```

### pyproject.toml (Poetry)

```toml
[tool.poetry.dependencies]
python = "^3.10"
langchain = "^0.2.0"
langchain-openai = "^0.1.0"
langchain-community = "^0.2.0"
qdrant-client = "^1.9.0"
sentence-transformers = "^2.7.0"
openai = "^1.30.0"
```

---

## Breaking Changes

### LangChain 0.1 → 0.2

```python
# OLD (0.1)
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Qdrant

# NEW (0.2)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import Qdrant  # 또는 langchain_community
```

### OpenAI SDK 0.x → 1.x

```python
# OLD (0.x)
import openai
openai.api_key = "..."
response = openai.Embedding.create(input="text", model="...")

# NEW (1.x)
from openai import OpenAI
client = OpenAI(api_key="...")
response = client.embeddings.create(input="text", model="...")
```

### Qdrant Client 1.6 → 1.9

```python
# 대부분 호환, 새 기능 추가
# 새 기능: Sparse vectors, Named vectors 개선

# 1.9+ 새 기능
from qdrant_client.models import SparseVector, NamedSparseVector
```

### Sentence Transformers 2.x

```python
# normalize_embeddings 파라미터 추가
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
embeddings = model.encode(texts, normalize_embeddings=True)  # 권장
```

---

## 호환성 매트릭스

### LangChain + Vector DB

| LangChain | Qdrant | Chroma | Pinecone |
|-----------|--------|--------|----------|
| 0.2.x | ✅ 1.6+ | ✅ 0.4+ | ✅ 3.0+ |
| 0.1.x | ✅ 1.4+ | ✅ 0.3+ | ✅ 2.0+ |
| 0.0.x | ⚠️ 1.1+ | ✅ 0.3+ | ✅ 2.0+ |

### Python + Major Libraries

| Python | LangChain 0.2 | Qdrant 1.9 | ST 2.7 |
|--------|---------------|------------|--------|
| 3.12 | ✅ | ✅ | ✅ |
| 3.11 | ✅ | ✅ | ✅ |
| 3.10 | ✅ | ✅ | ✅ |
| 3.9 | ✅ | ✅ | ✅ |
| 3.8 | ⚠️ | ✅ | ⚠️ |

### Embedding Models + Vector DBs

모든 임베딩 모델은 모든 벡터 DB와 호환됩니다. 단, 차원이 일치해야 합니다.

| Model | Dimensions | Distance |
|-------|------------|----------|
| text-embedding-3-small | 1536 | Cosine |
| text-embedding-3-large | 3072 | Cosine |
| bge-base-en-v1.5 | 768 | Cosine |
| bge-large-en-v1.5 | 1024 | Cosine |
| all-MiniLM-L6-v2 | 384 | Cosine |

---

## 마이그레이션 가이드

### Chroma → Qdrant

```python
# 1. Chroma에서 데이터 추출
chroma_data = chroma_collection.get(include=["embeddings", "metadatas", "documents"])

# 2. Qdrant 컬렉션 생성
qdrant_client.create_collection(
    collection_name="migrated",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# 3. 데이터 이전
points = [
    PointStruct(
        id=i,
        vector=emb,
        payload={"text": doc, **meta}
    )
    for i, (emb, doc, meta) in enumerate(zip(
        chroma_data["embeddings"],
        chroma_data["documents"],
        chroma_data["metadatas"]
    ))
]
qdrant_client.upsert(collection_name="migrated", points=points)
```

### LangChain 0.1 → 0.2

```bash
# 1. 패키지 업데이트
pip install --upgrade langchain langchain-openai langchain-community

# 2. Import 수정 (IDE 검색/치환)
# from langchain.embeddings → from langchain_openai
# from langchain.chat_models → from langchain_openai
# from langchain.vectorstores → from langchain_community.vectorstores
```

---

## 버전 확인 스크립트

```python
def check_versions():
    """설치된 라이브러리 버전 확인"""
    import importlib

    packages = [
        "langchain",
        "langchain_openai",
        "langchain_community",
        "openai",
        "qdrant_client",
        "chromadb",
        "sentence_transformers",
        "cohere",
        "ragas",
    ]

    print("Installed versions:")
    print("-" * 40)

    for pkg in packages:
        try:
            mod = importlib.import_module(pkg.replace("-", "_"))
            version = getattr(mod, "__version__", "unknown")
            print(f"{pkg}: {version}")
        except ImportError:
            print(f"{pkg}: not installed")

check_versions()
```

---

## 알려진 이슈

### LangChain 0.2 + Qdrant

```python
# 이슈: from_documents가 느림
# 해결: batch_size 설정
Qdrant.from_documents(
    documents,
    embeddings,
    url="...",
    batch_size=100  # 기본값이 너무 작음
)
```

### Sentence Transformers + M1/M2 Mac

```python
# 이슈: MPS 디바이스 오류
# 해결: CPU 강제
model = SentenceTransformer("...", device="cpu")
```

### OpenAI Rate Limits

```python
# 이슈: RateLimitError
# 해결: 재시도 로직
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(min=1, max=60))
def embed_with_retry(texts):
    return embeddings.embed_documents(texts)
```
