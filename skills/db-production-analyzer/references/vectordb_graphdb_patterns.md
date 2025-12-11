# VectorDB and GraphDB Best Practices

This document provides production-ready patterns for Vector and Graph databases.

## VectorDB Best Practices

### 1. Embedding Generation

#### Consistency is Critical

```python
# ❌ BAD: Inconsistent preprocessing
def index_document(text):
    embedding = model.encode(text.lower())  # lowercase
    
def search(query):
    embedding = model.encode(query)  # no lowercase!
    # Results will be inconsistent
```

```python
# ✅ GOOD: Consistent preprocessing
def preprocess_text(text):
    return text.lower().strip()

def index_document(text):
    return model.encode(preprocess_text(text))
    
def search(query):
    return model.encode(preprocess_text(query))
```

#### Handle Token Limits

```python
# ❌ BAD: Silent truncation or failure
embedding = model.encode(very_long_text)

# ✅ GOOD: Explicit chunking
MAX_TOKENS = 512

def chunk_text(text, max_tokens):
    """Split text into chunks that fit within token limit"""
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        if len(' '.join(current_chunk + [word])) > max_tokens * 4:  # ~4 chars per token
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

# Generate embeddings for each chunk
for chunk in chunk_text(long_text, MAX_TOKENS):
    embedding = model.encode(chunk)
    index.upsert([(chunk_id, embedding, metadata)])
```

#### Rate Limiting and Retries

```python
# ✅ Production-ready embedding generation
import backoff
from openai import RateLimitError

@backoff.on_exception(
    backoff.expo,
    RateLimitError,
    max_tries=5,
    max_time=300
)
def get_embedding(text, model="text-embedding-ada-002"):
    """Get embedding with automatic retry on rate limits"""
    response = openai.Embedding.create(
        input=text,
        model=model
    )
    return response['data'][0]['embedding']

# Batch processing with rate limiting
import time

def batch_embed(texts, batch_size=100, delay=1.0):
    """Batch embed with rate limit consideration"""
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = [get_embedding(text) for text in batch]
        embeddings.extend(batch_embeddings)
        
        # Respect rate limits
        if i + batch_size < len(texts):
            time.sleep(delay)
    
    return embeddings
```

### 2. Index Configuration

#### Choose the Right Index Type

```python
# For Pinecone
index_configs = {
    'small': {  # < 1M vectors
        'pod_type': 's1.x1',
        'replicas': 1,
        'index_type': 'flat',  # Highest accuracy
    },
    'medium': {  # 1M - 10M vectors
        'pod_type': 'p1.x1',
        'replicas': 2,
        'index_type': 'ivf',  # Good balance
    },
    'large': {  # > 10M vectors
        'pod_type': 'p1.x2',
        'replicas': 2,
        'index_type': 'hnsw',  # Fast search
    }
}

# For Milvus
milvus_index_params = {
    'small': {
        'index_type': 'FLAT',
        'metric_type': 'L2',
    },
    'medium': {
        'index_type': 'IVF_FLAT',
        'metric_type': 'L2',
        'params': {'nlist': 1024}
    },
    'large': {
        'index_type': 'HNSW',
        'metric_type': 'L2',
        'params': {
            'M': 16,
            'efConstruction': 256
        }
    }
}
```

#### Distance Metrics

```python
# Choose metric based on your use case
distance_metrics = {
    'cosine': {
        'use_when': 'Text embeddings, semantic similarity',
        'normalize': True,  # Vectors should be normalized
        'range': [-1, 1],
    },
    'euclidean': {
        'use_when': 'Image embeddings, absolute distance matters',
        'normalize': False,
        'range': [0, infinity],
    },
    'dot_product': {
        'use_when': 'Normalized embeddings, fastest computation',
        'normalize': True,
        'range': [-1, 1],
    }
}

# ✅ For text embeddings (most common)
index = pinecone.create_index(
    name='documents',
    dimension=1536,
    metric='cosine'  # Best for semantic similarity
)
```

### 3. Metadata Filtering

#### Design Efficient Metadata

```python
# ❌ BAD: Nested complex metadata
metadata = {
    'document': {
        'author': {
            'name': 'John',
            'department': {
                'name': 'Engineering',
                'company': 'Acme'
            }
        }
    }
}
# Hard to filter efficiently

# ✅ GOOD: Flat, indexed metadata
metadata = {
    'author_name': 'John',
    'department': 'Engineering',
    'company': 'Acme',
    'doc_type': 'report',
    'created_at': '2024-01-01',
    'category': 'technical'
}
# Easy to filter: {"department": "Engineering", "doc_type": "report"}
```

#### Pre-filter vs Post-filter

```python
# ❌ BAD: Post-filtering (inefficient)
results = index.query(
    vector=query_embedding,
    top_k=1000
)
filtered = [r for r in results if r.metadata['category'] == 'tech'][:10]
# Fetched 1000, used 10

# ✅ GOOD: Pre-filtering (efficient)
results = index.query(
    vector=query_embedding,
    top_k=10,
    filter={'category': {'$eq': 'tech'}}
)
# Fetched exactly 10
```

### 4. Batch Operations

