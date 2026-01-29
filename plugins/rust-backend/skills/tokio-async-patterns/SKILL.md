---
name: tokio-async-patterns
description: "Tokio 비동기 런타임 패턴. JoinSet, channels, select!, graceful shutdown 등을 다룹니다."
version: 1.0.0
category: async
user-invocable: true
triggers:
  keywords:
    - tokio
    - async
    - await
    - spawn
    - channel
    - mpsc
    - select
    - timeout
    - shutdown
  intentPatterns:
    - "(만들|구현).*(비동기|async|tokio)"
    - "(tokio|async).*(패턴|channel|spawn)"
---

# Tokio Async Patterns

Tokio 런타임을 사용한 비동기 프로그래밍 패턴.

## 관련 참조

- **common-backend/deployment-patterns**: Graceful shutdown, 컨테이너 헬스체크 연동

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Task Spawning | [modules/task-spawning.md](modules/task-spawning.md) | spawn, spawn_blocking, JoinSet |
| 2 | Channels | [modules/channels.md](modules/channels.md) | mpsc, oneshot, broadcast, watch |
| 3 | Select & Timeout | [modules/select-timeout.md](modules/select-timeout.md) | select!, timeout, cancellation |
| 4 | Graceful Shutdown | [modules/graceful-shutdown.md](modules/graceful-shutdown.md) | signal handling, shutdown tokens |

## Quick Reference

### Task Spawning

```rust
use tokio::task::JoinSet;

// 여러 태스크 동시 실행
async fn fetch_all(urls: Vec<String>) -> Vec<Result<String, Error>> {
    let mut set = JoinSet::new();

    for url in urls {
        set.spawn(async move { fetch(&url).await });
    }

    let mut results = Vec::new();
    while let Some(result) = set.join_next().await {
        results.push(result.unwrap());
    }
    results
}

// CPU 바운드 작업
let result = tokio::task::spawn_blocking(|| {
    expensive_computation()
}).await?;
```

### Channels

```rust
use tokio::sync::{mpsc, oneshot, broadcast, watch};

// mpsc: 다대일
let (tx, mut rx) = mpsc::channel(100);
tx.send(value).await?;
let received = rx.recv().await;

// oneshot: 일회성
let (tx, rx) = oneshot::channel();
tx.send(value).unwrap();
let received = rx.await?;

// broadcast: 다대다
let (tx, _) = broadcast::channel(100);
let mut rx = tx.subscribe();
tx.send(value)?;
let received = rx.recv().await?;

// watch: 최신 값 공유
let (tx, mut rx) = watch::channel(initial_value);
tx.send(new_value)?;
let current = rx.borrow().clone();
```

### Select & Timeout

```rust
use tokio::time::{timeout, Duration};

// 타임아웃
let result = timeout(Duration::from_secs(5), async_operation()).await;

// select!
tokio::select! {
    result = operation1() => { /* ... */ }
    result = operation2() => { /* ... */ }
    _ = tokio::time::sleep(Duration::from_secs(10)) => { /* timeout */ }
}
```

### Graceful Shutdown

```rust
async fn run_server(shutdown: tokio::sync::broadcast::Receiver<()>) {
    loop {
        tokio::select! {
            conn = listener.accept() => {
                // handle connection
            }
            _ = shutdown.recv() => {
                tracing::info!("Shutting down");
                break;
            }
        }
    }
}

async fn shutdown_signal() {
    tokio::signal::ctrl_c().await.expect("Failed to listen for Ctrl+C");
}
```

## 체크리스트

- [ ] 적절한 채널 타입 선택
- [ ] spawn_blocking for CPU-bound work
- [ ] 타임아웃 설정
- [ ] 취소 안전성 고려
- [ ] graceful shutdown 구현
- [ ] 에러 전파
