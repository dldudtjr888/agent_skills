---
name: rust-workspace-patterns
description: "Rust 워크스페이스 패턴. 모듈 구조, 가시성, 멀티크레이트 프로젝트."
version: 1.0.0
category: patterns
user-invocable: true
triggers:
  keywords:
    - workspace
    - 워크스페이스
    - module
    - 모듈
    - crate
    - visibility
  intentPatterns:
    - "(구조|설계).*(워크스페이스|모듈)"
    - "(멀티|multi).*(크레이트|crate)"
---

# Rust Workspace Patterns

Rust 워크스페이스와 모듈 구조 패턴.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Dependency Management | [modules/dependency-management.md](modules/dependency-management.md) | workspace deps, 버전 통합, feature flags |
| 2 | Cross-Crate Patterns | [modules/cross-crate-patterns.md](modules/cross-crate-patterns.md) | 공유 타입, 트레이트 추상화, 레이어 분리 |

## 워크스페이스 구조

```toml
# Cargo.toml (root)
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
```

```
my_workspace/
├── Cargo.toml
├── crates/
│   ├── domain/         # 공유 타입
│   ├── core/           # 비즈니스 로직
│   ├── api/            # HTTP 레이어
│   └── server/         # 바이너리
└── tests/
```

## 모듈 가시성

```rust
// 공개: 모든 곳에서 접근
pub fn public_fn() {}

// 크레이트 내부: 같은 크레이트에서만
pub(crate) fn crate_fn() {}

// 부모 모듈: 부모에서만
pub(super) fn super_fn() {}

// 비공개: 현재 모듈만
fn private_fn() {}
```

## 모듈 구조

```rust
// lib.rs
pub mod models;
pub mod services;
mod internal;  // 비공개

// models/mod.rs
pub mod user;
pub mod product;

pub use user::User;  // 재내보내기
pub use product::Product;
```

## 의존성 공유

```toml
# crates/api/Cargo.toml
[dependencies]
domain = { path = "../domain" }
tokio = { workspace = true }
```

## 체크리스트

- [ ] workspace.members 정의
- [ ] 공유 의존성 workspace.dependencies
- [ ] pub(crate) 적절히 사용
- [ ] 재내보내기로 API 정리
