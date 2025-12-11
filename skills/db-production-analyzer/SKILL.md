---
name: db-production-analyzer
description: "Deep analysis of database implementation in production environments. Use when users request database review, production readiness checks, or performance optimization analysis. Analyzes multi-database projects including SQL databases (PostgreSQL, MySQL, SQLite), NoSQL (MongoDB, Redis), VectorDB (Pinecone, Weaviate, Milvus, ChromaDB), and GraphDB (Neo4j, ArangoDB) to identify schema design issues, query performance problems (N+1, missing indexes), security vulnerabilities, transaction management issues, connection pooling problems, and code-schema inconsistencies. Provides detailed reports with file locations and line numbers."
---

# DB Production Analyzer

## Overview

This skill performs comprehensive, in-depth analysis of database implementations to ensure production readiness. Unlike superficial reviews, it systematically scans your entire project to find specific issues with concrete file locations and line numbers.

**What it analyzes:**
- SQL databases (PostgreSQL, MySQL, SQLite)
- NoSQL (MongoDB, Redis)
- VectorDB (Pinecone, Weaviate, Milvus, ChromaDB)
- GraphDB (Neo4j, ArangoDB)

**Analysis modes:**
1. **Static Analysis** - Code-based inspection (no DB connection needed)
2. **Live Analysis** - Connects to actual databases for verification (optional but recommended)

## Quick Start

### Basic Usage (Static Analysis Only)

1. Upload or provide access to your project codebase
2. Request analysis: "Analyze this project for production-ready database implementation"
3. Claude will scan the codebase and generate a detailed report

### Advanced Usage (With Live DB Connection)

For more thorough analysis, provide database connection strings:

```bash
# Example connection strings (stored in .env or provided securely)
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
MONGODB_URL=mongodb://localhost:27017/mydb
REDIS_URL=redis://localhost:6379/0
```

Claude will:
1. Perform static code analysis
2. Connect to databases (read-only) to verify:
   - Actual schema vs code definitions
   - Index existence and usage
   - Table sizes and row counts
3. Run EXPLAIN ANALYZE on queries to measure real performance
4. Generate comprehensive report with concrete issues and recommendations

**Safety:** All database connections are read-only. No write operations are performed.

## Analysis Workflow

The analysis follows a systematic multi-phase approach:

1. **Project Structure** - Identify languages, frameworks, DB types, and ORM tools
2. **DB Configuration** - Validate connection pooling, environment separation, multi-DB management
3. **Schema Analysis** - Check indexes, constraints, migrations, and design patterns
4. **Query Analysis** - Deep scan for N+1 queries, missing indexes, SQL injection risks
5. **Transaction Management** - Verify proper boundaries, isolation levels, deadlock prevention
6. **Error Handling** - Check resilience patterns and graceful degradation
7. **Security** - Scan for vulnerabilities and sensitive data exposure
8. **Performance** - Identify slow queries and optimization opportunities
9. **Consistency** - Cross-check code against schema definitions
10. **Reporting** - Generate actionable report with priorities

## Phase 1: Project Structure Discovery

**Goal:** Map the project landscape and identify ALL database types in use.

**Steps:**
1. Scan project directory structure to identify:
   - Programming language(s) and frameworks
   - **All database types in use:**
     - **SQL:** PostgreSQL, MySQL, SQLite, MariaDB
     - **NoSQL Document:** MongoDB, CouchDB, Firestore
     - **NoSQL Key-Value:** Redis, Memcached, DynamoDB
     - **VectorDB:** Pinecone, Weaviate, Milvus, ChromaDB, Qdrant, Faiss
     - **GraphDB:** Neo4j, ArangoDB, Neptune, TigerGraph
     - **Time-Series:** InfluxDB, TimescaleDB
   - ORM/Query tools and clients
   - Project architecture (monolith, microservices, serverless)

2. Create mental map of:
   - Where DB code lives (models/, repositories/, queries/, services/, vectorstore/, graph/)
   - Configuration file locations
   - Migration directories
   - Test directories

**Detection strategies by DB type:**

### SQL Databases
Check for:
- Imports: `pg`, `mysql2`, `sqlite3`, `psycopg2`, `pymysql`
- Config: Connection strings with `postgres://`, `mysql://`
- Files: `schema.prisma`, `migrations/`, `*.sql`

### VectorDB
Check for:
- Imports: `pinecone-client`, `weaviate-client`, `chromadb`, `pymilvus`, `qdrant-client`
- Config: API keys like `PINECONE_API_KEY`, `WEAVIATE_URL`
- Files: Vector dimension configs, embedding model references
- Code patterns: `similarity_search`, `vector_store`, `embeddings`

### GraphDB
Check for:
- Imports: `neo4j-driver`, `pyarango`, `gremlinpython`
- Config: `NEO4J_URI`, `bolt://` connections
- Files: `*.cypher`, graph schema definitions
- Code patterns: `CREATE`, `MATCH`, `RETURN`, relationship traversals

### NoSQL
Check for:
- MongoDB: `mongoose`, `pymongo`, `mongodb://` URIs
- Redis: `ioredis`, `redis-py`, `redis://` URIs
- Files: `*.json` schemas, Redis Lua scripts

**Key files to check:**
- `package.json`, `requirements.txt`, `Gemfile`, `go.mod` - Dependencies
- `.env`, `config/`, `settings.py` - Configuration
- `docker-compose.yml` - Services defined

## Phase 2: DB Connection & Configuration Analysis

**Critical checks:**

### Connection Pool Configuration
```
✓ Pool size appropriate for workload?
✓ Max overflow/connections configured?
✓ Connection timeout settings?
✓ Pool pre-ping/health check enabled?
✓ Connection leak prevention (proper cleanup)?
```

**Common issues:**
- Pool size too small (causes connection exhaustion under load)
- No timeout settings (hangs indefinitely)
- Missing connection cleanup in error paths
- Creating new connections instead of reusing pool

