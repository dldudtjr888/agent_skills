# Rust Testing Guide

cargo test 기반 Rust 테스트 상세 가이드.

## 기본 설정

### Cargo.toml

```toml
[package]
name = "my_project"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }

[dev-dependencies]
# 테스트 유틸리티
mockall = "0.12"              # 모킹
proptest = "1.4"              # Property-based testing
test-case = "3"               # Parametrized tests
rstest = "0.18"               # Fixture 기반 테스트
wiremock = "0.5"              # HTTP 모킹
fake = { version = "2", features = ["derive"] }  # 테스트 데이터 생성

# Async 테스트
tokio-test = "0.4"

# 벤치마크
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "benchmarks"
harness = false
```

## Unit Tests

### 기본 구조

```rust
// src/lib.rs
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn divide(a: i32, b: i32) -> Result<i32, String> {
    if b == 0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        // Arrange
        let a = 2;
        let b = 3;

        // Act
        let result = add(a, b);

        // Assert
        assert_eq!(result, 5);
    }

    #[test]
    fn test_divide_success() {
        let result = divide(10, 2).unwrap();
        assert_eq!(result, 5);
    }

    #[test]
    fn test_divide_by_zero() {
        let result = divide(10, 0);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Division by zero");
    }

    #[test]
    #[should_panic(expected = "panic message")]
    fn test_panic() {
        panic!("panic message");
    }

    #[test]
    #[ignore]  // cargo test -- --ignored 로 실행
    fn expensive_test() {
        // 느린 테스트
    }
}
```

### 모듈별 테스트 파일

```rust
// src/user.rs
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

impl User {
    pub fn new(name: &str, email: &str) -> Self {
        Self {
            id: 0,
            name: name.to_string(),
            email: email.to_string(),
        }
    }

    pub fn is_valid_email(&self) -> bool {
        self.email.contains('@') && self.email.contains('.')
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_user_creation() {
        let user = User::new("John", "john@example.com");

        assert_eq!(user.name, "John");
        assert_eq!(user.email, "john@example.com");
    }

    #[test]
    fn test_valid_email() {
        let user = User::new("John", "john@example.com");
        assert!(user.is_valid_email());
    }

    #[test]
    fn test_invalid_email() {
        let user = User::new("John", "invalid-email");
        assert!(!user.is_valid_email());
    }
}
```

## Integration Tests

```
my_project/
├── src/
│   ├── lib.rs
│   └── user.rs
├── tests/              # 통합 테스트 디렉토리
│   ├── common/         # 공유 유틸리티
│   │   └── mod.rs
│   ├── user_tests.rs
│   └── api_tests.rs
└── Cargo.toml
```

```rust
// tests/common/mod.rs
pub fn setup() -> TestContext {
    // 테스트 설정
    TestContext::new()
}

pub struct TestContext {
    pub db: MockDatabase,
}

impl TestContext {
    pub fn new() -> Self {
        Self {
            db: MockDatabase::new(),
        }
    }
}
```

```rust
// tests/user_tests.rs
use my_project::user::User;

mod common;

#[test]
fn test_user_workflow() {
    let ctx = common::setup();

    let user = User::new("Test", "test@example.com");

    // 통합 테스트 로직
    assert!(user.is_valid_email());
}
```

## Mockall 패턴

### Trait 모킹

```rust
use mockall::{automock, predicate::*};

#[automock]
pub trait UserRepository {
    fn find_by_id(&self, id: u64) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), String>;
    fn delete(&self, id: u64) -> Result<(), String>;
}

pub struct UserService<R: UserRepository> {
    repository: R,
}

impl<R: UserRepository> UserService<R> {
    pub fn new(repository: R) -> Self {
        Self { repository }
    }

    pub fn get_user(&self, id: u64) -> Option<User> {
        self.repository.find_by_id(id)
    }

    pub fn create_user(&self, name: &str, email: &str) -> Result<User, String> {
        let user = User::new(name, email);
        self.repository.save(&user)?;
        Ok(user)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_user() {
        // Arrange
        let mut mock_repo = MockUserRepository::new();

        mock_repo
            .expect_find_by_id()
            .with(eq(1))
            .times(1)
            .returning(|_| Some(User::new("John", "john@example.com")));

        let service = UserService::new(mock_repo);

        // Act
        let user = service.get_user(1);

        // Assert
        assert!(user.is_some());
        assert_eq!(user.unwrap().name, "John");
    }

    #[test]
    fn test_create_user() {
        let mut mock_repo = MockUserRepository::new();

        mock_repo
            .expect_save()
            .times(1)
            .returning(|_| Ok(()));

        let service = UserService::new(mock_repo);
        let result = service.create_user("Jane", "jane@example.com");

        assert!(result.is_ok());
    }

    #[test]
    fn test_save_failure() {
        let mut mock_repo = MockUserRepository::new();

        mock_repo
            .expect_save()
            .times(1)
            .returning(|_| Err("Database error".to_string()));

        let service = UserService::new(mock_repo);
        let result = service.create_user("Jane", "jane@example.com");

        assert!(result.is_err());
    }
}
```

