# vector-rag-backend

벡터 데이터베이스 및 RAG 패턴 플러그인 - Qdrant, FalkorDB, 시맨틱 검색, RAG 최적화

## 개요

이 플러그인은 벡터 데이터베이스(Qdrant, FalkorDB)와 RAG 시스템 설계/최적화를 위한 종합 가이드를 제공합니다.

- **벡터 DB 설계**: 컬렉션, 인덱싱, 양자화, 스케일링
- **GraphRAG**: 지식 그래프 기반 RAG
- **RAG 패턴**: 청킹, 검색, 리랭킹, 컨텍스트 엔지니어링
- **시맨틱 검색**: 임베딩, 하이브리드 검색

## 스킬 (4개)

| 스킬 | 설명 | 키워드 |
|------|------|--------|
| `qdrant-mastery` | Qdrant 컬렉션, 인덱싱, 양자화, 쿼리 | qdrant, vector, HNSW |
| `falkordb-graphrag` | FalkorDB 그래프 모델링, GraphRAG | falkordb, cypher, knowledge graph |
| `rag-patterns` | 청킹, 검색, 리랭킹, 컨텍스트 엔지니어링 | rag, chunking, reranking |
| `semantic-search` | 임베딩, 하이브리드 검색, 유사도 | embedding, hybrid search, BM25 |

## 에이전트 (4개)

| 에이전트 | 역할 |
|----------|------|
| `@vector-db-architect` | 벡터 DB 아키텍처 설계 |
| `@rag-system-builder` | 엔드투엔드 RAG 파이프라인 구축 |
| `@vector-db-reviewer` | 벡터 DB 구현 리뷰 |
| `@rag-performance-analyst` | RAG 성능 분석 및 최적화 |

## 핵심 기술 정보

### Qdrant HNSW 파라미터

| Scenario | m | ef_construct | hnsw_ef | Notes |
|----------|---|--------------|---------|-------|
| High Recall | 32 | 200 | 128 | 99%+ recall |
| Balanced | 16 | 100 | 64 | Default |
| Low Latency | 8 | 50 | 32 | <10ms queries |

### RAG 청킹 전략 효과

- Fixed-length: 50% accuracy (baseline)
- Semantic chunking: 87% accuracy (+37%)
- Reranking: highest ROI upgrade

### FalkorDB GraphRAG 장점

- 5x query speed vs traditional RAG
- 90% hallucination reduction
- 40% infrastructure cost reduction

## 다른 플러그인과의 관계

```
vector-rag-backend (벡터 DB + RAG 패턴)
       ↓ 연동
python-agent-backend (에이전트 인프라)
       ↓ 참조
common-backend (일반 백엔드 패턴)
```

**예시**: RAG 에이전트 구축 시
1. `vector-rag-backend/rag-patterns` → RAG 설계
2. `vector-rag-backend/qdrant-mastery` → 벡터 저장소
3. `python-agent-backend/agent-infra-builder` → 에이전트 통합

## 인프라 (로컬 개발 환경)

```bash
# 인프라 시작
cd infrastructure
docker-compose up -d

# 서비스 엔드포인트
# Qdrant:     http://localhost:6333
# FalkorDB:   localhost:6379, http://localhost:3000
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3001 (admin/admin)
```

자세한 내용: [infrastructure/README.md](infrastructure/README.md)

## 튜토리얼

| # | 튜토리얼 | 스킬 | 학습 내용 |
|---|----------|------|-----------|
| 1 | [Basic RAG](skills/rag-patterns/tutorials/01-basic-rag.md) | rag-patterns | PDF, 청킹, 벡터 저장, Q&A |
| 2 | [Advanced RAG](skills/rag-patterns/tutorials/02-advanced-rag-with-reranking.md) | rag-patterns | Cross-encoder, Cohere 리랭킹 |
| 3 | [Hybrid Search](skills/rag-patterns/tutorials/03-hybrid-search.md) | rag-patterns | BM25 + Vector, RRF 융합 |
| 4 | [GraphRAG](skills/rag-patterns/tutorials/04-graphrag-with-falkordb.md) | rag-patterns | FalkorDB + LangChain |
| 5 | [GraphRAG Quickstart](skills/falkordb-graphrag/tutorials/01-graphrag-quickstart.md) | falkordb-graphrag | GraphRAG-SDK로 KG 구축 |

## 프로덕션 가이드

| 가이드 | 파일 | 설명 |
|--------|------|------|
| Production Patterns | [modules/production-patterns.md](skills/rag-patterns/modules/production-patterns.md) | 에러 핸들링, Circuit Breaker, Retry |
| Monitoring Setup | [references/monitoring-setup.md](skills/qdrant-mastery/references/monitoring-setup.md) | Prometheus, Grafana 설정 |
| Cost Calculator | [references/cost-calculator.md](skills/rag-patterns/references/cost-calculator.md) | RAG 비용 계산 |
| Benchmark Scripts | [references/benchmark-scripts.md](skills/rag-patterns/references/benchmark-scripts.md) | 성능 벤치마크 |

## 구조

```
vector-rag-backend/
├── agents/           # 4개 에이전트
├── skills/           # 4개 스킬
│   └── {skill}/
│       ├── SKILL.md
│       ├── modules/      # 개념/패턴 가이드
│       ├── references/   # 치트시트, 템플릿
│       └── tutorials/    # 실습 튜토리얼
├── infrastructure/   # Docker Compose 환경
│   ├── docker-compose.yml
│   ├── prometheus.yml
│   └── README.md
└── README.md
```
