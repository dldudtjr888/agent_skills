# Python Message Queue Cheatsheet

## Celery

```python
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def process_order(self, order_id):
    try:
        # Process order
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# Call task
process_order.delay(order_id)

# With countdown
process_order.apply_async(args=[order_id], countdown=60)
```

## aiokafka

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio

# Producer
producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
await producer.start()
await producer.send_and_wait("orders", json.dumps(order).encode())
await producer.stop()

# Consumer
consumer = AIOKafkaConsumer(
    "orders",
    bootstrap_servers='localhost:9092',
    group_id="order-processor"
)
await consumer.start()
async for msg in consumer:
    order = json.loads(msg.value.decode())
    await process_order(order)
```

## pika (RabbitMQ)

```python
import pika
import json

# Producer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='orders', durable=True)
channel.basic_publish(
    exchange='',
    routing_key='orders',
    body=json.dumps(order),
    properties=pika.BasicProperties(delivery_mode=2)  # Persistent
)

# Consumer
def callback(ch, method, properties, body):
    order = json.loads(body)
    process_order(order)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='orders', on_message_callback=callback)
channel.start_consuming()
```

## FastAPI with Background Tasks

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

def send_email(email: str, message: str):
    # Send email
    pass

@app.post("/orders")
async def create_order(order: Order, background_tasks: BackgroundTasks):
    db_order = await db.create_order(order)

    # Run in background
    background_tasks.add_task(send_email, order.email, "Order confirmed!")

    return db_order
```

## arq (Async Redis Queue)

```python
from arq import create_pool
from arq.connections import RedisSettings

async def process_order(ctx, order_id: int):
    # Process order
    pass

class WorkerSettings:
    functions = [process_order]
    redis_settings = RedisSettings()

# Enqueue
redis = await create_pool(RedisSettings())
await redis.enqueue_job('process_order', order_id)
```
