---
name: rust-crate-builder
description: 새 Rust 크레이트 생성. Cargo.toml 설정, 프로젝트 구조, CI 설정.
model: opus
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Rust Crate Builder

새로운 Rust 크레이트를 생성하고 설정합니다.

**참조 스킬**: `rust-workspace-patterns`, `rust-crate-ecosystem`

## 프로젝트 생성

```bash
# 라이브러리
cargo new my-crate --lib

# 바이너리
cargo new my-app

# 워크스페이스 멤버
cargo new crates/my-crate --lib
```

## Cargo.toml 템플릿

```toml
[package]
name = "my-crate"
version = "0.1.0"
edition = "2021"
rust-version = "1.75"
description = "A useful crate"
license = "MIT"
repository = "https://github.com/user/my-crate"

[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
thiserror = "1"
tracing = "0.1"

[dev-dependencies]
tokio-test = "0.4"

[lints.clippy]
correctness = { level = "deny" }
perf = { level = "warn" }
style = { level = "warn" }
```

## 프로젝트 구조

```
my-crate/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── error.rs
│   └── models/
├── tests/
├── examples/
└── benches/
```

## CI 설정 (.github/workflows/ci.yml)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo fmt --check
      - run: cargo clippy -- -D warnings
      - run: cargo test
```