```python
# ❌ BAD: Individual operations
for doc in documents:
    embedding = get_embedding(doc.text)
    index.upsert([(doc.id, embedding, doc.metadata)])
# N network calls

# ✅ GOOD: Batch upsert
BATCH_SIZE = 100

def batch_upsert(documents):
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i+BATCH_SIZE]
        
        # Batch generate embeddings
        texts = [doc.text for doc in batch]
        embeddings = batch_embed(texts)
        
        # Prepare vectors
        vectors = [
            (doc.id, embedding, doc.metadata)
            for doc, embedding in zip(batch, embeddings)
        ]
        
        # Single network call per batch
        index.upsert(vectors)
```

### 5. Error Handling

```python
# ✅ Production-ready error handling
from pinecone.core.client.exceptions import (
    PineconeException,
    NotFoundException,
    ServiceException
)

def safe_vector_query(query_vector, top_k=10):
    """Query with comprehensive error handling"""
    try:
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        return results
        
    except NotFoundException:
        logger.error("Index not found")
        raise
        
    except ServiceException as e:
        if 'rate limit' in str(e).lower():
            logger.warning("Rate limit hit, retrying...")
            time.sleep(60)
            return safe_vector_query(query_vector, top_k)
        raise
        
    except PineconeException as e:
        logger.error(f"Pinecone error: {e}")
        # Return empty results as fallback
        return {'matches': []}
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### 6. Monitoring and Observability

```python
# ✅ Monitor key metrics
import time

class VectorStoreMetrics:
    def __init__(self):
        self.query_times = []
        self.upsert_times = []
        
    def time_query(self, func):
        """Decorator to time queries"""
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            
            self.query_times.append(duration)
            
            # Alert on slow queries
            if duration > 1.0:
                logger.warning(f"Slow vector query: {duration:.2f}s")
            
            return result
        return wrapper
    
    def get_stats(self):
        return {
            'avg_query_time': sum(self.query_times) / len(self.query_times),
            'p95_query_time': sorted(self.query_times)[int(len(self.query_times) * 0.95)],
            'total_queries': len(self.query_times)
        }

metrics = VectorStoreMetrics()

@metrics.time_query
def search_documents(query):
    embedding = get_embedding(query)
    return index.query(vector=embedding, top_k=10)
```

---

## GraphDB Best Practices

### 1. Neo4j Query Optimization

#### Avoid Cartesian Products

```cypher
-- ❌ CRITICAL: Cartesian product
MATCH (a:User), (b:Post)
WHERE a.id = b.author_id
RETURN a, b
-- Checks every User against every Post!

-- ✅ GOOD: Use relationships
MATCH (a:User)-[:AUTHORED]->(b:Post)
RETURN a, b

-- ✅ ALTERNATIVE: Use WHERE with EXISTS
MATCH (a:User), (b:Post)
WHERE EXISTS((a)-[:AUTHORED]->(b))
RETURN a, b
```

#### Limit Traversal Depth

```cypher
-- ❌ BAD: Unbounded traversal
MATCH path = (u:User)-[*]->(friend:User)
WHERE u.id = $userId
RETURN friend
-- Could traverse millions of nodes

-- ✅ GOOD: Bounded traversal
MATCH path = (u:User)-[*1..3]->(friend:User)
WHERE u.id = $userId
RETURN friend
-- Max 3 hops
```

#### Use Indexes

```cypher
-- Create indexes on frequently queried properties
CREATE INDEX user_email FOR (u:User) ON (u.email);
CREATE INDEX post_created FOR (p:Post) ON (p.created_at);

-- Create constraints (automatically creates index)
CREATE CONSTRAINT user_id_unique FOR (u:User) REQUIRE u.id IS UNIQUE;

-- Check index usage
PROFILE
MATCH (u:User {email: 'user@example.com'})
RETURN u
-- Look for "NodeIndexSeek" in plan
```

### 2. Efficient Pattern Matching

#### Start with Most Selective Patterns

```cypher
-- ❌ BAD: Start with broad match
MATCH (u:User)
WHERE u.country = 'US'
MATCH (u)-[:PURCHASED]->(p:Product)
WHERE p.price > 100
RETURN u, p
-- Scans all US users first

-- ✅ GOOD: Start with most selective
MATCH (p:Product)
WHERE p.price > 100
MATCH (u:User)-[:PURCHASED]->(p)
WHERE u.country = 'US'
RETURN u, p
-- Starts with expensive products (fewer)
```

#### Use LIMIT Early

```cypher
-- ❌ BAD: LIMIT at end
MATCH (u:User)-[:FOLLOWS]->(f:User)-[:POSTED]->(p:Post)
WHERE u.id = $userId
RETURN p
ORDER BY p.created_at DESC
LIMIT 10
-- Processes all posts, then limits

-- ✅ GOOD: LIMIT early with subquery
MATCH (u:User {id: $userId})-[:FOLLOWS]->(f:User)
WITH f LIMIT 100
MATCH (f)-[:POSTED]->(p:Post)
RETURN p
ORDER BY p.created_at DESC
LIMIT 10
```

### 3. Relationship Design

#### Model as Relationships, Not Properties

```cypher
-- ❌ BAD: Store relationships as properties
CREATE (u:User {
    id: 1,
    friends: [2, 3, 4, 5]  -- Array of IDs
})
-- Can't traverse efficiently, no relationship metadata

