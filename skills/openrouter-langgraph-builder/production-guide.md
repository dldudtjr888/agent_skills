# Production Guide

Deploy OpenRouter + LangGraph agents to production with proper structure, error handling, and observability.

## Project Structure

```
my-agent-project/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration management
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py             # Shared agent utilities
│   │   ├── researcher.py       # Research agent
│   │   ├── coder.py            # Coding agent
│   │   └── supervisor.py       # Supervisor workflow
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py
│   │   ├── code_executor.py
│   │   └── database.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── cost_tracking.py
│   │   └── rate_limiting.py
│   └── api/
│       ├── __init__.py
│       ├── routes.py           # API endpoints
│       └── schemas.py          # Pydantic models
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_agents.py
│   └── test_tools.py
├── .env.example
├── .env
├── pyproject.toml
└── README.md
```

## Environment Configuration

### .env.example

```bash
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_APP_URL=https://your-app.com
OPENROUTER_APP_NAME=YourAppName

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxx
LANGCHAIN_PROJECT=my-agent-project

# Database (for checkpointing)
DATABASE_URL=postgresql://user:pass@localhost:5432/agents
REDIS_URL=redis://localhost:6379

# App settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_AGENT_TURNS=50
DEFAULT_TIMEOUT_SECONDS=120
```

### config.py

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # OpenRouter
    openrouter_api_key: str
    openrouter_app_url: Optional[str] = None
    openrouter_app_name: Optional[str] = None
    
    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "default"
    
    # Database
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # App
    environment: str = "development"
    log_level: str = "INFO"
    max_agent_turns: int = 50
    default_timeout_seconds: int = 120
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

## FastAPI Integration

