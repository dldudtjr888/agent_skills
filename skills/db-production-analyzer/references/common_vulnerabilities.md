# Common Database Security Vulnerabilities

This document catalogs common database security vulnerabilities to watch for during analysis.

## SQL Injection

### High-Risk Patterns

#### 1. String Concatenation with User Input

**JavaScript/TypeScript:**
```javascript
// ❌ CRITICAL VULNERABILITY
const userId = req.params.id;
const query = `SELECT * FROM users WHERE id = '${userId}'`;
db.query(query);

// ❌ CRITICAL VULNERABILITY
const tableName = req.body.table;
const query = `SELECT * FROM ${tableName}`;

// ✅ SAFE
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);
```

**Python:**
```python
# ❌ CRITICAL VULNERABILITY
user_id = request.args.get('id')
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)

# ❌ CRITICAL VULNERABILITY  
query = "SELECT * FROM users WHERE id = '%s'" % user_id

# ✅ SAFE
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

#### 2. Dynamic Table/Column Names

```javascript
// ❌ CRITICAL - User controls table name
const table = req.query.table;
db.query(`SELECT * FROM ${table}`);

// ✅ SAFER - Whitelist approach
const ALLOWED_TABLES = ['users', 'posts', 'comments'];
const table = req.query.table;
if (ALLOWED_TABLES.includes(table)) {
    db.query(`SELECT * FROM ${table}`);
}
```

#### 3. LIKE Clause Injection

```javascript
// ❌ VULNERABLE
const search = req.query.search;
db.query(`SELECT * FROM products WHERE name LIKE '%${search}%'`);

// ✅ SAFE
db.query('SELECT * FROM products WHERE name LIKE ?', [`%${search}%`]);
```

### Detection Strategy

Look for these patterns:
- Template literals with SQL keywords: `` `SELECT * FROM ${variable}` ``
- String concatenation: `"SELECT * FROM " + variable`
- Python f-strings with SQL: `f"SELECT * FROM {table}"`
- Python %-formatting: `"SELECT * FROM %s" % table`
- No parameter binding in ORM raw queries

## Sensitive Data Exposure

### 1. Plaintext Passwords

```javascript
// ❌ CRITICAL VULNERABILITY
await db.users.create({
    email: req.body.email,
    password: req.body.password  // Plaintext!
});

// ✅ SAFE
const hashedPassword = await bcrypt.hash(req.body.password, 10);
await db.users.create({
    email: req.body.email,
    password: hashedPassword
});
```

### 2. API Keys/Tokens in Database

```python
# ❌ CRITICAL - Unencrypted API key
user.api_key = generate_api_key()
db.session.add(user)

# ✅ BETTER - Encrypt at rest
encrypted_key = encrypt(generate_api_key())
user.encrypted_api_key = encrypted_key
```

### 3. Sensitive Data in Logs

```javascript
// ❌ CRITICAL - Password in log
logger.info('User login attempt:', { 
    email: user.email, 
    password: req.body.password 
});

// ❌ CRITICAL - Credit card in query log
logger.error('Query failed:', {
    query: `INSERT INTO payments (cc_number) VALUES ('${ccNumber}')`
});

// ✅ SAFE - Redacted
logger.info('User login attempt:', { 
    email: user.email,
    password: '[REDACTED]'
});
```

### 4. PII Without Encryption

Tables that should have encrypted columns:
- `ssn`, `tax_id`
- `credit_card_number`, `cvv`
- `bank_account_number`
- `health_records`
- `passport_number`

## Authentication & Authorization Issues

### 1. Missing Row-Level Security

```sql
-- ❌ Users can access any row
SELECT * FROM documents WHERE id = ?

-- ✅ Filter by ownership
SELECT * FROM documents WHERE id = ? AND user_id = ?
```

### 2. Privilege Escalation Risks

```javascript
// ❌ No authorization check
app.delete('/users/:id', async (req, res) => {
    await db.users.delete({ id: req.params.id });
});