### Environment Separation
```
✓ Separate configs for dev/staging/prod?
✓ Credentials in environment variables (not hardcoded)?
✓ Different connection strings per environment?
✓ No production credentials in version control?
```

### Multiple Database Management
```
✓ Clear naming convention for connections?
✓ Each DB connection properly pooled?
✓ Transaction boundaries don't span multiple DBs incorrectly?
```

## Phase 3: Schema & Migration Analysis

**This phase has two modes: Static analysis (from code) and Live analysis (from actual DB)**

### Mode 1: Static Analysis (Code-based)

Analyze schema from:
- Migration files (`migrations/`, `alembic/`, `*.sql`)
- ORM models (Prisma schema, TypeORM entities, SQLAlchemy models)
- Schema definition files

**For each table/collection, verify:**

### Index Strategy
```
✓ Primary keys defined?
✓ Foreign keys with indexes?
✓ Indexes on frequently queried columns?
✓ Composite index column order optimal?
✓ No duplicate/redundant indexes?
```

**Find missing indexes by:**
1. Extract all `WHERE`, `JOIN`, `ORDER BY` clauses from query code
2. Check if those columns have indexes in schema
3. Report columns used in queries but not indexed

### Constraints & Data Integrity
```
✓ Foreign key constraints defined?
✓ ON DELETE/UPDATE cascade behavior specified?
✓ NOT NULL constraints appropriate?
✓ UNIQUE constraints where needed?
✓ CHECK constraints for business rules?
```

### Migration Quality
```
✓ Migrations have both up and down?
✓ Data migrations preserve existing data?
✓ Schema changes backward compatible?
✓ Migrations tested for rollback?
```

### Mode 2: Live DB Schema Inspection (Optional but Recommended)

**If database connection credentials are available**, connect to actual database and verify:

#### For SQL Databases (PostgreSQL, MySQL)

**Connect and query system tables:**

```python
# PostgreSQL example
import psycopg2

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 1. Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")
tables = cur.fetchall()

# 2. Get indexes for each table
cur.execute("""
    SELECT 
        t.tablename,
        i.indexname,
        array_agg(a.attname ORDER BY a.attnum) as columns
    FROM pg_indexes i
    JOIN pg_class c ON c.relname = i.indexname
    JOIN pg_attribute a ON a.attrelid = c.oid
    JOIN pg_tables t ON t.tablename = i.tablename
    WHERE t.schemaname = 'public'
    GROUP BY t.tablename, i.indexname
""")
indexes = cur.fetchall()

# 3. Get foreign keys
cur.execute("""
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
""")
foreign_keys = cur.fetchall()

# 4. Get table statistics
cur.execute("""
    SELECT 
        schemaname,
        tablename,
        n_live_tup as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC
""")
table_stats = cur.fetchall()
```

**Cross-reference with code:**
- Compare live schema with migration files
- Identify drift (schema changed but no migration)
- Find unused tables (in DB but not referenced in code)
- Check if indexes in code actually exist in DB

#### For MongoDB

```python
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# 1. List all collections
collections = db.list_collection_names()

# 2. Get indexes for each collection
for collection_name in collections:
    collection = db[collection_name]
    indexes = collection.index_information()
    
    # 3. Sample document structure
    sample_doc = collection.find_one()
    
    # 4. Collection stats
    stats = db.command("collStats", collection_name)
    doc_count = stats['count']
    avg_doc_size = stats['avgObjSize']
```

#### For Redis

```python
import redis

r = redis.Redis.from_url(REDIS_URL)

# 1. Get all keys (WARNING: Use SCAN in production, not KEYS)
for key in r.scan_iter(count=1000):
    key_type = r.type(key)
    ttl = r.ttl(key)
    
    # Check for keys without TTL
    if ttl == -1:
        # Potential memory leak
        pass

# 2. Memory usage
info = r.info('memory')
used_memory = info['used_memory_human']
```

#### For VectorDB (Pinecone)

```python
import pinecone

pinecone.init(api_key=API_KEY)

# 1. List indexes
indexes = pinecone.list_indexes()

# 2. Get index stats
index = pinecone.Index('index-name')
stats = index.describe_index_stats()
# Check: total_vector_count, dimension, index_fullness
```

#### For GraphDB (Neo4j)

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(NEO4J_URI, auth=(USER, PASSWORD))

with driver.session() as session:
    # 1. Get all node labels
    result = session.run("CALL db.labels()")
    labels = [record['label'] for record in result]
    
    # 2. Get all relationship types
    result = session.run("CALL db.relationshipTypes()")
    rel_types = [record['relationshipType'] for record in result]
    
    # 3. Check indexes
    result = session.run("SHOW INDEXES")
    indexes = list(result)
    
    # 4. Check constraints
    result = session.run("SHOW CONSTRAINTS")
    constraints = list(result)
    
    # 5. Get node counts
    for label in labels:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
        count = result.single()['count']
```

**Benefits of Live DB Inspection:**
- ✅ Catch schema drift (code vs reality)
- ✅ Identify actual table sizes and row counts
- ✅ Find unused indexes consuming space
- ✅ Verify constraints are actually enforced
- ✅ Check fragmentation and bloat

**When to use:**
- Production readiness final check
- After major migrations
- Performance troubleshooting
- Quarterly DB health audits

**Safety considerations:**
```
⚠️ Read-only queries only
⚠️ Use replica/read-only connection if available
⚠️ Rate limit queries to avoid load
⚠️ Never connect to production with write permissions
```

## Phase 4: Query Code Deep Analysis

**This is the most critical phase - scan ALL database query code thoroughly.**

### Step 4.1: Locate All Query Code

Systematically find:
- Raw SQL queries (grep for `SELECT`, `INSERT`, `UPDATE`, `DELETE`)
- ORM queries (`.find`, `.create`, `.update`, `.query`, etc.)
- Query builder usage
- Stored procedure calls
- GraphQL resolvers with DB access

**Record:** File path and line number for each query found.

### Step 4.2: N+1 Query Detection

**Dangerous patterns:**
```javascript
// BAD: Loop with individual queries
for (const post of posts) {
  const author = await db.users.findById(post.authorId);  // N+1!
}

