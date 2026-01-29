# Advanced Patterns

> 메인 스킬: `../SKILL.md`

## Redis Cache Layer

```python
from redis.asyncio import Redis

class CachedMarketRepository:
    def __init__(self, base_repo: MarketRepository, redis: Redis):
        self.base_repo = base_repo
        self.redis = redis
        self.ttl = 300  # 5분

    async def find_by_id(self, market_id: int) -> Market | None:
        cache_key = f"market:{market_id}"

        # 캐시 확인
        cached = await self.redis.get(cache_key)
        if cached:
            return Market.model_validate_json(cached)

        # 캐시 미스 → DB 조회
        market = await self.base_repo.find_by_id(market_id)
        if market:
            await self.redis.setex(
                cache_key, self.ttl,
                MarketResponse.model_validate(market, from_attributes=True).model_dump_json()
            )
        return market

    async def invalidate(self, market_id: int) -> None:
        await self.redis.delete(f"market:{market_id}")
```

## Background Tasks

```python
from fastapi import BackgroundTasks

# ✅ 간단한 작업: FastAPI BackgroundTasks
@router.post("/")
async def create_market(
    data: MarketCreate,
    bg: BackgroundTasks,
    service: MarketService = Depends(get_market_service),
):
    market = await service.create(data)
    bg.add_task(send_notification, market.id)        # 논블로킹
    bg.add_task(update_search_index, market.id)      # 논블로킹
    return market

async def send_notification(market_id: int) -> None:
    ...

async def update_search_index(market_id: int) -> None:
    ...

# ✅ 복잡한 작업: Celery (분산 큐)
from celery import Celery

celery_app = Celery("worker", broker="redis://localhost:6379/0")

@celery_app.task
def process_heavy_job(market_id: int) -> None:
    # CPU 집약적 작업
    ...

@router.post("/heavy")
async def trigger_heavy(data: HeavyJobRequest):
    process_heavy_job.delay(data.market_id)
    return {"status": "queued"}
```

## SSE Streaming

```python
import asyncio
import json
from fastapi import Request
from fastapi.responses import StreamingResponse

@router.get("/stream")
async def stream_updates(request: Request):
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await get_latest_update()
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

## Structured Logging

```python
import structlog
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

# ✅ 요청별 컨텍스트 로깅
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
            logger.info("request_completed", status=response.status_code)
            return response
        except Exception as exc:
            logger.error("request_failed", error=str(exc))
            raise
        finally:
            structlog.contextvars.unbind_contextvars("request_id", "method", "path")
```

## Testing

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

# ✅ GOOD: httpx.AsyncClient + 의존성 오버라이드
@pytest.fixture
async def client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def mock_service():
    service = AsyncMock(spec=MarketService)
    service.list_markets.return_value = [
        MarketResponse(id=1, name="Test", status="active", ...)
    ]
    return service

@pytest.fixture
def app(mock_service):
    app = create_app()
    app.dependency_overrides[get_market_service] = lambda: mock_service
    return app

async def test_list_markets(client: AsyncClient):
    response = await client.get("/markets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

async def test_create_market_validation(client: AsyncClient):
    response = await client.post("/markets/", json={"name": ""})
    assert response.status_code == 422

# ❌ BAD: TestClient (동기) → async 엔드포인트에서 이벤트 루프 충돌 가능
from fastapi.testclient import TestClient
client = TestClient(app)  # async 코드와 호환성 문제
```
