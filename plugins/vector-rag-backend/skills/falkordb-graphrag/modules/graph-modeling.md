# Graph Modeling

FalkorDB Property Graph 모델링 - 노드, 엣지, 프로퍼티 설계

## Property Graph 기초

### 구성 요소

```
Node (노드):
- 엔티티를 표현
- 하나 이상의 Label (타입)
- Properties (속성)

Edge (엣지/관계):
- 노드 간 관계
- 방향성 있음
- 하나의 Type
- Properties (속성)
```

### 예시

```cypher
// 노드 생성
CREATE (alice:Person:Employee {
    name: 'Alice',
    age: 30,
    email: 'alice@example.com'
})

// 관계 생성
CREATE (alice)-[:WORKS_AT {since: 2020, role: 'Engineer'}]->(company)
```

## RAG용 그래프 스키마 패턴

### Pattern 1: Document-Chunk-Entity

문서 기반 지식 그래프:

```cypher
// 스키마
(:Document {id, title, source, created_at})
(:Chunk {id, content, position, embedding})
(:Entity {name, type, description})
(:Concept {name, definition, embedding})

// 관계
(Document)-[:HAS_CHUNK {order}]->(Chunk)
(Chunk)-[:MENTIONS {confidence}]->(Entity)
(Entity)-[:RELATES_TO {type, weight}]->(Entity)
(Entity)-[:IS_A]->(Concept)
```

```cypher
// 구현 예시
CREATE (doc:Document {
    id: 'doc_001',
    title: 'Machine Learning Basics',
    source: 'textbook.pdf',
    created_at: datetime()
})

CREATE (chunk:Chunk {
    id: 'chunk_001',
    content: 'Neural networks are...',
    position: 0
})

CREATE (entity:Entity {
    name: 'Neural Network',
    type: 'TECHNOLOGY'
})

CREATE (doc)-[:HAS_CHUNK {order: 0}]->(chunk)
CREATE (chunk)-[:MENTIONS {confidence: 0.95}]->(entity)
```

### Pattern 2: Domain Ontology

도메인 특화 온톨로지:

```cypher
// 의료 도메인
(:Disease {name, icd_code, description})
(:Symptom {name, severity_levels})
(:Treatment {name, type, efficacy})
(:Drug {name, dosage, side_effects})

(Disease)-[:HAS_SYMPTOM {frequency}]->(Symptom)
(Disease)-[:TREATED_BY {evidence_level}]->(Treatment)
(Treatment)-[:USES]->(Drug)
(Drug)-[:INTERACTS_WITH {severity}]->(Drug)
```

```cypher
// 법률 도메인
(:Law {code, title, effective_date})
(:Article {number, content})
(:Case {id, title, date, court})
(:Precedent {ruling, principle})

(Law)-[:CONTAINS]->(Article)
(Case)-[:CITES]->(Article)
(Case)-[:ESTABLISHES]->(Precedent)
(Precedent)-[:INTERPRETS]->(Article)
```

### Pattern 3: Q&A Knowledge Base

질문-답변 시스템용:

```cypher
(:Question {text, embedding, category})
(:Answer {text, confidence, source})
(:Topic {name, description})
(:FAQ {id, views, last_updated})

(Question)-[:HAS_ANSWER {verified}]->(Answer)
(Question)-[:ABOUT]->(Topic)
(Topic)-[:PARENT_OF]->(Topic)  // 계층 구조
(FAQ)-[:CONTAINS]->(Question)
```

## 노드 설계 원칙

### 1. 단일 책임

```cypher
// GOOD: 명확한 역할 분리
(:Person {name, email})
(:Address {street, city, country})
(Person)-[:LIVES_AT]->(Address)

// BAD: 과도한 속성
(:Person {name, email, street, city, country, ...})
```

### 2. 적절한 Label 사용

```cypher
// GOOD: 다중 Label로 분류
CREATE (alice:Person:Employee:Manager {name: 'Alice'})

// 쿼리 시 필터링 활용
MATCH (m:Manager) RETURN m  // Manager만
MATCH (e:Employee) RETURN e  // 모든 Employee
MATCH (p:Person) RETURN p    // 모든 Person
```

### 3. 속성 vs 관계 선택

