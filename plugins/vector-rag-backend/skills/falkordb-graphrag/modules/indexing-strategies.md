# Indexing Strategies

FalkorDB 인덱싱 전략 - 풀텍스트, 벡터, 레인지 인덱스

## 인덱스 종류

| 인덱스 타입 | 용도 | 쿼리 예시 |
|------------|------|----------|
| **Full-Text** | 텍스트 검색 | "machine learning 포함 문서" |
| **Vector** | 시맨틱 유사도 | "이 임베딩과 유사한 노드" |
| **Range** | 숫자/날짜 범위 | "2024년 이후 생성된" |
| **Exact Match** | 정확한 값 매칭 | "name = 'Alice'" |

## Full-Text Index

### 생성

```cypher
// 단일 속성 인덱스
CALL db.idx.fulltext.createNodeIndex('Document', 'content')

// 여러 속성 인덱스
CALL db.idx.fulltext.createNodeIndex('Entity', 'name', 'description')

// 관계 인덱스
CALL db.idx.fulltext.createRelationshipIndex('MENTIONS', 'context')
```

### 쿼리

```cypher
// 기본 검색
CALL db.idx.fulltext.queryNodes('Document', 'machine learning')
YIELD node, score
RETURN node.title, score
ORDER BY score DESC
LIMIT 10

// 와일드카드 검색
CALL db.idx.fulltext.queryNodes('Entity', 'neural*')
YIELD node, score
RETURN node.name, score

// 불리언 검색
CALL db.idx.fulltext.queryNodes('Document', 'machine AND learning NOT deep')
YIELD node, score
RETURN node.title
```

### Full-Text 검색 문법

| 연산자 | 의미 | 예시 |
|--------|------|------|
| `AND` | 모두 포함 | `machine AND learning` |
| `OR` | 하나 이상 | `ML OR AI` |
| `NOT` | 제외 | `learning NOT deep` |
| `*` | 와일드카드 | `neural*` |
| `~` | 퍼지 검색 | `machin~` |
| `"..."` | 구문 검색 | `"machine learning"` |

## Vector Index

### 생성

```cypher
// 벡터 인덱스 생성
CALL db.idx.vector.createNodeIndex(
    'Chunk',           // Label
    'embedding',       // 속성명
    {
        dimension: 1536,
        similarityFunction: 'cosine'  // 'cosine', 'euclidean', 'ip'
    }
)

// 여러 벡터 인덱스
CALL db.idx.vector.createNodeIndex('Entity', 'embedding', {dimension: 768, similarityFunction: 'cosine'})
CALL db.idx.vector.createNodeIndex('Concept', 'vector', {dimension: 1536, similarityFunction: 'cosine'})
```

### 쿼리

```cypher
// 벡터 유사도 검색
CALL db.idx.vector.queryNodes(
    'Chunk',           // Label
    'embedding',       // 속성명
    $query_embedding,  // 쿼리 벡터
    10                 // top K
)
YIELD node, score
RETURN node.content, score
ORDER BY score DESC

// 그래프 탐색과 결합
CALL db.idx.vector.queryNodes('Chunk', 'embedding', $query_embedding, 5)
YIELD node as chunk, score
MATCH (chunk)-[:MENTIONS]->(e:Entity)
RETURN chunk.content, collect(e.name) as entities, score
```

### 유사도 함수

| 함수 | 설명 | 사용 시점 |
|------|------|----------|
| `cosine` | 코사인 유사도 | 텍스트 임베딩 (기본값) |
| `euclidean` | 유클리드 거리 | 이미지 특징 |
| `ip` | 내적 (Inner Product) | 정규화된 벡터 |

## Range Index

### 생성

```cypher
// 숫자 인덱스
CREATE INDEX FOR (d:Document) ON (d.year)

// 날짜 인덱스
CREATE INDEX FOR (d:Document) ON (d.created_at)

// 복합 인덱스
CREATE INDEX FOR (p:Person) ON (p.department, p.hire_date)
```

### 쿼리

```cypher
// 범위 쿼리
MATCH (d:Document)
WHERE d.year >= 2020 AND d.year <= 2024
RETURN d.title

// 날짜 범위
MATCH (d:Document)
WHERE d.created_at >= datetime('2024-01-01')
RETURN d.title, d.created_at
ORDER BY d.created_at DESC
```

## Exact Match Index

### 생성

```cypher
// 고유 제약조건 (자동 인덱스)
CREATE CONSTRAINT ON (d:Document) ASSERT d.id IS UNIQUE

// 복합 키
CREATE CONSTRAINT ON (e:Entity) ASSERT (e.name, e.type) IS NODE KEY

// 일반 인덱스
CREATE INDEX FOR (p:Person) ON (p.email)
```

