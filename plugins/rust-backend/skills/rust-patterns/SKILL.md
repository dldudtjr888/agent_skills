---
name: rust-patterns
description: Idiomatic Rust patterns, best practices, and conventions for building safe, performant, and maintainable Rust applications.
version: 1.0.0
category: language
user-invocable: true
triggers:
  keywords: [rust, cargo, crate, borrow, ownership, lifetime, tokio, axum, thiserror, anyhow, clippy]
  intentPatterns:
    - "(작성|생성|리뷰|리팩토링).*(rust|러스트)"
    - "(write|create|review|refactor).*(rust|crate)"
---

# Rust Development Patterns

Idiomatic Rust patterns and best practices for building safe, performant, and maintainable applications.

## When to Activate

- Writing new Rust code
- Reviewing Rust code
- Refactoring existing Rust code
- Designing Rust crates/modules

## Core Principles

### 1. Ownership and Borrowing

Rust's ownership system eliminates data races and memory bugs at compile time. Accept borrowed data when possible, return owned data when needed.

```rust
// Good: Accept borrowed data, return owned data
fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}

// Bad: Forcing caller to allocate unnecessarily
fn greet(name: String) -> String {
    format!("Hello, {name}!")
}
```

### 2. Make Invalid States Unrepresentable

Use Rust's type system to encode invariants so invalid states cause compile errors, not runtime bugs.

```rust
// Good: Compiler enforces valid states
enum ConnectionState {
    Disconnected,
    Connecting { attempt: u32 },
    Connected { session_id: String },
}

// Bad: Stringly-typed state allows invalid combinations
struct Connection {
    state: String,              // "connected", "disconnected", ...
    session_id: Option<String>, // Must be Some when connected, but nothing enforces this
}
```

### 3. Use the Type System, Not Runtime Checks

Leverage generics and trait bounds for compile-time guarantees instead of runtime validation.

```rust
// Good: Compile-time guarantee via trait bounds
fn serialize_all<T: serde::Serialize>(items: &[T]) -> serde_json::Result<String> {
    serde_json::to_string(items)
}

// Bad: Runtime type check with downcast
fn serialize_all(items: &[Box<dyn std::any::Any>]) -> Result<String, Box<dyn std::error::Error>> {
    // Must check types at runtime, no compile-time safety
    todo!()
}
```

## Error Handling Patterns

### thiserror for Libraries, anyhow for Applications

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

### Error Wrapping with Context

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

### Error Matching

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

### Never Use unwrap() Outside Tests

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
let data = serde_json::from_str(&input).unwrap();
```

## Ownership and Borrowing Patterns

### Prefer Slices and References in Parameters

```rust
// Good: Accept slices for maximum flexibility
fn sum(values: &[i32]) -> i32 {
    values.iter().sum()
}

fn contains_keyword(text: &str, keyword: &str) -> bool {
    text.contains(keyword)
}

// Bad: Require owned types unnecessarily
fn sum(values: Vec<i32>) -> i32 {
    values.iter().sum()
}

fn contains_keyword(text: String, keyword: String) -> bool {
    text.contains(&keyword)
}
```

### Avoid Unnecessary .clone()

```rust
// Good: Restructure to use references
fn process(data: &Data) -> Result<Output, Error> {
    let result = compute(&data.field)?;
    Ok(Output { result })
}

// Bad: Clone to satisfy the borrow checker — redesign instead
fn process(data: &Data) -> Result<Output, Error> {
    let owned = data.field.clone(); // Unnecessary heap allocation
    let result = compute(&owned)?;
    Ok(Output { result })
}
```

### Cow for Conditional Ownership

```rust
use std::borrow::Cow;

// Good: Zero-cost borrow when no modification needed, one allocation when needed
fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))
    } else {
        Cow::Borrowed(input) // No allocation
    }
}

// Usage: Deref handles both variants transparently
let result = normalize("hello world");
println!("{result}"); // Works for both Borrowed and Owned

// Bad: Always allocates even when the input is already valid
fn normalize(input: &str) -> String {
    if input.contains(' ') {
        input.replace(' ', "_")
    } else {
        input.to_owned() // Unnecessary heap allocation
    }
}
```

## Trait Design

### Small, Focused Traits

```rust
// Good: Single-purpose traits, composed when needed
pub trait Repository {
    type Error;
    fn find_by_id(&self, id: &str) -> Result<Option<Record>, Self::Error>;
    fn save(&self, record: &Record) -> Result<(), Self::Error>;
}

pub trait EventEmitter {
    fn emit(&self, event: Event);
}

