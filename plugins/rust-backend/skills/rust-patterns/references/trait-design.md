# Trait Design Patterns

## Small, Focused Traits

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

## Accept Generic Bounds, Not Concrete Types

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
```

## Define Traits at Consumer, Not Provider

```rust
// In the consumer crate — not the provider
pub trait UserStore: Send + Sync {
    fn get_user(&self, id: &str) -> Result<User, StoreError>;
    fn save_user(&self, user: &User) -> Result<(), StoreError>;
}

pub struct UserService<S: UserStore> {
    store: S,
}

// The concrete implementation lives in another crate.
// You write `impl UserStore for PostgresStore` in the
// consumer or an adapter crate.
```