// BAD: Lazy loading in loop
posts.forEach(post => {
  console.log(post.author.name);  // Triggers N queries
});
```

**Scan for:**
- Loops containing DB queries
- Sequential `await` calls in loops
- Lazy loading without explicit eager loading
- Nested loops with queries

**Solutions to suggest:**
- Use `JOIN` or `include`/`populate` (ORM eager loading)
- Implement DataLoader pattern
- Batch queries outside loop

### Step 4.3: Inefficient Query Patterns

**Patterns to flag:**

1. **SELECT * abuse**
```sql
SELECT * FROM large_table  -- Returns 50 columns but only uses 2
```

2. **Function in WHERE (kills index)**
```sql
WHERE LOWER(email) = 'test@example.com'  -- Index on email not used
WHERE DATE(created_at) = '2024-01-01'    -- Index on created_at not used
```

3. **Leading wildcard**
```sql
WHERE name LIKE '%john%'  -- Forces full table scan
```

4. **OR condition excess**
```sql
WHERE status = 'A' OR status = 'B' OR status = 'C' OR ...  -- Use IN
```

5. **Missing pagination**
```javascript
const allUsers = await db.users.findAll();  // Could be millions of rows
```

6. **Subquery in SELECT**
```sql
SELECT id, (SELECT COUNT(*) FROM orders WHERE user_id = users.id) 
FROM users;  -- Executes subquery N times
```

### Step 4.4: Index Utilization Analysis

**For each query:**
1. Extract columns used in WHERE, JOIN, ORDER BY
2. Check if schema has index on those columns
3. For composite indexes, verify column order matches query pattern

**Report template:**
```
Missing Index Detected:
- Table: `orders`
- Column: `customer_id, created_at`
- Query pattern: WHERE customer_id = ? ORDER BY created_at DESC
- Files affected: 
  - src/api/orders.js:45
  - src/services/report.js:120
- Impact: Full table scan on 1M+ rows
- Suggestion: CREATE INDEX idx_orders_customer_created ON orders(customer_id, created_at DESC);
```

### Step 4.5: Query Complexity Issues

Flag queries with:
- More than 5 JOINs
- Subqueries in FROM clause
- Complex CASE statements
- Multiple CTEs (Common Table Expressions)
- Self-joins

These may need optimization or breaking into multiple queries.

## Phase 4A: VectorDB-Specific Analysis

**For projects using Pinecone, Weaviate, Milvus, ChromaDB, Qdrant, or similar:**

### Embedding Dimension Consistency

**Critical check:**
```
✓ All vectors have consistent dimensions?
✓ Embedding model version documented?
✓ Dimension matches between:
  - Embedding generation code
  - Vector index configuration
  - Query operations
```

**Common issues:**
```python
# ❌ BAD: Inconsistent dimensions
embeddings_1 = model_v1.encode(text)  # Returns 768-dim
embeddings_2 = model_v2.encode(text)  # Returns 1536-dim
# Both stored in same index → errors!

# ✅ GOOD: Version control and validation
EMBEDDING_DIM = 768
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

def validate_embedding(embedding):
    assert len(embedding) == EMBEDDING_DIM, f"Expected {EMBEDDING_DIM} dims"
    return embedding
```

### Vector Index Configuration

**Check for optimal settings:**

**Pinecone:**
```python
# ❌ BAD: Default settings, no optimization
index = pinecone.Index("my-index")

# ✅ GOOD: Optimized for use case
index = pinecone.create_index(
    name="my-index",
    dimension=768,
    metric="cosine",  # or "euclidean", "dotproduct"
    pod_type="p1.x1",  # Size based on data volume
    replicas=2  # For high availability
)
```

**Milvus/Weaviate:**
```python
# Check index type is appropriate:
# - FLAT: Small datasets (< 1M vectors), highest accuracy
# - IVF_FLAT: Medium datasets (1M-10M), good accuracy
# - HNSW: Large datasets (> 10M), fast but memory-intensive
```

### Similarity Search Optimization

**Patterns to check:**

1. **Top-K parameter tuning**
```python
# ❌ BAD: Always fetching 100 results
results = index.query(vector, top_k=100)
# Then filtering to 10 → wasted compute

# ✅ GOOD: Fetch only what you need
results = index.query(vector, top_k=10)
```

2. **Metadata filtering efficiency**
```python
# ❌ BAD: Post-filter (inefficient)
results = index.query(vector, top_k=1000)
filtered = [r for r in results if r.metadata['category'] == 'tech'][:10]

# ✅ GOOD: Pre-filter in query
results = index.query(
    vector, 
    top_k=10,
    filter={"category": {"$eq": "tech"}}
)
```

3. **Batch operations**
```python
# ❌ BAD: Individual upserts
for doc in documents:
    embedding = embed(doc.text)
    index.upsert([(doc.id, embedding, doc.metadata)])

# ✅ GOOD: Batch upsert
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    vectors = [(d.id, embed(d.text), d.metadata) for d in batch]
    index.upsert(vectors)
```

### VectorDB-Specific Security

**Check for:**
```
✓ API keys in environment variables (not hardcoded)?
✓ Rate limiting on embedding generation?
✓ Vector data access control?
✓ Metadata filtering to prevent data leakage?
```

**Example issue:**
```python
# ❌ CRITICAL: User can access any vector
user_query = request.args.get('query')
results = index.query(embed(user_query), top_k=10)
# No filtering by user permissions!

# ✅ GOOD: Filter by user's accessible data
results = index.query(
    embed(user_query), 
    top_k=10,
    filter={"user_id": current_user.id}
)
```

### Embedding Generation Issues

**Watch for:**
1. **Inconsistent preprocessing**
```python
# ❌ BAD: Different preprocessing for index vs query
# Index time:
embedding = model.encode(text.lower().strip())

