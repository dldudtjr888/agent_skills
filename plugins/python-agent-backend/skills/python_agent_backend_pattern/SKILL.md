---
name: python-agent-backend-patterns
description: Python 에이전트 백엔드 아키텍처 패턴, API 설계, DB 최적화, 인증/인가 베스트 프랙티스. FastAPI, SQLAlchemy, Pydantic, Depends 기반 코드 템플릿 모음.
---

# FastAPI Backend Patterns

FastAPI 기반 백엔드 아키텍처 패턴과 코드 템플릿.

> 아키텍처 원칙: `rules/python_agent_rules/architecture.md` | 인프라 패턴: `rules/python_agent_rules/core-infrastructure.md`

**모듈 참조**:
- 인증/인가/Rate Limiting → `modules/auth-patterns.md`
- 캐싱/백그라운드/SSE/로깅/테스트 → `modules/advanced-patterns.md`

---

## API Design Patterns

### RESTful Router

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter(prefix="/markets", tags=["markets"])

# ✅ 리소스 기반 URL + 적절한 HTTP 메서드
@router.get("/", response_model=list[MarketResponse])
async def list_markets(
    status: str | None = Query(None),
    sort: str = Query("created_at"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MarketService = Depends(get_market_service),
):
    return await service.list_markets(status=status, sort=sort, limit=limit, offset=offset)

@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: int, service: MarketService = Depends(get_market_service)):
    market = await service.get_by_id(market_id)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    return market

