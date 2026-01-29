# Knowledge Graph Templates

도메인별 지식 그래프 스키마 템플릿

## 범용 RAG 스키마

### Document-Centric KG

```cypher
// 노드 타입
(:Document {id, title, source, created_at, doc_type})
(:Chunk {id, content, position, embedding, token_count})
(:Entity {id, name, type, description, embedding})
(:Topic {id, name, description})

// 관계
(Document)-[:HAS_CHUNK {order}]->(Chunk)
(Chunk)-[:MENTIONS {confidence, start_pos, end_pos}]->(Entity)
(Chunk)-[:DISCUSSES]->(Topic)
(Entity)-[:RELATES_TO {relation_type, weight}]->(Entity)
(Entity)-[:BELONGS_TO]->(Topic)
(Topic)-[:SUBTOPIC_OF]->(Topic)

// 인덱스
CREATE CONSTRAINT ON (d:Document) ASSERT d.id IS UNIQUE
CREATE CONSTRAINT ON (c:Chunk) ASSERT c.id IS UNIQUE
CREATE CONSTRAINT ON (e:Entity) ASSERT (e.name, e.type) IS NODE KEY
CALL db.idx.vector.createNodeIndex('Chunk', 'embedding', {dimension: 1536, similarityFunction: 'cosine'})
CALL db.idx.fulltext.createNodeIndex('Chunk', 'content')
```

## 기술 문서 도메인

### Tech Documentation KG

```cypher
// 노드 타입
(:Documentation {id, title, version, url})
(:Section {id, title, content, level})
(:CodeExample {id, language, code, description})
(:API {name, version, endpoint, method})
(:Parameter {name, type, required, description})
(:Concept {name, definition, related_terms})

// 관계
(Documentation)-[:CONTAINS]->(Section)
(Section)-[:HAS_SUBSECTION]->(Section)
(Section)-[:INCLUDES]->(CodeExample)
(Section)-[:DOCUMENTS]->(API)
(API)-[:HAS_PARAMETER]->(Parameter)
(Section)-[:EXPLAINS]->(Concept)
(Concept)-[:RELATED_TO]->(Concept)

// 사용 예시
CREATE (doc:Documentation {
    id: 'qdrant-docs',
    title: 'Qdrant Documentation',
    version: '1.8.0'
})
CREATE (sec:Section {
    id: 'collections',
    title: 'Collections',
    level: 1
})
CREATE (api:API {
    name: 'create_collection',
    endpoint: '/collections/{name}',
    method: 'PUT'
})
CREATE (doc)-[:CONTAINS]->(sec)
CREATE (sec)-[:DOCUMENTS]->(api)
```

## 기업 지식 도메인

### Enterprise Knowledge KG

```cypher
// 노드 타입
(:Employee {id, name, email, title, department})
(:Team {id, name, function, budget})
(:Project {id, name, status, start_date, end_date})
(:Skill {name, category, level})
(:Document {id, title, type, owner, created_at})
(:Meeting {id, title, date, attendees})

// 관계
(Employee)-[:MEMBER_OF {role, since}]->(Team)
(Employee)-[:WORKS_ON {role, allocation}]->(Project)
(Employee)-[:HAS_SKILL {proficiency, certified}]->(Skill)
(Employee)-[:AUTHORED]->(Document)
(Team)-[:OWNS]->(Project)
(Project)-[:REQUIRES]->(Skill)
(Meeting)-[:ABOUT]->(Project)
(Document)-[:RELATED_TO]->(Project)

// 샘플 쿼리: 프로젝트에 필요한 스킬을 가진 직원 찾기
MATCH (p:Project {name: 'AI Platform'})-[:REQUIRES]->(s:Skill)
MATCH (e:Employee)-[:HAS_SKILL {proficiency: 'expert'}]->(s)
WHERE NOT (e)-[:WORKS_ON]->(p)
RETURN e.name, collect(s.name) as matching_skills
```

## 고객 서비스 도메인

### Customer Support KG

```cypher
// 노드 타입
(:Ticket {id, title, description, status, priority, created_at})
(:Customer {id, name, email, tier, company})
(:Product {id, name, version, category})
(:Issue {id, name, description, severity})
(:Solution {id, description, steps, success_rate})
(:Agent {id, name, team, expertise})

// 관계
(Customer)-[:SUBMITTED]->(Ticket)
(Ticket)-[:ABOUT]->(Product)
(Ticket)-[:HAS_ISSUE]->(Issue)
(Issue)-[:RESOLVED_BY]->(Solution)
(Agent)-[:HANDLED {resolution_time}]->(Ticket)
(Solution)-[:APPLIES_TO]->(Product)
(Issue)-[:SIMILAR_TO {similarity}]->(Issue)

// 샘플 쿼리: 유사 이슈의 해결책 찾기
MATCH (t:Ticket {id: $ticket_id})-[:HAS_ISSUE]->(i:Issue)
MATCH (i)-[:SIMILAR_TO]->(similar:Issue)-[:RESOLVED_BY]->(s:Solution)
RETURN similar.name, s.description, s.success_rate
ORDER BY s.success_rate DESC
LIMIT 5
```

## 의료 도메인

### Medical Knowledge KG

