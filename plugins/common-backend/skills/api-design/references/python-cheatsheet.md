# Python API Cheatsheet

## FastAPI

### Basic Setup
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(title="My API", version="1.0.0")

class User(BaseModel):
    id: int
    email: str
    name: str | None = None

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Query Parameters
```python
@app.get("/users")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None
):
    return await db.get_users(page, per_page, status)
```

### Request Body
```python
class CreateUser(BaseModel):
    email: str
    password: str
    name: str | None = None

@app.post("/users", status_code=201)
async def create_user(user: CreateUser):
    return await db.create_user(user)
```

### Authentication
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/users/me")
async def read_me(user: User = Depends(get_current_user)):
    return user
```

### Versioning
```python
from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")

app.include_router(v1_router)
app.include_router(v2_router)
```

---

## Flask

### Basic Setup
```python
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = db.get_user(user_id)
    if not user:
        abort(404)
    return jsonify(user)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = db.create_user(data)
    return jsonify(user), 201
```

---

## Strawberry (GraphQL)

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class User:
    id: int
    email: str
    name: str | None

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, id: int) -> User | None:
        return await db.get_user(id)

schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```
