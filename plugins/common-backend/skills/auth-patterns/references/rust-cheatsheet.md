# Rust Auth Cheatsheet

## jsonwebtoken

### Cargo.toml
```toml
[dependencies]
jsonwebtoken = "9"
serde = { version = "1", features = ["derive"] }
chrono = "0.4"
```

### Create Token
```rust
use jsonwebtoken::{encode, Header, EncodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
    iat: usize,
    iss: String,
}

fn create_token(user_id: &str, secret: &[u8]) -> Result<String, jsonwebtoken::errors::Error> {
    let now = Utc::now();
    let claims = Claims {
        sub: user_id.to_owned(),
        iat: now.timestamp() as usize,
        exp: (now + Duration::minutes(15)).timestamp() as usize,
        iss: "myapp".to_owned(),
    };

    encode(&Header::default(), &claims, &EncodingKey::from_secret(secret))
}
```

### Verify Token
```rust
use jsonwebtoken::{decode, Validation, DecodingKey};

fn verify_token(token: &str, secret: &[u8]) -> Result<Claims, jsonwebtoken::errors::Error> {
    let mut validation = Validation::default();
    validation.set_issuer(&["myapp"]);

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret),
        &validation
    )?;

    Ok(token_data.claims)
}
```

### RS256 (Asymmetric)
```rust
// 서명 (private key)
let token = encode(
    &Header::new(Algorithm::RS256),
    &claims,
    &EncodingKey::from_rsa_pem(private_key)?
)?;

// 검증 (public key)
let token_data = decode::<Claims>(
    &token,
    &DecodingKey::from_rsa_pem(public_key)?,
    &Validation::new(Algorithm::RS256)
)?;
```

---

## oauth2-rs

### Cargo.toml
```toml
[dependencies]
oauth2 = "4"
reqwest = { version = "0.11", features = ["json"] }
```

### OAuth2 Client
```rust
use oauth2::{
    AuthorizationCode, AuthUrl, ClientId, ClientSecret,
    CsrfToken, PkceCodeChallenge, RedirectUrl, Scope, TokenUrl,
    basic::BasicClient,
};

fn create_client() -> BasicClient {
    BasicClient::new(
        ClientId::new("client_id".to_string()),
        Some(ClientSecret::new("client_secret".to_string())),
        AuthUrl::new("https://auth.example.com/authorize".to_string()).unwrap(),
        Some(TokenUrl::new("https://auth.example.com/token".to_string()).unwrap())
    )
    .set_redirect_uri(RedirectUrl::new("http://localhost:8080/callback".to_string()).unwrap())
}

// Authorization URL 생성 (PKCE)
let (pkce_challenge, pkce_verifier) = PkceCodeChallenge::new_random_sha256();
let (auth_url, csrf_token) = client
    .authorize_url(CsrfToken::new_random)
    .add_scope(Scope::new("openid".to_string()))
    .set_pkce_challenge(pkce_challenge)
    .url();

// Token 교환
let token_result = client
    .exchange_code(AuthorizationCode::new(code))
    .set_pkce_verifier(pkce_verifier)
    .request_async(oauth2::reqwest::async_http_client)
    .await?;
```

---

## Password Hashing (argon2)

```toml
[dependencies]
argon2 = "0.5"
```

```rust
use argon2::{
    password_hash::{rand_core::OsRng, PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};

fn hash_password(password: &str) -> Result<String, argon2::password_hash::Error> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    let hash = argon2.hash_password(password.as_bytes(), &salt)?;
    Ok(hash.to_string())
}

fn verify_password(password: &str, hash: &str) -> bool {
    let parsed_hash = PasswordHash::new(hash).ok();
    parsed_hash
        .map(|h| Argon2::default().verify_password(password.as_bytes(), &h).is_ok())
        .unwrap_or(false)
}
```

---

## Axum Middleware

```rust
use axum::{
    extract::State,
    http::{Request, StatusCode},
    middleware::Next,
    response::Response,
};

async fn auth_middleware<B>(
    State(secret): State<String>,
    mut request: Request<B>,
    next: Next<B>,
) -> Result<Response, StatusCode> {
    let token = request
        .headers()
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .and_then(|h| h.strip_prefix("Bearer "))
        .ok_or(StatusCode::UNAUTHORIZED)?;

    let claims = verify_token(token, secret.as_bytes())
        .map_err(|_| StatusCode::UNAUTHORIZED)?;

    request.extensions_mut().insert(claims);
    Ok(next.run(request).await)
}
```

---

## Quick Reference

| Task | Crate | Example |
|------|-------|---------|
| JWT Create | jsonwebtoken | `encode(&Header::default(), &claims, &key)` |
| JWT Verify | jsonwebtoken | `decode::<Claims>(token, &key, &validation)` |
| Password Hash | argon2 | `argon2.hash_password(password, &salt)` |
| OAuth2 Client | oauth2 | `BasicClient::new(...)` |
| Random Token | rand | `rand::thread_rng().gen::<[u8; 32]>()` |
