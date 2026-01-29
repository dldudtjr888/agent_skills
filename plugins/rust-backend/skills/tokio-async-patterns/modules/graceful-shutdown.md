# Graceful Shutdown

Tokio 애플리케이션의 안전한 종료 패턴.

## 기본 시그널 처리

```rust
use tokio::signal;

async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("Failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("Failed to install SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
}
```

## CancellationToken 패턴

```rust
use tokio_util::sync::CancellationToken;

struct Server {
    token: CancellationToken,
}

impl Server {
    fn new() -> Self {
        Self {
            token: CancellationToken::new(),
        }
    }

    async fn run(&self) {
        let listener = TcpListener::bind("0.0.0.0:8080").await.unwrap();

        loop {
            tokio::select! {
                result = listener.accept() => {
                    let (socket, _) = result.unwrap();
                    let token = self.token.child_token();

                    tokio::spawn(async move {
                        handle_connection(socket, token).await;
                    });
                }
                _ = self.token.cancelled() => {
                    tracing::info!("Server shutting down");
                    break;
                }
            }
        }
    }

    fn shutdown(&self) {
        self.token.cancel();
    }
}

async fn handle_connection(socket: TcpStream, token: CancellationToken) {
    loop {
        tokio::select! {
            result = read_from_socket(&socket) => {
                // 처리
            }
            _ = token.cancelled() => {
                tracing::info!("Connection closing due to shutdown");
                break;
            }
        }
    }
}
```

## Broadcast 기반 종료

```rust
use tokio::sync::broadcast;

async fn run_with_broadcast_shutdown() {
    let (shutdown_tx, _) = broadcast::channel::<()>(1);

    // 워커들 생성
    for i in 0..4 {
        let mut shutdown_rx = shutdown_tx.subscribe();
        tokio::spawn(async move {
            loop {
                tokio::select! {
                    _ = do_work() => {}
                    _ = shutdown_rx.recv() => {
                        tracing::info!("Worker {} shutting down", i);
                        break;
                    }
                }
            }
        });
    }

    // 종료 신호 대기
    shutdown_signal().await;

    // 모든 워커에게 종료 알림
    let _ = shutdown_tx.send(());
}
```

## Axum 서버 종료

```rust
use axum::{Router, routing::get};
use tokio::net::TcpListener;

async fn run_server() {
    let app = Router::new()
        .route("/", get(|| async { "Hello" }));

    let listener = TcpListener::bind("0.0.0.0:3000").await.unwrap();

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await
        .unwrap();
}
```

### 연결 드레이닝

```rust
use std::time::Duration;

async fn graceful_shutdown_with_timeout() {
    let app = create_app();
    let listener = TcpListener::bind("0.0.0.0:3000").await.unwrap();

    // 서버 태스크
    let server = tokio::spawn(
        axum::serve(listener, app)
            .with_graceful_shutdown(shutdown_signal())
    );

    // 종료 신호 후 최대 30초 대기
    let shutdown_timeout = Duration::from_secs(30);

    match tokio::time::timeout(shutdown_timeout, server).await {
        Ok(Ok(())) => tracing::info!("Server shut down gracefully"),
        Ok(Err(e)) => tracing::error!("Server error: {}", e),
        Err(_) => {
            tracing::warn!("Server shutdown timed out, forcing exit");
        }
    }
}
```

## 리소스 정리 패턴

```rust
struct App {
    db_pool: PgPool,
    cache: RedisPool,
    background_tasks: JoinSet<()>,
}

impl App {
    async fn shutdown(mut self) {
        tracing::info!("Starting graceful shutdown");

        // 1. 새 요청 수신 중지 (서버 종료)
        tracing::info!("Stopping new requests");

        // 2. 백그라운드 태스크 취소 및 대기
        tracing::info!("Waiting for background tasks");
        self.background_tasks.abort_all();
        while self.background_tasks.join_next().await.is_some() {}

        // 3. 캐시 플러시
        tracing::info!("Flushing cache");
        if let Err(e) = self.cache.flushall().await {
            tracing::error!("Cache flush error: {}", e);
        }

        // 4. DB 연결 종료
        tracing::info!("Closing database connections");
        self.db_pool.close().await;

        tracing::info!("Shutdown complete");
    }
}
```

## 완전한 예제

```rust
use axum::{Router, routing::get};
use tokio::sync::broadcast;
use std::sync::Arc;

struct AppState {
    shutdown_tx: broadcast::Sender<()>,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let (shutdown_tx, _) = broadcast::channel(1);
    let state = Arc::new(AppState {
        shutdown_tx: shutdown_tx.clone(),
    });

    let app = Router::new()
        .route("/health", get(|| async { "OK" }))
        .with_state(state);

    let listener = TcpListener::bind("0.0.0.0:3000").await.unwrap();
    tracing::info!("Server starting on :3000");

    // 종료 신호 처리
    let shutdown_signal = async move {
        shutdown_signal().await;
        tracing::info!("Shutdown signal received");
        let _ = shutdown_tx.send(());
    };

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal)
        .await
        .unwrap();

    tracing::info!("Server stopped");
}
```

## 체크리스트

- [ ] Ctrl+C (SIGINT) 처리
- [ ] SIGTERM 처리 (프로덕션)
- [ ] 진행 중인 요청 완료 대기
- [ ] 백그라운드 태스크 취소
- [ ] DB 연결 정리
- [ ] 로그/메트릭 플러시
- [ ] 종료 타임아웃 설정