# Query time:
query_embedding = model.encode(query_text)  # No preprocessing!
```

2. **Token limit exceeded**
```python
# ❌ BAD: No truncation
embedding = model.encode(very_long_text)  # May fail silently

# ✅ GOOD: Truncate or chunk
MAX_TOKENS = 512
chunks = chunk_text(very_long_text, MAX_TOKENS)
embeddings = [model.encode(chunk) for chunk in chunks]
```

3. **Missing error handling**
```python
# ❌ BAD: No error handling
embedding = openai.Embedding.create(input=text)

# ✅ GOOD: Handle rate limits and failures
@retry(max_attempts=3, backoff=exponential)
def get_embedding(text):
    try:
        return openai.Embedding.create(input=text)
    except RateLimitError:
        sleep(60)
        raise
```

## Phase 4B: GraphDB-Specific Analysis

**For projects using Neo4j, ArangoDB, Neptune, or similar:**

### Cypher/AQL Query Optimization (Neo4j)

**Critical patterns to check:**

1. **Cartesian products (VERY SLOW)**
```cypher
// ❌ CRITICAL: Cartesian product
MATCH (u:User), (p:Post)
WHERE u.id = p.author_id
RETURN u, p
// Checks EVERY user against EVERY post!

// ✅ GOOD: Proper relationship
MATCH (u:User)-[:AUTHORED]->(p:Post)
RETURN u, p
```

2. **Unbounded traversals**
```cypher
// ❌ BAD: May traverse millions of nodes
MATCH (u:User)-[*]->(friend:User)
RETURN friend

// ✅ GOOD: Limit traversal depth
MATCH (u:User)-[*1..3]->(friend:User)
RETURN friend
```

3. **Missing indexes on frequent lookups**
```cypher
// ❌ SLOW: Linear scan
MATCH (u:User {email: 'user@example.com'})
RETURN u

// ✅ FAST: Create index first
CREATE INDEX user_email FOR (u:User) ON (u.email)
```

### Graph Schema Design

**Check for:**

1. **Appropriate use of relationships vs properties**
```cypher
// ❌ BAD: Storing relationships as properties
(:User {friends: [123, 456, 789]})

// ✅ GOOD: Model as graph relationships
(:User)-[:FRIENDS_WITH]->(:User)
```

2. **Relationship direction consistency**
```cypher
// ❌ INCONSISTENT:
(:User)-[:LIKES]->(:Post)
(:Post)-[:LIKED_BY]->(:User)

// ✅ CONSISTENT: Pick one direction
(:User)-[:LIKES]->(:Post)
```

3. **Over-connected nodes (super nodes)**
```cypher
// ❌ PROBLEM: One node with millions of relationships
(:Category {name: 'General'})<-[:IN_CATEGORY]-(:Post) // x 10M posts
// Traversing this node is very slow

// ✅ SOLUTION: Hierarchical categories or use properties
(:Post {category: 'General'})
// Or subcategories to distribute load
```

### Graph Query Patterns

**Efficient patterns:**

1. **Use LIMIT early**
```cypher
// ❌ BAD: Processes all then limits
MATCH (u:User)-[:FOLLOWS]->(f:User)
WITH u, collect(f) as friends
RETURN u, friends
LIMIT 10

// ✅ GOOD: Limit early
MATCH (u:User)-[:FOLLOWS]->(f:User)
WITH u, f LIMIT 100
WITH u, collect(f) as friends
RETURN u, friends
LIMIT 10
```

2. **Use OPTIONAL MATCH carefully**
```cypher
// ❌ SLOW: Optional matches are expensive
MATCH (u:User)
OPTIONAL MATCH (u)-[:HAS_POST]->(p:Post)
OPTIONAL MATCH (u)-[:HAS_COMMENT]->(c:Comment)
RETURN u, p, c

// ✅ FASTER: Separate queries or use UNION
MATCH (u:User)
MATCH (u)-[:HAS_POST]->(p:Post)
RETURN u, p
```

### Neo4j-Specific Checks

**Indexes:**
```cypher
// Check for these indexes
CREATE INDEX FOR (u:User) ON (u.email)
CREATE INDEX FOR (p:Post) ON (p.created_at)
CREATE CONSTRAINT FOR (u:User) REQUIRE u.id IS UNIQUE
```

**Query profiling:**
```cypher
// Always profile slow queries
PROFILE
MATCH (u:User)-[:FOLLOWS*2..3]->(friend:User)
WHERE u.id = $userId
RETURN friend
// Look for: db hits, rows, execution time
```

### ArangoDB-Specific (AQL)

```javascript
// ❌ BAD: No index on edge collection
FOR v, e IN 1..3 OUTBOUND 'users/123' edges
  RETURN v

// ✅ GOOD: Index on _from and _to
db.edges.ensureIndex({ type: "persistent", fields: ["_from", "_to"] })
```

## Phase 4C: NoSQL-Specific Analysis

### MongoDB Analysis

**Critical checks:**

1. **Index usage**
```javascript
// ❌ BAD: Query without index
db.users.find({ email: "user@example.com" })

// Check if index exists:
db.users.getIndexes()

// ✅ GOOD: Create index
db.users.createIndex({ email: 1 })
```

2. **N+1 with populate**
```javascript
// ❌ BAD: N+1 with manual lookups
const posts = await Post.find();
for (const post of posts) {
  post.author = await User.findById(post.authorId);
}

// ✅ GOOD: Use populate
const posts = await Post.find().populate('author');
```

3. **Large document issues**
```javascript
// ❌ BAD: Fetching entire large documents
db.articles.find({ category: "tech" })
// Each document might be 16MB limit

// ✅ GOOD: Project only needed fields
db.articles.find(
  { category: "tech" },
  { title: 1, summary: 1, _id: 1 }
)
```

4. **Aggregation pipeline optimization**
```javascript
// ❌ BAD: Filter after expensive operations
db.posts.aggregate([
  { $lookup: { from: "users", ... } },
  { $unwind: "$comments" },
  { $match: { status: "published" } }  // Should be first!
])

