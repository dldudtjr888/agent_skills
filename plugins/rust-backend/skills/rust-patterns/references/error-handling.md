# Error Handling Patterns

## thiserror for Libraries, anyhow for Applications

Libraries expose precise, matchable error types. Applications use flexible error handling.

```rust
// Library crate: precise error types with thiserror
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("record not found: {id}")]
    NotFound { id: String },
    #[error("connection failed")]
    Connection(#[from] sqlx::Error),
    #[error("serialization failed")]
    Serialization(#[from] serde_json::Error),
}

// Application crate: flexible error handling with anyhow
use anyhow::Context;

fn main() -> anyhow::Result<()> {
    let config = load_config().context("failed to load config")?;
    run_server(config).context("server failed")?;
    Ok(())
}
```

## Error Wrapping with Context

```rust
use anyhow::Context;

// Good: Add context at each call site
fn load_user(path: &std::path::Path) -> anyhow::Result<User> {
    let data = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;
    let user: User = serde_json::from_str(&data)
        .context("failed to parse user JSON")?;
    Ok(user)
}

// Bad: Raw error propagation without context
fn load_user(path: &std::path::Path) -> Result<User, Box<dyn std::error::Error>> {
    let data = std::fs::read_to_string(path)?; // Which file failed?
    let user: User = serde_json::from_str(&data)?; // What was the input?
    Ok(user)
}
```

## Error Matching

```rust
fn handle_error(err: &StorageError) {
    match err {
        StorageError::NotFound { id } => {
            tracing::warn!("record {id} not found, returning 404");
        }
        StorageError::Connection(source) => {
            tracing::error!("database connection error: {source}");
        }
        StorageError::Serialization(source) => {
            tracing::error!("serialization error: {source}");
        }
    }
}
```

## Never Use unwrap() Outside Tests

```rust
// Good: Propagate with ? in application code
let config = load_config()?;

// Good: Use expect() with reason for known-safe unwraps
let port: u16 = env::var("PORT")
    .expect("PORT env var must be set")
    .parse()
    .expect("PORT must be a valid u16");

// Good: unwrap() is fine in tests
#[cfg(test)]
mod tests {
    #[test]
    fn test_parse() {
        let result = parse_input("valid").unwrap();
        assert_eq!(result, expected);
    }
}

// Bad: Panic in production code
let config = load_config().unwrap();
```