// Bad: God trait with unrelated methods
pub trait Service {
    fn find_by_id(&self, id: &str) -> Option<Record>;
    fn save(&self, record: &Record);
    fn emit_event(&self, event: Event);
    fn log(&self, message: &str);
    fn health_check(&self) -> bool;
}
```

### Accept Generic Bounds, Not Concrete Types

```rust
// Good: Flexible input types via Into/AsRef
fn connect(addr: impl Into<String>) -> Connection {
    let addr = addr.into();
    Connection { addr }
}

fn read_file(path: impl AsRef<std::path::Path>) -> std::io::Result<String> {
    std::fs::read_to_string(path.as_ref())
}

// These all work:
// connect("localhost:8080");
// connect(String::from("localhost:8080"));
// read_file("/tmp/file.txt");
// read_file(PathBuf::from("/tmp/file.txt"));

// Bad: Only accepts one concrete type
fn connect(addr: String) -> Connection {
    Connection { addr }
}
```

### Define Traits at Consumer, Not Provider

```rust
// In the consumer crate — not the provider
// consumer/src/service.rs
pub trait UserStore: Send + Sync {
    fn get_user(&self, id: &str) -> Result<User, StoreError>;
    fn save_user(&self, user: &User) -> Result<(), StoreError>;
}

pub struct UserService<S: UserStore> {
    store: S,
}

// The concrete implementation lives in another crate.
// You write `impl UserStore for PostgresStore` in the
// consumer or an adapter crate — Rust requires explicit impl.
```

## Builder and Typestate Patterns

### Builder Pattern

Rust's equivalent of Go's functional options pattern.

```rust
pub struct ServerConfig {
    addr: String,
    timeout: std::time::Duration,
    max_connections: usize,
}

pub struct ServerConfigBuilder {
    addr: String,
    timeout: Option<std::time::Duration>,
    max_connections: Option<usize>,
}

impl ServerConfigBuilder {
    pub fn new(addr: impl Into<String>) -> Self {
        Self {
            addr: addr.into(),
            timeout: None,
            max_connections: None,
        }
    }

    pub fn timeout(mut self, timeout: std::time::Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }

    pub fn max_connections(mut self, max: usize) -> Self {
        self.max_connections = Some(max);
        self
    }

    pub fn build(self) -> ServerConfig {
        ServerConfig {
            addr: self.addr,
            timeout: self.timeout.unwrap_or(std::time::Duration::from_secs(30)),
            max_connections: self.max_connections.unwrap_or(100),
        }
    }
}

// Usage
let config = ServerConfigBuilder::new("0.0.0.0:8080")
    .timeout(std::time::Duration::from_secs(60))
    .max_connections(500)
    .build();
```

### Typestate Pattern for Compile-Time Validation

```rust
use std::marker::PhantomData;

struct Unconfigured;
struct Configured;

struct Pipeline<State = Unconfigured> {
    steps: Vec<String>,
    _state: PhantomData<State>,
}

impl Pipeline<Unconfigured> {
    fn new() -> Self {
        Self { steps: Vec::new(), _state: PhantomData }
    }

    fn add_step(mut self, step: impl Into<String>) -> Self {
        self.steps.push(step.into());
        self
    }

    fn configure(self) -> Pipeline<Configured> {
        Pipeline { steps: self.steps, _state: PhantomData }
    }
}

impl Pipeline<Configured> {
    fn run(&self) {
        for step in &self.steps {
            println!("Running: {step}");
        }
    }
}

// Usage — run() is only available after configure()
let pipeline = Pipeline::new()
    .add_step("lint")
    .add_step("test")
    .configure();
pipeline.run();
// Pipeline::new().run(); // Compile error!
```

## Concurrency Patterns

### Prefer Message Passing Over Shared State

```rust
use tokio::sync::{mpsc, oneshot};
use std::collections::HashMap;

// Good: Actor model with message passing
enum Message {
    Set { key: String, value: String },
    Get { key: String, reply: oneshot::Sender<Option<String>> },
}

struct Actor {
    receiver: mpsc::Receiver<Message>,
    state: HashMap<String, String>,
}

impl Actor {
    async fn run(mut self) {
        while let Some(msg) = self.receiver.recv().await {
            match msg {
                Message::Set { key, value } => {
                    self.state.insert(key, value);
                }
                Message::Get { key, reply } => {
                    let _ = reply.send(self.state.get(&key).cloned());
                }
            }
        }
    }
}

// Bad: Shared state with Mutex — potential contention and deadlocks
use std::sync::Arc;
use tokio::sync::Mutex;

let state = Arc::new(Mutex::new(HashMap::new()));
let state_clone = state.clone();
tokio::spawn(async move {
    let mut lock = state_clone.lock().await;
    lock.insert("key".into(), "value".into());
});
```

### Concurrent Tasks with JoinSet

```rust
use tokio::task::JoinSet;

