# Dependency Management

워크스페이스 의존성 관리 패턴.

## 워크스페이스 구조

```toml
# 루트 Cargo.toml
[workspace]
resolver = "2"
members = [
    "crates/core",
    "crates/api",
    "crates/db",
    "crates/cli",
]

# 워크스페이스 공통 의존성
[workspace.dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
tracing = "0.1"
thiserror = "1"
anyhow = "1"

# 내부 크레이트
my-core = { path = "crates/core" }
my-db = { path = "crates/db" }
```

## 멤버 크레이트 설정

```toml
# crates/api/Cargo.toml
[package]
name = "my-api"
version.workspace = true
edition.workspace = true

[dependencies]
# 워크스페이스 의존성 상속
tokio.workspace = true
serde.workspace = true
tracing.workspace = true

# 내부 의존성
my-core.workspace = true
my-db.workspace = true

# 크레이트 전용 의존성
axum = "0.7"
```

## 버전 통합 관리

```toml
# 루트 Cargo.toml
[workspace.package]
version = "0.1.0"
edition = "2021"
rust-version = "1.75"
license = "MIT"
repository = "https://github.com/org/project"
authors = ["Your Name <you@example.com>"]

# 멤버에서 상속
[package]
name = "my-crate"
version.workspace = true
edition.workspace = true
license.workspace = true
```

## Feature 플래그 관리

```toml
# 워크스페이스 레벨 feature
[workspace.dependencies]
sqlx = { version = "0.7", default-features = false }

# 멤버별 feature 선택
# crates/db/Cargo.toml
[dependencies]
sqlx = { workspace = true, features = ["runtime-tokio", "postgres"] }

# crates/api/Cargo.toml
[dependencies]
sqlx = { workspace = true, features = ["runtime-tokio", "postgres", "json"] }
```

## 조건부 의존성

```toml
# crates/core/Cargo.toml
[features]
default = []
full = ["feature-a", "feature-b"]
feature-a = ["dep:optional-crate-a"]
feature-b = ["dep:optional-crate-b"]

[dependencies]
optional-crate-a = { version = "1", optional = true }
optional-crate-b = { version = "1", optional = true }
```

## Dev Dependencies 공유

```toml
# 루트 Cargo.toml
[workspace.dependencies]
tokio-test = "0.4"
mockall = "0.11"
proptest = "1"
criterion = "0.5"

# 멤버에서 사용
[dev-dependencies]
tokio-test.workspace = true
mockall.workspace = true
```

## 의존성 감사

```bash
# 취약점 검사
cargo audit

# 미사용 의존성
cargo +nightly udeps

# 의존성 트리
cargo tree

# 특정 크레이트 찾기
cargo tree -i serde

# 중복 버전 찾기
cargo tree -d
```

## Lockfile 관리

```bash
# lockfile 업데이트
cargo update

# 특정 크레이트만
cargo update -p serde

# 최소 버전으로 잠금
cargo update -Z minimal-versions
```

## 버전 범위 전략

```toml
[dependencies]
# 정확한 버전 (라이브러리 비권장)
serde = "=1.0.193"

# 호환 버전 (권장)
serde = "1.0"  # ^1.0.0과 동일

# 틸드 (패치만 허용)
serde = "~1.0.193"

# 와일드카드 (비권장)
serde = "1.*"
```

## 체크리스트

- [ ] 워크스페이스 resolver = "2" 설정
- [ ] 공통 의존성 workspace.dependencies로 통합
- [ ] 버전 정보 워크스페이스 레벨로
- [ ] Feature 플래그 정리
- [ ] cargo audit 정기 실행
- [ ] cargo tree -d로 중복 확인
