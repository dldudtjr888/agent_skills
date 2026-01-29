# Mocking Patterns

mockall을 사용한 Rust 모킹 패턴.

## mockall 기본 사용

```rust
use mockall::{automock, predicate::*};

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: i64) -> Option<User>;
    fn create(&self, user: &NewUser) -> Result<User, DbError>;
    fn delete(&self, id: i64) -> Result<(), DbError>;
}

#[test]
fn test_with_mock() {
    let mut mock = MockUserRepository::new();

    // 기대 설정
    mock.expect_find_by_id()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(User { id: 1, name: "Test".into() }));

    // 테스트
    let result = mock.find_by_id(1);
    assert!(result.is_some());
}
```

## 비동기 트레이트 모킹

```rust
use async_trait::async_trait;
use mockall::automock;

#[automock]
#[async_trait]
trait AsyncRepository {
    async fn find(&self, id: i64) -> Option<User>;
    async fn save(&self, user: &User) -> Result<(), Error>;
}

#[tokio::test]
async fn test_async_mock() {
    let mut mock = MockAsyncRepository::new();

    mock.expect_find()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(User::default()));

    let result = mock.find(1).await;
    assert!(result.is_some());
}
```

## Expectation 패턴

### 호출 횟수

```rust
// 정확히 N번
mock.expect_method()
    .times(3)
    .returning(|_| ());

// 최소 N번
mock.expect_method()
    .times(1..)
    .returning(|_| ());

// 최대 N번
mock.expect_method()
    .times(..=5)
    .returning(|_| ());

// 범위
mock.expect_method()
    .times(2..=4)
    .returning(|_| ());
```

### 인자 매칭

```rust
use mockall::predicate::*;

// 정확한 값
mock.expect_find_by_id()
    .with(eq(42))
    .returning(|_| None);

// 함수 조건
mock.expect_find_by_name()
    .with(function(|name: &str| name.starts_with("test")))
    .returning(|_| None);

// 항상 매치
mock.expect_process()
    .with(always())
    .returning(|_| Ok(()));

// 여러 인자
mock.expect_create()
    .with(eq("name"), gt(0))
    .returning(|_, _| Ok(1));
```

### 순차 반환

```rust
// 순서대로 다른 값 반환
let mut mock = MockCounter::new();
mock.expect_next()
    .times(3)
    .returning(|| 1)
    .returning(|| 2)
    .returning(|| 3);

assert_eq!(mock.next(), 1);
assert_eq!(mock.next(), 2);
assert_eq!(mock.next(), 3);
```

## 제네릭 트레이트

```rust
#[automock]
trait Repository<T> {
    fn find(&self, id: i64) -> Option<T>;
    fn save(&self, item: &T) -> Result<(), Error>;
}

#[test]
fn test_generic_mock() {
    let mut mock = MockRepository::<User>::new();

    mock.expect_find()
        .returning(|_| Some(User::default()));

    let result = mock.find(1);
    assert!(result.is_some());
}
```

## Struct 메서드 모킹

```rust
mockall::mock! {
    pub HttpClient {
        pub fn get(&self, url: &str) -> Result<Response, Error>;
        pub fn post(&self, url: &str, body: &[u8]) -> Result<Response, Error>;
    }
}

#[test]
fn test_http_client() {
    let mut mock = MockHttpClient::new();

    mock.expect_get()
        .with(eq("https://api.example.com/users"))
        .returning(|_| Ok(Response::new(200, b"[]".to_vec())));

    let result = mock.get("https://api.example.com/users");
    assert!(result.is_ok());
}
```

## Context (Static 메서드)

```rust
mockall::mock! {
    pub Config {
        pub fn load() -> Result<Config, Error>;
        pub fn get_env(key: &str) -> Option<String>;
    }
}

#[test]
fn test_static_method() {
    let ctx = MockConfig::load_context();
    ctx.expect()
        .returning(|| Ok(Config::default()));

    let config = MockConfig::load();
    assert!(config.is_ok());
}
```

## 의존성 주입 패턴

```rust
// 트레이트 기반 DI
pub struct UserService<R: UserRepository> {
    repo: R,
}

impl<R: UserRepository> UserService<R> {
    pub fn new(repo: R) -> Self {
        Self { repo }
    }

    pub fn get_user(&self, id: i64) -> Option<User> {
        self.repo.find_by_id(id)
    }
}

#[test]
fn test_user_service() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo.expect_find_by_id()
        .returning(|_| Some(User::default()));

    let service = UserService::new(mock_repo);
    assert!(service.get_user(1).is_some());
}
```

## Spy 패턴 (호출 기록)

```rust
use std::sync::{Arc, Mutex};

struct SpyRepository {
    calls: Arc<Mutex<Vec<String>>>,
    inner: Box<dyn UserRepository>,
}

impl UserRepository for SpyRepository {
    fn find_by_id(&self, id: i64) -> Option<User> {
        self.calls.lock().unwrap().push(format!("find_by_id({})", id));
        self.inner.find_by_id(id)
    }
}

#[test]
fn test_with_spy() {
    let calls = Arc::new(Mutex::new(Vec::new()));
    let spy = SpyRepository {
        calls: calls.clone(),
        inner: Box::new(RealRepository::new()),
    };

    spy.find_by_id(1);
    spy.find_by_id(2);

    let recorded = calls.lock().unwrap();
    assert_eq!(recorded.len(), 2);
    assert!(recorded[0].contains("find_by_id(1)"));
}
```

## 체크리스트

- [ ] 테스트 대상과 mock 경계 정의
- [ ] `#[automock]` 또는 `mock!` 사용
- [ ] 적절한 expectation 설정
- [ ] 호출 횟수 검증
- [ ] 인자 매칭 패턴 활용
- [ ] 비동기 트레이트 처리
- [ ] 의존성 주입으로 테스트 용이성 확보