### 호출 순서 검증

```rust
#[test]
fn test_call_sequence() {
    let mut mock = MockUserRepository::new();
    let mut seq = mockall::Sequence::new();

    mock.expect_find_by_id()
        .times(1)
        .in_sequence(&mut seq)
        .returning(|_| None);

    mock.expect_save()
        .times(1)
        .in_sequence(&mut seq)
        .returning(|_| Ok(()));

    // find_by_id가 먼저, 그 다음 save가 호출되어야 함
}
```

## Async Tests

### Tokio 테스트

```rust
use tokio;

#[tokio::test]
async fn test_async_function() {
    let result = async_fetch_data().await;
    assert!(result.is_ok());
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn test_with_multiple_threads() {
    // 멀티 스레드 환경에서 테스트
}

#[tokio::test]
async fn test_with_timeout() {
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(5),
        async_operation()
    ).await;

    assert!(result.is_ok());
}
```

### Async Mock

```rust
use mockall::automock;
use async_trait::async_trait;

#[async_trait]
#[automock]
pub trait AsyncUserRepository {
    async fn find_by_id(&self, id: u64) -> Option<User>;
    async fn save(&self, user: &User) -> Result<(), String>;
}

#[tokio::test]
async fn test_async_service() {
    let mut mock_repo = MockAsyncUserRepository::new();

    mock_repo
        .expect_find_by_id()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(User::new("Async User", "async@example.com")));

    let service = AsyncUserService::new(mock_repo);
    let user = service.get_user(1).await;

    assert!(user.is_some());
}
```

## HTTP 모킹 (Wiremock)

```rust
use wiremock::{MockServer, Mock, ResponseTemplate};
use wiremock::matchers::{method, path, body_json};

#[tokio::test]
async fn test_api_client() {
    // Mock 서버 시작
    let mock_server = MockServer::start().await;

    // Mock 응답 설정
    Mock::given(method("GET"))
        .and(path("/users/1"))
        .respond_with(ResponseTemplate::new(200)
            .set_body_json(serde_json::json!({
                "id": 1,
                "name": "Test User"
            })))
        .mount(&mock_server)
        .await;

    // API 클라이언트 테스트
    let client = ApiClient::new(&mock_server.uri());
    let user = client.get_user(1).await.unwrap();

    assert_eq!(user.name, "Test User");
}

#[tokio::test]
async fn test_post_request() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/users"))
        .and(body_json(serde_json::json!({
            "name": "New User",
            "email": "new@example.com"
        })))
        .respond_with(ResponseTemplate::new(201)
            .set_body_json(serde_json::json!({
                "id": 2,
                "name": "New User"
            })))
        .mount(&mock_server)
        .await;

    let client = ApiClient::new(&mock_server.uri());
    let result = client.create_user("New User", "new@example.com").await;

    assert!(result.is_ok());
}
```

## Parametrized Tests

### test-case

```rust
use test_case::test_case;

#[test_case(2, 3, 5 ; "positive numbers")]
#[test_case(0, 0, 0 ; "zeros")]
#[test_case(-1, 1, 0 ; "negative and positive")]
#[test_case(-5, -3, -8 ; "negative numbers")]
fn test_add(a: i32, b: i32, expected: i32) {
    assert_eq!(add(a, b), expected);
}

#[test_case("hello", "HELLO")]
#[test_case("world", "WORLD")]
#[test_case("Rust", "RUST")]
fn test_uppercase(input: &str, expected: &str) {
    assert_eq!(input.to_uppercase(), expected);
}
```

### rstest

```rust
use rstest::rstest;

#[rstest]
#[case(2, 3, 5)]
#[case(0, 0, 0)]
#[case(-1, 1, 0)]
fn test_add(#[case] a: i32, #[case] b: i32, #[case] expected: i32) {
    assert_eq!(add(a, b), expected);
}

// Fixture 사용
#[rstest]
fn test_with_fixture(#[values("user1", "user2", "user3")] name: &str) {
    let user = User::new(name, &format!("{}@example.com", name));
    assert!(user.is_valid_email());
}
```

