# Cypher Patterns

OpenCypher 쿼리 패턴 - CRUD, 패턴 매칭, 경로 탐색

## 기본 CRUD

### CREATE

```cypher
// 단일 노드
CREATE (p:Person {name: 'Alice', age: 30})

// 여러 노드
CREATE (a:Person {name: 'Alice'}),
       (b:Person {name: 'Bob'}),
       (c:Company {name: 'TechCorp'})

// 노드와 관계 함께
CREATE (a:Person {name: 'Alice'})-[:WORKS_AT {since: 2020}]->(c:Company {name: 'TechCorp'})

// 기존 노드에 관계 추가
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
CREATE (a)-[:KNOWS {since: date()}]->(b)
```

### MERGE (Upsert)

```cypher
// 없으면 생성, 있으면 매칭
MERGE (p:Person {name: 'Alice'})
ON CREATE SET p.created_at = datetime()
ON MATCH SET p.last_seen = datetime()

// 관계 MERGE
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
MERGE (a)-[r:KNOWS]->(b)
ON CREATE SET r.since = date()
```

### READ (MATCH)

```cypher
// 기본 조회
MATCH (p:Person) RETURN p

// 조건 필터
MATCH (p:Person)
WHERE p.age > 25 AND p.name STARTS WITH 'A'
RETURN p.name, p.age

// 관계 조회
MATCH (p:Person)-[r:WORKS_AT]->(c:Company)
RETURN p.name, type(r), c.name

// 선택적 매칭 (LEFT JOIN 같은)
MATCH (p:Person)
OPTIONAL MATCH (p)-[:HAS_ADDRESS]->(a:Address)
RETURN p.name, a.city
```

### UPDATE

```cypher
// 속성 수정
MATCH (p:Person {name: 'Alice'})
SET p.age = 31, p.updated_at = datetime()

// 속성 추가/제거
MATCH (p:Person {name: 'Alice'})
SET p.title = 'Senior Engineer'
REMOVE p.temp_field

// Label 추가/제거
MATCH (p:Person {name: 'Alice'})
SET p:Manager
REMOVE p:Junior
```

### DELETE

```cypher
// 노드 삭제 (관계 없어야 함)
MATCH (p:Person {name: 'Alice'})
DELETE p

// 노드와 관계 함께 삭제
MATCH (p:Person {name: 'Alice'})
DETACH DELETE p

// 관계만 삭제
MATCH (a:Person)-[r:KNOWS]->(b:Person)
WHERE a.name = 'Alice' AND b.name = 'Bob'
DELETE r

// 조건부 삭제
MATCH (p:Person)
WHERE p.last_login < datetime() - duration('P30D')
DETACH DELETE p
```

## 패턴 매칭

### 기본 패턴

```cypher
// 방향 있는 관계
MATCH (a)-[:KNOWS]->(b)

// 방향 없는 관계
MATCH (a)-[:KNOWS]-(b)

// 여러 관계 타입
MATCH (a)-[:KNOWS|:WORKS_WITH]->(b)

// 가변 길이 경로
MATCH (a)-[:KNOWS*1..3]->(b)  // 1~3 홉
MATCH (a)-[:KNOWS*2]->(b)     // 정확히 2 홉
MATCH (a)-[:KNOWS*]->(b)      // 모든 길이
```

### 복합 패턴

```cypher
// 삼각 관계
MATCH (a:Person)-[:KNOWS]->(b:Person)-[:KNOWS]->(c:Person)
WHERE (a)-[:KNOWS]->(c)
RETURN a, b, c

// 경로와 함께
MATCH path = (a:Person)-[:KNOWS*1..3]->(b:Person)
WHERE a.name = 'Alice'
RETURN path, length(path)

// 여러 패턴 조합
MATCH (p:Person)-[:WORKS_AT]->(c:Company),
      (p)-[:LIVES_IN]->(city:City)
WHERE c.name = 'TechCorp'
RETURN p.name, city.name
```

### 제외 패턴

```cypher
// NOT EXISTS
MATCH (p:Person)
WHERE NOT EXISTS ((p)-[:HAS_ADDRESS]->())
RETURN p.name

// 특정 관계 없는 경우
MATCH (a:Person), (b:Person)
WHERE a.name = 'Alice'
  AND NOT (a)-[:KNOWS]->(b)
RETURN b.name
```

## 집계 및 그룹핑

### 기본 집계

```cypher
// COUNT
MATCH (p:Person)
RETURN count(p) as total

// 조건부 카운트
MATCH (p:Person)
RETURN
    count(p) as total,
    count(CASE WHEN p.age > 30 THEN 1 END) as over_30

// SUM, AVG, MIN, MAX
MATCH (p:Person)-[:PURCHASED]->(o:Order)
RETURN
    p.name,
    sum(o.amount) as total_spent,
    avg(o.amount) as avg_order,
    count(o) as order_count
```