```cypher
// 노드 타입
(:Disease {icd_code, name, description, prevalence})
(:Symptom {id, name, severity_levels, body_system})
(:Treatment {id, name, type, evidence_level})
(:Drug {id, name, generic_name, dosage_forms})
(:Interaction {type, severity, description})
(:ClinicalTrial {id, title, phase, status})

// 관계
(Disease)-[:HAS_SYMPTOM {frequency, specificity}]->(Symptom)
(Disease)-[:TREATED_BY {first_line, evidence}]->(Treatment)
(Treatment)-[:USES]->(Drug)
(Drug)-[:INTERACTS_WITH {severity}]->(Drug)
(Disease)-[:STUDIED_IN]->(ClinicalTrial)
(Disease)-[:COMORBID_WITH {correlation}]->(Disease)

// 약물 상호작용 체크 쿼리
MATCH (d1:Drug {name: $drug1})-[i:INTERACTS_WITH]-(d2:Drug {name: $drug2})
RETURN d1.name, d2.name, i.severity, i.description
```

## 법률 도메인

### Legal Knowledge KG

```cypher
// 노드 타입
(:Law {code, title, effective_date, jurisdiction})
(:Article {number, title, content, version})
(:Case {id, title, date, court, outcome})
(:Precedent {id, ruling, principle, importance})
(:Party {id, name, type, role})
(:Judge {id, name, court, tenure})

// 관계
(Law)-[:CONTAINS]->(Article)
(Case)-[:CITES {context}]->(Article)
(Case)-[:ESTABLISHES]->(Precedent)
(Precedent)-[:INTERPRETS]->(Article)
(Case)-[:INVOLVES {role}]->(Party)
(Judge)-[:PRESIDED]->(Case)
(Case)-[:OVERRULED_BY]->(Case)
(Article)-[:AMENDED_BY]->(Article)

// 관련 판례 검색 쿼리
MATCH (a:Article {number: $article_num})<-[:CITES]-(c:Case)
OPTIONAL MATCH (c)-[:ESTABLISHES]->(p:Precedent)
RETURN c.title, c.date, c.outcome, collect(p.principle) as principles
ORDER BY c.date DESC
```

## 전자상거래 도메인

### E-commerce KG

```cypher
// 노드 타입
(:Product {id, name, price, category, brand})
(:Customer {id, name, segment, lifetime_value})
(:Order {id, date, total, status})
(:Review {id, rating, text, date})
(:Category {id, name, parent_id})
(:Feature {name, value, unit})

// 관계
(Customer)-[:PURCHASED {quantity}]->(Product)
(Customer)-[:PLACED]->(Order)
(Order)-[:CONTAINS {quantity, price}]->(Product)
(Customer)-[:WROTE]->(Review)
(Review)-[:ABOUT]->(Product)
(Product)-[:IN_CATEGORY]->(Category)
(Product)-[:HAS_FEATURE]->(Feature)
(Product)-[:SIMILAR_TO {score}]->(Product)
(Customer)-[:VIEWED]->(Product)

// 추천 쿼리: 협업 필터링
MATCH (c:Customer {id: $customer_id})-[:PURCHASED]->(p:Product)
MATCH (p)<-[:PURCHASED]-(other:Customer)-[:PURCHASED]->(rec:Product)
WHERE NOT (c)-[:PURCHASED]->(rec)
RETURN rec.name, count(other) as buyer_overlap
ORDER BY buyer_overlap DESC
LIMIT 10
```

## Q&A 시스템 도메인

### FAQ Knowledge KG

```cypher
// 노드 타입
(:Question {id, text, embedding, views, helpful_votes})
(:Answer {id, text, confidence, verified, author})
(:Topic {id, name, description})
(:Tag {name})
(:User {id, name, role, expertise})

// 관계
(Question)-[:HAS_ANSWER {accepted}]->(Answer)
(Question)-[:TAGGED_WITH]->(Tag)
(Question)-[:ABOUT]->(Topic)
(Topic)-[:PARENT]->(Topic)
(User)-[:ASKED]->(Question)
(User)-[:ANSWERED]->(Answer)
(Question)-[:SIMILAR_TO {similarity}]->(Question)
(Answer)-[:REFERENCES]->(Answer)

// 인덱스
CALL db.idx.vector.createNodeIndex('Question', 'embedding', {dimension: 1536, similarityFunction: 'cosine'})
CALL db.idx.fulltext.createNodeIndex('Question', 'text')
CALL db.idx.fulltext.createNodeIndex('Answer', 'text')

// 유사 질문 검색
CALL db.idx.vector.queryNodes('Question', 'embedding', $query_embedding, 5)
YIELD node as q, score
MATCH (q)-[:HAS_ANSWER {accepted: true}]->(a:Answer)
RETURN q.text, a.text, score
ORDER BY score DESC
```

## 스키마 설계 체크리스트

### 노드 설계
- [ ] 명확한 엔티티 타입 정의
- [ ] 고유 식별자 (id) 포함
- [ ] 필수 속성 vs 선택 속성 구분
- [ ] 임베딩 필드 포함 (시맨틱 검색용)

### 관계 설계
- [ ] 의미 있는 관계명 (동사형)
- [ ] 관계 방향 정의
- [ ] 관계 속성 (가중치, 타임스탬프)

### 인덱스 설계
- [ ] 고유 제약조건 (ID 필드)
- [ ] 자주 필터링하는 속성
- [ ] 벡터 인덱스 (임베딩)
- [ ] Full-text 인덱스 (텍스트 검색)
