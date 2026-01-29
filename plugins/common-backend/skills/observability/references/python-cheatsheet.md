# Python Observability Cheatsheet

## Structlog

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

logger.info("user_logged_in", user_id="123", ip="1.2.3.4")
# {"timestamp": "2024-01-01T12:00:00", "event": "user_logged_in", "user_id": "123", "ip": "1.2.3.4"}
```

## Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration', ['method', 'endpoint'])

# Usage
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_DURATION.labels(request.method, request.url.path).observe(duration)

    return response

# Expose metrics
start_http_server(8001)  # /metrics on port 8001
```

## OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Usage
with tracer.start_as_current_span("process_order") as span:
    span.set_attribute("order_id", order_id)
    process_order(order_id)
```

## FastAPI Integration

```python
from fastapi import FastAPI, Request
import structlog

app = FastAPI()
logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    with structlog.contextvars.bound_contextvars(request_id=request_id):
        logger.info("request_started", method=request.method, path=request.url.path)
        response = await call_next(request)
        logger.info("request_completed", status=response.status_code)

    response.headers["X-Request-ID"] = request_id
    return response
```
