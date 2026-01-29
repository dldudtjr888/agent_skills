# Rust Database Cheatsheet

## Diesel

### Model Definition
```rust
use diesel::prelude::*;

#[derive(Queryable, Selectable)]
#[diesel(table_name = users)]
pub struct User {
    pub id: i64,
    pub email: String,
    pub name: Option<String>,
    pub is_active: bool,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Insertable)]
#[diesel(table_name = users)]
pub struct NewUser<'a> {
    pub email: &'a str,
    pub name: Option<&'a str>,
}
```

### Schema (schema.rs)
```rust
diesel::table! {
    users (id) {
        id -> Int8,
        email -> Text,
        name -> Nullable<Text>,
        is_active -> Bool,
        created_at -> Timestamptz,
    }
}
```

### CRUD Operations
```rust
use diesel::prelude::*;

// Create
diesel::insert_into(users::table)
    .values(&new_user)
    .get_result::<User>(&mut conn)?;

// Read
users::table
    .filter(users::id.eq(1))
    .first::<User>(&mut conn)?;

// Update
diesel::update(users::table.find(1))
    .set(users::is_active.eq(true))
    .execute(&mut conn)?;

// Delete
diesel::delete(users::table.find(1))
    .execute(&mut conn)?;
```

### Eager Loading
```rust
// Join
users::table
    .inner_join(orders::table)
    .select((User::as_select(), Order::as_select()))
    .load::<(User, Order)>(&mut conn)?;
```

---

## SQLx (Async)

### Connection Pool
```rust
use sqlx::postgres::PgPoolOptions;

let pool = PgPoolOptions::new()
    .max_connections(20)
    .connect("postgres://user:pass@localhost/db")
    .await?;
```

### Query Macros (Compile-time checked)
```rust
// Single row
let user = sqlx::query_as!(
    User,
    "SELECT id, email, name FROM users WHERE id = $1",
    user_id
)
.fetch_one(&pool)
.await?;

// Multiple rows
let users = sqlx::query_as!(
    User,
    "SELECT id, email, name FROM users WHERE is_active = $1",
    true
)
.fetch_all(&pool)
.await?;
```

### Dynamic Query
```rust
let mut query = sqlx::QueryBuilder::new("SELECT * FROM users WHERE 1=1");

if let Some(email) = email_filter {
    query.push(" AND email = ").push_bind(email);
}

let users = query.build_query_as::<User>()
    .fetch_all(&pool)
    .await?;
```

### Transactions
```rust
let mut tx = pool.begin().await?;

sqlx::query!("UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, from_id)
    .execute(&mut *tx)
    .await?;

sqlx::query!("UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, to_id)
    .execute(&mut *tx)
    .await?;

tx.commit().await?;
```

---

## SeaORM

### Entity Definition
```rust
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i64,
    pub email: String,
    pub name: Option<String>,
    pub is_active: bool,
    pub created_at: DateTimeWithTimeZone,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(has_many = "super::order::Entity")]
    Orders,
}
```

### CRUD Operations
```rust
// Create
let user = user::ActiveModel {
    email: Set("test@example.com".to_owned()),
    ..Default::default()
};
user.insert(&db).await?;

// Read
User::find_by_id(1).one(&db).await?;

// Update
let mut user: user::ActiveModel = user.into();
user.is_active = Set(true);
user.update(&db).await?;

// Delete
User::delete_by_id(1).exec(&db).await?;
```

### Eager Loading
```rust
User::find()
    .find_with_related(Order)
    .all(&db)
    .await?;
```

---

## Quick Reference

| Task | Diesel | SQLx | SeaORM |
|------|--------|------|--------|
| Pool | `r2d2` | `PgPoolOptions` | `Database::connect` |
| Query | `filter().first()` | `query_as!` | `find_by_id()` |
| Insert | `insert_into().values()` | `query!("INSERT...")` | `ActiveModel.insert()` |
| Update | `update().set()` | `query!("UPDATE...")` | `ActiveModel.update()` |
| Transaction | `conn.transaction()` | `pool.begin()` | `db.begin()` |
| Compile-time check | Schema | query macros | - |
| Async | ❌ | ✅ | ✅ |

## Migration Tools

```bash
# Diesel
diesel migration generate create_users
diesel migration run
diesel migration revert

# SQLx
sqlx migrate add create_users
sqlx migrate run

# SeaORM
sea-orm-cli migrate generate create_users
sea-orm-cli migrate up
```
