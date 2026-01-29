# Query Optimization

쿼리 빌더 패턴 및 성능 최적화.

## SQLx 쿼리 패턴

### 타입 안전 쿼리

```rust
// query_as!로 컴파일 타임 검증
let users = sqlx::query_as!(
    User,
    r#"
    SELECT id, name, email, created_at
    FROM users
    WHERE status = $1
    ORDER BY created_at DESC
    LIMIT $2
    "#,
    "active",
    10i64
)
.fetch_all(&pool)
.await?;
```

### 동적 쿼리 빌더

```rust
use sqlx::QueryBuilder;

pub async fn search_users(
    pool: &PgPool,
    filters: &UserFilters,
) -> Result<Vec<User>, sqlx::Error> {
    let mut builder = QueryBuilder::new(
        "SELECT id, name, email FROM users WHERE 1=1"
    );

    if let Some(name) = &filters.name {
        builder.push(" AND name ILIKE ");
        builder.push_bind(format!("%{}%", name));
    }

    if let Some(status) = &filters.status {
        builder.push(" AND status = ");
        builder.push_bind(status);
    }

    if let Some(created_after) = &filters.created_after {
        builder.push(" AND created_at > ");
        builder.push_bind(created_after);
    }

    builder.push(" ORDER BY created_at DESC");

    if let Some(limit) = filters.limit {
        builder.push(" LIMIT ");
        builder.push_bind(limit as i64);
    }

    builder
        .build_query_as::<User>()
        .fetch_all(pool)
        .await
}
```

### 벌크 INSERT

```rust
pub async fn bulk_insert_users(
    pool: &PgPool,
    users: &[NewUser],
) -> Result<(), sqlx::Error> {
    let mut builder = QueryBuilder::new(
        "INSERT INTO users (name, email, status) "
    );

    builder.push_values(users.iter(), |mut b, user| {
        b.push_bind(&user.name)
         .push_bind(&user.email)
         .push_bind(&user.status);
    });

    builder.push(" ON CONFLICT (email) DO NOTHING");

    builder.build().execute(pool).await?;
    Ok(())
}
```

## Diesel 쿼리 패턴

### 타입 안전 쿼리

```rust
use diesel::prelude::*;

pub fn get_active_users(conn: &mut PgConnection) -> QueryResult<Vec<User>> {
    users::table
        .filter(users::status.eq("active"))
        .order(users::created_at.desc())
        .limit(10)
        .load::<User>(conn)
}
```

### 동적 필터링

```rust
pub fn search_users(
    conn: &mut PgConnection,
    filters: &UserFilters,
) -> QueryResult<Vec<User>> {
    let mut query = users::table.into_boxed();

    if let Some(name) = &filters.name {
        query = query.filter(users::name.ilike(format!("%{}%", name)));
    }

    if let Some(status) = &filters.status {
        query = query.filter(users::status.eq(status));
    }

    if let Some(created_after) = &filters.created_after {
        query = query.filter(users::created_at.gt(created_after));
    }

    query
        .order(users::created_at.desc())
        .limit(filters.limit.unwrap_or(100) as i64)
        .load(conn)
}
```

### JOIN 최적화

```rust
// N+1 방지: eager loading
pub fn get_users_with_posts(
    conn: &mut PgConnection,
) -> QueryResult<Vec<(User, Vec<Post>)>> {
    let users_list = users::table.load::<User>(conn)?;

    let posts_list = Post::belonging_to(&users_list)
        .load::<Post>(conn)?
        .grouped_by(&users_list);

    Ok(users_list.into_iter().zip(posts_list).collect())
}

// 또는 명시적 JOIN
pub fn get_users_with_latest_post(
    conn: &mut PgConnection,
) -> QueryResult<Vec<(User, Option<Post>)>> {
    users::table
        .left_join(posts::table)
        .select((users::all_columns, posts::all_columns.nullable()))
        .load(conn)
}
```

## SeaORM 쿼리 패턴

```rust
use sea_orm::*;

pub async fn search_users(
    db: &DatabaseConnection,
    filters: &UserFilters,
) -> Result<Vec<user::Model>, DbErr> {
    let mut query = User::find();

    if let Some(name) = &filters.name {
        query = query.filter(user::Column::Name.contains(name));
    }

    if let Some(status) = &filters.status {
        query = query.filter(user::Column::Status.eq(status));
    }

    query
        .order_by_desc(user::Column::CreatedAt)
        .limit(filters.limit.unwrap_or(100))
        .all(db)
        .await
}
```

## 인덱스 활용

### 쿼리 플랜 확인

```rust
// SQLx
let plan: String = sqlx::query_scalar(
    "EXPLAIN ANALYZE SELECT * FROM users WHERE email = $1"
)
.bind("test@example.com")
.fetch_one(&pool)
.await?;

println!("{}", plan);
```

### 인덱스 힌트 (PostgreSQL)

```sql
-- 생성
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX idx_users_status_created ON users(status, created_at DESC);

-- 복합 인덱스 활용
SELECT * FROM users
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 10;
```

## 페이지네이션

### Offset 기반 (단순하지만 느림)

```rust
pub async fn get_users_page(
    pool: &PgPool,
    page: i64,
    per_page: i64,
) -> Result<Vec<User>, sqlx::Error> {
    sqlx::query_as!(
        User,
        "SELECT * FROM users ORDER BY id LIMIT $1 OFFSET $2",
        per_page,
        (page - 1) * per_page
    )
    .fetch_all(pool)
    .await
}
```

### Cursor 기반 (권장)

```rust
pub async fn get_users_after(
    pool: &PgPool,
    cursor: Option<i64>,
    limit: i64,
) -> Result<(Vec<User>, Option<i64>), sqlx::Error> {
    let users = match cursor {
        Some(cursor_id) => {
            sqlx::query_as!(
                User,
                "SELECT * FROM users WHERE id > $1 ORDER BY id LIMIT $2",
                cursor_id,
                limit + 1  // 다음 페이지 확인용
            )
            .fetch_all(pool)
            .await?
        }
        None => {
            sqlx::query_as!(
                User,
                "SELECT * FROM users ORDER BY id LIMIT $1",
                limit + 1
            )
            .fetch_all(pool)
            .await?
        }
    };

    let has_more = users.len() > limit as usize;
    let users: Vec<User> = users.into_iter().take(limit as usize).collect();
    let next_cursor = if has_more {
        users.last().map(|u| u.id)
    } else {
        None
    };

    Ok((users, next_cursor))
}
```

## 체크리스트

- [ ] query_as! 또는 타입 안전 빌더 사용
- [ ] 동적 쿼리에 boxed() 또는 QueryBuilder 사용
- [ ] N+1 쿼리 방지 (eager loading)
- [ ] 적절한 인덱스 생성
- [ ] EXPLAIN ANALYZE로 쿼리 플랜 확인
- [ ] Cursor 기반 페이지네이션 사용
- [ ] 벌크 작업에 batch insert 사용