// ✅ GOOD: Filter early
db.posts.aggregate([
  { $match: { status: "published" } },  // Filter first
  { $lookup: { from: "users", ... } },
  { $unwind: "$comments" }
])
```

### Redis Analysis

**Critical checks:**

1. **Key naming consistency**
```javascript
// ❌ BAD: Inconsistent naming
redis.set("user123", data)
redis.set("user:456", data)
redis.set("users_789", data)

// ✅ GOOD: Consistent pattern
redis.set("user:123", data)
redis.set("user:456", data)
```

2. **Missing expiration (TTL)**
```javascript
// ❌ BAD: No expiration → memory leak
redis.set("session:abc123", sessionData)

// ✅ GOOD: Set TTL
redis.setex("session:abc123", 3600, sessionData)  // 1 hour
```

3. **Large data structures**
```javascript
// ❌ BAD: Storing huge list in single key
redis.lpush("all_events", event)  // Millions of events

// ✅ GOOD: Partition by time/category
redis.lpush(`events:${date}`, event)
redis.expire(`events:${date}`, 86400)  // 24 hour retention
```

4. **Pipeline usage**
```javascript
// ❌ BAD: Individual commands
for (const key of keys) {
  await redis.get(key);
}

// ✅ GOOD: Pipeline
const pipeline = redis.pipeline();
keys.forEach(key => pipeline.get(key));
const results = await pipeline.exec();
```

5. **Pub/Sub vs Streams**
```javascript
// ❌ SUBOPTIMAL: Using pub/sub for data that needs persistence
redis.publish('events', data)
// Lost if no subscribers

// ✅ BETTER: Use streams for persistent messaging
redis.xadd('events', '*', 'data', JSON.stringify(data))
```

## Phase 5: Transaction Analysis

**Critical transaction checks:**

### Transaction Boundaries
```
✓ Related operations wrapped in single transaction?
✓ Transaction scope not too large (holding locks too long)?
✓ No external API calls inside transactions?
✓ Proper commit/rollback in error cases?
```

**Anti-patterns:**
```javascript
// BAD: API call in transaction
await db.transaction(async tx => {
  await tx.users.create(user);
  await callExternalAPI();  // Transaction held during network call!
  await tx.orders.create(order);
});

// BAD: Missing transaction
await db.users.create(user);
await db.accounts.create(account);  // If this fails, orphaned user!
```

### Isolation Levels
```
✓ Isolation level explicitly set?
✓ Level appropriate for use case?
✓ Understanding of read phenomena (dirty reads, phantom reads)?
```

### Deadlock Prevention
```
✓ Tables accessed in consistent order?
✓ Timeout configured?
✓ Retry logic for deadlock errors?
✓ Minimal lock duration?
```

## Phase 6: Error Handling & Resilience

**Required error handling patterns:**

### Database Errors
```javascript
// Check for proper handling:
try {
  await db.query(...);
} catch (error) {
  // Must handle:
  - Connection timeout
  - Unique constraint violation
  - Foreign key violation  
  - Deadlock
  - Connection pool exhausted
}
```

**Look for:**
- Generic error catching without specific handling
- No retry logic for transient errors
- Missing circuit breaker pattern for DB failures
- No fallback strategy (cache, read replicas)

### Connection Management
```
✓ Connections closed in finally blocks?
✓ Connection leaks prevented?
✓ Proper cleanup on application shutdown?
```

## Phase 7: Security Analysis

**Critical security scans:**

### SQL Injection Vulnerabilities

**High-risk patterns (MUST FLAG):**
```javascript
// CRITICAL: String concatenation with user input
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// CRITICAL: Dynamic table/column names from user input  
const table = req.params.table;
const query = `SELECT * FROM ${table}`;

// CRITICAL: Unescaped user input
db.raw(`WHERE name = '${req.body.name}'`);
```

**Safe patterns:**
```javascript
// GOOD: Parameterized query
db.query('SELECT * FROM users WHERE id = ?', [userId]);

// GOOD: ORM with proper escaping
db.users.findOne({ where: { id: userId } });
```

**Scan strategy:**
1. Search for template literals containing SQL keywords
2. Find string concatenation near SQL queries
3. Check for `req.body`, `req.params`, `req.query` used in queries
4. Verify all dynamic values use parameterized queries

### Sensitive Data Exposure

**Check for:**
```
✓ Passwords stored in plaintext (CRITICAL)?
✓ API keys/tokens unencrypted?
✓ PII (emails, SSN, etc.) encrypted at rest?
✓ Sensitive data in logs?
✓ Sensitive columns in error messages?
```

**Scan logs for:**
```javascript
// BAD: Password in log
console.log('User login:', { email, password });

// BAD: Full query with sensitive data
logger.error('Query failed:', sqlQuery);
```

### Access Control
```
✓ Database user has minimal privileges?
✓ Separate DB users per service?
✓ Production DB not accessible from development?
✓ Row-level security where needed?
```

## Phase 8: Performance & Monitoring

**This phase combines static analysis with optional live performance testing.**

### Slow Query Risks (Static Analysis)

**Patterns indicating slow queries:**
- Full table scans (no WHERE clause or unindexed columns)
- Large JOINs without indexes
- COUNT(*) on large tables without conditions
- GROUP BY on non-indexed columns
- DISTINCT on large result sets

### Live Query Performance Testing (Recommended)

**If database connection is available**, test actual query performance:

#### For PostgreSQL

```python
import psycopg2
import time

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

def analyze_query(query, params=None):
    """
    Run EXPLAIN ANALYZE to get actual execution stats
    """
    # Add EXPLAIN ANALYZE
    explain_query = f"EXPLAIN ANALYZE {query}"
    
    try:
        cur.execute(explain_query, params)
        plan = cur.fetchall()
        
        # Parse execution time
        execution_time = None
        for line in plan:
            if 'Execution Time' in line[0]:
                execution_time = float(line[0].split(':')[1].strip().split(' ')[0])
        
        # Parse plan details
        has_seq_scan = any('Seq Scan' in str(line) for line in plan)
        has_index_scan = any('Index Scan' in str(line) or 'Index Only Scan' in str(line) for line in plan)
        
        return {
            'execution_time_ms': execution_time,
            'has_seq_scan': has_seq_scan,
            'has_index_scan': has_index_scan,
            'full_plan': plan,
            'query': query
        }
    except Exception as e:
        return {'error': str(e), 'query': query}

