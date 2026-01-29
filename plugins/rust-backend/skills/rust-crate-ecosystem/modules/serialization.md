# Serialization

serde 심화 및 커스텀 직렬화 패턴.

## 기본 Derive

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub name: String,
    #[serde(rename = "emailAddress")]
    pub email: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub phone: Option<String>,
    #[serde(default)]
    pub active: bool,
}
```

## 필드 속성

```rust
#[derive(Serialize, Deserialize)]
pub struct Config {
    // 이름 변경
    #[serde(rename = "apiKey")]
    pub api_key: String,

    // 기본값
    #[serde(default = "default_timeout")]
    pub timeout: u64,

    // 조건부 스킵
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,

    // 직렬화 전용
    #[serde(skip_deserializing)]
    pub computed: String,

    // 역직렬화 전용
    #[serde(skip_serializing)]
    pub secret: String,

    // flatten
    #[serde(flatten)]
    pub extra: HashMap<String, Value>,
}

fn default_timeout() -> u64 {
    30
}
```

## 커스텀 직렬화

```rust
use serde::{Deserializer, Serializer};

#[derive(Debug)]
pub struct Money {
    pub cents: i64,
}

impl Serialize for Money {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        // cents를 달러 문자열로
        let dollars = self.cents as f64 / 100.0;
        serializer.serialize_str(&format!("${:.2}", dollars))
    }
}

impl<'de> Deserialize<'de> for Money {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        let s = s.trim_start_matches('$');
        let dollars: f64 = s.parse().map_err(serde::de::Error::custom)?;
        Ok(Money { cents: (dollars * 100.0) as i64 })
    }
}
```

## serialize_with / deserialize_with

```rust
mod date_format {
    use chrono::{DateTime, Utc, TimeZone};
    use serde::{self, Deserialize, Deserializer, Serializer};

    const FORMAT: &str = "%Y-%m-%d %H:%M:%S";

    pub fn serialize<S>(date: &DateTime<Utc>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&date.format(FORMAT).to_string())
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<DateTime<Utc>, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Utc.datetime_from_str(&s, FORMAT)
            .map_err(serde::de::Error::custom)
    }
}

#[derive(Serialize, Deserialize)]
pub struct Event {
    pub name: String,
    #[serde(with = "date_format")]
    pub timestamp: DateTime<Utc>,
}
```

## Enum 직렬화

```rust
#[derive(Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Message {
    #[serde(rename = "text")]
    Text { content: String },
    #[serde(rename = "image")]
    Image { url: String, width: u32, height: u32 },
}
// {"type": "text", "content": "Hello"}

#[derive(Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum Response {
    Success(Data),
    Error(String),
}
// {"type": "Success", "data": {...}}

#[derive(Serialize, Deserialize)]
#[serde(untagged)]
pub enum Value {
    Int(i64),
    Float(f64),
    String(String),
}
// 태그 없이 값 자체로 구분
```

## 제네릭 타입

```rust
#[derive(Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

#[derive(Serialize, Deserialize)]
#[serde(bound = "T: Serialize + for<'de> Deserialize<'de>")]
pub struct Paginated<T> {
    pub items: Vec<T>,
    pub total: i64,
    pub page: i64,
}
```

## 포맷별 설정

```rust
// JSON (pretty)
let json = serde_json::to_string_pretty(&data)?;

// JSON (compact)
let json = serde_json::to_string(&data)?;

// TOML
let toml = toml::to_string(&config)?;

// YAML
let yaml = serde_yaml::to_string(&config)?;

// MessagePack (바이너리)
let bytes = rmp_serde::to_vec(&data)?;

// 역직렬화
let data: User = serde_json::from_str(&json)?;
let config: Config = toml::from_str(&toml_str)?;
```

## 성능 최적화

```rust
// 제로 카피 역직렬화
#[derive(Deserialize)]
pub struct LogEntry<'a> {
    #[serde(borrow)]
    pub message: &'a str,
    pub level: &'a str,
}

// Cow for optional ownership
use std::borrow::Cow;

#[derive(Deserialize)]
pub struct Config<'a> {
    #[serde(borrow)]
    pub name: Cow<'a, str>,
}
```

## 체크리스트

- [ ] 필드 명명 규칙 통일 (camelCase, snake_case)
- [ ] Option 필드 skip_serializing_if 설정
- [ ] 적절한 기본값 정의
- [ ] 커스텀 직렬화 필요 여부 확인
- [ ] Enum 태그 전략 선택
- [ ] 성능 최적화 (borrow, Cow)
