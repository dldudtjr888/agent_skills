# Rust Caching Cheatsheet

## redis-rs

```rust
use redis::{Client, Commands, AsyncCommands};

// Sync
let client = Client::open("redis://127.0.0.1/")?;
let mut con = client.get_connection()?;

con.set_ex::<_, _, ()>("key", "value", 300)?;  // TTL 5분
let value: Option<String> = con.get("key")?;
con.del::<_, ()>("key")?;

// Async
let client = Client::open("redis://127.0.0.1/")?;
let mut con = client.get_async_connection().await?;

con.set_ex::<_, _, ()>("key", "value", 300).await?;
let value: Option<String> = con.get("key").await?;
```

## Cache-Aside Pattern

```rust
use redis::{Client, AsyncCommands};
use serde::{Serialize, Deserialize};

async fn get_cached_or_fetch<T, F, Fut>(
    redis: &mut redis::aio::Connection,
    key: &str,
    ttl: usize,
    fetch: F,
) -> Result<T, Error>
where
    T: Serialize + for<'de> Deserialize<'de>,
    F: FnOnce() -> Fut,
    Fut: Future<Output = Result<T, Error>>,
{
    // Check cache
    if let Some(cached) = redis.get::<_, Option<String>>(key).await? {
        return Ok(serde_json::from_str(&cached)?);
    }

    // Fetch from source
    let data = fetch().await?;

    // Store in cache
    let json = serde_json::to_string(&data)?;
    redis.set_ex::<_, _, ()>(key, json, ttl).await?;

    Ok(data)
}
```

## moka (In-Memory)

```rust
use moka::sync::Cache;
use std::time::Duration;

let cache: Cache<String, User> = Cache::builder()
    .max_capacity(1000)
    .time_to_live(Duration::from_secs(300))
    .build();

// Insert
cache.insert("user:123".to_string(), user);

// Get
if let Some(user) = cache.get(&"user:123".to_string()) {
    // Use cached user
}

// Remove
cache.invalidate(&"user:123".to_string());
```

## cached crate

```rust
use cached::proc_macro::cached;

#[cached(time = 300, key = "i64", convert = r#"{ user_id }"#)]
async fn get_user(user_id: i64) -> Option<User> {
    db::get_user(user_id).await
}

// With Redis
use cached::stores::RedisCache;

#[cached(
    ty = "RedisCache<i64, User>",
    create = r#"{ RedisCache::new("redis://127.0.0.1", 300) }"#,
    convert = r#"{ user_id }"#
)]
async fn get_user_redis(user_id: i64) -> Option<User> {
    db::get_user(user_id).await
}
```

## Axum with Cache

```rust
use axum::{extract::State, Json};
use redis::aio::ConnectionManager;

async fn get_user(
    State(redis): State<ConnectionManager>,
    Path(user_id): Path<i64>,
) -> Json<User> {
    let mut redis = redis.clone();

    let user = get_cached_or_fetch(
        &mut redis,
        &format!("user:{}", user_id),
        300,
        || async { db::get_user(user_id).await }
    ).await.unwrap();

    Json(user)
}
```