# Test queries found in codebase
queries_to_test = [
    "SELECT * FROM users WHERE email = %s",
    "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT 10",
    # ... (from find_queries.py output)
]

results = []
for query in queries_to_test:
    result = analyze_query(query, ['test@example.com'])
    results.append(result)
    
    # Flag slow queries
    if result.get('execution_time_ms', 0) > 100:
        print(f"⚠️  SLOW QUERY ({result['execution_time_ms']}ms): {query}")
    
    # Flag sequential scans
    if result.get('has_seq_scan'):
        print(f"⚠️  SEQUENTIAL SCAN: {query}")
```

**What to look for in EXPLAIN ANALYZE output:**

1. **Sequential Scans** (bad on large tables)
```
Seq Scan on users  (cost=0.00..1000000.00 rows=1000000)
```
→ Should be Index Scan

2. **High cost numbers**
```
cost=10000.00..20000.00
```
→ Optimize query or add indexes

3. **Many rows examined vs returned**
```
rows=1000000 → actual rows=10
```
→ Better filtering needed

4. **Nested loops on large tables**
```
Nested Loop (cost=...)
  -> Seq Scan on table1 (rows=100000)
  -> Index Scan on table2 (rows=50)
```
→ Consider different JOIN strategy

#### For MySQL

```python
import mysql.connector

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

def analyze_mysql_query(query, params=None):
    """Run EXPLAIN for MySQL"""
    explain_query = f"EXPLAIN {query}"
    
    cursor.execute(explain_query, params)
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    # Parse result
    explain_dict = dict(zip(columns, result[0]))
    
    # Check for issues
    issues = []
    
    # Check type (should not be ALL)
    if explain_dict['type'] == 'ALL':
        issues.append('Full table scan (type=ALL)')
    
    # Check rows examined
    if explain_dict['rows'] > 10000:
        issues.append(f'High row count: {explain_dict["rows"]}')
    
    # Check if using index
    if not explain_dict['key']:
        issues.append('No index used')
    
    return {
        'explain': explain_dict,
        'issues': issues,
        'query': query
    }
```

#### For MongoDB

```python
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def analyze_mongodb_query(collection_name, query_filter, sort=None):
    """Analyze MongoDB query using explain()"""
    collection = db[collection_name]
    
    # Build query
    cursor = collection.find(query_filter)
    if sort:
        cursor = cursor.sort(sort)
    
    # Get execution stats
    explain = cursor.explain()
    
    exec_stats = explain['executionStats']
    
    return {
        'execution_time_ms': exec_stats['executionTimeMillis'],
        'docs_examined': exec_stats['totalDocsExamined'],
        'docs_returned': exec_stats['nReturned'],
        'index_used': explain['queryPlanner'].get('winningPlan', {}).get('inputStage', {}).get('indexName'),
        'is_covered': exec_stats.get('totalDocsExamined', 0) == exec_stats.get('nReturned', 0)
    }

# Example
result = analyze_mongodb_query(
    'users',
    {'email': 'test@example.com'},
    sort=[('created_at', -1)]
)

if result['docs_examined'] > result['docs_returned'] * 10:
    print(f"⚠️  Inefficient query: examined {result['docs_examined']} docs to return {result['docs_returned']}")
```

#### For Neo4j (GraphDB)

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(NEO4J_URI, auth=(USER, PASSWORD))

def analyze_neo4j_query(query, params=None):
    """Profile Neo4j query"""
    with driver.session() as session:
        # Add PROFILE
        profile_query = f"PROFILE {query}"
        result = session.run(profile_query, params or {})
        
        # Get profile
        profile = result.consume().profile
        
        # Extract metrics
        db_hits = profile.get('db_hits', 0)
        rows = profile.get('rows', 0)
        
        # Check for issues
        issues = []
        
        # High db hits per row
        if rows > 0 and db_hits / rows > 1000:
            issues.append(f'High db_hits per row: {db_hits / rows:.0f}')
        
        # Look for expensive operations
        if 'NodeByLabelScan' in str(profile):
            issues.append('Full label scan (add index)')
        
        return {
            'db_hits': db_hits,
            'rows': rows,
            'profile': profile,
            'issues': issues,
            'query': query
        }

# Example
result = analyze_neo4j_query(
    "MATCH (u:User {email: $email}) RETURN u",
    {'email': 'test@example.com'}
)
```

### Performance Testing Strategy

**Step-by-step process:**

1. **Collect queries from code** (using find_queries.py)
2. **Prioritize by frequency** (queries in hot paths first)
3. **Test with realistic data volumes**
   - Use production-like dataset size
   - Test with actual data distribution
4. **Run EXPLAIN ANALYZE on each query**
5. **Flag issues:**
   - Execution time > 100ms (web endpoints)
   - Execution time > 1000ms (background jobs)
   - Sequential scans on tables > 10k rows
   - High rows examined to returned ratio (> 10:1)
6. **Generate performance report**

### Automated Performance Testing Script

Create a test script that:
```python
def performance_test_suite():
    """
    Automated performance testing
    """
    # 1. Load queries from find_queries.py output
    with open('queries_found.json') as f:
        queries = json.load(f)
    
    # 2. Test each query
    results = []
    for query_info in queries:
        if query_info['type'] == 'raw_sql':
            result = analyze_query(query_info['query'])
            results.append({
                'file': query_info['file'],
                'line': query_info['line'],
                'performance': result
            })
    
    # 3. Generate report
    slow_queries = [r for r in results if r['performance'].get('execution_time_ms', 0) > 100]
    seq_scans = [r for r in results if r['performance'].get('has_seq_scan')]
    
    print(f"\nPerformance Test Results:")
    print(f"Total queries tested: {len(results)}")
    print(f"Slow queries (>100ms): {len(slow_queries)}")
    print(f"Sequential scans: {len(seq_scans)}")
    
    return {
        'total': len(results),
        'slow_queries': slow_queries,
        'seq_scans': seq_scans
    }
```

