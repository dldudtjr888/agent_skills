# Python Database Cheatsheet

## SQLAlchemy

### Model Definition
```python
from sqlalchemy import Column, BigInteger, Text, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(Text, nullable=False, unique=True)
    name = Column(Text)
    balance = Column(Numeric(12, 2), default=0)
    is_active = Column(Boolean, default=True)
    metadata_ = Column('metadata', JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    orders = relationship('Order', back_populates='user')
```

### Eager Loading (N+1 방지)
```python
from sqlalchemy.orm import joinedload, selectinload

# joinedload: JOIN으로 한 번에
users = session.query(User).options(joinedload(User.orders)).all()

# selectinload: IN 쿼리로 배치 로드
users = session.query(User).options(selectinload(User.orders)).all()
```

### Index Definition
```python
from sqlalchemy import Index

class Order(Base):
    __tablename__ = 'orders'
    __table_args__ = (
        Index('orders_user_created_idx', 'user_id', 'created_at'),
        Index('orders_pending_idx', 'created_at', postgresql_where=(status == 'pending')),
    )
```

### Batch Operations
```python
# Bulk insert
session.bulk_insert_mappings(User, [
    {'email': 'a@example.com', 'name': 'A'},
    {'email': 'b@example.com', 'name': 'B'},
])

# Batch update
session.query(User).filter(User.is_active == False).update(
    {'is_active': True},
    synchronize_session=False
)
```

---

## Alembic (Migrations)

### Create Migration
```bash
# 자동 생성
alembic revision --autogenerate -m "add user status"

# 수동 생성
alembic revision -m "add user status"
```

### Migration File
```python
# migrations/versions/001_add_user_status.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('status', sa.Text(), nullable=True))
    op.execute("UPDATE users SET status = 'active'")
    op.alter_column('users', 'status', nullable=False)

def downgrade():
    op.drop_column('users', 'status')
```

### Run Migrations
```bash
# 최신으로
alembic upgrade head

# 특정 버전으로
alembic upgrade abc123

# 롤백
alembic downgrade -1
```

### Safe Migration Patterns
```python
# Index 생성 (락 없이)
def upgrade():
    op.execute('CREATE INDEX CONCURRENTLY users_email_idx ON users(email)')

# 배치 업데이트
def upgrade():
    conn = op.get_bind()
    while True:
        result = conn.execute("""
            UPDATE users SET status = 'active'
            WHERE id IN (SELECT id FROM users WHERE status IS NULL LIMIT 10000)
            RETURNING id
        """)
        if result.rowcount == 0:
            break
```

---

## asyncpg (Async PostgreSQL)

### Connection Pool
```python
import asyncpg

pool = await asyncpg.create_pool(
    'postgresql://user:pass@localhost/db',
    min_size=5,
    max_size=20
)

async with pool.acquire() as conn:
    rows = await conn.fetch('SELECT * FROM users WHERE id = $1', user_id)
```

### Batch Operations
```python
# Batch insert
await conn.executemany(
    'INSERT INTO users (email, name) VALUES ($1, $2)',
    [('a@example.com', 'A'), ('b@example.com', 'B')]
)
```

---

## Quick Reference

| Task | SQLAlchemy |
|------|------------|
| Create | `session.add(obj)` |
| Read | `session.query(Model).filter_by(id=1).first()` |
| Update | `obj.field = value` |
| Delete | `session.delete(obj)` |
| Commit | `session.commit()` |
| Rollback | `session.rollback()` |
| Eager Load | `.options(joinedload(Model.relation))` |
| Raw SQL | `session.execute(text("SELECT..."))` |
