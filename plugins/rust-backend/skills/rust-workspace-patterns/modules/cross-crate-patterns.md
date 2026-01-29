# Cross-Crate Patterns

크레이트 간 코드 공유 및 구조화 패턴.

## 공유 타입 크레이트

```
workspace/
├── crates/
│   ├── types/        # 공유 타입
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── models.rs
│   │       └── errors.rs
│   ├── core/         # 비즈니스 로직
│   ├── api/          # HTTP API
│   └── cli/          # CLI 도구
```

```rust
// crates/types/src/lib.rs
pub mod models;
pub mod errors;

pub use models::*;
pub use errors::*;
```

```rust
// crates/types/src/models.rs
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub name: String,
    pub email: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateUserRequest {
    pub name: String,
    pub email: String,
}
```

## 트레이트 기반 추상화

```rust
// crates/types/src/traits.rs
use async_trait::async_trait;

#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: i64) -> Result<Option<User>, Error>;
    async fn create(&self, req: &CreateUserRequest) -> Result<User, Error>;
    async fn delete(&self, id: i64) -> Result<(), Error>;
}

// crates/db/src/lib.rs
use my_types::UserRepository;

pub struct PgUserRepository { /* ... */ }

#[async_trait]
impl UserRepository for PgUserRepository {
    // 구현
}

// crates/api/src/handlers.rs
use my_types::UserRepository;

pub async fn get_user<R: UserRepository>(
    repo: &R,
    id: i64,
) -> Result<User, Error> {
    repo.find_by_id(id).await?.ok_or(Error::NotFound)
}
```

## 레이어 분리

```
crates/
├── domain/           # 도메인 모델, 비즈니스 규칙
├── application/      # 유스케이스, 서비스
├── infrastructure/   # DB, 외부 서비스
└── interfaces/       # API, CLI
```

```rust
// 의존성 방향: interfaces -> application -> domain
//                           infrastructure -> domain

// crates/domain/src/lib.rs
// 외부 의존성 최소화, 순수 Rust 타입
pub struct User { /* ... */ }
pub trait UserRepository { /* ... */ }

// crates/application/src/lib.rs
// domain만 의존
use domain::{User, UserRepository};

pub struct UserService<R: UserRepository> {
    repo: R,
}

// crates/infrastructure/src/lib.rs
// domain만 의존, 구현 제공
use domain::UserRepository;
use sqlx::PgPool;

pub struct PgUserRepository { pool: PgPool }
impl UserRepository for PgUserRepository { /* ... */ }
```

## Feature 기반 조건부 코드

```rust
// crates/core/src/lib.rs

#[cfg(feature = "postgres")]
pub mod postgres;

#[cfg(feature = "sqlite")]
pub mod sqlite;

// 공통 트레이트
pub trait Database {
    fn connect(&self) -> Result<(), Error>;
}

// 조건부 re-export
#[cfg(feature = "postgres")]
pub use postgres::PostgresDb as DefaultDb;

#[cfg(all(feature = "sqlite", not(feature = "postgres")))]
pub use sqlite::SqliteDb as DefaultDb;
```

## 테스트 유틸리티 공유

```rust
// crates/test-utils/src/lib.rs
use my_types::{User, CreateUserRequest};

pub mod fixtures {
    use super::*;

    pub fn user() -> User {
        User {
            id: 1,
            name: "Test User".into(),
            email: "test@example.com".into(),
        }
    }

    pub fn create_user_request() -> CreateUserRequest {
        CreateUserRequest {
            name: "New User".into(),
            email: "new@example.com".into(),
        }
    }
}

pub mod mocks {
    use super::*;
    use mockall::mock;

    mock! {
        pub UserRepo {}

        #[async_trait::async_trait]
        impl my_types::UserRepository for UserRepo {
            async fn find_by_id(&self, id: i64) -> Result<Option<User>, Error>;
            async fn create(&self, req: &CreateUserRequest) -> Result<User, Error>;
        }
    }
}
```

```toml
# 테스트 전용 의존성으로 추가
[dev-dependencies]
my-test-utils = { path = "../test-utils" }
```

## 매크로 크레이트

```rust
// crates/macros/src/lib.rs
use proc_macro::TokenStream;

#[proc_macro_derive(MyDerive)]
pub fn my_derive(input: TokenStream) -> TokenStream {
    // 매크로 구현
}

// 사용
// crates/core/Cargo.toml
[dependencies]
my-macros = { path = "../macros" }

// crates/core/src/lib.rs
use my_macros::MyDerive;

#[derive(MyDerive)]
pub struct MyStruct { /* ... */ }
```

## Prelude 패턴

```rust
// crates/core/src/prelude.rs
pub use crate::error::{Error, Result};
pub use crate::models::{User, Post};
pub use crate::traits::{Repository, Service};

// 사용하는 크레이트에서
use my_core::prelude::*;
```

## 순환 의존성 해결

```
# 문제: A -> B -> A

# 해결: 공통 타입을 C로 추출
C (types)
├── A -> C
└── B -> C
```

```bash
# 순환 확인
cargo tree
```

## 체크리스트

- [ ] 공유 타입 크레이트 분리
- [ ] 트레이트로 추상화
- [ ] 의존성 방향 단방향 유지
- [ ] Feature 기반 조건부 컴파일
- [ ] 테스트 유틸리티 공유
- [ ] Prelude 모듈 제공
- [ ] 순환 의존성 확인
