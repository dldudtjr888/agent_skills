# Rust Message Queue Cheatsheet

## rdkafka

```rust
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::consumer::{StreamConsumer, Consumer};
use rdkafka::Message;

// Producer
let producer: FutureProducer = ClientConfig::new()
    .set("bootstrap.servers", "localhost:9092")
    .create()?;

producer.send(
    FutureRecord::to("orders")
        .key(&order.id.to_string())
        .payload(&serde_json::to_string(&order)?),
    Duration::from_secs(5),
).await?;

// Consumer
let consumer: StreamConsumer = ClientConfig::new()
    .set("bootstrap.servers", "localhost:9092")
    .set("group.id", "order-processor")
    .create()?;

consumer.subscribe(&["orders"])?;

loop {
    match consumer.recv().await {
        Ok(msg) => {
            let payload = msg.payload().unwrap();
            let order: Order = serde_json::from_slice(payload)?;
            process_order(order).await?;
            consumer.commit_message(&msg, CommitMode::Async)?;
        }
        Err(e) => eprintln!("Error: {:?}", e),
    }
}
```

## lapin (RabbitMQ)

```rust
use lapin::{Connection, ConnectionProperties, options::*, types::FieldTable};

// Connect
let conn = Connection::connect("amqp://localhost:5672", ConnectionProperties::default()).await?;
let channel = conn.create_channel().await?;

// Declare queue
channel.queue_declare("orders", QueueDeclareOptions::default(), FieldTable::default()).await?;

// Publish
channel.basic_publish(
    "",
    "orders",
    BasicPublishOptions::default(),
    serde_json::to_vec(&order)?,
    BasicProperties::default(),
).await?;

// Consume
let mut consumer = channel.basic_consume(
    "orders",
    "order-processor",
    BasicConsumeOptions::default(),
    FieldTable::default(),
).await?;

while let Some(delivery) = consumer.next().await {
    let delivery = delivery?;
    let order: Order = serde_json::from_slice(&delivery.data)?;
    process_order(order).await?;
    delivery.ack(BasicAckOptions::default()).await?;
}
```

## Tokio Channels (In-Process)

```rust
use tokio::sync::mpsc;

#[derive(Debug)]
struct Order { id: i64 }

#[tokio::main]
async fn main() {
    let (tx, mut rx) = mpsc::channel::<Order>(100);

    // Producer
    tokio::spawn(async move {
        tx.send(Order { id: 1 }).await.unwrap();
    });

    // Consumer
    while let Some(order) = rx.recv().await {
        println!("Processing order: {:?}", order);
    }
}
```

## Background Jobs with Tokio

```rust
use tokio::task;

async fn process_order_background(order_id: i64) {
    task::spawn(async move {
        // Long-running task
        process_order(order_id).await;
    });
}

// With semaphore for concurrency control
use tokio::sync::Semaphore;

static SEMAPHORE: Semaphore = Semaphore::const_new(10);

async fn process_with_limit(order_id: i64) {
    let permit = SEMAPHORE.acquire().await.unwrap();
    task::spawn(async move {
        process_order(order_id).await;
        drop(permit);
    });
}
```
