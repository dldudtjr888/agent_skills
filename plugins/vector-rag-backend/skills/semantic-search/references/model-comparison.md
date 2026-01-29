# Embedding Model Comparison

임베딩 모델 상세 비교표

## API 기반 모델

### OpenAI

| 모델 | 차원 | MTEB | 컨텍스트 | 비용/1M | 특징 |
|------|------|------|---------|--------|------|
| text-embedding-3-small | 1536 | 62.3 | 8191 | $0.02 | 비용 효율 |
| text-embedding-3-large | 3072 | 64.6 | 8191 | $0.13 | 최고 품질 |
| text-embedding-ada-002 | 1536 | 61.0 | 8191 | $0.10 | Legacy |

### Cohere

| 모델 | 차원 | MTEB | 컨텍스트 | 비용/1M | 특징 |
|------|------|------|---------|--------|------|
| embed-english-v3.0 | 1024 | 64.5 | 512 | $0.10 | 검색 최적화 |
| embed-multilingual-v3.0 | 1024 | 61.2 | 512 | $0.10 | 100+ 언어 |
| embed-english-light-v3.0 | 384 | 62.0 | 512 | $0.10 | 경량 |

### Voyage AI

| 모델 | 차원 | MTEB | 컨텍스트 | 비용/1M | 특징 |
|------|------|------|---------|--------|------|
| voyage-2 | 1024 | 65.3 | 4000 | $0.10 | RAG 특화 |
| voyage-large-2 | 1536 | 65.8 | 16000 | $0.12 | 긴 컨텍스트 |
| voyage-code-2 | 1536 | - | 16000 | $0.12 | 코드 특화 |

## 오픈소스 모델

### BAAI BGE 시리즈

| 모델 | 차원 | MTEB | 크기 | 언어 | 특징 |
|------|------|------|------|------|------|
| bge-small-en-v1.5 | 384 | 62.2 | 134MB | EN | 경량 |
| bge-base-en-v1.5 | 768 | 63.6 | 438MB | EN | 균형 |
| bge-large-en-v1.5 | 1024 | 64.2 | 1.3GB | EN | 고품질 |
| bge-m3 | 1024 | 62.8 | 2.3GB | Multi | 다국어+긴문서 |

### E5 시리즈 (Microsoft)

| 모델 | 차원 | MTEB | 크기 | 언어 | 특징 |
|------|------|------|------|------|------|
| e5-small-v2 | 384 | 59.9 | 134MB | EN | 경량 |
| e5-base-v2 | 768 | 61.5 | 438MB | EN | 균형 |
| e5-large-v2 | 1024 | 62.0 | 1.3GB | EN | 고품질 |
| multilingual-e5-large | 1024 | 61.5 | 2.2GB | Multi | 100+ 언어 |

### Sentence Transformers

| 모델 | 차원 | MTEB | 크기 | 속도 | 특징 |
|------|------|------|------|------|------|
| all-MiniLM-L6-v2 | 384 | 56.3 | 91MB | 매우 빠름 | 경량 |
| all-MiniLM-L12-v2 | 384 | 59.8 | 134MB | 빠름 | 균형 |
| all-mpnet-base-v2 | 768 | 57.8 | 438MB | 중간 | 범용 |

### 긴 컨텍스트 모델

| 모델 | 차원 | 컨텍스트 | 크기 | 특징 |
|------|------|---------|------|------|
| nomic-embed-text-v1.5 | 768 | 8192 | 548MB | 긴 문서 |
| jina-embeddings-v2-base-en | 768 | 8192 | 548MB | 긴 문서 |
| bge-m3 | 1024 | 8192 | 2.3GB | 다국어+긴문서 |

### 코드 특화 모델

| 모델 | 차원 | 크기 | 특징 |
|------|------|------|------|
| CodeBERT | 768 | 500MB | MS, 코드+자연어 |
| code-search-net-bert | 768 | 438MB | 코드 검색 |
| unixcoder-base | 768 | 500MB | 6개 언어 코드 |

## 선택 가이드

### 예산 기준

```
예산 없음 (API 사용)
└── 고품질: text-embedding-3-large
└── 비용 효율: text-embedding-3-small

예산 제한 (로컬 실행)
└── GPU 있음: bge-large-en-v1.5
└── GPU 없음: all-MiniLM-L6-v2
```

### 언어 기준

```
영어 전용
└── API: text-embedding-3-small
└── 로컬: bge-large-en-v1.5

다국어
└── API: embed-multilingual-v3.0
└── 로컬: multilingual-e5-large
```

### 문서 길이 기준

```
짧은 문서 (< 512 tokens)
└── 대부분 모델 가능

긴 문서 (> 512 tokens)
└── nomic-embed-text-v1.5
└── jina-embeddings-v2
└── bge-m3
```

### 속도 기준

```
최고 속도
└── all-MiniLM-L6-v2 (91MB, 384d)

균형
└── bge-base-en-v1.5 (438MB, 768d)

품질 우선
└── bge-large-en-v1.5 (1.3GB, 1024d)
```

## 벤치마크 결과

### MTEB Retrieval (검색 태스크)

| 모델 | NDCG@10 | Recall@100 |
|------|---------|------------|
| text-embedding-3-large | 0.587 | 0.912 |
| voyage-2 | 0.582 | 0.908 |
| bge-large-en-v1.5 | 0.573 | 0.901 |
| text-embedding-3-small | 0.561 | 0.889 |
| all-MiniLM-L6-v2 | 0.487 | 0.832 |

### 처리 속도 (1000 문장)

| 모델 | GPU (ms) | CPU (ms) |
|------|----------|----------|
| all-MiniLM-L6-v2 | 120 | 2,500 |
| bge-base-en-v1.5 | 280 | 6,000 |
| bge-large-en-v1.5 | 450 | 12,000 |

## 비용 계산

### 월간 비용 예측 (100만 쿼리)

| 모델 | 임베딩 비용 | 저장 비용* | 총 비용 |
|------|------------|-----------|--------|
| text-embedding-3-small | $20 | $5 | $25 |
| text-embedding-3-large | $130 | $10 | $140 |
| bge-large-en-v1.5 (self) | $0 | $3 | $3** |

*Qdrant Cloud 기준
**서버 비용 별도

## 마이그레이션 고려사항

### 모델 변경 시

1. **차원 변경**: 인덱스 재생성 필요
2. **유사도 분포 변화**: 임계값 재조정
3. **성능 테스트**: A/B 테스트 권장

### 호환성

```python
# 다른 모델의 임베딩은 비교 불가
# 쿼리와 문서는 같은 모델로 임베딩 필수

# WRONG
query_emb = openai_embed(query)
doc_emb = bge_embed(document)  # 호환 안됨!

# CORRECT
query_emb = bge_embed(query)
doc_emb = bge_embed(document)  # 같은 모델
```
