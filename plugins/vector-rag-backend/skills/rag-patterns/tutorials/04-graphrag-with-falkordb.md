# Tutorial 04: GraphRAG with FalkorDB + LangChain

LangChain과 FalkorDB를 통합한 하이브리드 GraphRAG 시스템 구축

## 목표

- LangChain에서 FalkorDB 사용
- 엔티티/관계 추출 파이프라인 구축
- Vector + Graph 하이브리드 검색
- 기존 RAG 대비 성능 비교

## 사전 요구사항

```bash
# FalkorDB 실행
docker run -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest

# 패키지 설치
pip install falkordb langchain langchain-openai langchain-community
pip install qdrant-client  # 벡터 DB
```

---

## Step 1: Vector RAG vs GraphRAG 비교

### 기존 Vector RAG의 한계

```
Query: "스티브 잡스가 설립한 회사들의 CEO는 누구인가요?"

Vector RAG 동작:
1. 쿼리 임베딩 → [0.12, -0.34, ...]
2. 유사 문서 검색 → "스티브 잡스는 Apple을 설립했습니다..."
3. 문제: 멀티홉 추론 불가 (잡스 → Apple → CEO)
```

### GraphRAG의 장점

```
GraphRAG 동작:
1. 쿼리 → Cypher: MATCH (p:Person)-[:FOUNDED]->(c:Company)<-[:CEO_OF]-(ceo)
2. 그래프 탐색 → 잡스 → Apple → 팀 쿡
3. 관계 기반 정확한 답변
```

---

## Step 2: FalkorDB + LangChain 연결

### 기본 연결

```python
from falkordb import FalkorDB
from langchain_community.graphs import FalkorDBGraph

# 방법 1: 직접 연결
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('langchain_demo')

# 방법 2: LangChain 래퍼
langchain_graph = FalkorDBGraph(
    host='localhost',
    port=6379,
    database='langchain_demo'
)

# 스키마 확인
print(langchain_graph.get_schema)
```

---

## Step 3: 엔티티/관계 추출 파이프라인

### LLM 기반 추출

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import json
import re

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 추출 프롬프트
extraction_prompt = ChatPromptTemplate.from_template("""
Extract entities and relationships from the following text.

Return a JSON object with:
- "entities": list of {{"type": "...", "name": "...", "attributes": {{}}}}
- "relationships": list of {{"source": "...", "relation": "...", "target": "..."}}

Text:
{text}

JSON:
""")

def extract_graph_data(text: str) -> dict:
    """텍스트에서 엔티티와 관계 추출"""
    chain = extraction_prompt | llm | StrOutputParser()
    result = chain.invoke({"text": text})

    # JSON 파싱
    try:
        # 코드 블록 제거
        json_str = re.sub(r'```json\n?|\n?```', '', result)
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"entities": [], "relationships": []}


# 테스트
text = """
Apple Inc. was founded by Steve Jobs in 1976.
Tim Cook became CEO of Apple in 2011.
Apple created the iPhone in 2007.
"""

data = extract_graph_data(text)
print(json.dumps(data, indent=2))
```

**출력 예시:**
```json
{
  "entities": [
    {"type": "Company", "name": "Apple Inc.", "attributes": {"founded": 1976}},
    {"type": "Person", "name": "Steve Jobs", "attributes": {}},
    {"type": "Person", "name": "Tim Cook", "attributes": {}},
    {"type": "Product", "name": "iPhone", "attributes": {"year": 2007}}
  ],
  "relationships": [
    {"source": "Steve Jobs", "relation": "FOUNDED", "target": "Apple Inc."},
    {"source": "Tim Cook", "relation": "CEO_OF", "target": "Apple Inc."},
    {"source": "Apple Inc.", "relation": "CREATED", "target": "iPhone"}
  ]
}
```

---

## Step 4: Knowledge Graph 구축

```python
def build_knowledge_graph(graph, data: dict):
    """추출된 데이터로 Knowledge Graph 구축"""

    # 1. 엔티티(노드) 생성
    for entity in data["entities"]:
        node_type = entity["type"]
        name = entity["name"]
        attrs = entity.get("attributes", {})

        # 속성 문자열 생성
        attr_str = ", ".join(f"{k}: ${k}" for k in attrs.keys())
        params = {"name": name, **attrs}

        query = f"""
        MERGE (n:{node_type} {{name: $name}})
        SET n += {{{attr_str}}}
        RETURN n
        """
        graph.query(query, params)

    # 2. 관계(엣지) 생성
    for rel in data["relationships"]:
        query = f"""
        MATCH (a {{name: $source}})
        MATCH (b {{name: $target}})
        MERGE (a)-[r:{rel['relation']}]->(b)
        RETURN r
        """
        graph.query(query, {
            "source": rel["source"],
            "target": rel["target"]
        })

    print(f"Created {len(data['entities'])} nodes, {len(data['relationships'])} relationships")


