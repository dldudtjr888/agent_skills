# FastAPI & Multi-Agent Testing

> 메인 스킬: `../SKILL.md`

## FastAPI 기본 테스트

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "secret"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

## 비동기 테스트

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/async-data")
    assert response.status_code == 200
```

## DB 의존성 오버라이드

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

def test_create_item(test_db):
    response = client.post("/items/", json={"name": "Test"})
    assert response.status_code == 201
```

---

## Multi-Agent 테스트

### Agent 테스트

```python
import pytest
from agents import MyAgent
from openai import AsyncOpenAI

@pytest.fixture
def mock_openai(mocker):
    mock = mocker.patch("agents.AsyncOpenAI")
    mock.return_value.chat.completions.create = AsyncMock(
        return_value=Mock(choices=[Mock(message=Mock(content="response"))])
    )
    return mock

@pytest.mark.asyncio
async def test_agent_responds(mock_openai):
    agent = MyAgent()
    response = await agent.run("Hello")
    assert response is not None

@pytest.mark.asyncio
async def test_agent_uses_tool(mock_openai, mocker):
    tool_mock = mocker.patch("agents.tools.search")
    tool_mock.return_value = "search result"

    agent = MyAgent()
    await agent.run("search for python")

    tool_mock.assert_called_once()
```

### Tool 테스트

```python
def test_search_tool():
    result = search_tool(query="python tutorial")
    assert "results" in result
    assert len(result["results"]) > 0

def test_calculator_tool():
    result = calculator_tool(expression="2 + 2")
    assert result == 4

def test_tool_validation():
    with pytest.raises(ValueError, match="query is required"):
        search_tool(query="")
```