### GROUP BY

```cypher
// 부서별 직원 수
MATCH (e:Employee)-[:WORKS_IN]->(d:Department)
RETURN d.name, count(e) as employee_count
ORDER BY employee_count DESC

// 복합 그룹핑
MATCH (e:Employee)-[:WORKS_IN]->(d:Department)
RETURN d.name, e.role, count(e) as count
```

### COLLECT

```cypher
// 리스트로 수집
MATCH (p:Person)-[:KNOWS]->(friend:Person)
RETURN p.name, collect(friend.name) as friends

// 중복 제거
MATCH (p:Person)-[:VISITED]->(c:City)
RETURN p.name, collect(DISTINCT c.name) as cities
```

## 경로 탐색

### 최단 경로

```cypher
// shortestPath
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
MATCH path = shortestPath((a)-[:KNOWS*]-(b))
RETURN path, length(path)

// 조건부 최단 경로
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
MATCH path = shortestPath((a)-[:KNOWS*]-(b))
WHERE all(node IN nodes(path) WHERE node.active = true)
RETURN path
```

### 모든 경로

```cypher
// allShortestPaths
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
MATCH path = allShortestPaths((a)-[:KNOWS*]-(b))
RETURN path
```

### 경로 분석

```cypher
// 경로의 노드와 관계 추출
MATCH path = (a:Person)-[:KNOWS*1..3]->(b:Person)
WHERE a.name = 'Alice'
RETURN
    nodes(path) as people,
    relationships(path) as connections,
    length(path) as hops
```

## GraphRAG 쿼리 패턴

### 엔티티 기반 검색

```cypher
// 엔티티에서 관련 청크 찾기
MATCH (e:Entity {name: $entity_name})<-[:MENTIONS]-(c:Chunk)
RETURN c.content, c.id
ORDER BY c.position
LIMIT 5
```

### 다중 홉 추론

```cypher
// 2홉 관계 탐색
MATCH (e1:Entity {name: $entity})-[r1]-(e2:Entity)-[r2]-(e3:Entity)
RETURN e1.name, type(r1), e2.name, type(r2), e3.name
LIMIT 10
```

### 컨텍스트 수집

```cypher
// 질문 관련 모든 컨텍스트 수집
MATCH (q:Question {text: $question})
MATCH (q)-[:ABOUT]->(t:Topic)
MATCH (t)<-[:ABOUT]-(related:Question)-[:HAS_ANSWER]->(a:Answer)
WHERE related <> q
RETURN related.text, a.text, a.confidence
ORDER BY a.confidence DESC
LIMIT 5
```

### 하이브리드 검색

```cypher
// 벡터 + 그래프 조합
// 1. 벡터 검색으로 관련 청크 찾기
CALL db.idx.vector.queryNodes('Chunk', 'embedding', $query_embedding, 10)
YIELD node as chunk, score
// 2. 그래프 탐색으로 관련 엔티티 확장
MATCH (chunk)-[:MENTIONS]->(e:Entity)-[:RELATES_TO*1..2]-(related:Entity)
RETURN chunk.content, collect(DISTINCT related.name) as entities, score
ORDER BY score DESC
```

## 고급 패턴

### WITH 절 활용

```cypher
// 중간 결과 필터링
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WITH c, count(p) as employee_count
WHERE employee_count > 100
MATCH (c)-[:LOCATED_IN]->(city:City)
RETURN c.name, employee_count, city.name
```

### UNWIND

```cypher
// 리스트 펼치기
UNWIND $entity_list as entity_name
MERGE (e:Entity {name: entity_name})
RETURN count(e)

// 배치 관계 생성
UNWIND $relations as rel
MATCH (a:Entity {name: rel.from}), (b:Entity {name: rel.to})
MERGE (a)-[:RELATES_TO {type: rel.type}]->(b)
```

### CASE 표현식

```cypher
MATCH (p:Person)
RETURN p.name,
    CASE
        WHEN p.age < 20 THEN 'Teen'
        WHEN p.age < 40 THEN 'Adult'
        ELSE 'Senior'
    END as age_group
```

### 서브쿼리

```cypher
// EXISTS 서브쿼리
MATCH (p:Person)
WHERE EXISTS {
    MATCH (p)-[:AUTHORED]->(d:Document)
    WHERE d.citations > 100
}
RETURN p.name

// COUNT 서브쿼리
MATCH (p:Person)
RETURN p.name,
    COUNT { (p)-[:AUTHORED]->(:Document) } as doc_count
```
