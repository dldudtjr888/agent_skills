# Python Testing Guide

pytest 기반 Python 테스트 상세 가이드.

## pytest 설정

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: 느린 테스트
    integration: 통합 테스트
    unit: 단위 테스트
```

### pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: 느린 테스트",
    "integration: 통합 테스트",
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## conftest.py 패턴

### 기본 구조

```python
# tests/conftest.py
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app

# 테스트 DB 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """세션 범위 DB 엔진"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """각 테스트마다 새로운 DB 세션"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session):
    """FastAPI 테스트 클라이언트"""
    from fastapi.testclient import TestClient

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Factory Fixtures

```python
@pytest.fixture
def user_factory(db: Session):
    """유저 팩토리"""
    def create_user(
        email: str = "test@example.com",
        name: str = "Test User",
        is_active: bool = True,
    ) -> User:
        user = User(email=email, name=name, is_active=is_active)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return create_user


@pytest.fixture
def sample_user(user_factory):
    """기본 샘플 유저"""
    return user_factory()
```

## Fixtures 고급 패턴

### Scope 활용

```python
@pytest.fixture(scope="session")
def expensive_resource():
    """세션 동안 한 번만 생성"""
    resource = create_expensive_resource()
    yield resource
    resource.cleanup()


@pytest.fixture(scope="module")
def module_data():
    """모듈당 한 번 생성"""
    return {"shared": "data"}


@pytest.fixture(scope="function")  # 기본값
def fresh_data():
    """매 테스트마다 새로 생성"""
    return {"fresh": "data"}
```

### Autouse

```python
@pytest.fixture(autouse=True)
def reset_cache():
    """모든 테스트 전에 캐시 리셋"""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def mock_time(mocker):
    """모든 테스트에서 시간 고정"""
    mocker.patch("time.time", return_value=1234567890)
```

### Yield vs Return

```python
@pytest.fixture
def temp_file():
    """정리가 필요한 리소스"""
    path = Path("/tmp/test_file.txt")
    path.write_text("test content")

    yield path  # 테스트 실행

    # 테스트 후 정리
    if path.exists():
        path.unlink()
```

## Parametrize 패턴

### 기본 사용

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("Python", "PYTHON"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### 여러 매개변수

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### ID 지정

```python
@pytest.mark.parametrize("user_type,expected_role", [
    pytest.param("admin", "ADMIN", id="admin-user"),
    pytest.param("guest", "GUEST", id="guest-user"),
    pytest.param("member", "MEMBER", id="member-user"),
])
def test_user_role(user_type, expected_role):
    user = create_user(user_type)
    assert user.role == expected_role
```

### 중첩 Parametrize

```python
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    # 6개 테스트 케이스 생성: (1,10), (1,20), (2,10), (2,20), (3,10), (3,20)
    assert x * y == x * y
```

## Mock/Patch 패턴

### 기본 Mock

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    mock_service = Mock()
    mock_service.get_data.return_value = {"key": "value"}

    result = process_data(mock_service)

    mock_service.get_data.assert_called_once()
    assert result == {"key": "value"}
```

### Patch Decorator

```python
@patch("app.services.external_api.fetch")
def test_fetch_data(mock_fetch):
    mock_fetch.return_value = {"data": "mocked"}

    result = get_external_data()

    mock_fetch.assert_called_once_with("https://api.example.com")
    assert result == {"data": "mocked"}
```

### Patch Context Manager

```python
def test_with_context_manager():
    with patch("app.utils.get_current_time") as mock_time:
        mock_time.return_value = datetime(2024, 1, 1)

        result = create_timestamped_record()

        assert result.created_at == datetime(2024, 1, 1)
```

### pytest-mock (mocker fixture)

```python
def test_with_mocker(mocker):
    mock_send = mocker.patch("app.email.send_email")
    mock_send.return_value = True

    result = notify_user("test@example.com")

    mock_send.assert_called_once_with("test@example.com", mocker.ANY)
    assert result is True
```

### Async Mock

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function(mocker):
    mock_fetch = mocker.patch("app.api.fetch_data", new_callable=AsyncMock)
    mock_fetch.return_value = {"async": "data"}

    result = await process_async_data()

    mock_fetch.assert_awaited_once()
    assert result == {"async": "data"}
```

## FastAPI 테스트

### TestClient 기본

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.5}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data
```

### 의존성 오버라이드

```python
from app.dependencies import get_current_user, get_db

def test_protected_route(client, sample_user):
    # 인증 오버라이드
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = client.get("/protected")

    assert response.status_code == 200
    app.dependency_overrides.clear()


def test_with_mock_db(client):
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/items")

    assert response.status_code == 200
    app.dependency_overrides.clear()
```

### Async TestClient

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/async-endpoint")

    assert response.status_code == 200
```

### 파일 업로드 테스트

```python
def test_file_upload(client):
    files = {"file": ("test.txt", b"file content", "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"
```

## Async 테스트 (pytest-asyncio)

### 기본 설정

```python
# pytest.ini
[pytest]
asyncio_mode = auto

# 또는 pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Async 테스트

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_fetch_data()
    assert result is not None


@pytest.mark.asyncio
async def test_async_with_fixture(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
```

### Async Fixtures

```python
@pytest.fixture
async def async_db():
    """비동기 DB 세션"""
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture
async def async_client():
    """비동기 HTTP 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## 커버리지 설정

### 실행

```bash
# 기본 커버리지
pytest --cov=src

# 누락 라인 표시
pytest --cov=src --cov-report=term-missing

# HTML 리포트
pytest --cov=src --cov-report=html

# 최소 커버리지 강제
pytest --cov=src --cov-fail-under=80

# XML 리포트 (CI용)
pytest --cov=src --cov-report=xml
```

### .coveragerc

```ini
[run]
source = src
omit =
    tests/*
    */__init__.py
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

## 테스트 구조 권장

```
tests/
├── conftest.py           # 공통 fixtures
├── unit/                 # 단위 테스트
│   ├── conftest.py
│   ├── test_models.py
│   └── test_services.py
├── integration/          # 통합 테스트
│   ├── conftest.py
│   └── test_api.py
└── e2e/                  # E2E 테스트
    └── test_workflows.py
```

## 디버깅 팁

```bash
# 첫 실패에서 중단
pytest -x

# 마지막 실패 테스트만
pytest --lf

# 실패한 테스트 먼저
pytest --ff

# 디버거 진입
pytest --pdb

# 출력 보기
pytest -s

# 상세 출력
pytest -vv
```
