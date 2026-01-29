# Rust (cargo test) Cheatsheet

## cargo test 기본 명령어

```bash
# 전체 테스트
cargo test

# 상세 출력 (print! 보기)
cargo test -- --nocapture

# 특정 테스트
cargo test test_name

# 특정 모듈
cargo test module_name::

# 무시된 테스트 실행
cargo test -- --ignored

# 단일 스레드로 실행
cargo test -- --test-threads=1

# 통합 테스트만
cargo test --test integration_tests

# 릴리스 모드
cargo test --release
```

## 커버리지

```bash
# cargo-llvm-cov 설치
cargo install cargo-llvm-cov

# 커버리지 측정
cargo llvm-cov

# HTML 리포트
cargo llvm-cov --html

# 최소 커버리지 강제
cargo llvm-cov --fail-under-lines 80
```

## 기본 테스트 구조

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        // Arrange
        let input = 5;

        // Act
        let result = double(input);

        // Assert
        assert_eq!(result, 10);
    }

    #[test]
    #[should_panic(expected = "error")]
    fn test_panic() {
        panic!("error message");
    }

    #[test]
    #[ignore]
    fn slow_test() {
        // cargo test -- --ignored
    }
}
```

## Assertions

```rust
// 동등성
assert_eq!(a, b);           // a == b
assert_ne!(a, b);           // a != b

// Boolean
assert!(condition);         // true 확인
assert!(!condition);        // false 확인

// Result
assert!(result.is_ok());
assert!(result.is_err());

// Option
assert!(option.is_some());
assert!(option.is_none());

// 메시지 포함
assert_eq!(a, b, "Expected {} but got {}", b, a);
```

## Result 반환 테스트

```rust
#[test]
fn test_with_result() -> Result<(), String> {
    let result = divide(10, 2)?;
    assert_eq!(result, 5);
    Ok(())
}
```

## Async 테스트

```rust
#[tokio::test]
async fn test_async() {
    let result = async_function().await;
    assert!(result.is_ok());
}

#[tokio::test(flavor = "multi_thread")]
async fn test_multi_thread() {
    // 멀티 스레드 환경
}
```

## Mock (mockall)

```rust
use mockall::{automock, predicate::*};

#[automock]
trait Repository {
    fn find(&self, id: u64) -> Option<Item>;
}

#[test]
fn test_with_mock() {
    let mut mock = MockRepository::new();

    mock.expect_find()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(Item::new()));

    let result = mock.find(1);
    assert!(result.is_some());
}
```

## Parametrized (test-case)

```rust
use test_case::test_case;

#[test_case(2, 3, 5 ; "positive")]
#[test_case(0, 0, 0 ; "zeros")]
#[test_case(-1, 1, 0 ; "mixed")]
fn test_add(a: i32, b: i32, expected: i32) {
    assert_eq!(add(a, b), expected);
}
```

## Fixtures (rstest)

```rust
use rstest::{rstest, fixture};

#[fixture]
fn user() -> User {
    User::new("test", "test@example.com")
}

#[rstest]
fn test_with_fixture(user: User) {
    assert!(user.is_valid());
}

#[rstest]
#[case(1, 2)]
#[case(3, 4)]
fn test_parametrized(#[case] a: i32, #[case] b: i32) {
    assert!(a < b);
}
```

## Property-Based (proptest)

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_commutative(a: i32, b: i32) {
        prop_assert_eq!(add(a, b), add(b, a));
    }
}
```

## 통합 테스트

```rust
// tests/integration_test.rs
use my_crate::public_function;

#[test]
fn test_integration() {
    let result = public_function();
    assert!(result.is_ok());
}

// 공유 유틸리티: tests/common/mod.rs
mod common;

#[test]
fn test_with_common() {
    let ctx = common::setup();
    // ...
}
```

## 벤치마크 (criterion)

```rust
// benches/bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark(c: &mut Criterion) {
    c.bench_function("my_function", |b| {
        b.iter(|| my_function(black_box(100)))
    });
}

criterion_group!(benches, benchmark);
criterion_main!(benches);
```

```bash
cargo bench
```

## 테스트 구조

```
my_project/
├── src/
│   ├── lib.rs          # #[cfg(test)] mod tests
│   └── user.rs
├── tests/              # 통합 테스트
│   ├── common/
│   │   └── mod.rs
│   └── user_tests.rs
├── benches/            # 벤치마크
│   └── bench.rs
└── Cargo.toml
```

## 유용한 dev-dependencies

```toml
[dev-dependencies]
mockall = "0.12"        # 모킹
proptest = "1.4"        # Property-based
test-case = "3"         # Parametrized
rstest = "0.18"         # Fixtures
wiremock = "0.5"        # HTTP 모킹
fake = "2"              # 테스트 데이터
tokio-test = "0.4"      # Async 유틸
criterion = "0.5"       # 벤치마크
```
