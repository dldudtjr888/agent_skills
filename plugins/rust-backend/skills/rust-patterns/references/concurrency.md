# Concurrency Patterns

## Prefer Message Passing Over Shared State

```rust
use tokio::sync::{mpsc, oneshot};

// Actor model with message passing — avoids Mutex contention
enum Message {
    Set { key: String, value: String },
    Get { key: String, reply: oneshot::Sender<Option<String>> },
}

struct Actor {
    receiver: mpsc::Receiver<Message>,
    state: HashMap<String, String>,
}

impl Actor {
    async fn run(mut self) {
        while let Some(msg) = self.receiver.recv().await {
            match msg {
                Message::Set { key, value } => { self.state.insert(key, value); }
                Message::Get { key, reply } => { let _ = reply.send(self.state.get(&key).cloned()); }
            }
        }
    }
}
```

## Concurrent Tasks with JoinSet

```rust
use tokio::task::JoinSet;

async fn fetch_all(urls: Vec<String>) -> Vec<anyhow::Result<String>> {
    let mut set = JoinSet::new();
    for url in urls {
        set.spawn(async move {
            let resp = reqwest::get(&url).await?;
            Ok(resp.text().await?)
        });
    }
    let mut results = Vec::new();
    while let Some(result) = set.join_next().await {
        match result {
            Ok(value) => results.push(value),
            Err(join_err) => tracing::error!("task panicked: {join_err}"),
        }
    }
    results
}
```

## Cancellation with select!

```rust
tokio::select! {
    result = do_work() => handle(result),
    _ = tokio::time::sleep(Duration::from_secs(5)) => bail!("timed out"),
}
```
