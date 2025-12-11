# Database Query Optimization Patterns

This document provides patterns and techniques for optimizing database queries.

## Index Optimization

### 1. Single Column Indexes

**When to use:**
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY
- Foreign key columns

```sql
-- Create index on frequently queried column
CREATE INDEX idx_users_email ON users(email);

-- Query now uses index
SELECT * FROM users WHERE email = 'user@example.com';
```

### 2. Composite (Multi-Column) Indexes

**Column order matters!** Put most selective columns first.

```sql
-- Good: Status is selective, created_at for sorting
CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC);

-- Query can use this index efficiently
SELECT * FROM orders 
WHERE status = 'pending' 
ORDER BY created_at DESC;

-- Also uses index (prefix match)
SELECT * FROM orders WHERE status = 'pending';

-- ❌ Does NOT use index (wrong column order)
SELECT * FROM orders WHERE created_at > '2024-01-01';
```

**Rule:** Index columns in order: WHERE = → WHERE IN → ORDER BY

### 3. Covering Indexes

Include frequently accessed columns in the index to avoid table lookups.

```sql
-- Index covers query - no table access needed
CREATE INDEX idx_users_email_name ON users(email, name);

SELECT name FROM users WHERE email = 'user@example.com';
-- Reads only from index, no table scan
```

### 4. Partial Indexes

Index only relevant rows to save space.

```sql
-- PostgreSQL: Only index active users
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Query benefits if filtering by is_active
SELECT * FROM users WHERE is_active = true AND email LIKE 'john%';
```

### 5. When NOT to Index

Avoid indexes on:
- Small tables (< 1000 rows)
- Columns with low cardinality (e.g., boolean, status with 3 values)
- Frequently updated columns (indexes slow writes)
- Columns never used in WHERE/JOIN/ORDER BY

## Query Pattern Optimizations

### 1. Avoiding SELECT *

```javascript
// ❌ BAD - Fetches all 50 columns
const users = await db.users.findAll();

// ✅ GOOD - Select only needed columns
const users = await db.users.findAll({
    attributes: ['id', 'email', 'name']
});
```

**Benefits:**
- Reduced network transfer
- Lower memory usage
- Faster query execution
- Better cache utilization

### 2. Pagination (Avoid OFFSET)

```sql
-- ❌ BAD - OFFSET scans and discards rows
SELECT * FROM posts 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 10000;
-- Scans 10,020 rows, returns 20

-- ✅ GOOD - Cursor-based pagination
SELECT * FROM posts 
WHERE created_at < '2024-01-01 12:00:00'  -- Last seen timestamp
ORDER BY created_at DESC 
LIMIT 20;
-- Scans only 20 rows
```

**Implementation:**
```javascript
// Page 1
const posts = await db.posts.findAll({
    limit: 20,
    order: [['created_at', 'DESC']]
});

// Page 2 - use cursor
const lastPost = posts[posts.length - 1];
const nextPosts = await db.posts.findAll({
    where: {
        created_at: { $lt: lastPost.created_at }
    },
    limit: 20,
    order: [['created_at', 'DESC']]
});
```

### 3. EXISTS vs COUNT

```sql
-- ❌ BAD - Counts all rows
SELECT COUNT(*) FROM orders WHERE user_id = 123;
IF count > 0 THEN ...

-- ✅ GOOD - Stops at first match
SELECT EXISTS(SELECT 1 FROM orders WHERE user_id = 123);
```

### 4. IN vs JOIN

```sql
-- ❌ SLOWER - Subquery executed multiple times
SELECT * FROM orders 
WHERE user_id IN (
    SELECT id FROM users WHERE country = 'US'
);

-- ✅ FASTER - Single join operation
SELECT orders.* 
FROM orders 
JOIN users ON orders.user_id = users.id 
WHERE users.country = 'US';
```

### 5. Avoiding Functions in WHERE

