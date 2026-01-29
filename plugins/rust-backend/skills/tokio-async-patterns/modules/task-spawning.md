# Task Spawning

Tokio에서 비동기 태스크 생성 및 관리 패턴.

## spawn vs spawn_blocking

### tokio::spawn

```rust
use tokio::task::JoinHandle;

// 비동기 태스크 생성
let handle: JoinHandle<String> = tokio::spawn(async {
    // I/O 바운드 작업
    let result = fetch_data().await;
    process_result(result)
});

// 결과 대기
let output = handle.await?;
```

### spawn_blocking

```rust
// CPU 바운드 작업은 spawn_blocking 사용
let result = tokio::task::spawn_blocking(|| {
    // 블로킹 또는 CPU 집약적 작업
    expensive_computation()
}).await?;

// 예: 이미지 처리
let processed = tokio::task::spawn_blocking(move || {
    image::load_from_memory(&bytes)?.resize(800, 600, FilterType::Lanczos3)
}).await??;
```

## JoinSet

여러 태스크를 동시에 관리하고 결과 수집.

```rust
use tokio::task::JoinSet;

async fn fetch_all_urls(urls: Vec<String>) -> Vec<Result<Response, Error>> {
    let mut set = JoinSet::new();

    // 모든 URL에 대해 태스크 생성
    for url in urls {
        set.spawn(async move {
            reqwest::get(&url).await
        });
    }

    // 완료되는 순서대로 결과 수집
    let mut results = Vec::new();
    while let Some(result) = set.join_next().await {
        match result {
            Ok(response) => results.push(response),
            Err(join_err) => {
                tracing::error!("Task panicked: {}", join_err);
            }
        }
    }

    results
}
```

### JoinSet with Abort

```rust
async fn fetch_with_limit(urls: Vec<String>, max_concurrent: usize) {
    let mut set = JoinSet::new();
    let mut url_iter = urls.into_iter();

    // 초기 태스크들 생성
    for url in url_iter.by_ref().take(max_concurrent) {
        set.spawn(fetch_url(url));
    }

    // 하나 완료되면 새 태스크 추가
    while let Some(result) = set.join_next().await {
        handle_result(result);

        if let Some(url) = url_iter.next() {
            set.spawn(fetch_url(url));
        }
    }
}

// 모든 태스크 취소
set.abort_all();
```

## Task-Local Storage

```rust
tokio::task_local! {
    static REQUEST_ID: String;
}

async fn handle_request(request_id: String) {
    REQUEST_ID.scope(request_id, async {
        // 이 스코프 내에서 REQUEST_ID 접근 가능
        process_request().await;
    }).await;
}

async fn log_something() {
    REQUEST_ID.with(|id| {
        tracing::info!(request_id = %id, "Processing");
    });
}
```

## 에러 처리 패턴

```rust
// JoinError 처리
match handle.await {
    Ok(result) => {
        // 태스크가 정상 완료
        match result {
            Ok(value) => println!("Success: {:?}", value),
            Err(e) => println!("Task error: {}", e),
        }
    }
    Err(join_error) => {
        if join_error.is_cancelled() {
            println!("Task was cancelled");
        } else if join_error.is_panic() {
            println!("Task panicked");
        }
    }
}
```

## 베스트 프랙티스

1. **I/O 바운드 → `spawn`**: 네트워크, 파일 I/O
2. **CPU 바운드 → `spawn_blocking`**: 암호화, 이미지 처리, 압축
3. **많은 태스크 → `JoinSet`**: 동적 태스크 관리
4. **리소스 제한 → Semaphore와 함께 사용**

```rust
use tokio::sync::Semaphore;
use std::sync::Arc;

async fn limited_concurrent(urls: Vec<String>, limit: usize) {
    let semaphore = Arc::new(Semaphore::new(limit));
    let mut handles = Vec::new();

    for url in urls {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        handles.push(tokio::spawn(async move {
            let result = fetch_url(&url).await;
            drop(permit); // 명시적으로 permit 해제
            result
        }));
    }

    for handle in handles {
        let _ = handle.await;
    }
}
```