@router.post("/", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market(data: MarketCreate, service: MarketService = Depends(get_market_service)):
    return await service.create(data)

@router.patch("/{market_id}", response_model=MarketResponse)
async def update_market(market_id: int, data: MarketUpdate, service: MarketService = Depends(get_market_service)):
    return await service.update(market_id, data)

@router.delete("/{market_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_market(market_id: int, service: MarketService = Depends(get_market_service)):
    await service.delete(market_id)
```

### Pydantic Schemas (Create / Update / Response 분리)

```python
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

# ✅ GOOD: 용도별 스키마 분리
class MarketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    status: str = "draft"

class MarketUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None

class MarketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

# ✅ GOOD: camelCase alias (프론트엔드 JS ↔ 백엔드 Python)
class MarketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    market_name: str = Field(alias="marketName")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

# ❌ BAD: 수동 변환
@router.get("/")
async def list_markets(service: MarketService = Depends(get_market_service)):
    data = await service.list_markets()
    return [{"marketName": m.market_name, ...} for m in data]  # 수동 매핑

# ❌ BAD: 하나의 스키마로 모든 용도 처리
class Market(BaseModel):
    id: int | None = None       # Create시 None, Response시 필수 → 혼란
    name: str | None = None     # Update시 Optional, Create시 필수 → 혼란
    status: str | None = None
```

### Dependency Injection (Depends 체이닝)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# ✅ GOOD: Depends 체이닝으로 의존성 주입
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

def get_market_repo(db: AsyncSession = Depends(get_db)) -> MarketRepository:
    return MarketRepository(db)

def get_market_service(repo: MarketRepository = Depends(get_market_repo)) -> MarketService:
    return MarketService(repo)

# ❌ BAD: 엔드포인트에서 직접 생성
@router.get("/")
async def list_markets():
    db = await get_db_connection()       # 수동 관리
    repo = MarketRepository(db)          # 직접 생성
    service = MarketService(repo)        # 테스트 불가
    return await service.list_markets()
```

### Middleware 패턴

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

# ✅ 미들웨어: 횡단 관심사 (로깅, 타이밍, CORS 등)
class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response

app.add_middleware(RequestTimingMiddleware)

# ✅ Depends: 엔드포인트별 인증/인가
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = await verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user
```

---

## Database Patterns

### Repository 패턴

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class MarketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, market_id: int) -> Market | None:
        return await self.db.get(Market, market_id)

    async def find_all(
        self, *, status: str | None = None, skip: int = 0, limit: int = 20
    ) -> list[Market]:
        stmt = select(Market)
        if status:
            stmt = stmt.where(Market.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: MarketCreate) -> Market:
        market = Market(**data.model_dump())
        self.db.add(market)
        await self.db.flush()
        await self.db.refresh(market)
        return market

    async def count(self, *, status: str | None = None) -> int:
        stmt = select(func.count(Market.id))
        if status:
            stmt = stmt.where(Market.status == status)
        result = await self.db.execute(stmt)
        return result.scalar_one()
```

### Query Optimization

```python
from sqlalchemy import select, exists
from sqlalchemy.orm import load_only

# ✅ GOOD: 필요한 컬럼만 선택
stmt = (
    select(Market)
    .options(load_only(Market.id, Market.name, Market.status, Market.volume))
    .where(Market.status == "active")
    .order_by(Market.volume.desc())
    .limit(10)
)

# ❌ BAD: 모든 컬럼 로드 (큰 텍스트 필드 포함)
stmt = select(Market).where(Market.status == "active")

# ✅ GOOD: 존재 여부만 확인할 때
stmt = select(exists().where(Market.id == market_id))

# ❌ BAD: 전체 레코드를 로드해서 존재 여부 확인
market = await db.get(Market, market_id)
if market is not None: ...
```

### N+1 Query Prevention

```python
from sqlalchemy.orm import selectinload, joinedload

# ❌ BAD: N+1 문제
stmt = select(User)
result = await db.execute(stmt)
users = result.scalars().all()
for user in users:
    # 각 user마다 별도 쿼리 발생 → N개 추가 쿼리
    posts = await db.execute(select(Post).where(Post.user_id == user.id))

# ✅ GOOD: selectinload (1:N 관계, SELECT IN 방식)
stmt = select(User).options(selectinload(User.posts))
result = await db.execute(stmt)
users = result.scalars().all()  # 2번의 쿼리로 모든 데이터 로드

# ✅ GOOD: joinedload (N:1 관계, JOIN 방식)
stmt = select(Post).options(joinedload(Post.author))
result = await db.execute(stmt)
posts = result.unique().scalars().all()  # 1번의 JOIN 쿼리
```

### Transaction 패턴

```python
from sqlalchemy.ext.asyncio import AsyncSession

# ✅ GOOD: 서비스 레이어에서 트랜잭션 관리
class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order_with_items(
        self, order_data: OrderCreate, items: list[OrderItemCreate]
    ) -> Order:
        try:
            order = Order(**order_data.model_dump())
            self.db.add(order)
            await self.db.flush()  # order.id 생성

            for item_data in items:
                item = OrderItem(order_id=order.id, **item_data.model_dump())
                self.db.add(item)

            await self.db.commit()
            await self.db.refresh(order)
            return order
        except Exception:
            await self.db.rollback()
            raise

# ❌ BAD: 엔드포인트에서 직접 커밋
@router.post("/orders")
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    order = Order(**data.model_dump())
    db.add(order)
    await db.commit()  # 라우터에 비즈니스 로직 혼재
```

---

## Error Handling

### 중앙 집중 예외 처리

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

class AppError(Exception):
    def __init__(self, status_code: int, detail: str, is_operational: bool = True):
        self.status_code = status_code
        self.detail = detail
        self.is_operational = is_operational

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Validation failed", "details": exc.errors()},
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
    )
```

### Retry with Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

# ✅ tenacity 사용
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
)
async def call_external_api(url: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

# ✅ 커스텀 retry (간단한 경우)
async def fetch_with_retry(fn, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await fn()
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

---

## Lifespan Events

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

# ✅ GOOD: lifespan context manager (FastAPI 0.93+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.db_pool = await create_db_pool()
    app.state.redis = await create_redis_pool()
    yield
    # shutdown
    await app.state.db_pool.close()
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

# ❌ BAD: deprecated on_event 데코레이터
@app.on_event("startup")
async def startup():
    ...
```

---

**Remember**: 패턴은 프로젝트 복잡도에 맞게 선택. 간단한 CRUD에 모든 패턴을 적용할 필요 없음.
