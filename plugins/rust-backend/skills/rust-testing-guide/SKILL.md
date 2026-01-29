---
name: rust-testing-guide
description: "Rust 테스트 가이드. cargo test, mockall, proptest, criterion 벤치마크."
version: 1.0.0
category: testing
user-invocable: true
triggers:
  keywords:
    - test
    - 테스트
    - mock
    - benchmark
    - 벤치마크
    - proptest
    - criterion
  intentPatterns:
    - "(작성|만들).*(테스트|test)"
    - "(rust|러스트).*(테스트|벤치마크)"
---

# Rust Testing Guide

Rust 테스트 작성 가이드.

## 관련 참조

- **common-dev-workflow/tdd-fundamentals**: TDD 방법론 및 테스트 전략

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Integration Testing | [modules/integration-testing.md](modules/integration-testing.md) | 통합 테스트 구조, fixtures, API/DB 테스트 |
| 2 | Test Organization | [modules/test-organization.md](modules/test-organization.md) | 모듈별 테스트 구조, 네이밍, 헬퍼 |
| 3 | Mocking Patterns | [modules/mocking-patterns.md](modules/mocking-patterns.md) | mockall 심화, 트레이트 모킹, DI |

## 단위 테스트

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn test_overflow() {
        add(u32::MAX, 1);
    }
}
```

## 비동기 테스트

```rust
#[tokio::test]
async fn test_async_function() {
    let result = async_operation().await;
    assert!(result.is_ok());
}
```

## Mocking (mockall)

```rust
use mockall::{automock, predicate::*};

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: i64) -> Option<User>;
}

#[test]
fn test_with_mock() {
    let mut mock = MockUserRepository::new();
    mock.expect_find_by_id()
        .with(eq(1))
        .returning(|_| Some(User { id: 1, name: "Test".into() }));

    let service = UserService::new(mock);
    let user = service.get_user(1);
    assert!(user.is_some());
}
```

## Property Testing (proptest)

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_parse_roundtrip(s in "[a-z]+") {
        let parsed = parse(&s)?;
        let back = parsed.to_string();
        prop_assert_eq!(s, back);
    }
}
```

## Benchmarks (criterion)

```rust
use criterion::{criterion_group, criterion_main, Criterion};

fn benchmark_sort(c: &mut Criterion) {
    let mut data = vec![5, 4, 3, 2, 1];
    c.bench_function("sort", |b| {
        b.iter(|| {
            data.sort();
        })
    });
}

criterion_group!(benches, benchmark_sort);
criterion_main!(benches);
```

## Commands

```bash
cargo test                    # 모든 테스트
cargo test test_name          # 특정 테스트
cargo test -- --nocapture     # 출력 표시
cargo bench                   # 벤치마크
```
