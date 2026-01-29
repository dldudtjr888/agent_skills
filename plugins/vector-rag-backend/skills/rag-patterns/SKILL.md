---
name: rag-patterns
description: |
  RAG (Retrieval-Augmented Generation) 시스템 설계 패턴.
  청킹 전략, 검색 최적화, 리랭킹, 컨텍스트 엔지니어링 종합 가이드.
version: 1.0.0
category: rag
user-invocable: true
triggers:
  keywords:
    - rag
    - retrieval augmented generation
    - 검색 증강 생성
    - chunking
    - 청킹
    - reranking
    - 리랭킹
    - retrieval
    - context engineering
    - 컨텍스트 엔지니어링
    - rag 파이프라인
  intentPatterns:
    - "(구축|설계|구현|최적화).*(rag|검색.*증강)"
    - "(build|create|implement|optimize).*(rag|retrieval)"
    - "(청킹|리랭킹|검색).*(전략|최적화|개선)"
---

# RAG Patterns

RAG 시스템을 효과적으로 설계하고 최적화하기 위한 패턴 가이드.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Chunking Strategies | [modules/chunking-strategies.md](modules/chunking-strategies.md) | 시맨틱, 적응형, 계층적 청킹 |
| 2 | Retrieval Optimization | [modules/retrieval-optimization.md](modules/retrieval-optimization.md) | 쿼리 변환, 필터링, 다단계 검색 |
| 3 | Reranking Patterns | [modules/reranking-patterns.md](modules/reranking-patterns.md) | Cross-encoder, LLM 리랭커 |
| 4 | Context Engineering | [modules/context-engineering.md](modules/context-engineering.md) | 리패킹, 압축, 롱컨텍스트 전략 |
| 5 | **Production Patterns** | [modules/production-patterns.md](modules/production-patterns.md) | 에러 핸들링, Circuit Breaker, 재시도 |

## 빠른 참조

| 참조 | 파일 | 설명 |
|------|------|------|
| Evaluation Metrics | [references/evaluation-metrics.md](references/evaluation-metrics.md) | 품질 측정 메트릭 |
| Pipeline Templates | [references/pipeline-templates.md](references/pipeline-templates.md) | RAG 파이프라인 코드 템플릿 |
| Troubleshooting | [references/troubleshooting.md](references/troubleshooting.md) | 일반 오류 해결 가이드 |
| Compatibility | [references/compatibility.md](references/compatibility.md) | 라이브러리 버전 호환성 |
| **Cost Calculator** | [references/cost-calculator.md](references/cost-calculator.md) | RAG 비용 계산 및 최적화 |
| **Benchmark Scripts** | [references/benchmark-scripts.md](references/benchmark-scripts.md) | 성능 벤치마크 스크립트 |

## 실습 튜토리얼

| # | 튜토리얼 | 파일 | 학습 내용 |
|---|----------|------|-----------|
| 1 | Basic RAG | [tutorials/01-basic-rag.md](tutorials/01-basic-rag.md) | PDF 로드, 청킹, 벡터 저장, Q&A |
| 2 | Advanced RAG | [tutorials/02-advanced-rag-with-reranking.md](tutorials/02-advanced-rag-with-reranking.md) | Cross-encoder, Cohere 리랭킹 |
| 3 | Hybrid Search | [tutorials/03-hybrid-search.md](tutorials/03-hybrid-search.md) | BM25 + Vector, RRF 융합 |
| 4 | **GraphRAG** | [tutorials/04-graphrag-with-falkordb.md](tutorials/04-graphrag-with-falkordb.md) | FalkorDB + LangChain 하이브리드 |

## RAG 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Indexing Pipeline:                                          │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │Document │──▶│  Chunk  │──▶│  Embed  │──▶│  Store  │     │
│  │ Loader  │   │         │   │         │   │(Vector) │     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘     │
│                                                              │
│  Query Pipeline:                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │  Query  │──▶│Transform│──▶│Retrieve │──▶│ Rerank  │     │
│  │         │   │         │   │         │   │         │     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘     │
│                                    │                         │
│  ┌─────────┐   ┌─────────┐   ┌────┴────┐                   │
│  │Response │◀──│Generate │◀──│ Repack  │                   │
│  │         │   │  (LLM)  │   │         │                   │
│  └─────────┘   └─────────┘   └─────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 핵심 인사이트

### 청킹의 중요성

| 전략 | 정확도 | 특징 |
|------|--------|------|
| Fixed-length | 50% | 빠르지만 의미 단위 손실 |
| Semantic | **87%** | 의미 경계 보존 (+37%) |
| Adaptive | 85-90% | 문서 구조 활용 |

### Reranking ROI

> "Reranking is one of the highest ROI upgrades in RAG"

- 초기 검색 후 10-15% 정확도 향상
- Cross-encoder로 top-k 재정렬
- 비용 대비 효과가 가장 좋음

### Context Engineering

| 전략 | 설명 | 효과 |
|------|------|------|
| Forward | 관련도 높은 것 먼저 | 기본 |
| Reverse | 관련도 높은 것 마지막 | "Lost in the middle" 완화 |
| Sides | 관련도 높은 것 처음과 끝 | **최적** |

## RAG 최적화 우선순위

```
1. Chunking 최적화 (가장 큰 영향)
   └─ 시맨틱 청킹, 적절한 크기

2. 검색 품질 향상
   ├─ 하이브리드 검색 (BM25 + Vector)
   └─ 쿼리 변환 (HyDE, Multi-Query)

3. Reranking 추가 (높은 ROI)
   └─ Cross-encoder 또는 Cohere

4. Context Engineering
   ├─ Repacking 전략
   └─ 압축 및 필터링

5. 생성 최적화
   └─ 프롬프트 엔지니어링, Citation
```

## 사용 시점

### When to Optimize RAG
- Recall@10 < 0.9
- 답변의 환각(Hallucination)이 빈번
- 응답 시간이 느림
- 비용이 과도함

### RAG vs Fine-tuning

| 항목 | RAG | Fine-tuning |
|------|-----|-------------|
| 지식 업데이트 | 실시간 가능 | 재학습 필요 |
| 환각 제어 | 쉬움 (소스 명시) | 어려움 |
| 도메인 지식 | 외부 데이터 활용 | 모델에 내재화 |
| 비용 | 검색 비용 | 학습 비용 |
| 적합 상황 | 동적 지식, 출처 중요 | 스타일/형식, 정적 지식 |

## 관련 에이전트

- `@rag-system-builder` - RAG 파이프라인 구축
- `@rag-performance-analyst` - RAG 성능 분석
- `@vector-db-architect` - 벡터 저장소 설계

## 관련 스킬

- `qdrant-mastery` - 벡터 데이터베이스
- `falkordb-graphrag` - GraphRAG 패턴
- `semantic-search` - 시맨틱 검색