```cypher
// 속성으로 표현 (단순 값)
(:Person {name: 'Alice', age: 30})

// 관계로 표현 (다른 엔티티와 연결)
(Person)-[:BORN_IN]->(City)
(Person)-[:WORKS_AT]->(Company)

// 판단 기준:
// - 다른 노드와 공유 가능? → 관계
// - 쿼리에서 자주 조인? → 관계
// - 단순 값이고 독립적? → 속성
```

## 관계 설계 원칙

### 1. 의미 있는 관계명

```cypher
// GOOD: 명확한 의미
(Person)-[:AUTHORED]->(Document)
(Document)-[:CITES]->(Document)
(Person)-[:SUPERVISES]->(Person)

// BAD: 모호한 관계
(Person)-[:RELATED_TO]->(Document)  // 어떤 관계?
```

### 2. 관계 방향성

```cypher
// 자연스러운 방향
(Author)-[:WROTE]->(Book)        // Author → Book
(Employee)-[:REPORTS_TO]->(Manager)

// 역방향 쿼리도 가능
MATCH (book:Book)<-[:WROTE]-(author)
```

### 3. 관계 속성 활용

```cypher
// 관계에 메타데이터 추가
(Person)-[:WORKED_AT {
    from: date('2020-01-01'),
    to: date('2023-12-31'),
    role: 'Engineer',
    department: 'R&D'
}]->(Company)

// 시간 기반 쿼리
MATCH (p:Person)-[r:WORKED_AT]->(c:Company)
WHERE r.from <= date('2022-06-01') <= r.to
RETURN p.name, c.name
```

## GraphRAG 스키마 설계

### 기본 스키마

```cypher
// 1. Document Layer
CREATE CONSTRAINT ON (d:Document) ASSERT d.id IS UNIQUE

// 2. Chunk Layer (임베딩 포함)
CREATE CONSTRAINT ON (c:Chunk) ASSERT c.id IS UNIQUE

// 3. Entity Layer
CREATE CONSTRAINT ON (e:Entity) ASSERT (e.name, e.type) IS NODE KEY

// 4. Concept Layer (온톨로지)
CREATE CONSTRAINT ON (co:Concept) ASSERT co.name IS UNIQUE
```

### 인덱스 설정

```cypher
// 벡터 인덱스 (시맨틱 검색)
CALL db.idx.vector.createNodeIndex(
    'Chunk', 'embedding',
    {dimension: 1536, similarityFunction: 'cosine'}
)

// 전문 검색 인덱스
CALL db.idx.fulltext.createNodeIndex('Chunk', 'content')
CALL db.idx.fulltext.createNodeIndex('Entity', 'name', 'description')

// Range 인덱스
CREATE INDEX FOR (d:Document) ON (d.created_at)
```

## 스키마 마이그레이션

### 노드 Label 추가

```cypher
// 기존 노드에 Label 추가
MATCH (p:Person)
WHERE p.role = 'Manager'
SET p:Manager
```

### 관계 리팩토링

```cypher
// 관계 타입 변경
MATCH (a)-[old:KNOWS]->(b)
CREATE (a)-[new:IS_FRIEND_OF]->(b)
SET new = properties(old)
DELETE old
```

### 속성을 관계로 변환

```cypher
// company 속성을 관계로 변환
MATCH (p:Person)
WHERE p.company IS NOT NULL
MERGE (c:Company {name: p.company})
CREATE (p)-[:WORKS_AT]->(c)
REMOVE p.company
```

## 성능 고려사항

### 1. 슈퍼노드 방지

```cypher
// BAD: 모든 문서가 하나의 노드에 연결
(:Category {name: 'All'})<-[:IN_CATEGORY]-(millions of documents)

// GOOD: 계층 구조로 분산
(:Category)-[:PARENT_OF]->(:SubCategory)-[:CONTAINS]->(Document)
```

### 2. 관계 방향 최적화

```cypher
// 쿼리 패턴에 맞는 방향 선택
// 주로 "사용자의 주문 찾기" 쿼리면:
(User)-[:PLACED]->(Order)  // User → Order 방향

// 주로 "주문의 사용자 찾기" 쿼리면:
(Order)-[:PLACED_BY]->(User)  // Order → User 방향
```

### 3. 속성 크기 제한

```cypher
// BAD: 대용량 텍스트 직접 저장
(:Document {content: '... 100KB text ...'})

// GOOD: 청크로 분리
(:Document)-[:HAS_CHUNK]->(:Chunk {content: '... 1KB ...'})
```