// Good: JoinSet for coordinated concurrent tasks
async fn fetch_all(urls: Vec<String>) -> Vec<anyhow::Result<String>> {
    let mut set = JoinSet::new();

    for url in urls {
        set.spawn(async move {
            let resp = reqwest::get(&url).await?;
            Ok(resp.text().await?)
        });
    }

    let mut results = Vec::new();
    while let Some(result) = set.join_next().await {
        match result {
            Ok(value) => results.push(value),
            Err(join_err) => tracing::error!("task panicked: {join_err}"),
        }
    }
    results
}
```

### Cancellation Safety

```rust
use std::time::Duration;

// Good: Cancellation-safe with tokio::select!
async fn fetch_with_timeout(url: &str) -> anyhow::Result<String> {
    tokio::select! {
        result = reqwest::get(url) => {
            let resp = result?;
            Ok(resp.text().await?)
        }
        _ = tokio::time::sleep(Duration::from_secs(5)) => {
            Err(anyhow::anyhow!("request timed out"))
        }
    }
}
```

### Graceful Shutdown

```rust
async fn run_server(
    listener: tokio::net::TcpListener,
    app: axum::Router,
) -> anyhow::Result<()> {
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = tokio::signal::ctrl_c();

    #[cfg(unix)]
    let mut sigterm = tokio::signal::unix::signal(
        tokio::signal::unix::SignalKind::terminate(),
    )
    .expect("failed to install SIGTERM handler");

    #[cfg(unix)]
    tokio::select! {
        _ = ctrl_c => {}
        _ = sigterm.recv() => {}
    }

    #[cfg(not(unix))]
    ctrl_c.await.expect("failed to listen for Ctrl+C");

    tracing::info!("shutdown signal received");
}
```

## Project Structure

### Standard Project Layout

```text
my_project/
├── src/
│   ├── lib.rs              # Core logic (testable)
│   ├── main.rs             # Thin entry point
│   ├── error.rs            # Error types (thiserror)
│   ├── config.rs           # Configuration
│   ├── models/             # Domain models
│   ├── handlers/           # Request handlers
│   ├── services/           # Business logic
│   └── repository/         # Data access
├── tests/                  # Integration tests
├── benches/                # Benchmarks
├── examples/               # Example programs
├── Cargo.toml
└── Cargo.lock
```

Workspace layout for multi-crate projects:

```text
my_workspace/
├── Cargo.toml              # [workspace] members = ["crates/*"]
├── crates/
│   ├── domain/             # Shared types, no external deps
│   ├── core/               # Business logic
│   ├── api/                # HTTP layer (axum)
│   └── server/             # Binary entry point
└── tests/                  # Integration tests
```

### Module Visibility

```rust
// Good: Use pub(crate) for internal-only items
pub(crate) fn validate_input(input: &str) -> bool {
    !input.is_empty()
}

// Good: Keep lib.rs for logic, main.rs thin
// lib.rs
pub fn run(config: Config) -> anyhow::Result<()> { /* ... */ }

// main.rs
fn main() -> anyhow::Result<()> {
    let config = my_lib::Config::load()?;
    my_lib::run(config)
}

// Bad: Everything pub — exposes internal details
pub fn validate_input(input: &str) -> bool {
    !input.is_empty()
}
```

## Memory and Performance

### Preallocate Collections

```rust
// Best: Iterator chain — collect() uses size_hint() to preallocate automatically
fn process_items(items: &[Item]) -> Vec<Result> {
    items.iter().map(transform).collect()
}

// Good: Explicit preallocation when a loop is needed
fn process_items(items: &[Item]) -> Vec<Result> {
    let mut results = Vec::with_capacity(items.len());
    for item in items {
        results.push(transform(item));
    }
    results
}

// Bad: Multiple reallocations as Vec grows
fn process_items(items: &[Item]) -> Vec<Result> {
    let mut results = Vec::new();
    for item in items {
        results.push(transform(item));
    }
    results
}
```

### Use Iterators (Zero-Cost Abstraction)

Iterator chains compile to the same assembly as hand-written loops.

```rust
// Good: Iterator chain — zero overhead, expressive
fn sum_of_squares(values: &[i32]) -> i32 {
    values.iter()
        .filter(|&&v| v > 0)
        .map(|&v| v * v)
        .sum()
}

// Equivalent but less idiomatic
fn sum_of_squares(values: &[i32]) -> i32 {
    let mut total = 0;
    for &v in values {
        if v > 0 {
            total += v * v;
        }
    }
    total
}
```

### String Allocation Awareness

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
        if i > 0 {
            query.push_str(", ");
        }
        query.push_str(field);
    }
    query
}

// Bad: format!() in a loop — allocates a new String every iteration
fn build_query(fields: &[&str]) -> String {
    let mut query = String::from("SELECT ");
    for field in fields {
        query = format!("{query}{field}, "); // New allocation each time
    }
    query
}
```