### 쿼리

```cypher
// 정확한 매칭 (인덱스 활용)
MATCH (p:Person {email: 'alice@example.com'})
RETURN p

// 복합 키 매칭
MATCH (e:Entity {name: 'Python', type: 'LANGUAGE'})
RETURN e
```

## 인덱스 관리

### 인덱스 조회

```cypher
// 모든 인덱스 조회
CALL db.indexes()
YIELD name, type, labelsOrTypes, properties, state
RETURN name, type, labelsOrTypes, properties, state

// 제약조건 조회
CALL db.constraints()
```

### 인덱스 삭제

```cypher
// Full-text 인덱스 삭제
CALL db.idx.fulltext.drop('Document')

// Vector 인덱스 삭제
CALL db.idx.vector.drop('Chunk', 'embedding')

// Range 인덱스 삭제
DROP INDEX index_name

// 제약조건 삭제
DROP CONSTRAINT constraint_name
```

## GraphRAG 인덱싱 전략

### 권장 인덱스 구성

```cypher
// 1. Document Layer - Exact Match
CREATE CONSTRAINT ON (d:Document) ASSERT d.id IS UNIQUE
CREATE INDEX FOR (d:Document) ON (d.created_at)

// 2. Chunk Layer - Vector + Full-Text
CREATE CONSTRAINT ON (c:Chunk) ASSERT c.id IS UNIQUE
CALL db.idx.vector.createNodeIndex('Chunk', 'embedding', {dimension: 1536, similarityFunction: 'cosine'})
CALL db.idx.fulltext.createNodeIndex('Chunk', 'content')

// 3. Entity Layer - Exact + Full-Text
CREATE CONSTRAINT ON (e:Entity) ASSERT (e.name, e.type) IS NODE KEY
CALL db.idx.fulltext.createNodeIndex('Entity', 'name', 'description')

// 4. Optional: Entity Vector Index (시맨틱 엔티티 검색)
CALL db.idx.vector.createNodeIndex('Entity', 'embedding', {dimension: 768, similarityFunction: 'cosine'})
```

### 하이브리드 검색 패턴

```cypher
// 1. Vector 검색으로 후보 추출
CALL db.idx.vector.queryNodes('Chunk', 'embedding', $query_embedding, 20)
YIELD node as chunk, score as vector_score

// 2. Full-text로 키워드 부스팅
OPTIONAL CALL db.idx.fulltext.queryNodes('Chunk', $keywords)
YIELD node as text_match, score as text_score
WHERE text_match = chunk

// 3. 결합 점수 계산
WITH chunk,
     vector_score,
     COALESCE(text_score, 0) as text_score,
     (vector_score * 0.7 + COALESCE(text_score, 0) * 0.3) as combined_score

// 4. 그래프 확장
MATCH (chunk)-[:MENTIONS]->(e:Entity)
RETURN chunk.content, collect(e.name) as entities, combined_score
ORDER BY combined_score DESC
LIMIT 10
```

## 인덱스 성능 최적화

### 쿼리 실행 계획 분석

```cypher
// EXPLAIN으로 실행 계획 확인
EXPLAIN MATCH (p:Person {email: 'alice@example.com'})
RETURN p

// PROFILE로 실제 실행 통계 확인
PROFILE MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE p.age > 30
RETURN p.name, c.name
```

### 인덱스 힌트

```cypher
// 특정 인덱스 사용 강제
MATCH (p:Person)
USING INDEX p:Person(email)
WHERE p.email = 'alice@example.com'
RETURN p
```

### 인덱스 선택 가이드

| 쿼리 패턴 | 권장 인덱스 |
|----------|------------|
| `WHERE node.id = value` | Unique Constraint |
| `WHERE node.field = value` | Exact Match Index |
| `WHERE node.field > value` | Range Index |
| `텍스트 검색` | Full-Text Index |
| `시맨틱 유사도` | Vector Index |
| `MATCH (n:Label)` | Label Index (자동) |

## 인덱스 워밍업

대량 데이터 로드 후 인덱스 워밍업:

```cypher
// 인덱스 캐시 워밍업 쿼리
MATCH (c:Chunk)
WHERE c.id IS NOT NULL
RETURN count(c)

// 벡터 인덱스 워밍업
CALL db.idx.vector.queryNodes('Chunk', 'embedding', $sample_embedding, 1)
YIELD node
RETURN count(node)
```