```sql
-- ❌ BAD - Function prevents index use
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';

-- ✅ GOOD - Use functional index or case-insensitive collation
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
-- OR normalize data before insert

-- ❌ BAD - Date function prevents index
SELECT * FROM orders WHERE DATE(created_at) = '2024-01-01';

-- ✅ GOOD - Range query uses index
SELECT * FROM orders 
WHERE created_at >= '2024-01-01' 
  AND created_at < '2024-01-02';
```

## N+1 Query Solutions

### Problem

```javascript
// ❌ 1 + N queries
const posts = await db.posts.findAll();  // 1 query
for (const post of posts) {
    post.author = await db.users.findByPk(post.authorId);  // N queries
}
```

### Solution 1: Eager Loading (JOIN)

```javascript
// ✅ Single query with JOIN
const posts = await db.posts.findAll({
    include: [{ model: User, as: 'author' }]
});
// SELECT posts.*, users.* FROM posts LEFT JOIN users...
```

### Solution 2: Batch Loading

```javascript
// ✅ 2 queries total
const posts = await db.posts.findAll();
const authorIds = posts.map(p => p.authorId);
const authors = await db.users.findAll({
    where: { id: authorIds }
});
const authorsMap = new Map(authors.map(a => [a.id, a]));
posts.forEach(post => {
    post.author = authorsMap.get(post.authorId);
});
```

### Solution 3: DataLoader (GraphQL)

```javascript
const DataLoader = require('dataloader');

const userLoader = new DataLoader(async (ids) => {
    const users = await db.users.findAll({ where: { id: ids } });
    return ids.map(id => users.find(u => u.id === id));
});

// Automatically batches requests
for (const post of posts) {
    post.author = await userLoader.load(post.authorId);
}
```

## JOIN Optimizations

### 1. JOIN Order

```sql
-- ❌ BAD - Joins large tables first
SELECT * 
FROM orders  -- 10M rows
JOIN users ON orders.user_id = users.id  -- 1M rows
WHERE orders.status = 'pending';  -- 100 rows

-- ✅ GOOD - Filter first, then join small result set
SELECT * 
FROM (
    SELECT * FROM orders WHERE status = 'pending'
) AS pending_orders
JOIN users ON pending_orders.user_id = users.id;
```

### 2. JOIN vs Subquery

```sql
-- ❌ SLOWER - Correlated subquery
SELECT u.name,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
FROM users u;

-- ✅ FASTER - Single join with aggregation
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;
```

## Aggregation Optimizations

### 1. COUNT(*) vs COUNT(column)

```sql
-- Fastest (uses index if available)
SELECT COUNT(*) FROM users;

-- Slower (must check NULL values)
SELECT COUNT(email) FROM users;
```

### 2. Conditional Aggregation

```sql
-- ❌ BAD - Multiple queries
SELECT COUNT(*) FROM orders WHERE status = 'pending';
SELECT COUNT(*) FROM orders WHERE status = 'completed';

-- ✅ GOOD - Single query
SELECT 
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count
FROM orders;

-- Or using CASE
SELECT 
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count
FROM orders;
```

## Caching Strategies

### 1. Query Result Caching

```javascript
// Simple cache implementation
const cache = new Map();

async function getUserById(id) {
    const cacheKey = `user:${id}`;
    
    // Check cache
    if (cache.has(cacheKey)) {
        return cache.get(cacheKey);
    }
    
    // Query database
    const user = await db.users.findByPk(id);
    
    // Store in cache with TTL
    cache.set(cacheKey, user);
    setTimeout(() => cache.delete(cacheKey), 300000); // 5 min
    
    return user;
}
```

### 2. Cache Invalidation

```javascript
// Invalidate on update
async function updateUser(id, data) {
    await db.users.update(data, { where: { id } });
    
    // Invalidate cache
    cache.delete(`user:${id}`);
}
```

### 3. When to Cache