-- ✅ GOOD: Use actual relationships
CREATE (u1:User {id: 1})
CREATE (u2:User {id: 2})
CREATE (u1)-[:FRIENDS_WITH {since: '2020-01-01'}]->(u2)
-- Can traverse, can store metadata
```

#### Avoid Super Nodes

```cypher
-- ❌ PROBLEM: One node with millions of relationships
CREATE (general:Category {name: 'General'})
-- Later: 10 million posts connect to this
MATCH (p:Post)-[:IN_CATEGORY]->(general)
-- Very slow to traverse

-- ✅ SOLUTION 1: Hierarchical structure
CREATE (general:Category {name: 'General'})
CREATE (tech:Category {name: 'Tech', parent: 'General'})
CREATE (ai:Category {name: 'AI', parent: 'Tech'})

-- ✅ SOLUTION 2: Use properties when appropriate
CREATE (p:Post {category: 'General'})
-- For simple categorization
```

### 4. Batch Operations

```cypher
-- ❌ BAD: Individual creates
CREATE (u:User {id: 1, name: 'Alice'});
CREATE (u:User {id: 2, name: 'Bob'});
-- ... N transactions

-- ✅ GOOD: Batch with UNWIND
UNWIND $users AS userData
CREATE (u:User)
SET u = userData
-- Single transaction for N users
```

```python
# Python example
def batch_create_users(session, users):
    query = """
    UNWIND $users AS user
    CREATE (u:User)
    SET u = user
    """
    session.run(query, users=users)

# Create 1000 users in one call
users = [{'id': i, 'name': f'User{i}'} for i in range(1000)]
batch_create_users(session, users)
```

### 5. Transaction Management

```python
# ✅ Use write transactions for writes
def create_user_with_friends(tx, user_id, friend_ids):
    # Create user
    tx.run("""
        CREATE (u:User {id: $userId})
    """, userId=user_id)
    
    # Create friendships
    tx.run("""
        MATCH (u:User {id: $userId})
        UNWIND $friendIds AS friendId
        MATCH (f:User {id: friendId})
        CREATE (u)-[:FRIENDS_WITH]->(f)
    """, userId=user_id, friendIds=friend_ids)

# Execute as single transaction
with driver.session() as session:
    session.write_transaction(create_user_with_friends, 123, [456, 789])
```

### 6. Query Profiling

```cypher
-- Always profile slow queries
PROFILE
MATCH (u:User {email: $email})-[:FRIENDS_WITH*2..3]->(friend)
RETURN friend.name

-- Look for in execution plan:
-- - "NodeByLabelScan" (bad, should be index seek)
-- - "Expand(All)" with high db hits
-- - Rows examined vs rows returned ratio
```

### 7. ArangoDB Specific (AQL)

```javascript
// ✅ Efficient AQL patterns

// 1. Use indexes
db.users.ensureIndex({ type: "persistent", fields: ["email"] });

// 2. Filter early
FOR doc IN users
  FILTER doc.country == "US"  // Filter first
  FOR edge IN edges
    FILTER edge._from == doc._id
    RETURN edge

// 3. Limit traversal depth
FOR v, e, p IN 1..3 OUTBOUND 'users/123' edges
  RETURN v

// 4. Use COLLECT for aggregation
FOR doc IN users
  COLLECT country = doc.country WITH COUNT INTO count
  RETURN { country, count }
```

### 8. Common Pitfalls

#### 1. Not Using Parameters

```cypher
-- ❌ BAD: String interpolation (slow + injection risk)
f"MATCH (u:User) WHERE u.id = '{user_id}' RETURN u"

-- ✅ GOOD: Parameterized query
"MATCH (u:User) WHERE u.id = $userId RETURN u"
session.run(query, userId=user_id)
```

#### 2. Fetching Too Much Data

```cypher
-- ❌ BAD: Return all properties
MATCH (u:User)-[:FRIENDS_WITH]->(f:User)
RETURN u, f
-- Returns ALL properties of both nodes

-- ✅ GOOD: Return only what you need
MATCH (u:User)-[:FRIENDS_WITH]->(f:User)
RETURN u.id, u.name, f.id, f.name
```

#### 3. Not Closing Sessions

```python
# ❌ BAD: Session leak
session = driver.session()
result = session.run(query)
# No close!

# ✅ GOOD: Context manager
with driver.session() as session:
    result = session.run(query)
    # Automatically closed
```

## Performance Monitoring Checklist

### VectorDB
- [ ] Embedding generation time (< 1s per batch)
- [ ] Query latency p95 (< 500ms)
- [ ] Index build time
- [ ] Storage utilization
- [ ] API rate limit usage

### GraphDB  
- [ ] Query execution time p95 (< 100ms)
- [ ] Transaction duration
- [ ] Page cache hit ratio (> 90%)
- [ ] Relationship traversal count
- [ ] Lock contention events