// ✅ Check permissions
app.delete('/users/:id', async (req, res) => {
    if (req.user.id !== req.params.id && !req.user.isAdmin) {
        return res.status(403).send('Forbidden');
    }
    await db.users.delete({ id: req.params.id });
});
```

## Mass Assignment Vulnerabilities

```javascript
// ❌ User can set any field, including 'is_admin'
app.post('/users', async (req, res) => {
    const user = await db.users.create(req.body);
});

// ✅ Explicitly allow only safe fields
app.post('/users', async (req, res) => {
    const { email, name } = req.body;  // Whitelist
    const user = await db.users.create({ email, name });
});
```

## Connection String Exposure

### 1. Hardcoded Credentials

```javascript
// ❌ CRITICAL - Credentials in code
const db = new Database({
    host: 'prod-db.example.com',
    user: 'admin',
    password: 'SuperSecret123!'
});

// ✅ SAFE - Environment variables
const db = new Database({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD
});
```

### 2. Connection Strings in Version Control

Check for:
- `.env` files committed (should be in `.gitignore`)
- Config files with real credentials
- Connection strings in comments

## Timing Attack Vulnerabilities

```javascript
// ❌ VULNERABLE - Timing attack possible
if (user.password === req.body.password) {
    // Early return reveals timing
}

// ✅ SAFE - Constant time comparison
if (crypto.timingSafeEqual(
    Buffer.from(user.password),
    Buffer.from(req.body.password)
)) {
    // Timing safe
}
```

## Second-Order SQL Injection

```javascript
// ❌ VULNERABLE - User input stored, then used unsafely
// Step 1: Store (safely)
await db.users.create({ name: req.body.name });

// Step 2: Use later (UNSAFE!)
const users = await db.users.findAll();
users.forEach(user => {
    db.query(`INSERT INTO log VALUES ('User ${user.name} logged in')`);
    // If user.name = "'); DROP TABLE users; --" → injection!
});
```

## NoSQL Injection (MongoDB, etc.)

```javascript
// ❌ VULNERABLE
const username = req.body.username;
const user = await db.users.findOne({ 
    username: username 
});
// If username = { $ne: null }, returns any user!

// ✅ SAFE - Validate type
if (typeof username !== 'string') {
    throw new Error('Invalid username');
}
const user = await db.users.findOne({ username });
```

## Insecure Direct Object Reference (IDOR)

```javascript
// ❌ No ownership check
app.get('/orders/:id', async (req, res) => {
    const order = await db.orders.findOne({ id: req.params.id });
    res.json(order);
    // Any user can view any order!
});

// ✅ Check ownership
app.get('/orders/:id', async (req, res) => {
    const order = await db.orders.findOne({ 
        id: req.params.id,
        user_id: req.user.id  // Filter by current user
    });
    if (!order) return res.status(404).send('Not found');
    res.json(order);
});
```

## Detection Checklist

When analyzing code, check for:

1. **String manipulation near SQL keywords** - grep for `SELECT`, `INSERT`, `UPDATE`, `DELETE`
2. **Template literals/f-strings with queries** - `${`, `{variable}`
3. **User input variables** - `req.body`, `req.params`, `request.args`
4. **No parameterized queries** - absence of `?` or `$1` placeholders
5. **Plaintext sensitive data** - password fields without hashing
6. **Logged sensitive data** - logger calls with user input
7. **Missing authorization checks** - write operations without permission checks
8. **Hardcoded credentials** - connection strings in code
9. **Mass assignment** - `create(req.body)` without filtering

## Reporting Template

```markdown
### SQL Injection Vulnerability
**Severity:** CRITICAL
**Location:** `src/api/users.js:45`
**Issue:**
\```javascript
const query = `SELECT * FROM users WHERE id = '${userId}'`;
\```
**Risk:** Attacker can inject malicious SQL, leading to:
- Unauthorized data access
- Data modification or deletion  
- Potential server compromise

**Fix:**
\```javascript
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);
\```

**Verify fix by:**
1. Test with malicious input: `1' OR '1'='1`
2. Confirm error or safe handling
3. Review all similar patterns in codebase
```