### Connection Pool Monitoring
```
✓ Pool statistics logged?
✓ Alerts for pool exhaustion?
✓ Monitoring active vs idle connections?
```

### Caching Strategy
```
✓ Frequently accessed data cached?
✓ Cache invalidation strategy defined?
✓ Cache keys well-designed?
✓ TTL appropriate?
```

**Check for repeated identical queries:**
```javascript
// BAD: Same query in loop
for (const id of userIds) {
  const config = await db.config.findOne({ key: 'setting' });  // Always same!
}
```

## Phase 9: Code-Schema Consistency

**Cross-validation checks:**

### Orphaned Indexes
Find indexes in schema not used by any query:
1. List all indexes from schema
2. Check if any query uses those indexed columns
3. Report unused indexes (waste space, slow writes)

### Missing Tables/Columns in Code
```
✓ All schema tables referenced in code?
✓ No queries referencing dropped columns?
✓ Type mismatches (code expects string, DB has int)?
```

### Dead Code
```
✓ Unused repository methods?
✓ Obsolete query functions?
✓ Legacy models no longer in schema?
```

## Comprehensive Scanning Techniques

**To ensure nothing is missed:**

1. **Multi-pass scanning:** 
   - First pass: Identify all DB-related files
   - Second pass: Extract all queries and patterns
   - Third pass: Deep analysis of flagged items

2. **Pattern matching:**
   - Use regex to find SQL keywords in strings
   - Search for ORM method calls across all files
   - Grep for common vulnerability patterns

3. **Context analysis:**
   - Don't just flag isolated lines
   - Understand surrounding code context
   - Trace data flow from user input to query

4. **Cross-reference:**
   - Match code queries against schema
   - Verify transaction boundaries span related operations
   - Check error handlers cover all DB error types

## Reporting Format

Generate structured report with prioritized findings:

```markdown
# Database Production Readiness Analysis

**Project:** [Project Name]
**Databases:** PostgreSQL, Redis, MongoDB
**Analysis Date:** [Date]

## Executive Summary
- Total files analyzed: X
- Critical issues: X
- Warnings: X
- Optimization opportunities: X

## 🔴 Critical Issues (IMMEDIATE ACTION REQUIRED)

### 1. SQL Injection Vulnerability
**Severity:** CRITICAL
**Location:** `src/api/user-controller.js:45-47`
**Issue:**
```javascript
const userId = req.params.id;
const query = `SELECT * FROM users WHERE id = '${userId}'`;
```
**Risk:** Direct SQL injection, can lead to data breach
**Fix:** Use parameterized queries:
```javascript
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);
```

### 2. Missing Transaction for Related Writes
**Severity:** CRITICAL
**Location:** `src/services/order-service.js:120-135`
**Issue:** Order creation and inventory update not in transaction
**Risk:** Data inconsistency if one operation fails
**Fix:** Wrap in transaction

## ⚠️ Warnings (HIGH PRIORITY)

### 1. N+1 Query Pattern
**Severity:** HIGH
**Location:** `src/api/posts-controller.js:67-72`
**Issue:**
```javascript
for (const post of posts) {
  post.author = await getUser(post.authorId);  // N queries
}
```
**Impact:** 1000 posts = 1001 queries (1 + 1000)
**Fix:** Use JOIN or eager loading:
```javascript
const posts = await db.posts.findAll({
  include: [{ model: User, as: 'author' }]
});
```

### 2. Missing Index on Frequently Queried Column
**Severity:** HIGH
**Table:** `orders`
**Column:** `customer_id, created_at`
**Queries affected:** 3 locations
- `src/api/orders.js:45`
- `src/services/analytics.js:120`  
- `src/reports/monthly.js:89`
**Impact:** Full table scan on 2M rows
**Fix:** 
```sql
CREATE INDEX idx_orders_customer_created 
ON orders(customer_id, created_at DESC);
```

## 💡 Optimization Opportunities

### 1. SELECT * Overuse
**Severity:** MEDIUM
**Locations:** 15 instances found
**Impact:** Fetching unnecessary data, network overhead
**Example:** `src/api/users.js:34`
**Fix:** Select only needed columns

### 2. Missing Connection Pool Configuration
**Severity:** MEDIUM
**Location:** `config/database.js`
**Issue:** Using default pool size (10)
**Recommendation:** Configure based on workload:
```javascript
pool: {
  min: 5,
  max: 30,
  acquireTimeoutMillis: 30000,
  idleTimeoutMillis: 30000
}
```

### 3. VectorDB: Inconsistent Embedding Dimensions
**Severity:** MEDIUM
**Database:** Pinecone
**Location:** `src/services/embedding-service.js:23, 67`
**Issue:**
```python
# Two different models used
embeddings_v1 = model_old.encode(text)  # 768 dims
embeddings_v2 = model_new.encode(text)  # 1536 dims
```
**Impact:** Dimension mismatch errors, inconsistent search results
**Fix:** Standardize on single embedding model and dimension:
```python
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIM = 1536
```

### 4. GraphDB: Unbounded Traversal
**Severity:** HIGH
**Database:** Neo4j
**Location:** `src/graph/friend-finder.js:45`
**Issue:**
```cypher
MATCH (u:User)-[*]->(friend:User)
WHERE u.id = $userId
RETURN friend
```
**Impact:** May traverse millions of nodes, causing timeouts
**Fix:** Limit traversal depth:
```cypher
MATCH (u:User)-[*1..3]->(friend:User)
WHERE u.id = $userId
RETURN friend
```

### 5. Redis: Missing TTL on Session Keys
**Severity:** MEDIUM
**Database:** Redis
**Locations:** 8 instances in `src/auth/`
**Issue:**
```javascript
redis.set(`session:${sessionId}`, sessionData)
// No expiration → memory leak
```
**Fix:** Always set TTL:
```javascript
redis.setex(`session:${sessionId}`, 3600, sessionData)
```

### 6. MongoDB: Inefficient Aggregation Pipeline
**Severity:** MEDIUM
**Database:** MongoDB
**Location:** `src/services/analytics.js:120`
**Issue:**
```javascript
db.posts.aggregate([
  { $lookup: { from: "users", ... } },  // Expensive
  { $match: { status: "published" } }   // Should be first!
])
```
**Fix:** Filter early in pipeline:
```javascript
db.posts.aggregate([
  { $match: { status: "published" } },  // Filter first
  { $lookup: { from: "users", ... } }
])
```

## ✅ Good Practices Found

- ✓ Parameterized queries used in user authentication
- ✓ Connection pooling enabled
- ✓ Migrations have rollback scripts
- ✓ Sensitive data encrypted (passwords bcrypt hashed)
- ✓ Transaction boundaries clear in payment processing

## Statistics

**Overall:**
- Total queries analyzed: 347
- Files scanned: 128
- Critical issues: 3
- High priority warnings: 12
- Medium optimizations: 23

**By Database Type:**
- SQL (PostgreSQL, MySQL): 245 queries
  - SQL injection risks: 3
  - N+1 patterns: 7
  - Missing indexes: 12
  - Transaction issues: 4
  - Unused indexes: 2

- NoSQL (MongoDB, Redis): 67 operations
  - Missing indexes (MongoDB): 5
  - Missing TTL (Redis): 8
  - Inefficient aggregations: 3

- VectorDB (Pinecone): 25 operations
  - Dimension inconsistencies: 2
  - Missing batch operations: 4
  - Inefficient metadata filters: 3

- GraphDB (Neo4j): 10 queries
  - Unbounded traversals: 2
  - Missing indexes on nodes: 3
  - Cartesian products: 1

## Recommendations Priority

1. **Week 1:** Fix all CRITICAL issues (SQL injection, missing transactions)
2. **Week 2:** Address HIGH priority warnings (N+1 queries, critical indexes)
3. **Month 1:** Implement MEDIUM optimizations (SELECT *, pool configuration)
4. **Ongoing:** Monitor slow queries, add indexes as needed
```