### rstest Fixtures

```rust
use rstest::{rstest, fixture};

#[fixture]
fn user() -> User {
    User::new("Test User", "test@example.com")
}

#[fixture]
fn admin_user() -> User {
    let mut user = User::new("Admin", "admin@example.com");
    user.role = Role::Admin;
    user
}

#[rstest]
fn test_user_email(user: User) {
    assert!(user.is_valid_email());
}

#[rstest]
fn test_admin_permissions(admin_user: User) {
    assert!(admin_user.can_delete_users());
}
```

## Property-Based Testing (Proptest)

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_add_commutative(a: i32, b: i32) {
        prop_assert_eq!(add(a, b), add(b, a));
    }

    #[test]
    fn test_add_associative(a: i32, b: i32, c: i32) {
        prop_assert_eq!(add(add(a, b), c), add(a, add(b, c)));
    }

    #[test]
    fn test_string_reverse_reverse(s: String) {
        let reversed: String = s.chars().rev().collect();
        let double_reversed: String = reversed.chars().rev().collect();
        prop_assert_eq!(s, double_reversed);
    }
}
```

### 커스텀 전략

```rust
use proptest::prelude::*;

fn valid_email_strategy() -> impl Strategy<Value = String> {
    "[a-z]{1,10}@[a-z]{1,10}\\.[a-z]{2,4}".prop_map(|s| s)
}

fn user_strategy() -> impl Strategy<Value = User> {
    (any::<String>(), valid_email_strategy())
        .prop_map(|(name, email)| User::new(&name, &email))
}

proptest! {
    #[test]
    fn test_user_email_always_valid(user in user_strategy()) {
        prop_assert!(user.is_valid_email());
    }
}
```

## Benchmarking (Criterion)

```rust
// benches/benchmarks.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use my_project::{add, complex_algorithm};

fn benchmark_add(c: &mut Criterion) {
    c.bench_function("add", |b| {
        b.iter(|| add(black_box(2), black_box(3)))
    });
}

fn benchmark_complex_algorithm(c: &mut Criterion) {
    let data = vec![1, 2, 3, 4, 5];

    c.bench_function("complex_algorithm", |b| {
        b.iter(|| complex_algorithm(black_box(&data)))
    });
}

fn benchmark_with_different_inputs(c: &mut Criterion) {
    let mut group = c.benchmark_group("sorting");

    for size in [100, 1000, 10000].iter() {
        let data: Vec<i32> = (0..*size).collect();

        group.bench_with_input(
            format!("size_{}", size),
            &data,
            |b, data| b.iter(|| sort(black_box(data.clone())))
        );
    }

    group.finish();
}

criterion_group!(benches, benchmark_add, benchmark_complex_algorithm, benchmark_with_different_inputs);
criterion_main!(benches);
```

```bash
# 벤치마크 실행
cargo bench

# 특정 벤치마크만 실행
cargo bench -- add

# HTML 리포트 확인
open target/criterion/report/index.html
```

## 테스트 커버리지

```bash
# cargo-llvm-cov 설치
cargo install cargo-llvm-cov

# 커버리지 측정
cargo llvm-cov

# HTML 리포트 생성
cargo llvm-cov --html
open target/llvm-cov/html/index.html

# 임계값 강제
cargo llvm-cov --fail-under-lines 80
```

## 디버깅

```bash
# 기본 테스트 실행
cargo test

# 상세 출력
cargo test -- --nocapture

# 특정 테스트만 실행
cargo test test_name

# 무시된 테스트 실행
cargo test -- --ignored

# 모든 테스트 (무시된 테스트 포함)
cargo test -- --include-ignored

# 병렬 실행 제한
cargo test -- --test-threads=1

# 특정 통합 테스트 파일
cargo test --test user_tests

# 문서 테스트만
cargo test --doc

# 릴리스 모드로 테스트
cargo test --release
```

## 테스트 구조 권장

```
my_project/
├── src/
│   ├── lib.rs
│   ├── user.rs           # 각 모듈에 #[cfg(test)] mod tests
│   ├── service.rs
│   └── repository.rs
├── tests/                # 통합 테스트
│   ├── common/
│   │   └── mod.rs        # 테스트 유틸리티
│   ├── user_tests.rs
│   └── api_tests.rs
├── benches/              # 벤치마크
│   └── benchmarks.rs
└── Cargo.toml
```
