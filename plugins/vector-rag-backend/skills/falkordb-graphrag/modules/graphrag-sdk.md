# GraphRAG SDK

FalkorDB GraphRAG-SDK를 활용한 자동 지식 그래프 구축 및 RAG 파이프라인

## 설치

```bash
pip install graphrag-sdk
pip install falkordb
```

## 기본 사용법

### 초기화

```python
from graphrag_sdk import KnowledgeGraph, Ontology
from graphrag_sdk.source import Source
from falkordb import FalkorDB

# FalkorDB 연결
db = FalkorDB(host='localhost', port=6379)

# Knowledge Graph 초기화
kg = KnowledgeGraph(
    name="my_knowledge_graph",
    host="localhost",
    port=6379,
)
```

### 문서에서 지식 그래프 자동 생성

```python
from graphrag_sdk import KnowledgeGraph
from graphrag_sdk.source import Source

# 1. Knowledge Graph 생성
kg = KnowledgeGraph(name="documents_kg")

# 2. 문서 소스 추가
sources = [
    Source.from_file("document1.pdf"),
    Source.from_file("document2.txt"),
    Source.from_url("https://example.com/article"),
]

# 3. 자동으로 엔티티 추출 및 그래프 구축
kg.process_sources(sources)

# 4. 질문-답변
answer = kg.ask("What is the main topic discussed?")
print(answer)
```

## 온톨로지 정의

### 자동 온톨로지 생성

```python
from graphrag_sdk import KnowledgeGraph, Ontology

# 문서에서 자동으로 온톨로지 추론
kg = KnowledgeGraph(name="auto_ontology_kg")
sources = [Source.from_file("domain_documents.pdf")]

# 온톨로지 자동 생성
ontology = kg.detect_ontology(sources)
print(ontology.to_json())
```

### 수동 온톨로지 정의

```python
from graphrag_sdk import Ontology
from graphrag_sdk.models import Entity, Relation

# 도메인 온톨로지 정의
ontology = Ontology()

# 엔티티 타입 정의
ontology.add_entity(Entity(
    name="Person",
    properties=["name", "title", "email"],
    description="A human individual"
))

ontology.add_entity(Entity(
    name="Organization",
    properties=["name", "industry", "founded"],
    description="A company or institution"
))

ontology.add_entity(Entity(
    name="Technology",
    properties=["name", "category", "version"],
    description="A technical tool or framework"
))

# 관계 타입 정의
ontology.add_relation(Relation(
    name="WORKS_AT",
    source="Person",
    target="Organization",
    properties=["role", "since"]
))

ontology.add_relation(Relation(
    name="USES",
    source="Person",
    target="Technology",
    properties=["proficiency"]
))

ontology.add_relation(Relation(
    name="DEVELOPS",
    source="Organization",
    target="Technology",
    properties=["since"]
))

# 온톨로지 적용
kg = KnowledgeGraph(name="tech_kg", ontology=ontology)
```

## 문서 처리

### 다양한 소스 지원

```python
from graphrag_sdk.source import Source

# 파일 소스
pdf_source = Source.from_file("document.pdf")
txt_source = Source.from_file("notes.txt")
md_source = Source.from_file("readme.md")

# URL 소스
web_source = Source.from_url("https://docs.example.com")

# 텍스트 직접 입력
text_source = Source.from_text("""
    Alice is a software engineer at TechCorp.
    She specializes in machine learning and Python.
""")

# 배치 처리
all_sources = [pdf_source, txt_source, web_source, text_source]
kg.process_sources(all_sources)
```

### 처리 옵션

```python
# 커스텀 처리 설정
kg.process_sources(
    sources,
    chunk_size=1000,           # 청크 크기
    chunk_overlap=200,          # 청크 오버랩
    extraction_model="gpt-4",   # 엔티티 추출 모델
    embedding_model="text-embedding-3-small",  # 임베딩 모델
)
```

## 질문-답변

### 기본 Q&A

```python
# 단순 질문
answer = kg.ask("Who works at TechCorp?")

# 상세 응답 (소스 포함)
response = kg.ask("What technologies does Alice use?", include_sources=True)
print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")
print(f"Confidence: {response.confidence}")
```

### 대화 컨텍스트

```python
from graphrag_sdk import Conversation

# 대화 세션 생성
conv = Conversation(kg)

# 멀티턴 대화
conv.ask("Tell me about Alice")
conv.ask("What company does she work for?")  # 컨텍스트 유지
conv.ask("What do they build?")               # 이전 대화 참조
```

### 고급 쿼리

