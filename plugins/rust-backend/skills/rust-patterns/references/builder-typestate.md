# Builder and Typestate Patterns

## Builder Pattern

Use `impl Into<String>` for flexible string inputs in builder methods.

```rust
pub struct ServerConfigBuilder {
    addr: String,
    timeout: Option<std::time::Duration>,
    max_connections: Option<usize>,
}

impl ServerConfigBuilder {
    pub fn new(addr: impl Into<String>) -> Self {
        Self { addr: addr.into(), timeout: None, max_connections: None }
    }

    pub fn timeout(mut self, timeout: std::time::Duration) -> Self {
        self.timeout = Some(timeout);
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
```

## Typestate Pattern

Use `PhantomData<State>` markers to enforce state transitions at compile time.

```rust
use std::marker::PhantomData;

struct Unconfigured;
struct Configured;

struct Pipeline<State = Unconfigured> {
    steps: Vec<String>,
    _state: PhantomData<State>,
}

impl Pipeline<Unconfigured> {
    fn configure(self) -> Pipeline<Configured> {
        Pipeline { steps: self.steps, _state: PhantomData }
    }
}

impl Pipeline<Configured> {
    fn run(&self) { /* only available after configure() */ }
}
```
