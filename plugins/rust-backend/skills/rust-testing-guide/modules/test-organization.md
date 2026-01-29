# Test Organization

테스트 코드 구성 및 구조화 패턴.

## 테스트 유형별 구조

```
my-project/
├── src/
│   ├── lib.rs           # 단위 테스트 포함
│   ├── models/
│   │   └── user.rs      # 모델별 단위 테스트
│   └── services/
│       └── user.rs      # 서비스별 단위 테스트
├── tests/               # 통합 테스트
│   ├── common/
│   │   └── mod.rs
│   └── api_tests.rs
├── benches/             # 벤치마크
│   └── performance.rs
└── examples/            # 사용 예제 (테스트 겸용)
    └── basic_usage.rs
```

## 모듈 내 테스트 구성

```rust
// src/services/user.rs

pub struct UserService { /* ... */ }

impl UserService {
    pub fn create(&self, user: NewUser) -> Result<User, Error> {
        // ...
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // 헬퍼 함수
    fn create_test_service() -> UserService {
        UserService::new(MockRepo::new())
    }

    // 그룹: 생성 테스트
    mod create {
        use super::*;

        #[test]
        fn success_with_valid_input() {
            let service = create_test_service();
            let result = service.create(valid_user());
            assert!(result.is_ok());
        }

        #[test]
        fn fails_with_duplicate_email() {
            let service = create_test_service();
            service.create(valid_user()).unwrap();
            let result = service.create(valid_user());
            assert!(matches!(result, Err(Error::DuplicateEmail)));
        }
    }

    // 그룹: 조회 테스트
    mod find {
        use super::*;

        #[test]
        fn returns_none_for_nonexistent() {
            let service = create_test_service();
            let result = service.find_by_id(999);
            assert!(result.is_none());
        }
    }
}
```

## 테스트 네이밍 컨벤션

```rust
// 1. should 패턴
#[test]
fn should_return_error_when_input_is_invalid() { }

// 2. given_when_then 패턴
#[test]
fn given_valid_user_when_create_then_returns_user() { }

// 3. 동작 설명 패턴
#[test]
fn create_returns_user_with_id() { }

// 4. 실패 케이스 명시
#[test]
fn create_fails_with_empty_name() { }

#[test]
#[should_panic(expected = "overflow")]
fn add_panics_on_overflow() { }
```

## 테스트 헬퍼 모듈

```rust
// tests/common/mod.rs (또는 src/test_utils.rs)

#[cfg(test)]
pub mod test_utils {
    use crate::models::*;

    // Builders
    pub struct UserBuilder {
        id: Option<i64>,
        name: String,
        email: String,
    }

    impl UserBuilder {
        pub fn new() -> Self {
            Self {
                id: None,
                name: "Test User".into(),
                email: "test@example.com".into(),
            }
        }

        pub fn with_id(mut self, id: i64) -> Self {
            self.id = Some(id);
            self
        }

        pub fn with_name(mut self, name: &str) -> Self {
            self.name = name.into();
            self
        }

        pub fn build(self) -> User {
            User {
                id: self.id.unwrap_or(1),
                name: self.name,
                email: self.email,
                created_at: chrono::Utc::now(),
            }
        }
    }

    // Assertions
    pub fn assert_user_eq(actual: &User, expected: &User) {
        assert_eq!(actual.name, expected.name);
        assert_eq!(actual.email, expected.email);
    }
}
```

## 테스트 Attributes

```rust
// 기본
#[test]
fn basic_test() { }

// 비동기
#[tokio::test]
async fn async_test() { }

// 무시 (CI에서 제외)
#[test]
#[ignore]
fn slow_test() { }

// 조건부 실행
#[test]
#[cfg(feature = "expensive-tests")]
fn expensive_test() { }

// 패닉 예상
#[test]
#[should_panic(expected = "out of bounds")]
fn panics_on_invalid_index() { }

// 타임아웃 (tokio)
#[tokio::test(flavor = "multi_thread")]
#[timeout(Duration::from_secs(5))]
async fn test_with_timeout() { }

// 직렬 실행
#[test]
#[serial_test::serial]
fn test_needs_isolation() { }
```

## Feature Flag로 테스트 분리

```toml
# Cargo.toml
[features]
default = []
expensive-tests = []
integration-tests = []
```

```rust
#[cfg(all(test, feature = "expensive-tests"))]
mod expensive_tests {
    #[test]
    fn very_slow_test() {
        // 오래 걸리는 테스트
    }
}
```

```bash
# 기본 테스트만
cargo test

# expensive 테스트 포함
cargo test --features expensive-tests
```

## 테스트 실행 패턴

```bash
# 모든 테스트
cargo test

# 특정 테스트
cargo test test_name

# 특정 모듈
cargo test services::user

# 특정 파일
cargo test --test api_tests

# 무시된 테스트 포함
cargo test -- --ignored

# 출력 표시
cargo test -- --nocapture

# 병렬 제한
cargo test -- --test-threads=1

# 첫 실패에서 중단
cargo test -- --fail-fast
```

## 문서 테스트

```rust
/// 두 숫자를 더합니다.
///
/// # Examples
///
/// ```
/// let result = my_crate::add(2, 2);
/// assert_eq!(result, 4);
/// ```
///
/// # Panics
///
/// 오버플로 시 패닉합니다.
///
/// ```should_panic
/// my_crate::add(u32::MAX, 1);
/// ```
pub fn add(a: u32, b: u32) -> u32 {
    a.checked_add(b).expect("overflow")
}
```

## 체크리스트

- [ ] 테스트 유형별 디렉토리 구조
- [ ] 일관된 네이밍 컨벤션
- [ ] 공유 헬퍼/fixtures 분리
- [ ] 적절한 테스트 attributes 사용
- [ ] Feature flag로 무거운 테스트 분리
- [ ] 문서 테스트 작성
