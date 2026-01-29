# FalkorDB Quick Reference

Cypher 문법 및 자주 사용하는 명령어 빠른 참조

## 설치

```bash
# Docker
docker run -p 6379:6379 -it --rm falkordb/falkordb

# Python Client
pip install falkordb
```

## 연결

```python
from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('my_graph')
```

## CRUD 치트시트

### CREATE

```cypher
-- 노드
CREATE (n:Label {prop: value})

-- 관계
CREATE (a)-[:REL_TYPE {prop: value}]->(b)

-- 기존 노드에 관계
MATCH (a:Label1 {id: 1}), (b:Label2 {id: 2})
CREATE (a)-[:RELATES_TO]->(b)
```

### MATCH

```cypher
-- 기본
MATCH (n:Label) RETURN n

-- 조건
MATCH (n:Label) WHERE n.prop = value RETURN n

-- 관계
MATCH (a)-[r:REL]->(b) RETURN a, r, b

-- 경로
MATCH path = (a)-[:REL*1..3]->(b) RETURN path
```

### MERGE (Upsert)

```cypher
MERGE (n:Label {id: 1})
ON CREATE SET n.created = datetime()
ON MATCH SET n.updated = datetime()
```

### UPDATE

```cypher
MATCH (n:Label {id: 1})
SET n.prop = newValue
REMOVE n.oldProp
```

### DELETE

```cypher
-- 노드 (관계 없어야 함)
MATCH (n:Label {id: 1}) DELETE n

-- 노드 + 관계
MATCH (n:Label {id: 1}) DETACH DELETE n

-- 관계만
MATCH ()-[r:REL]->() DELETE r
```

## 패턴 매칭

```cypher
-- 방향 있음
(a)-[:REL]->(b)

-- 방향 없음
(a)-[:REL]-(b)

-- 여러 타입
(a)-[:REL1|:REL2]->(b)

-- 가변 길이
(a)-[:REL*1..3]->(b)  -- 1~3 홉
(a)-[:REL*]->(b)      -- 모든 길이
```

## 필터링

```cypher
-- 비교
WHERE n.age > 30
WHERE n.name = 'Alice'
WHERE n.name STARTS WITH 'A'
WHERE n.name CONTAINS 'ice'

-- 논리 연산
WHERE n.age > 30 AND n.active = true
WHERE n.role = 'admin' OR n.role = 'manager'
WHERE NOT n.deleted

-- IN 연산
WHERE n.status IN ['active', 'pending']

-- NULL 체크
WHERE n.email IS NOT NULL
```

## 집계

```cypher
-- 카운트
RETURN count(n)

-- 합계/평균
RETURN sum(n.amount), avg(n.amount)

-- 최소/최대
RETURN min(n.date), max(n.date)

-- 그룹화
RETURN n.category, count(n)

-- 수집
RETURN collect(n.name)
```

## 정렬 및 제한

```cypher
ORDER BY n.name ASC
ORDER BY n.created DESC
LIMIT 10
SKIP 20
```

## 경로

```cypher
-- 최단 경로
MATCH path = shortestPath((a)-[:REL*]-(b))
RETURN path

-- 경로 길이
RETURN length(path)

-- 경로 노드/관계
RETURN nodes(path), relationships(path)
```

## 인덱스

```cypher
-- Exact 인덱스
CREATE INDEX FOR (n:Label) ON (n.prop)

-- Unique 제약
CREATE CONSTRAINT ON (n:Label) ASSERT n.id IS UNIQUE

-- Full-Text
CALL db.idx.fulltext.createNodeIndex('Label', 'prop')

-- Vector
CALL db.idx.vector.createNodeIndex('Label', 'embedding', {dimension: 1536, similarityFunction: 'cosine'})

-- 인덱스 조회
CALL db.indexes()

-- 삭제
DROP INDEX index_name
```

## 검색

### Full-Text 검색

```cypher
CALL db.idx.fulltext.queryNodes('Label', 'search term')
YIELD node, score
RETURN node, score
ORDER BY score DESC
```

### Vector 검색

```cypher
CALL db.idx.vector.queryNodes('Label', 'embedding', $vector, 10)
YIELD node, score
RETURN node.content, score
```

## 유용한 함수

```cypher
-- 문자열
toString(n.id), toUpper(n.name), toLower(n.name)
trim(n.text), replace(n.text, 'old', 'new')

-- 숫자
toInteger('123'), toFloat('3.14')
abs(n), ceil(n), floor(n), round(n)

-- 리스트
size(list), head(list), tail(list), last(list)
range(0, 10), reverse(list)

-- 날짜
datetime(), date(), time()
datetime().year, datetime().month

-- 타입 체크
type(r), labels(n)
```

## WITH 절

```cypher
-- 중간 결과 처리
MATCH (n:Label)
WITH n, count(*) as cnt
WHERE cnt > 5
RETURN n
```

## UNWIND

```cypher
-- 리스트 펼치기
UNWIND [1, 2, 3] as x
CREATE (n:Node {id: x})
```

## CASE

```cypher
RETURN CASE
    WHEN n.age < 20 THEN 'Teen'
    WHEN n.age < 40 THEN 'Adult'
    ELSE 'Senior'
END as category
```

## GraphRAG SDK 빠른 시작

```python
from graphrag_sdk import KnowledgeGraph
from graphrag_sdk.source import Source

# KG 생성
kg = KnowledgeGraph(name="my_kg")

# 문서 처리
kg.process_sources([Source.from_file("doc.pdf")])

# 질문
answer = kg.ask("What is the main topic?")
```