## Best Practices for Analysis

**Be thorough:**
- Don't skip files that "look fine"
- Check test files too (they reveal usage patterns)
- Examine migration history for clues
- Read comments (often indicate known issues)

**Be specific:**
- Always provide exact file paths and line numbers
- Include code snippets showing the issue
- Suggest concrete fixes, not just "improve this"
- Show before/after examples

**Be practical:**
- Prioritize by severity and impact
- Consider team's ability to fix (quick wins vs long-term)
- Note good practices found (positive reinforcement)
- Provide statistics to show scope

**Stay focused:**
- This skill analyzes DB implementation, not application logic
- Flag DB-related issues only
- Don't review general code quality unless it affects DB operations

## Common Frameworks & Tools

Recognize these patterns for accurate analysis:

**Node.js/TypeScript:**
- SQL: Prisma, TypeORM, Sequelize, Knex, pg
- NoSQL: Mongoose, ioredis
- VectorDB: @pinecone-database/pinecone, chromadb, weaviate-ts-client
- GraphDB: neo4j-driver, arangojs
- Look in: `*.js`, `*.ts`, `repositories/`, `models/`, `vectorstore/`

**Python:**
- SQL: SQLAlchemy, Django ORM, Peewee, Tortoise ORM, psycopg2
- NoSQL: pymongo, redis-py
- VectorDB: pinecone-client, chromadb, weaviate-client, pymilvus, qdrant-client
- GraphDB: neo4j, pyarango, gremlinpython
- Look in: `*.py`, `models/`, `queries/`, `repositories/`, `vectorstore/`

**Ruby:**
- SQL: ActiveRecord, Sequel
- GraphDB: neo4j-ruby-driver
- Look in: `*.rb`, `models/`, `app/`

**Go:**
- SQL: GORM, sqlx, ent
- NoSQL: mongo-driver, go-redis
- GraphDB: neo4j-go-driver
- Look in: `*.go`, `repository/`, `model/`

**Java:**
- SQL: Hibernate, JPA, MyBatis, JDBC
- NoSQL: MongoDB Java Driver
- GraphDB: Neo4j Java Driver
- Look in: `*.java`, `repository/`, `entity/`

**PHP:**
- SQL: Laravel Eloquent, Doctrine, PDO
- NoSQL: MongoDB PHP Library
- Look in: `*.php`, `Models/`, `Repositories/`

## Resources

### scripts/
Contains helper utilities for automated analysis tasks:

**Static Analysis:**
- `find_queries.py` - Extract all database queries from code (SQL, NoSQL, VectorDB, GraphDB)
- `analyze_schema.py` - Parse and validate database schema from migration files
- `detect_n_plus_one.py` - Identify N+1 query patterns in code

**Live Database Analysis:**
- `inspect_live_schema.py` - Connect to actual databases to inspect schema, indexes, and statistics
  - Supports: PostgreSQL, MySQL, MongoDB, Redis
  - Retrieves: Tables/collections, indexes, foreign keys, row counts, sizes
  - Usage: `python inspect_live_schema.py <connection_string>`

- `test_query_performance.py` - Test actual query performance with EXPLAIN ANALYZE
  - Supports: PostgreSQL, MySQL, MongoDB
  - Measures: Execution time, plan analysis, sequential scan detection
  - Usage: `python test_query_performance.py <connection_string> queries_found.json`

### references/
- `common_vulnerabilities.md` - Database security vulnerability patterns (SQL injection, etc.)
- `optimization_patterns.md` - Query optimization techniques for SQL databases
- `vectordb_graphdb_patterns.md` - Best practices for VectorDB and GraphDB
