# Select & Timeout

Tokio의 select!, timeout, 취소 패턴.

## tokio::select!

여러 비동기 작업 중 먼저 완료되는 것 처리.

### 기본 사용

```rust
use tokio::select;

async fn race_operations() {
    select! {
        result = operation_a() => {
            println!("A finished first: {:?}", result);
        }
        result = operation_b() => {
            println!("B finished first: {:?}", result);
        }
    }
    // 완료되지 않은 작업은 자동 취소됨
}
```

### 타임아웃 패턴

```rust
use tokio::time::{sleep, Duration};

async fn with_timeout() -> Result<Data, Error> {
    select! {
        result = fetch_data() => result,
        _ = sleep(Duration::from_secs(5)) => {
            Err(Error::Timeout)
        }
    }
}
```

### 채널 + 타임아웃

```rust
async fn recv_with_timeout(
    rx: &mut mpsc::Receiver<Message>
) -> Option<Message> {
    select! {
        msg = rx.recv() => msg,
        _ = sleep(Duration::from_secs(30)) => {
            tracing::warn!("Receive timeout");
            None
        }
    }
}
```

## biased 모드

특정 브랜치 우선순위 부여.

```rust
select! {
    biased;  // 위에서 아래 순서로 우선순위

    // 종료 신호가 항상 먼저 체크됨
    _ = shutdown_signal() => {
        tracing::info!("Shutting down");
        return;
    }

    // 그 다음 일반 작업
    msg = rx.recv() => {
        if let Some(m) = msg {
            handle_message(m).await;
        }
    }
}
```

## 루프에서 select!

```rust
async fn event_loop(
    mut rx: mpsc::Receiver<Command>,
    mut shutdown: broadcast::Receiver<()>,
) {
    loop {
        select! {
            cmd = rx.recv() => {
                match cmd {
                    Some(c) => handle_command(c).await,
                    None => break,  // 채널 닫힘
                }
            }
            _ = shutdown.recv() => {
                tracing::info!("Shutdown signal received");
                break;
            }
        }
    }
}
```

## tokio::time::timeout

간단한 타임아웃 적용.

```rust
use tokio::time::{timeout, Duration};

async fn fetch_with_timeout() -> Result<Data, Error> {
    match timeout(Duration::from_secs(10), fetch_data()).await {
        Ok(Ok(data)) => Ok(data),
        Ok(Err(e)) => Err(Error::Fetch(e)),
        Err(_elapsed) => Err(Error::Timeout),
    }
}

// 더 간단하게
let result = timeout(Duration::from_secs(10), fetch_data())
    .await
    .map_err(|_| Error::Timeout)??;
```

## 취소 안전성 (Cancellation Safety)

### 안전한 작업

```rust
// ✅ 안전: 취소되어도 데이터 손실 없음
select! {
    msg = rx.recv() => { /* ... */ }  // mpsc::Receiver::recv
    _ = sleep(Duration::from_secs(1)) => { /* ... */ }
}
```

### 안전하지 않은 작업

```rust
// ❌ 위험: read 중간에 취소되면 데이터 손실
select! {
    result = reader.read(&mut buf) => { /* ... */ }
    _ = timeout => { /* buf에 일부만 기록됨 */ }
}
```

### 취소 안전하게 만들기

```rust
use tokio::io::AsyncReadExt;

// 완전히 읽거나 안 읽거나
async fn read_message(reader: &mut TcpStream) -> Result<Message, Error> {
    let len = reader.read_u32().await?;
    let mut buf = vec![0u8; len as usize];
    reader.read_exact(&mut buf).await?;
    Ok(Message::decode(&buf)?)
}

// select에서 사용 시 tokio::pin! 사용
let read_fut = read_message(&mut reader);
tokio::pin!(read_fut);

select! {
    result = &mut read_fut => {
        // 완료됨
    }
    _ = shutdown.recv() => {
        // read_fut은 아직 pending 상태로 남음
        // 다음 루프에서 계속 진행 가능
    }
}
```

## 고급 패턴

### 재시도 with 지수 백오프

```rust
use tokio::time::{sleep, Duration};

async fn retry_with_backoff<T, E, F, Fut>(
    mut operation: F,
    max_retries: u32,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
{
    let mut delay = Duration::from_millis(100);

    for attempt in 0..max_retries {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempt == max_retries - 1 => return Err(e),
            Err(_) => {
                sleep(delay).await;
                delay = delay.saturating_mul(2);
            }
        }
    }
    unreachable!()
}
```

### 동시 요청 + 첫 번째 성공

```rust
async fn first_success<T>(
    futures: Vec<impl Future<Output = Result<T, Error>>>
) -> Result<T, Error> {
    let mut set = JoinSet::new();

    for fut in futures {
        set.spawn(fut);
    }

    while let Some(result) = set.join_next().await {
        if let Ok(Ok(value)) = result {
            set.abort_all();  // 나머지 취소
            return Ok(value);
        }
    }

    Err(Error::AllFailed)
}
```
