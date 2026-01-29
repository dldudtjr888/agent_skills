---
name: rust-error-handling
description: "Rust 에러 처리 심화. thiserror, anyhow, 커스텀 에러, 에러 전파 패턴."
version: 1.0.0
category: patterns
user-invocable: true
triggers:
  keywords:
    - error
    - 에러
    - thiserror
    - anyhow
    - result
    - option
  intentPatterns:
    - "(처리|다루).*(에러|error)"
    - "(thiserror|anyhow).*(사용|패턴)"
---

# Rust Error Handling

Rust 에러 처리 패턴.

## 관련 참조

- **common-backend/observability**: 에러 로깅, 메트릭스, 분산 트레이싱 연동

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Error Recovery | [modules/error-recovery.md](modules/error-recovery.md) | 재시도, fallback, circuit breaker 패턴 |
| 2 | Context Propagation | [modules/context-propagation.md](modules/context-propagation.md) | anyhow context, 스택 트레이스, 에러 체인 |
| 3 | Production Patterns | [modules/production-patterns.md](modules/production-patterns.md) | 로깅 연동, 메트릭스, 에러 리포팅 |

## thiserror (라이브러리용)

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum StorageError {
    #[error("not found: {id}")]
    NotFound { id: String },

    #[error("connection failed")]
    Connection(#[from] sqlx::Error),

    #[error("serialization failed")]
    Serialization(#[from] serde_json::Error),
}
```

## anyhow (애플리케이션용)

```rust
use anyhow::{Context, Result};

fn load_config(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read {}", path))?;

    let config: Config = toml::from_str(&content)
        .context("Failed to parse config")?;

    Ok(config)
}
```

## 에러 전파

```rust
// ? 연산자
fn process() -> Result<Output, Error> {
    let data = read_data()?;
    let parsed = parse_data(&data)?;
    let result = transform(parsed)?;
    Ok(result)
}

// map_err로 변환
fn process() -> Result<Output, AppError> {
    let data = read_data()
        .map_err(|e| AppError::Io(e))?;
    Ok(data)
}
```

## 에러 매칭

```rust
match result {
    Ok(value) => println!("Success: {}", value),
    Err(StorageError::NotFound { id }) => {
        println!("Not found: {}", id);
    }
    Err(StorageError::Connection(e)) => {
        eprintln!("DB error: {}", e);
    }
    Err(e) => {
        eprintln!("Other error: {}", e);
    }
}
```

## 체크리스트

- [ ] 라이브러리: thiserror
- [ ] 애플리케이션: anyhow
- [ ] Context 추가
- [ ] 에러 매칭
- [ ] unwrap() 금지 (프로덕션)
