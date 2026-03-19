---
name: rust-patterns
description: >-
  Idiomatic Rust patterns and best practices. MUST use for ANY Rust code task.
  Covers: thiserror(#[error]/#[from]) for libs, anyhow::Context for bins, ownership(&str/Cow/Arc),
  trait design(impl Into<T>, trait objects vs generics), builder/typestate(PhantomData),
  tokio JoinSet/select!/actor model, project structure(lib.rs+main.rs, pub(crate)),
  performance(Iterator chains, Vec::with_capacity, SmallVec, Cow<str>),
  Swatinem/rust-cache CI 캐싱, musl static 빌드(cross/cargo-zigbuild),
  clippy::pedantic + rustfmt 설정, cargo-deny/audit 보안 검사.
  MUST TRIGGER for: .rs 파일 편집, Cargo.toml 수정, borrow checker 에러 수정, lifetime 문제 해결,
  trait 설계, derive 매크로 선택, cargo workspace 구성, CI/CD 파이프라인 Rust 빌드 최적화.
  러스트 코드 작성/리뷰/리팩토링/디버깅, borrow 에러, lifetime 문제, 크레이트 구조, CI 캐시 설정,
  musl 정적 빌드, clippy 린트 설정 시 반드시 활성화. Rust 관련 작업이면 무조건 사용할 것.
version: 1.3.0
category: language
user-invocable: true
triggers:
  keywords: [rust, cargo, crate, borrow, ownership, lifetime, tokio, axum, thiserror, anyhow, clippy, rustc, rustup]
  intentPatterns:
    - "(작성|생성|리뷰|리팩토링).*(rust|러스트)"
    - "(write|create|review|refactor).*(rust|crate)"
  file_patterns: ["*.rs", "Cargo.toml", "Cargo.lock"]
metadata:
  author: youngseoklee
  version: "1.2.0"
  date: "March 2026"
  filePattern:
    - "*.rs"
    - "Cargo.toml"
    - "Cargo.lock"
    - "clippy.toml"
    - ".cargo/config.toml"
  bashPattern:
    - "cargo"
    - "rustc"
    - "rustup"
    - "clippy"
---

# Rust Development Patterns

## 1. Decision Flow

```
어떤 종류의 코드인가?
├── Error handling → references/error-handling.md
│   ├── 라이브러리 크레이트 → thiserror (matchable errors)
│   └── 어플리케이션 바이너리 → anyhow + .context() 필수
├── Ownership 이슈 → references/ownership-borrowing.md
│   ├── 함수 파라미터 → &str, &[T] 슬라이스 우선
│   ├── 불필요한 .clone() → into_iter() + iterator chain
│   └── 조건부 소유권 → Cow<str>
├── Trait 설계 → references/trait-design.md
│   ├── 인터페이스 → 소비자 측에서 정의, 최소 메서드
│   └── 유연한 입력 → impl Into<T>, impl AsRef<T>
├── Builder / 상태 머신 → references/builder-typestate.md
├── 비동기/동시성 → references/concurrency.md
│   ├── 공유 상태 → Actor model (mpsc) 우선
│   └── 병렬 작업 → JoinSet + select!
└── 성능 → references/performance.md
```

## 2. Core Rules

These are the patterns that matter most — baseline Claude often misses them:

**Error handling is the #1 differentiator.** Libraries MUST use `thiserror` with structured, matchable error enums. Applications MUST use `anyhow` with `.context()` on every fallible call. This is not optional — it's the difference between professional and amateur Rust code.

```rust
// Library: thiserror — callers can match on variants
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("not found: {id}")]
    NotFound { id: String },
    #[error("connection failed")]
    Connection(#[from] sqlx::Error),
}

// Application: anyhow + context on EVERY ? call
let config = load_config().context("failed to load config")?;
```

**Zero unwrap() outside tests — no exceptions.** Before writing any `.unwrap()`, ask: "Is this inside `#[cfg(test)]`?" If no, use `?` with `.context()` instead. This applies to `.expect()` too — prefer `?` + context. Grep your output for `.unwrap()` and verify every occurrence is in a test block.

```rust
// Production code: ALWAYS use ? + context
let addr: SocketAddr = bind_addr.parse().context("invalid bind address")?;

// Test code: unwrap() is fine
#[cfg(test)]
mod tests {
    fn test_parse() { let r = parse("ok").unwrap(); }
}
```

**Accept borrowed, return owned.** Function parameters should be `&str`, `&[T]`, `&Path` — not `String`, `Vec<T>`, `PathBuf`.

**Default to `pub(crate)`, not `pub`.** Internal struct fields, helper functions, and module-private types should use `pub(crate)`. Only make things `pub` if they're part of the external API. This controls your crate's API surface and prevents accidental exposure.

```rust
// Good: internal state is pub(crate)
pub struct AppState {
    pub(crate) pool: PgPool,
    pub(crate) config: AppConfig,
}

// Bad: everything is pub — leaks internal details
pub struct AppState {
    pub pool: PgPool,
    pub config: AppConfig,
}
```

## 3. Reference Guide

| Topic | File | When to Read |
|-------|------|-------------|
| Error handling | `references/error-handling.md` | thiserror vs anyhow, Context, error matching |
| Ownership | `references/ownership-borrowing.md` | 슬라이스, clone 제거, Cow 패턴 |
| Trait design | `references/trait-design.md` | 트레이트 설계, 제네릭 바운드 |
| Builder & typestate | `references/builder-typestate.md` | 빌더 패턴, PhantomData 상태 전이 |
| Concurrency | `references/concurrency.md` | Actor, JoinSet, select! |
| Performance | `references/performance.md` | 이터레이터, 메모리, API 네이밍 |

## 4. Project Structure

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
└── Cargo.toml
```

- Keep `main.rs` thin — all logic in `lib.rs` and modules
- Use `pub(crate)` for internal APIs

## 5. Tooling

```toml
# Cargo.toml
[lints.clippy]
correctness = { level = "deny" }
perf = { level = "warn" }
complexity = { level = "warn" }
style = { level = "warn" }
```

```bash
cargo clippy --all-targets -- -D warnings
cargo fmt --check
cargo test --workspace
```

## 6. Verification Checklist

- [ ] Error types use `thiserror` (lib) or `anyhow` (bin)
- [ ] Every `?` in application code has `.context()`
- [ ] **Grep for `.unwrap()` — every occurrence must be inside `#[cfg(test)]`**
- [ ] Internal fields/helpers use `pub(crate)`, not `pub`
- [ ] Function params use `&str`/`&[T]` not `String`/`Vec<T>`
- [ ] `lib.rs` contains logic, `main.rs` is thin
- [ ] `cargo clippy -- -D warnings` passes