# 문서들 처리
documents = [
    "Apple Inc. was founded by Steve Jobs in 1976.",
    "Tim Cook became CEO of Apple in 2011.",
    "Google was founded by Larry Page and Sergey Brin.",
    "Sundar Pichai is the CEO of Google."
]

for doc in documents:
    data = extract_graph_data(doc)
    build_knowledge_graph(graph, data)
```

---

## Step 5: Cypher 쿼리 생성 (LLM)

```python
from langchain.chains import GraphCypherQAChain

# Cypher QA 체인
cypher_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=langchain_graph,
    verbose=True,
    return_intermediate_steps=True
)

# 자연어 → Cypher → 답변
result = cypher_chain.invoke({
    "query": "Who is the CEO of Apple?"
})

print(f"Answer: {result['result']}")
print(f"Cypher: {result['intermediate_steps'][0]['query']}")
```

### 커스텀 Cypher 생성

```python
cypher_prompt = ChatPromptTemplate.from_template("""
You are a Cypher expert. Generate a Cypher query for FalkorDB.

Schema:
{schema}

Question: {question}

Return ONLY the Cypher query, no explanation.
Cypher:
""")

def generate_cypher(question: str, schema: str) -> str:
    chain = cypher_prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "schema": schema})

# 사용
schema = langchain_graph.get_schema
cypher = generate_cypher("Find all companies founded by Steve Jobs", schema)
print(cypher)

# 실행
result = graph.query(cypher)
print(result.result_set)
```

---

## Step 6: 하이브리드 검색 (Vector + Graph)

### 벡터 저장소 설정

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 문서를 벡터 DB에도 저장
vectorstore = Qdrant.from_texts(
    texts=documents,
    embedding=embeddings,
    location=":memory:",
    collection_name="hybrid_docs"
)

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

### 하이브리드 검색 구현

```python
from typing import List
from langchain.schema import Document

class HybridGraphVectorRetriever:
    """Vector + Graph 하이브리드 검색"""

    def __init__(self, vector_retriever, graph, llm):
        self.vector_retriever = vector_retriever
        self.graph = graph
        self.llm = llm

    def retrieve(self, query: str) -> dict:
        # 1. Vector 검색
        vector_docs = self.vector_retriever.get_relevant_documents(query)
        vector_context = "\n".join(doc.page_content for doc in vector_docs)

        # 2. Graph 검색
        try:
            cypher = self._generate_cypher(query)
            graph_result = self.graph.query(cypher)
            graph_context = self._format_graph_result(graph_result)
        except Exception as e:
            graph_context = ""
            print(f"Graph query failed: {e}")

        return {
            "vector_context": vector_context,
            "graph_context": graph_context,
            "combined": f"Vector Results:\n{vector_context}\n\nGraph Results:\n{graph_context}"
        }

    def _generate_cypher(self, query: str) -> str:
        # 간단한 패턴 매칭 (프로덕션에서는 LLM 사용)
        if "CEO" in query:
            return "MATCH (p:Person)-[:CEO_OF]->(c:Company) RETURN p.name, c.name"
        elif "founded" in query.lower():
            return "MATCH (p:Person)-[:FOUNDED]->(c:Company) RETURN p.name, c.name"
        else:
            return "MATCH (n) RETURN n.name LIMIT 10"

    def _format_graph_result(self, result) -> str:
        if not result.result_set:
            return "No graph results found."
        return "\n".join(str(row) for row in result.result_set)


# 하이브리드 검색기 사용
hybrid_retriever = HybridGraphVectorRetriever(
    vector_retriever=vector_retriever,
    graph=graph,
    llm=llm
)

# 검색
results = hybrid_retriever.retrieve("Who founded Apple?")
print(results["combined"])
```

---

## Step 7: 하이브리드 RAG 체인

```python
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough

# 하이브리드 프롬프트
hybrid_prompt = ChatPromptTemplate.from_template("""
Answer the question using both vector search results and knowledge graph data.

Vector Search Results:
{vector_context}

Knowledge Graph Data:
{graph_context}

Question: {question}

Provide a comprehensive answer that combines insights from both sources.
If information conflicts, prefer the knowledge graph data for factual relationships.

Answer:
""")