## Naming and API Design

### Conversion Method Names

Follow Rust API Guidelines for method prefixes:

```rust
struct Token {
    raw: String,
    kind: TokenKind,
}

impl Token {
    // as_ prefix: cheap, borrowed view — returns a reference, no allocation
    fn as_str(&self) -> &str {
        &self.raw
    }

    // to_ prefix: expensive conversion (allocates or computes)
    fn to_uppercase(&self) -> String {
        self.raw.to_uppercase()
    }

    // into_ prefix: consumes self, zero-cost ownership transfer
    fn into_raw(self) -> String {
        self.raw
    }
}

// No get_ prefix for getters
impl User {
    // Good: bare noun
    fn name(&self) -> &str { &self.name }

    // Bad: redundant get_ prefix
    fn get_name(&self) -> &str { &self.name }
}
```

### Standard Traits and Newtype Pattern

```rust
// Good: Implement From, Display, Debug for interop
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(String);

impl std::fmt::Display for UserId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl From<String> for UserId {
    fn from(s: String) -> Self {
        Self(s)
    }
}

impl From<&str> for UserId {
    fn from(s: &str) -> Self {
        Self(s.to_owned())
    }
}

impl UserId {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// Newtype prevents mixing ID types at compile time
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct OrderId(u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct ProductId(u64);

fn get_order(id: OrderId) -> Order { /* ... */ }
// get_order(ProductId(1)); // Compile error!
```

## Rust Tooling Integration

### Essential Commands

```bash
# Build and run
cargo build
cargo run
cargo build --release

# Testing
cargo test
cargo test -- --nocapture
cargo test --workspace

# Linting and formatting
cargo clippy --all-targets --all-features -- -D warnings
cargo fmt --check

# Documentation
cargo doc --open

# Dependency management
cargo update
cargo audit
```

### Recommended Clippy Configuration

```toml
# Cargo.toml
[lints.clippy]
# Always fix: outright bugs
correctness = { level = "deny" }
# Review carefully: easy performance wins
perf = { level = "warn" }
# Simplify: overly complex code
complexity = { level = "warn" }
# Readability: idiomatic style
style = { level = "warn" }

# Selectively enable pedantic lints
needless_pass_by_value = { level = "warn" }
cloned_instead_of_copied = { level = "warn" }
explicit_iter_loop = { level = "warn" }
implicit_clone = { level = "warn" }
```

## Quick Reference: Rust Idioms

| Idiom | Description |
|-------|-------------|
| Accept `&str`, return `String` | Borrow for input, own for output |
| Use `?` for error propagation | Never use `.unwrap()` in production code |
| Prefer message passing | Use channels over `Arc<Mutex<T>>` when possible |
| Make invalid states unrepresentable | Encode invariants in the type system |
| Use iterators over manual loops | Zero-cost abstractions, more readable |
| `thiserror` for libs, `anyhow` for apps | Structured errors in libraries, flexible in binaries |
| `pub(crate)` for internal APIs | Do not expose more than necessary |
| Implement `From`, `Display`, `Debug` | Standard traits enable ecosystem interop |
| `clippy` is your co-pilot | Run with `-D warnings` in CI |
| Prefer `Cow<str>` for optional ownership | Avoid allocations when borrowing suffices |

## Anti-Patterns to Avoid

```rust
// Bad: unwrap() in production code
let config = load_config().unwrap();

// Bad: Unnecessary .clone() to satisfy borrow checker
let name = user.name.clone(); // Redesign ownership instead

// Bad: String in function parameters when &str suffices
fn greet(name: String) { /* ... */ }

// Bad: Box<dyn Error> instead of proper error types
fn parse(input: &str) -> Result<Data, Box<dyn std::error::Error>> { /* ... */ }

// Bad: Arc<Mutex<T>> when message passing would work
let shared = Arc::new(Mutex::new(Vec::new()));

// Bad: Over-complicated lifetime annotations
fn process<'a, 'b: 'a>(x: &'a str, y: &'b str) -> &'a str { x }
// Often means the design needs rethinking

// Bad: Mixing async runtimes or blocking in async context
fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async { /* ... */ }); // Use #[tokio::main] instead
}
```

**Remember**: Rust's compiler is your strongest ally. If the code compiles, entire categories of bugs — data races, use-after-free, null dereferences — are eliminated. When fighting the borrow checker, redesign your data flow instead of adding clones and lifetimes.