```python
# Cypher 직접 실행
result = kg.query("""
    MATCH (p:Person)-[:WORKS_AT]->(o:Organization)
    WHERE o.name = 'TechCorp'
    RETURN p.name, p.title
""")

# 그래프 탐색 기반 답변
answer = kg.ask(
    "What is the relationship between Alice and Python?",
    max_hops=3,  # 최대 탐색 깊이
)
```

## 그래프 관리

### 그래프 조회

```python
# 통계 조회
stats = kg.get_statistics()
print(f"Nodes: {stats['node_count']}")
print(f"Relationships: {stats['relationship_count']}")
print(f"Labels: {stats['labels']}")

# 스키마 조회
schema = kg.get_schema()
print(schema)
```

### 데이터 내보내기/가져오기

```python
# 그래프 내보내기
kg.export_to_file("knowledge_graph_backup.json")

# 그래프 가져오기
kg.import_from_file("knowledge_graph_backup.json")
```

### 그래프 시각화

```python
# NetworkX로 변환
import networkx as nx
G = kg.to_networkx()

# 시각화
import matplotlib.pyplot as plt
nx.draw(G, with_labels=True)
plt.show()
```

## LLM 통합

### OpenAI 연동

```python
from graphrag_sdk import KnowledgeGraph
import os

os.environ["OPENAI_API_KEY"] = "your-api-key"

kg = KnowledgeGraph(
    name="openai_kg",
    llm_model="gpt-4",
    embedding_model="text-embedding-3-small",
)
```

### 로컬 LLM (Ollama)

```python
kg = KnowledgeGraph(
    name="local_kg",
    llm_model="ollama/llama2",
    embedding_model="ollama/nomic-embed-text",
    ollama_host="http://localhost:11434",
)
```

### Claude 연동

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

kg = KnowledgeGraph(
    name="claude_kg",
    llm_model="claude-3-sonnet-20240229",
)
```

## 고급 패턴

### 커스텀 엔티티 추출기

```python
from graphrag_sdk.extractors import EntityExtractor

class CustomExtractor(EntityExtractor):
    def extract(self, text: str) -> list:
        # 커스텀 엔티티 추출 로직
        entities = []
        # ... NER, regex, 또는 LLM 기반 추출
        return entities

kg = KnowledgeGraph(
    name="custom_kg",
    entity_extractor=CustomExtractor(),
)
```

### 증분 업데이트

```python
# 새 문서 추가 (기존 그래프 유지)
kg.process_sources(
    new_sources,
    mode="incremental",  # 'replace' or 'incremental'
)

# 특정 소스 삭제
kg.remove_source(source_id="doc_123")
```

### 멀티테넌트

```python
# 테넌트별 별도 그래프
tenant1_kg = KnowledgeGraph(name="tenant1_knowledge")
tenant2_kg = KnowledgeGraph(name="tenant2_knowledge")

# 또는 단일 그래프에서 필터링
kg.ask(
    "What projects are active?",
    filters={"tenant_id": "tenant_123"}
)
```

## RAG 파이프라인 통합

### LangChain 연동

```python
from langchain.retrievers import BaseRetriever
from graphrag_sdk import KnowledgeGraph

class GraphRAGRetriever(BaseRetriever):
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def _get_relevant_documents(self, query: str):
        # GraphRAG 검색
        results = self.kg.search(query, top_k=5)
        return [
            Document(page_content=r.content, metadata=r.metadata)
            for r in results
        ]

# LangChain RAG 체인에서 사용
retriever = GraphRAGRetriever(kg)
```

### 하이브리드 RAG (Vector + Graph)

```python
from graphrag_sdk import KnowledgeGraph
from qdrant_client import QdrantClient

# 하이브리드 검색
def hybrid_search(query: str, kg: KnowledgeGraph, vector_client: QdrantClient):
    # 1. 벡터 검색
    vector_results = vector_client.search(
        collection_name="documents",
        query_vector=embed(query),
        limit=10
    )

    # 2. 그래프 검색
    graph_results = kg.search(query, top_k=10)

    # 3. 결과 병합 (RRF)
    combined = reciprocal_rank_fusion(vector_results, graph_results)

    return combined[:10]
```

## 모니터링 및 디버깅

### 로깅

```python
import logging
logging.basicConfig(level=logging.DEBUG)

kg = KnowledgeGraph(name="debug_kg", verbose=True)
```

### 쿼리 추적

```python
# 쿼리 실행 추적
response = kg.ask("What does Alice do?", trace=True)
print(f"Query trace: {response.trace}")
print(f"Cypher queries executed: {response.trace.queries}")
print(f"Entities found: {response.trace.entities}")
```