def get_hybrid_context(query: str) -> dict:
    return hybrid_retriever.retrieve(query)

# 하이브리드 RAG 체인
hybrid_rag_chain = (
    {
        "vector_context": lambda x: get_hybrid_context(x)["vector_context"],
        "graph_context": lambda x: get_hybrid_context(x)["graph_context"],
        "question": RunnablePassthrough()
    }
    | hybrid_prompt
    | llm
    | StrOutputParser()
)

# 사용
answer = hybrid_rag_chain.invoke("Who are the CEOs of companies founded by Steve Jobs?")
print(answer)
```

---

## Step 8: 성능 비교 테스트

```python
import time

# 테스트 쿼리
test_queries = [
    "Who is the CEO of Apple?",
    "What companies did Steve Jobs found?",
    "List all CEOs and their companies",
    "What's the relationship between Tim Cook and Apple?"
]

# Vector Only
print("=== Vector RAG ===")
for query in test_queries:
    start = time.time()
    docs = vector_retriever.get_relevant_documents(query)
    elapsed = (time.time() - start) * 1000
    print(f"  {query[:40]}... → {elapsed:.0f}ms, {len(docs)} docs")

# Graph Only
print("\n=== Graph RAG ===")
for query in test_queries:
    start = time.time()
    try:
        cypher = generate_cypher(query, schema)
        result = graph.query(cypher)
        elapsed = (time.time() - start) * 1000
        print(f"  {query[:40]}... → {elapsed:.0f}ms, {len(result.result_set)} rows")
    except Exception as e:
        print(f"  {query[:40]}... → Error: {e}")

# Hybrid
print("\n=== Hybrid RAG ===")
for query in test_queries:
    start = time.time()
    result = hybrid_retriever.retrieve(query)
    elapsed = (time.time() - start) * 1000
    print(f"  {query[:40]}... → {elapsed:.0f}ms")
```

---

## 전체 코드

```python
import os
from falkordb import FalkorDB
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# 1. 환경 설정
os.environ["OPENAI_API_KEY"] = "your-api-key"

# 2. 컴포넌트 초기화
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('hybrid_rag')
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 3. 데이터 준비
documents = [
    "Apple Inc. was founded by Steve Jobs in 1976.",
    "Tim Cook became CEO of Apple in 2011.",
    "The iPhone was created by Apple in 2007.",
]

# 4. Vector DB 구축
vectorstore = Qdrant.from_texts(
    texts=documents,
    embedding=embeddings,
    location=":memory:",
    collection_name="docs"
)

# 5. Knowledge Graph 구축 (간소화된 예시)
graph.query("""
CREATE (:Person {name: 'Steve Jobs'})-[:FOUNDED]->(:Company {name: 'Apple'})
""")
graph.query("""
MATCH (c:Company {name: 'Apple'})
CREATE (:Person {name: 'Tim Cook'})-[:CEO_OF]->(c)
""")

# 6. 하이브리드 RAG 체인
def hybrid_retrieve(query: str) -> str:
    # Vector
    docs = vectorstore.similarity_search(query, k=3)
    vector_ctx = "\n".join(d.page_content for d in docs)

    # Graph (간단한 패턴)
    graph_ctx = ""
    if "CEO" in query:
        result = graph.query("MATCH (p)-[:CEO_OF]->(c) RETURN p.name, c.name")
        graph_ctx = str(result.result_set)

    return f"Vector:\n{vector_ctx}\n\nGraph:\n{graph_ctx}"

prompt = ChatPromptTemplate.from_template("""
Context:
{context}

Question: {question}

Answer:
""")

chain = (
    {"context": hybrid_retrieve, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. 사용
answer = chain.invoke("Who is the CEO of Apple?")
print(answer)
```

---

## 다음 단계

- [falkordb-graphrag/modules/graphrag-sdk.md](../../falkordb-graphrag/modules/graphrag-sdk.md) - SDK 상세
- [rag-patterns/modules/retrieval-optimization.md](../modules/retrieval-optimization.md) - 검색 최적화

## 체크리스트

- [ ] FalkorDB + LangChain 연결
- [ ] 엔티티/관계 추출 파이프라인
- [ ] Knowledge Graph 구축
- [ ] Cypher 쿼리 생성
- [ ] Vector + Graph 하이브리드 검색
- [ ] 성능 비교 완료
