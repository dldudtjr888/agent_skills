# Memory and Performance Patterns

## Prefer Iterator Chains

Iterator chains compile to the same assembly as hand-written loops and auto-preallocate via `size_hint()`.

```rust
// Best: Iterator chain
fn process_items(items: &[Item]) -> Vec<Result> {
    items.iter().map(transform).collect()
}

// Good: Explicit preallocation when a loop is needed
let mut results = Vec::with_capacity(items.len());
```

## String Allocation Awareness

```rust
// Good: &str when no ownership needed
fn log_message(level: &str, msg: &str) {
    println!("[{level}] {msg}");
}

// Good: String::with_capacity for known-size building
fn build_query(fields: &[&str]) -> String {
    let mut query = String::with_capacity(fields.len() * 20);
    query.push_str("SELECT ");
    for (i, field) in fields.iter().enumerate() {
        if i > 0 { query.push_str(", "); }
        query.push_str(field);
    }
    query
}
```

## Naming Conventions

| Prefix | Meaning | Example |
|--------|---------|---------|
| `as_` | Cheap borrowed view | `fn as_str(&self) -> &str` |
| `to_` | Expensive conversion | `fn to_uppercase(&self) -> String` |
| `into_` | Consumes self | `fn into_raw(self) -> String` |
| (bare noun) | Getter, no `get_` prefix | `fn name(&self) -> &str` |

## Standard Traits

For interop, always implement: `From`, `Display`, `Debug` on public types.