Cache these queries:
- ✅ Frequently read, rarely changed (config, categories)
- ✅ Expensive aggregations
- ✅ Denormalized data
- ✅ Lookup tables

Don't cache:
- ❌ Real-time data (stock prices, live scores)
- ❌ User-specific sensitive data
- ❌ Data that changes frequently

## Connection Pool Optimization

### Configuration

```javascript
// ❌ BAD - Default settings
const db = new Sequelize(DATABASE_URL);

// ✅ GOOD - Tuned for production
const db = new Sequelize(DATABASE_URL, {
    pool: {
        max: 30,              // Max connections
        min: 5,               // Min connections
        acquire: 30000,       // Max time to get connection (ms)
        idle: 10000,          // Max idle time before release (ms)
        evict: 10000,         // Eviction check interval
    },
    dialectOptions: {
        connectTimeout: 5000, // Connection timeout
    }
});
```

### Pool Sizing Formula

```
Optimal Pool Size = ((Core Count × 2) + Effective Spindle Count)

Example:
- 4 CPU cores
- 1 disk (or SSD, treat as 1)
- Pool size = (4 × 2) + 1 = 9

Adjust based on:
- Application concurrency
- Query complexity (CPU-bound vs I/O-bound)
- Available memory
```

## Query Analysis Tools

### 1. EXPLAIN ANALYZE (PostgreSQL)

```sql
EXPLAIN ANALYZE
SELECT * FROM orders 
WHERE status = 'pending' 
ORDER BY created_at DESC 
LIMIT 10;

-- Look for:
-- - Seq Scan (bad, should be Index Scan)
-- - High cost numbers
-- - Many rows examined vs returned
```

### 2. Slow Query Log

```sql
-- PostgreSQL: Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1s

-- MySQL
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
```

### 3. Query Execution Metrics

Monitor:
- Query execution time (p50, p95, p99)
- Rows examined vs rows returned ratio
- Index hit rate
- Cache hit rate
- Connection pool utilization

## Common Anti-Patterns

### 1. "God Query" Anti-Pattern

```sql
-- ❌ BAD - One massive query
SELECT 
    u.*, 
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as orders,
    (SELECT COUNT(*) FROM reviews WHERE user_id = u.id) as reviews,
    (SELECT AVG(rating) FROM reviews WHERE user_id = u.id) as avg_rating,
    ... -- 20 more subqueries
FROM users u;

-- ✅ GOOD - Split into manageable queries
-- Query 1: Get users
-- Query 2: Get aggregated stats (single query with JOINs)
-- Combine in application code
```

### 2. "Chatty" Anti-Pattern

```javascript
// ❌ BAD - Many small queries
for (const item of items) {
    await db.items.update({ stock: item.stock - 1 }, { 
        where: { id: item.id } 
    });
}

// ✅ GOOD - Single batch query
await db.items.update({ 
    stock: db.literal('stock - 1') 
}, {
    where: { id: { $in: items.map(i => i.id) } }
});
```

### 3. "Golden Hammer" Anti-Pattern

Not everything needs a query:

```javascript
// ❌ BAD - Query for static data
const statuses = await db.query('SELECT * FROM order_statuses');

// ✅ GOOD - Use constants
const ORDER_STATUSES = {
    PENDING: 'pending',
    PROCESSING: 'processing',
    COMPLETED: 'completed'
};
```

## Performance Checklist

Before deploying:

- [ ] All queries have appropriate indexes
- [ ] No N+1 queries in critical paths
- [ ] SELECT only needed columns
- [ ] Pagination implemented (no OFFSET on large tables)
- [ ] Connection pool sized correctly
- [ ] Slow query logging enabled
- [ ] Query execution plans reviewed (EXPLAIN ANALYZE)
- [ ] Caching strategy for frequently accessed data
- [ ] Database monitoring in place
- [ ] Load testing performed with realistic data volumes
