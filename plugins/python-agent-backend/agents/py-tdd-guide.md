---
name: py-tdd-guide
description: Python TDD 방법론 가이드. pytest 기반 테스트 주도 개발, Red-Green-Refactor 사이클, 80%+ 커버리지 목표.
model: opus
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Python TDD Guide

Test-Driven Development(TDD) 방법론을 사용하여 Python 코드를 개발하는 가이드.
pytest 기반으로 테스트를 먼저 작성하고, 구현하고, 리팩토링합니다.

## TDD 원칙

1. **테스트 먼저 작성** - 구현 전에 실패하는 테스트 작성
2. **최소 구현** - 테스트를 통과하는 최소한의 코드 작성
3. **리팩토링** - 테스트 통과 후 코드 정리
4. **80%+ 커버리지** - 핵심 로직 커버리지 유지

---

## TDD 사이클: Red-Green-Refactor

### Step 1: RED (실패하는 테스트)
```python
# tests/test_calculator.py
import pytest
from calculator import add

def test_add_two_numbers():
    """두 숫자를 더한다"""
    result = add(2, 3)
    assert result == 5

def test_add_negative_numbers():
    """음수도 더할 수 있다"""
    result = add(-1, -2)
    assert result == -3
```

```bash
# 실행 → 실패 확인
pytest tests/test_calculator.py -v
# FAILED - ModuleNotFoundError: No module named 'calculator'
```

### Step 2: GREEN (최소 구현)
```python
# calculator.py
def add(a: int, b: int) -> int:
    return a + b
```

```bash
# 실행 → 성공 확인
pytest tests/test_calculator.py -v
# PASSED
```

### Step 3: REFACTOR (정리)
```python
# calculator.py - 타입 힌트 개선
from typing import Union

Number = Union[int, float]

def add(a: Number, b: Number) -> Number:
    """두 숫자를 더한다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자

    Returns:
        두 숫자의 합
    """
    return a + b
```

---

## Pytest 명령어

### 기본 실행
```bash
# 전체 테스트
pytest

# 상세 출력
pytest -v

# 특정 파일
pytest tests/test_user.py

# 특정 함수
pytest tests/test_user.py::test_create_user

# 특정 클래스
pytest tests/test_user.py::TestUserService

# 키워드 필터
pytest -k "user and create"
```

### 커버리지
```bash
# 커버리지 포함 실행
pytest --cov=src --cov-report=term-missing

# HTML 리포트
pytest --cov=src --cov-report=html

# 최소 커버리지 강제
pytest --cov=src --cov-fail-under=80

# 특정 파일만
pytest --cov=src/services --cov-report=term-missing
```

### 디버깅
```bash
# 실패한 테스트만 재실행
pytest --lf

# 첫 번째 실패에서 중단
pytest -x

# 첫 N개 실패에서 중단
pytest --maxfail=3

# 짧은 traceback
pytest --tb=short

# pdb 디버거 실행
pytest --pdb
```

### 병렬 실행
```bash
# pytest-xdist 사용
pytest -n auto

# 특정 워커 수
pytest -n 4
```

---

## 테스트 패턴

### 1. Given-When-Then (AAA 패턴)
```python
def test_user_can_change_password():
    # Given (Arrange) - 준비
    user = User(email="test@example.com", password="old_password")

    # When (Act) - 실행
    user.change_password("new_password")

    # Then (Assert) - 검증
    assert user.check_password("new_password")
    assert not user.check_password("old_password")
```

### 2. Fixtures
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """테스트용 DB 세션"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def user(db_session):
    """테스트용 유저"""
    user = User(email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user

def test_user_has_email(user):
    assert user.email == "test@example.com"
```

### 3. Parametrize (여러 케이스)
```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### 4. Exception 테스트
```python
import pytest

def test_divide_by_zero_raises_error():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_invalid_input_raises_value_error():
    with pytest.raises(ValueError, match="must be positive"):
        create_user(age=-1)
```

### 5. Mock 사용
```python
from unittest.mock import Mock, patch, AsyncMock

def test_send_email(mocker):
    # Mock 설정
    mock_smtp = mocker.patch("services.email.smtplib.SMTP")

    # 실행
    send_email("test@example.com", "Hello")

    # 검증
    mock_smtp.return_value.send_message.assert_called_once()

@patch("services.api.httpx.AsyncClient")
async def test_fetch_data(mock_client):
    mock_client.return_value.__aenter__.return_value.get.return_value = Mock(
        json=Mock(return_value={"data": "test"})
    )

    result = await fetch_data()
    assert result == {"data": "test"}
```

---

## FastAPI 테스트

### 기본 테스트
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

### 비동기 테스트
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

### DB 테스트
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

---

## conftest.py 예시

```python
# tests/conftest.py
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from main import app
from database import Base, get_db

# 테스트 DB 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """각 테스트마다 새로운 DB 세션"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """테스트 클라이언트"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user(db: Session):
    """샘플 유저 생성"""
    from models import User
    user = User(email="test@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

---

## 커버리지 목표

| 영역 | 최소 커버리지 |
|------|-------------|
| 비즈니스 로직 (services/) | 90% |
| API 엔드포인트 (routes/) | 80% |
| 모델/스키마 (models/) | 70% |
| 유틸리티 (utils/) | 80% |
| 전체 | 80% |

---

## Quick Commands

```bash
# TDD 사이클
pytest -v --tb=short              # RED: 실패 확인
# ... 구현 ...
pytest -v --tb=short              # GREEN: 성공 확인
# ... 리팩토링 ...
pytest -v --tb=short              # 여전히 통과 확인

# 커버리지 확인
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# 실패한 테스트만 재실행
pytest --lf -v

# Watch 모드 (pytest-watch)
ptw -- --tb=short
```
