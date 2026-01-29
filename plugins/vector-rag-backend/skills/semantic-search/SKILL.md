---
name: semantic-search
description: |
  시맨틱 검색 패턴. 임베딩 모델 선택, 하이브리드 검색,
  필터링 전략, 유사도 메트릭 최적화.
version: 1.0.0
category: search
user-invocable: true
triggers:
  keywords:
    - semantic search
    - 시맨틱 검색
    - embedding
    - 임베딩
    - hybrid search
    - 하이브리드 검색
    - bm25
    - similarity
    - 유사도
    - vector search
    - 벡터 검색
  intentPatterns:
    - "(구현|구축|설계).*(시맨틱|의미.*검색)"
    - "(implement|build).*(semantic.*search)"
    - "(하이브리드|혼합).*(검색|retrieval)"
    - "(임베딩|embedding).*(모델|선택)"
---

# Semantic Search

시맨틱 검색 시스템 설계 및 최적화 가이드.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Embedding Selection | [modules/embedding-selection.md](modules/embedding-selection.md) | 모델 선택, 차원, 성능 비교 |
| 2 | Hybrid Search | [modules/hybrid-search.md](modules/hybrid-search.md) | BM25 + Vector, RRF 조합 |
| 3 | Filtering Strategies | [modules/filtering-strategies.md](modules/filtering-strategies.md) | Pre/Post 필터링, 메타데이터 |
| 4 | Similarity Metrics | [modules/similarity-metrics.md](modules/similarity-metrics.md) | Cosine, Euclidean, Dot Product |

## 빠른 참조

| 참조 | 파일 | 설명 |
|------|------|------|
| Model Comparison | [references/model-comparison.md](references/model-comparison.md) | 임베딩 모델 비교표 |

## 시맨틱 검색이란?

의미 기반 검색. 키워드가 아닌 의미적 유사성으로 문서를 찾습니다.

```
Keyword Search: "ML" → "ML"이 포함된 문서만
Semantic Search: "ML" → "machine learning", "AI", "딥러닝" 등 관련 문서
```

## 아키텍처

```
Query → Embed → Vector Search → Results
          ↓
  Query: "Python tutorials"
          ↓
  Vector: [0.12, -0.34, 0.56, ...]
          ↓
  Similar vectors in DB
          ↓
  Results: Python docs, coding guides, etc.
```

## 임베딩 모델 빠른 선택

| 상황 | 권장 모델 | 차원 |
|------|----------|------|
| 일반 (영어) | `text-embedding-3-small` | 1536 |
| 고품질 (영어) | `text-embedding-3-large` | 3072 |
| 다국어 | `multilingual-e5-large` | 1024 |
| 로컬/무료 | `bge-large-en-v1.5` | 1024 |
| 경량 | `all-MiniLM-L6-v2` | 384 |

## 하이브리드 검색 필요성

| 시나리오 | Keyword | Semantic | Hybrid |
|----------|---------|----------|--------|
| 정확한 용어 | ✅ | ❌ | ✅ |
| 동의어/관련어 | ❌ | ✅ | ✅ |
| 코드/ID 검색 | ✅ | ❌ | ✅ |
| 자연어 질문 | ❌ | ✅ | ✅ |

**결론:** 대부분의 경우 하이브리드 검색이 최적

## 유사도 메트릭 선택

| 메트릭 | 사용 시점 | 특징 |
|--------|----------|------|
| **Cosine** | 텍스트 임베딩 | 방향 비교, 크기 무시 |
| **Euclidean** | 이미지/좌표 | 절대 거리 |
| **Dot Product** | 정규화된 벡터 | 빠른 계산 |

**기본 선택:** Cosine (대부분의 텍스트 임베딩에 적합)

## 필터링 전략

```
Pre-filtering (권장):
Query → Filter → Search → Results
         ↓
    인덱스 활용, 빠름

Post-filtering:
Query → Search → Filter → Results
                   ↓
              느림, 결과 부족 가능
```

## 성능 최적화 체크리스트

### 검색 품질
- [ ] 적절한 임베딩 모델 선택
- [ ] 하이브리드 검색 적용
- [ ] 리랭킹 추가
- [ ] 청킹 최적화

### 검색 속도
- [ ] 벡터 양자화 (int8)
- [ ] HNSW 파라미터 튜닝
- [ ] 배치 검색 활용
- [ ] Pre-filtering 사용

### 비용 최적화
- [ ] 로컬 임베딩 모델 고려
- [ ] 캐싱 적용
- [ ] 적절한 차원 선택

## 관련 에이전트

- `@vector-db-architect` - 벡터 DB 설계
- `@rag-system-builder` - RAG 시스템 구축
- `@rag-performance-analyst` - 성능 분석

## 관련 스킬

- `qdrant-mastery` - Qdrant 벡터 DB
- `rag-patterns` - RAG 패턴
