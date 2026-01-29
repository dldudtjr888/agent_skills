# Test Patterns

> 메인 스킬: `../SKILL.md`

## 1. Given-When-Then (AAA 패턴)

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

## 2. Fixtures

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

## 3. Parametrize (여러 케이스)

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

## 4. Exception 테스트

```python
import pytest

def test_divide_by_zero_raises_error():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_invalid_input_raises_value_error():
    with pytest.raises(ValueError, match="must be positive"):
        create_user(age=-1)
```

## 5. Mock 사용

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

## conftest.py 템플릿

```python
# tests/conftest.py
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from main import app
from database import Base, get_db

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