### main.py

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.config import settings
from src.api.routes import router
from src.agents.supervisor import create_workflow

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global workflow instance
workflow = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    global workflow
    
    # Startup
    logger.info("Initializing agent workflow...")
    workflow = create_workflow()
    logger.info("Workflow ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "healthy", "environment": settings.environment}
```

### api/routes.py

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import json

from src.config import settings
from src.agents.supervisor import get_workflow

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    thread_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    workflow = get_workflow()
    
    config = {"configurable": {"thread_id": request.thread_id or "default"}}
    
    try:
        result = await asyncio.wait_for(
            workflow.ainvoke(
                {"messages": [{"role": "user", "content": request.message}]},
                config=config,
            ),
            timeout=settings.default_timeout_seconds,
        )
        
        return ChatResponse(
            response=result["messages"][-1].content,
            thread_id=config["configurable"]["thread_id"],
        )
    
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint."""
    workflow = get_workflow()
    config = {"configurable": {"thread_id": request.thread_id or "default"}}
    
    async def event_generator():
        try:
            async for event in workflow.astream_events(
                {"messages": [{"role": "user", "content": request.message}]},
                config=config,
                version="v2",
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                elif event["event"] == "on_tool_start":
                    yield f"data: {json.dumps({'tool': event['name'], 'status': 'started'})}\n\n"
                
                elif event["event"] == "on_tool_end":
                    yield f"data: {json.dumps({'tool': event['name'], 'status': 'completed'})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

## Error Handling

### OpenRouter-Specific Errors

```python
from enum import Enum
from typing import Optional
import httpx

class OpenRouterError(Exception):
    """Base exception for OpenRouter errors."""
    pass

class OpenRouterErrorCode(str, Enum):
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_CREDITS = "insufficient_credits"
    MODEL_UNAVAILABLE = "model_unavailable"
    PROVIDER_ERROR = "provider_error"
    CONTEXT_LENGTH = "context_length_exceeded"
    CONTENT_FILTERED = "content_filtered"

def parse_openrouter_error(error: Exception) -> tuple[OpenRouterErrorCode, str]:
    """Parse OpenRouter error response."""
    error_str = str(error).lower()
    
    if "rate limit" in error_str or "429" in error_str:
        return OpenRouterErrorCode.RATE_LIMITED, "Rate limited. Retry after delay."
    
    if "insufficient" in error_str or "credits" in error_str:
        return OpenRouterErrorCode.INSUFFICIENT_CREDITS, "Insufficient credits."
    
    if "model" in error_str and ("unavailable" in error_str or "not found" in error_str):
        return OpenRouterErrorCode.MODEL_UNAVAILABLE, "Model unavailable."
    
    if "context" in error_str or "token" in error_str:
        return OpenRouterErrorCode.CONTEXT_LENGTH, "Context length exceeded."
    
    if "content" in error_str and "filter" in error_str:
        return OpenRouterErrorCode.CONTENT_FILTERED, "Content filtered."
    
    return OpenRouterErrorCode.PROVIDER_ERROR, str(error)
```

### Retry Middleware with Backoff

```python
from langchain.agents.middleware import AgentMiddleware
import asyncio
import random
from typing import Callable

class RetryMiddleware(AgentMiddleware):
    """Retry with exponential backoff for transient errors."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retry_on: tuple = (Exception,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_on = retry_on
    
    def _calculate_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay
    
    def modify_model_request(self, request):
        """Wrap model call with retry logic."""
        original_handler = request._handler
        
        async def retry_handler(req):
            last_error = None
            for attempt in range(self.max_retries + 1):
                try:
                    return await original_handler(req)
                except self.retry_on as e:
                    last_error = e
                    error_code, _ = parse_openrouter_error(e)
                    
                    # Don't retry non-transient errors
                    if error_code in [
                        OpenRouterErrorCode.INSUFFICIENT_CREDITS,
                        OpenRouterErrorCode.CONTENT_FILTERED,
                    ]:
                        raise
                    
                    if attempt < self.max_retries:
                        delay = self._calculate_delay(attempt)
                        await asyncio.sleep(delay)
            
            raise last_error
        
        request._handler = retry_handler
        return request
```

### Fallback Model Middleware

```python
class FallbackMiddleware(AgentMiddleware):
    """Fall back to alternative models on failure."""
    
    def __init__(self, fallback_models: list[str]):
        self.fallback_models = fallback_models
    
    def modify_model_request(self, request):
        original_handler = request._handler
        
        async def fallback_handler(req):
            # Try primary model
            try:
                return await original_handler(req)
            except Exception as primary_error:
                # Try fallbacks
                for fallback_model in self.fallback_models:
                    try:
                        fallback_llm = ChatOpenRouter(model=fallback_model)
                        req = req.override(model=fallback_llm)
                        return await original_handler(req)
                    except Exception:
                        continue
                
                raise primary_error
        
        request._handler = fallback_handler
        return request
```

## Checkpointing for Production

### PostgreSQL Checkpointer

```python
from langgraph.checkpoint.postgres import PostgresSaver
from src.config import settings

def get_checkpointer():
    """Get production checkpointer."""
    if settings.database_url:
        return PostgresSaver.from_conn_string(settings.database_url)
    
    # Fallback to in-memory for development
    from langgraph.checkpoint.memory import InMemorySaver
    return InMemorySaver()
```

### Redis for Distributed State

```python
from langgraph.checkpoint.redis import RedisSaver
import redis

def get_distributed_checkpointer():
    """Get Redis checkpointer for distributed deployments."""
    if not settings.redis_url:
        raise ValueError("REDIS_URL required for distributed deployment")
    
    return RedisSaver.from_url(settings.redis_url)
```

## Complete Agent Setup

### agents/supervisor.py

```python
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from src.config import settings
from src.middleware.logging import LoggingMiddleware
from src.middleware.cost_tracking import CostTrackingMiddleware
from src.tools import web_search, code_executor

# Global workflow instance
_workflow = None

def create_workflow():
    """Create and configure the agent workflow."""
    global _workflow
    
    # Base LLM configuration
    base_config = {
        "api_key": settings.openrouter_api_key,
        "app_url": settings.openrouter_app_url,
        "app_name": settings.openrouter_app_name,
    }
    
    # Middleware stack
    middleware = [
        LoggingMiddleware(),
        CostTrackingMiddleware(),
    ]
    
    # Create specialized agents
    researcher = create_agent(
        model=ChatOpenRouter(model="anthropic/claude-sonnet-4", **base_config),
        tools=[web_search],
        name="researcher",
        system_prompt="Research specialist. Find accurate information.",
        middleware=middleware,
    )
    
    coder = create_agent(
        model=ChatOpenRouter(model="openai/gpt-4o", **base_config),
        tools=[code_executor],
        name="coder",
        system_prompt="Coding specialist. Write clean, efficient code.",
        middleware=middleware,
    )
    
    # Create supervisor
    supervisor_llm = ChatOpenRouter(
        model="anthropic/claude-sonnet-4",
        temperature=0.3,
        **base_config,
    )
    
    workflow = create_supervisor(
        agents=[researcher, coder],
        model=supervisor_llm,
        prompt="Route research tasks to researcher, coding tasks to coder.",
    )
    
    # Compile with checkpointing
    checkpointer = get_checkpointer()
    _workflow = workflow.compile(checkpointer=checkpointer)
    
    return _workflow

def get_workflow():
    """Get the workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = create_workflow()
    return _workflow
```

## Testing

### conftest.py

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    llm = MagicMock()
    llm.invoke = MagicMock(return_value=MagicMock(content="Test response"))
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="Test response"))
    return llm

@pytest.fixture
def mock_openrouter_response():
    """Mock successful OpenRouter response."""
    return {
        "id": "gen-123",
        "choices": [{"message": {"content": "Hello!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    from langchain_core.tools import tool
    
    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    @tool
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}!"
    
    return [add, greet]
```

### test_agents.py

```python
import pytest
from src.agents.supervisor import create_workflow

class TestAgentWorkflow:
    
    @pytest.mark.asyncio
    async def test_basic_invocation(self, mock_llm):
        """Test basic agent invocation."""
        # Setup with mock
        workflow = create_workflow()
        
        result = await workflow.ainvoke({
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        assert "messages" in result
        assert len(result["messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_routing_to_researcher(self, mock_llm):
        """Test that research queries route to researcher."""
        workflow = create_workflow()
        
        result = await workflow.ainvoke({
            "messages": [{"role": "user", "content": "Research AI trends"}]
        })
        
        # Check researcher was called
        # (Actual implementation depends on tracing)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        import asyncio
        
        workflow = create_workflow()
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                workflow.ainvoke({"messages": [...]}),
                timeout=0.001,  # Very short timeout
            )
```

### test_tools.py

```python
import pytest
from src.tools import web_search, code_executor

class TestTools:
    
    def test_tool_schema(self, sample_tools):
        """Test tool schemas are valid."""
        for tool in sample_tools:
            assert tool.name
            assert tool.description
            assert tool.args_schema
    
    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Test async tool execution."""
        from langchain_core.tools import tool
        
        @tool
        async def async_add(a: int, b: int) -> int:
            """Add asynchronously."""
            return a + b
        
        result = await async_add.ainvoke({"a": 1, "b": 2})
        assert result == 3
```

## Deployment Checklist

### Pre-deployment

- [ ] Set all environment variables
- [ ] Configure production checkpointer (PostgreSQL/Redis)
- [ ] Enable LangSmith tracing
- [ ] Set appropriate log level
- [ ] Configure CORS for production domains
- [ ] Set up health check monitoring
- [ ] Configure rate limiting

### Security

- [ ] Rotate API keys regularly
- [ ] Use secrets manager for credentials
- [ ] Enable ZDR for sensitive data
- [ ] Implement input validation
- [ ] Set up PII middleware

### Performance

- [ ] Use connection pooling for database
- [ ] Configure appropriate timeouts
- [ ] Set up caching where applicable
- [ ] Monitor token usage and costs

## Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- LangSmith Dashboard: https://smith.langchain.com
- LangSmith Docs: https://docs.smith.langchain.com
- Persistence/Checkpointing: https://docs.langchain.com/oss/python/langgraph/persistence
- Memory Guide: https://docs.langchain.com/oss/python/langgraph/add-memory
- OpenRouter Status: https://status.openrouter.ai
