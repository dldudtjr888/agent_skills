# Rust API Cheatsheet

## Axum

### Basic Setup
```rust
use axum::{
    routing::{get, post},
    Router, Json, extract::{Path, Query, State},
    http::StatusCode,
};
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct User {
    id: i64,
    email: String,
    name: Option<String>,
}

async fn get_user(Path(id): Path<i64>) -> Result<Json<User>, StatusCode> {
    let user = db::get_user(id).await
        .ok_or(StatusCode::NOT_FOUND)?;
    Ok(Json(user))
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/users/:id", get(get_user))
        .route("/users", post(create_user));

    axum::Server::bind(&"0.0.0.0:3000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}
```

### Query Parameters
```rust
#[derive(Deserialize)]
struct ListParams {
    page: Option<i32>,
    per_page: Option<i32>,
}

async fn list_users(Query(params): Query<ListParams>) -> Json<Vec<User>> {
    let page = params.page.unwrap_or(1);
    let per_page = params.per_page.unwrap_or(20);
    Json(db::list_users(page, per_page).await)
}
```

### Request Body
```rust
#[derive(Deserialize)]
struct CreateUser {
    email: String,
    password: String,
    name: Option<String>,
}

async fn create_user(Json(payload): Json<CreateUser>) -> (StatusCode, Json<User>) {
    let user = db::create_user(payload).await;
    (StatusCode::CREATED, Json(user))
}
```

### Error Handling
```rust
use axum::response::IntoResponse;

enum AppError {
    NotFound,
    Unauthorized,
    Internal(anyhow::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, message) = match self {
            AppError::NotFound => (StatusCode::NOT_FOUND, "Not found"),
            AppError::Unauthorized => (StatusCode::UNAUTHORIZED, "Unauthorized"),
            AppError::Internal(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Internal error"),
        };
        (status, Json(json!({"error": message}))).into_response()
    }
}
```

---

## Actix-web

```rust
use actix_web::{web, App, HttpServer, HttpResponse};

async fn get_user(path: web::Path<i64>) -> HttpResponse {
    let id = path.into_inner();
    match db::get_user(id).await {
        Some(user) => HttpResponse::Ok().json(user),
        None => HttpResponse::NotFound().finish(),
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/users/{id}", web::get().to(get_user))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
```

---

## async-graphql

```rust
use async_graphql::{Object, Schema, EmptyMutation, EmptySubscription};

struct Query;

#[Object]
impl Query {
    async fn user(&self, id: i64) -> Option<User> {
        db::get_user(id).await
    }
}

type AppSchema = Schema<Query, EmptyMutation, EmptySubscription>;

// Axum integration
async fn graphql_handler(
    schema: Extension<AppSchema>,
    req: GraphQLRequest,
) -> GraphQLResponse {
    schema.execute(req.into_inner()).await.into()
}
```
