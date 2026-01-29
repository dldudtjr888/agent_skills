# Python (pytest) Cheatsheet

## pytest 기본 명령어

```bash
# 전체 테스트
pytest

# 상세 출력
pytest -v

# 특정 파일
pytest tests/test_user.py

# 특정 함수
pytest tests/test_user.py::test_create_user

# 키워드 필터
pytest -k "user and create"

# 마커 필터
pytest -m "slow"

# 첫 실패에서 중단
pytest -x

# 실패한 테스트만 재실행
pytest --lf

# 디버거 실행
pytest --pdb
```

## 커버리지

```bash
# 기본 커버리지
pytest --cov=src

# 누락 라인 표시
pytest --cov=src --cov-report=term-missing

# 최소 커버리지 강제
pytest --cov=src --cov-fail-under=80

# HTML 리포트
pytest --cov=src --cov-report=html
```

## 기본 테스트 구조

```python
import pytest

def test_add():
    # Arrange
    a, b = 2, 3

    # Act
    result = add(a, b)

    # Assert
    assert result == 5

class TestUser:
    def test_create(self):
        user = User("test@example.com")
        assert user.email == "test@example.com"
```

## Fixtures

```python
@pytest.fixture
def user():
    return User(email="test@example.com")

@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.close()

def test_with_fixtures(user, db_session):
    db_session.add(user)
    assert user.id is not None
```

## Parametrize

```python
@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

## 예외 테스트

```python
def test_raises_error():
    with pytest.raises(ValueError):
        divide(10, 0)

def test_raises_with_message():
    with pytest.raises(ValueError, match="must be positive"):
        create_user(age=-1)
```

## Mock

```python
from unittest.mock import Mock, patch

def test_with_mock(mocker):
    mock_api = mocker.patch("services.external_api")
    mock_api.return_value = {"data": "test"}

    result = fetch_data()

    mock_api.assert_called_once()
    assert result == {"data": "test"}

@patch("services.email.send")
def test_send_email(mock_send):
    send_notification("test@example.com")
    mock_send.assert_called_with("test@example.com")
```

## Async 테스트

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_fetch()
    assert result is not None
```

## conftest.py

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def db():
    """세션 범위 DB fixture"""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture(autouse=True)
def reset_db(db):
    """매 테스트마다 DB 리셋"""
    db.execute("DELETE FROM users")
```

## 마커

```python
@pytest.mark.slow
def test_slow_operation():
    ...

@pytest.mark.skip(reason="not implemented")
def test_future_feature():
    ...

@pytest.mark.skipif(sys.version_info < (3, 10), reason="3.10+ only")
def test_new_syntax():
    ...
```
