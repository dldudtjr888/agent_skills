---
name: falkordb-graphrag
description: |
  FalkorDB 그래프 데이터베이스 및 GraphRAG 패턴. 지식 그래프 구축,
  OpenCypher 쿼리, 벡터/풀텍스트 인덱싱, GraphRAG-SDK 활용.
version: 1.0.0
category: graph-database
user-invocable: true
triggers:
  keywords:
    - falkordb
    - graphrag
    - knowledge graph
    - 지식 그래프
    - cypher
    - graph database
    - 그래프 DB
    - 그래프 데이터베이스
    - property graph
    - 프로퍼티 그래프
    - graph rag
  intentPatterns:
    - "(구축|생성|설계).*(지식.*그래프|knowledge.*graph|graphrag)"
    - "(build|create|implement).*(knowledge.*graph|graphrag)"
    - "(쿼리|검색).*(그래프|cypher)"
    - "(falkordb|graphrag).*(설정|사용|구현)"
---

# FalkorDB GraphRAG

FalkorDB를 활용한 지식 그래프 구축 및 GraphRAG 패턴 가이드.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Graph Modeling | [modules/graph-modeling.md](modules/graph-modeling.md) | 노드, 엣지, 프로퍼티 설계 |
| 2 | Cypher Patterns | [modules/cypher-patterns.md](modules/cypher-patterns.md) | OpenCypher 쿼리 패턴 |
| 3 | Indexing Strategies | [modules/indexing-strategies.md](modules/indexing-strategies.md) | 풀텍스트, 벡터, 레인지 인덱스 |
| 4 | GraphRAG SDK | [modules/graphrag-sdk.md](modules/graphrag-sdk.md) | 자동 KG 구축, 온톨로지 |

## 빠른 참조

| 참조 | 파일 | 설명 |
|------|------|------|
| Quick Reference | [references/quick-reference.md](references/quick-reference.md) | Cypher 문법 및 명령 |
| KG Templates | [references/knowledge-graph-templates.md](references/knowledge-graph-templates.md) | 도메인별 KG 스키마 |

## 실습 튜토리얼

| # | 튜토리얼 | 파일 | 학습 내용 |
|---|----------|------|-----------|
| 1 | **GraphRAG Quickstart** | [tutorials/01-graphrag-quickstart.md](tutorials/01-graphrag-quickstart.md) | GraphRAG-SDK로 KG 구축 |

## FalkorDB란?

FalkorDB는 LLM을 위한 고성능 그래프 데이터베이스입니다.

### 핵심 특징

- **초저지연**: 희소 행렬 기반으로 빠른 그래프 연산
- **GraphRAG**: 지식 그래프 + RAG 통합
- **벡터 검색**: 그래프 내 벡터 유사도 검색
- **AVX 가속**: 하드웨어 최적화

### GraphRAG vs Traditional RAG

| 항목 | Traditional RAG | GraphRAG |
|------|----------------|----------|
| 데이터 구조 | 벡터 청크 | 구조화된 그래프 |
| 쿼리 속도 | Baseline | **5x 빠름** |
| 환각 감소 | ~50% | **~90%** |
| 인프라 비용 | Baseline | **40% 절감** |
| 추론 지연 | Baseline | **70% 감소** |
| 설명 가능성 | 낮음 | **높음** (경로 추적) |

## 사용 시점

### When to Use FalkorDB
- 엔티티 간 관계가 중요한 RAG 시스템
- 다중 홉 추론이 필요한 질의 (A→B→C 관계)
- 설명 가능한 AI 응답이 필요할 때
- 복잡한 도메인 지식 모델링 (의료, 법률, 금융)

### When NOT to Use
- 단순 시맨틱 검색 → Qdrant (`qdrant-mastery` skill)
- 관계가 없는 독립 문서 → Vector DB
- 실시간 임베딩 검색만 필요 → Vector DB

## 핵심 개념

### Property Graph Model

```
┌─────────────────────────────────────────────────────────┐
│                    Knowledge Graph                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌──────────┐         ┌──────────┐         ┌─────────┐ │
│   │  Node    │──EDGE──▶│  Node    │──EDGE──▶│  Node   │ │
│   │ (Entity) │         │ (Entity) │         │(Entity) │ │
│   │ :Label   │         │ :Label   │         │ :Label  │ │
│   │ {props}  │         │ {props}  │         │ {props} │ │
│   └──────────┘         └──────────┘         └─────────┘ │
│                                                          │
│   Components:                                            │
│   - Node: 엔티티 (Person, Document, Concept)            │
│   - Edge: 관계 (KNOWS, MENTIONS, RELATED_TO)            │
│   - Label: 노드/엣지 타입                                │
│   - Properties: 속성 (key-value)                         │
└─────────────────────────────────────────────────────────┘
```

### GraphRAG 아키텍처

```
Document Ingestion:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Document │───▶│ Extract  │───▶│ Resolve  │───▶│  Store   │
│          │    │ Entities │    │ Relations│    │ in Graph │
└──────────┘    └──────────┘    └──────────┘    └──────────┘

Query Pipeline:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Query   │───▶│ Identify │───▶│ Traverse │───▶│ Generate │
│          │    │ Entities │    │  Graph   │    │ Response │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 설치 및 시작

### Docker

```bash
docker run -p 6379:6379 -it --rm falkordb/falkordb
```

### Python Client

```bash
pip install falkordb
```

### 기본 사용

```python
from falkordb import FalkorDB

# 연결
db = FalkorDB(host='localhost', port=6379)

# 그래프 선택/생성
graph = db.select_graph('knowledge')

# 노드 생성
graph.query("""
    CREATE (p:Person {name: 'Alice', role: 'Engineer'})
    CREATE (c:Company {name: 'TechCorp'})
    CREATE (p)-[:WORKS_AT {since: 2020}]->(c)
""")

# 조회
result = graph.query("""
    MATCH (p:Person)-[r:WORKS_AT]->(c:Company)
    RETURN p.name, c.name, r.since
""")
```

## 관련 에이전트

- `@vector-db-architect` - 하이브리드 벡터+그래프 설계
- `@rag-system-builder` - GraphRAG 파이프라인 구축
- `@rag-performance-analyst` - GraphRAG 성능 분석

## 관련 스킬

- `qdrant-mastery` - 벡터 데이터베이스 (하이브리드 구성 시)
- `rag-patterns` - RAG 시스템 패턴
