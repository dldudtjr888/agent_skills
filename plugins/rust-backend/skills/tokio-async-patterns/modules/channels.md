# Channels

Tokio의 비동기 채널 타입과 사용 패턴.

## 채널 타입 비교

| 채널 | 패턴 | 버퍼 | 사용 사례 |
|------|------|------|-----------|
| `mpsc` | N:1 | 유한/무한 | 워커 큐, 이벤트 수집 |
| `oneshot` | 1:1 | 없음 | 요청-응답, 결과 반환 |
| `broadcast` | N:M | 유한 | 이벤트 브로드캐스트 |
| `watch` | 1:N | 1 (최신값) | 설정 변경 알림 |

## mpsc (Multi-Producer Single-Consumer)

```rust
use tokio::sync::mpsc;

#[derive(Debug)]
enum Command {
    Get { key: String, resp: oneshot::Sender<Option<String>> },
    Set { key: String, value: String },
}

async fn run_worker(mut rx: mpsc::Receiver<Command>) {
    let mut store = HashMap::new();

    while let Some(cmd) = rx.recv().await {
        match cmd {
            Command::Get { key, resp } => {
                let value = store.get(&key).cloned();
                let _ = resp.send(value);
            }
            Command::Set { key, value } => {
                store.insert(key, value);
            }
        }
    }
}

async fn client(tx: mpsc::Sender<Command>) -> Option<String> {
    let (resp_tx, resp_rx) = oneshot::channel();

    tx.send(Command::Get {
        key: "my_key".to_string(),
        resp: resp_tx,
    }).await.ok()?;

    resp_rx.await.ok()?
}
```

### 버퍼 크기 선택

```rust
// 유한 버퍼 (백프레셔 적용)
let (tx, rx) = mpsc::channel(100);

// 무한 버퍼 (메모리 주의)
let (tx, rx) = mpsc::unbounded_channel();

// send vs try_send
tx.send(value).await?;  // 버퍼 가득 차면 대기
tx.try_send(value)?;     // 즉시 반환 (에러 가능)
```

## oneshot (One-Shot)

```rust
use tokio::sync::oneshot;

async fn compute_and_respond(resp: oneshot::Sender<i32>) {
    let result = expensive_computation().await;
    let _ = resp.send(result);  // 수신자가 drop 됐을 수 있음
}

async fn request_computation() -> Result<i32, oneshot::error::RecvError> {
    let (tx, rx) = oneshot::channel();

    tokio::spawn(compute_and_respond(tx));

    rx.await
}
```

### 타임아웃과 함께

```rust
use tokio::time::{timeout, Duration};

async fn request_with_timeout() -> Result<i32, Error> {
    let (tx, rx) = oneshot::channel();
    tokio::spawn(compute_and_respond(tx));

    timeout(Duration::from_secs(5), rx)
        .await
        .map_err(|_| Error::Timeout)?
        .map_err(|_| Error::Cancelled)
}
```

## broadcast

```rust
use tokio::sync::broadcast;

async fn event_system() {
    let (tx, _) = broadcast::channel::<Event>(100);

    // 구독자 1
    let mut rx1 = tx.subscribe();
    tokio::spawn(async move {
        while let Ok(event) = rx1.recv().await {
            println!("Subscriber 1: {:?}", event);
        }
    });

    // 구독자 2
    let mut rx2 = tx.subscribe();
    tokio::spawn(async move {
        while let Ok(event) = rx2.recv().await {
            println!("Subscriber 2: {:?}", event);
        }
    });

    // 이벤트 발행
    tx.send(Event::UserLoggedIn { user_id: 1 })?;
}
```

### Lagging 처리

```rust
loop {
    match rx.recv().await {
        Ok(event) => handle_event(event),
        Err(broadcast::error::RecvError::Lagged(n)) => {
            tracing::warn!("Missed {} events", n);
        }
        Err(broadcast::error::RecvError::Closed) => break,
    }
}
```

## watch

```rust
use tokio::sync::watch;

struct Config {
    log_level: String,
    max_connections: usize,
}

async fn config_watcher() {
    let (tx, rx) = watch::channel(Config {
        log_level: "info".to_string(),
        max_connections: 100,
    });

    // 설정 변경 감지
    let mut rx_clone = rx.clone();
    tokio::spawn(async move {
        while rx_clone.changed().await.is_ok() {
            let config = rx_clone.borrow();
            tracing::info!("Config updated: log_level={}", config.log_level);
        }
    });

    // 현재 값 읽기 (대기 없음)
    {
        let config = rx.borrow();
        println!("Current log level: {}", config.log_level);
    }

    // 설정 업데이트
    tx.send(Config {
        log_level: "debug".to_string(),
        max_connections: 200,
    })?;
}
```

## 채널 선택 가이드

```
Q: 몇 명의 송신자/수신자?
├── 1:1 (일회성) → oneshot
├── N:1 (워커 큐) → mpsc
├── 1:N (최신값 공유) → watch
└── N:M (이벤트 브로드캐스트) → broadcast

Q: 버퍼 필요?
├── 버퍼 없음 → oneshot
├── 최신값만 → watch (버퍼 1)
└── 여러 메시지 → mpsc/broadcast

Q: 메시지 손실 허용?
├── 허용 → broadcast (lagged 발생 가능)
└── 불허 → mpsc (백프레셔 적용)
```
