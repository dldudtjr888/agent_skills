---
name: qdrant-mastery
description: |
  Qdrant 벡터 데이터베이스 마스터리. 컬렉션 설계, HNSW 인덱싱, 양자화,
  쿼리 최적화, 메모리 관리 전문 가이드.
version: 1.0.0
category: vector-database
user-invocable: true
triggers:
  keywords:
    - qdrant
    - vector database
    - 벡터 DB
    - 벡터 데이터베이스
    - collection
    - 컬렉션
    - HNSW
    - quantization
    - 양자화
    - vector search
    - 벡터 검색
    - embedding storage
    - 임베딩 저장
  intentPatterns:
    - "(설계|생성|구축|최적화).*(qdrant|벡터.*DB|컬렉션)"
    - "(setup|configure|create|optimize).*(qdrant|vector.*database|collection)"
    - "(양자화|quantization).*(적용|설정)"
---

# Qdrant Mastery

Qdrant 벡터 데이터베이스를 효과적으로 설계하고 운영하기 위한 종합 가이드.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Collection Design | [modules/collection-design.md](modules/collection-design.md) | 컬렉션 구조, 페이로드, 샤딩, 거리 메트릭 |
| 2 | Indexing Optimization | [modules/indexing-optimization.md](modules/indexing-optimization.md) | HNSW 파라미터, 세그먼트 설정 |
| 3 | Quantization Strategies | [modules/quantization-strategies.md](modules/quantization-strategies.md) | Scalar, Binary, Product 양자화 |
| 4 | Query Patterns | [modules/query-patterns.md](modules/query-patterns.md) | 검색, 필터링, 배치, 리스코어링 |

## 빠른 참조

| 참조 | 파일 | 설명 |
|------|------|------|
| Quick Reference | [references/quick-reference.md](references/quick-reference.md) | 자주 사용하는 설정 및 명령 |
| Python Cheatsheet | [references/python-cheatsheet.md](references/python-cheatsheet.md) | qdrant-client 코드 예제 |
| **Monitoring Setup** | [references/monitoring-setup.md](references/monitoring-setup.md) | Prometheus/Grafana 모니터링 |

## 사용 시점

### When to Use Qdrant
- 벡터 검색 기반 애플리케이션 구축 (RAG, 추천, 유사도 검색)
- 대규모 임베딩 저장 및 검색 시스템 설계 (1M+ vectors)
- 실시간 필터링이 필요한 시맨틱 검색
- 멀티테넌트 벡터 저장소

### When NOT to Use
- 단순 키-값 저장 → Redis/DynamoDB
- 관계형 데이터 쿼리 → PostgreSQL
- 그래프 기반 추론 → FalkorDB (see `falkordb-graphrag` skill)
- 전문 검색(Full-text) 전용 → Elasticsearch

## 핵심 개념

### Qdrant 아키텍처

```
┌─────────────────────────────────────────────────┐
│                   Collection                     │
├─────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Segment │  │ Segment │  │ Segment │  ...    │
│  │ (HNSW)  │  │ (HNSW)  │  │ (HNSW)  │         │
│  └─────────┘  └─────────┘  └─────────┘         │
├─────────────────────────────────────────────────┤
│  Point = Vector + Payload + ID                   │
│  - Vector: [0.1, 0.2, ..., 0.n] (float32/int8)  │
│  - Payload: {"category": "tech", "date": "..."}  │
│  - ID: UUID or integer                           │
└─────────────────────────────────────────────────┘
```

### 거리 메트릭 선택

| 메트릭 | 사용 시점 | 특징 |
|--------|----------|------|
| **Cosine** | 텍스트 임베딩, 대부분의 경우 | 방향 유사도, 크기 무시 |
| **Euclidean** | 이미지 특징, 좌표 데이터 | 절대 거리 |
| **Dot Product** | 정규화된 벡터, 추천 시스템 | 빠른 계산 |

### HNSW 파라미터 가이드

| Scenario | m | ef_construct | hnsw_ef | Memory | Recall |
|----------|---|--------------|---------|--------|--------|
| **High Recall** | 32 | 200 | 128 | High | 99%+ |
| **Balanced** | 16 | 100 | 64 | Medium | 95%+ |
| **Low Latency** | 8 | 50 | 32 | Low | 90%+ |
| **Memory Limited** | 8 | 100 | 64 | Minimal | 93%+ |

## 관련 에이전트

- `@vector-db-architect` - 벡터 DB 아키텍처 설계
- `@vector-db-reviewer` - 구현 리뷰 및 최적화 제안
- `@rag-performance-analyst` - 성능 분석

## 관련 스킬

- `semantic-search` - 시맨틱 검색 패턴
- `rag-patterns` - RAG 시스템 설계
