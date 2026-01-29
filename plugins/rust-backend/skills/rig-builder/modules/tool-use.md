# Tool Use

Rig 에이전트의 도구 사용 패턴.

## Tool Trait 구현

### 기본 도구 정의

```rust
use rig::tool::{Tool, ToolDescription};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct WeatherInput {
    city: String,
    unit: Option<String>,
}

#[derive(Serialize)]
struct WeatherOutput {
    temperature: f64,
    unit: String,
    description: String,
}

struct WeatherTool {
    api_key: String,
}

impl Tool for WeatherTool {
    const NAME: &'static str = "get_weather";

    type Input = WeatherInput;
    type Output = WeatherOutput;
    type Error = anyhow::Error;

    fn description(&self) -> ToolDescription {
        ToolDescription {
            name: Self::NAME.into(),
            description: "Get current weather for a city".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius"
                    }
                },
                "required": ["city"]
            }),
        }
    }

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        // API 호출 로직
        let unit = input.unit.unwrap_or_else(|| "celsius".into());

        // 실제로는 외부 API 호출
        Ok(WeatherOutput {
            temperature: 22.5,
            unit,
            description: "Partly cloudy".into(),
        })
    }
}
```

### 여러 도구 등록

```rust
let agent = client
    .agent("gpt-4o")
    .preamble("You have access to various tools to help answer questions.")
    .tool(WeatherTool::new())
    .tool(CalculatorTool)
    .tool(WebSearchTool::new())
    .build();
```

## 도구 패턴

### 데이터베이스 쿼리 도구

```rust
use sqlx::PgPool;

struct DbQueryTool {
    pool: PgPool,
}

#[derive(Deserialize)]
struct DbQueryInput {
    table: String,
    filter: Option<String>,
    limit: Option<i32>,
}

#[derive(Serialize)]
struct DbQueryOutput {
    rows: Vec<serde_json::Value>,
    count: usize,
}

impl Tool for DbQueryTool {
    const NAME: &'static str = "query_database";

    type Input = DbQueryInput;
    type Output = DbQueryOutput;
    type Error = anyhow::Error;

    fn description(&self) -> ToolDescription {
        ToolDescription {
            name: Self::NAME.into(),
            description: "Query the database for information".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["users", "products", "orders"]
                    },
                    "filter": {
                        "type": "string",
                        "description": "SQL WHERE clause (sanitized)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "maximum": 100
                    }
                },
                "required": ["table"]
            }),
        }
    }

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        let limit = input.limit.unwrap_or(10).min(100);

        // 안전한 쿼리 빌드 (SQL 인젝션 방지)
        let query = format!(
            "SELECT * FROM {} {} LIMIT {}",
            input.table,
            input.filter.map(|f| format!("WHERE {}", f)).unwrap_or_default(),
            limit
        );

        let rows: Vec<serde_json::Value> = sqlx::query_scalar(&query)
            .fetch_all(&self.pool)
            .await?;

        Ok(DbQueryOutput {
            count: rows.len(),
            rows,
        })
    }
}
```

### HTTP 요청 도구

```rust
use reqwest::Client;

struct HttpTool {
    client: Client,
}

#[derive(Deserialize)]
struct HttpInput {
    method: String,
    url: String,
    headers: Option<std::collections::HashMap<String, String>>,
    body: Option<String>,
}

#[derive(Serialize)]
struct HttpOutput {
    status: u16,
    body: String,
}

impl Tool for HttpTool {
    const NAME: &'static str = "http_request";

    type Input = HttpInput;
    type Output = HttpOutput;
    type Error = anyhow::Error;

    fn description(&self) -> ToolDescription {
        ToolDescription {
            name: Self::NAME.into(),
            description: "Make HTTP requests to external APIs".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"]
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL to request"
                    },
                    "headers": {
                        "type": "object",
                        "additionalProperties": { "type": "string" }
                    },
                    "body": {
                        "type": "string",
                        "description": "Request body (for POST/PUT)"
                    }
                },
                "required": ["method", "url"]
            }),
        }
    }

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        let mut request = match input.method.as_str() {
            "GET" => self.client.get(&input.url),
            "POST" => self.client.post(&input.url),
            "PUT" => self.client.put(&input.url),
            "DELETE" => self.client.delete(&input.url),
            _ => anyhow::bail!("Unsupported method"),
        };

        if let Some(headers) = input.headers {
            for (key, value) in headers {
                request = request.header(&key, &value);
            }
        }

        if let Some(body) = input.body {
            request = request.body(body);
        }

        let response = request.send().await?;
        let status = response.status().as_u16();
        let body = response.text().await?;

        Ok(HttpOutput { status, body })
    }
}
```

### 파일 시스템 도구

```rust
use std::path::PathBuf;

struct FileSystemTool {
    base_path: PathBuf,
}

#[derive(Deserialize)]
#[serde(tag = "action")]
enum FileSystemInput {
    #[serde(rename = "read")]
    Read { path: String },
    #[serde(rename = "write")]
    Write { path: String, content: String },
    #[serde(rename = "list")]
    List { path: String },
}

#[derive(Serialize)]
struct FileSystemOutput {
    success: bool,
    data: Option<String>,
    error: Option<String>,
}

impl Tool for FileSystemTool {
    const NAME: &'static str = "file_system";

    type Input = FileSystemInput;
    type Output = FileSystemOutput;
    type Error = anyhow::Error;

    fn description(&self) -> ToolDescription {
        ToolDescription {
            name: Self::NAME.into(),
            description: "Read, write, or list files".into(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "list"]
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative file path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write action)"
                    }
                },
                "required": ["action", "path"]
            }),
        }
    }

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        match input {
            FileSystemInput::Read { path } => {
                let full_path = self.base_path.join(&path);
                match tokio::fs::read_to_string(&full_path).await {
                    Ok(content) => Ok(FileSystemOutput {
                        success: true,
                        data: Some(content),
                        error: None,
                    }),
                    Err(e) => Ok(FileSystemOutput {
                        success: false,
                        data: None,
                        error: Some(e.to_string()),
                    }),
                }
            }
            FileSystemInput::Write { path, content } => {
                let full_path = self.base_path.join(&path);
                match tokio::fs::write(&full_path, &content).await {
                    Ok(()) => Ok(FileSystemOutput {
                        success: true,
                        data: None,
                        error: None,
                    }),
                    Err(e) => Ok(FileSystemOutput {
                        success: false,
                        data: None,
                        error: Some(e.to_string()),
                    }),
                }
            }
            FileSystemInput::List { path } => {
                let full_path = self.base_path.join(&path);
                match tokio::fs::read_dir(&full_path).await {
                    Ok(mut entries) => {
                        let mut files = Vec::new();
                        while let Some(entry) = entries.next_entry().await? {
                            files.push(entry.file_name().to_string_lossy().to_string());
                        }
                        Ok(FileSystemOutput {
                            success: true,
                            data: Some(files.join("\n")),
                            error: None,
                        })
                    }
                    Err(e) => Ok(FileSystemOutput {
                        success: false,
                        data: None,
                        error: Some(e.to_string()),
                    }),
                }
            }
        }
    }
}
```

## 도구 체이닝

### 순차 도구 사용

```rust
// 에이전트가 여러 도구를 순차적으로 호출
let agent = client
    .agent("gpt-4o")
    .preamble(r#"
        You can use multiple tools to complete a task.
        Think step by step and use tools as needed.
    "#)
    .tool(WebSearchTool::new())
    .tool(SummarizerTool)
    .tool(EmailTool::new())
    .build();

let response = agent
    .prompt("Search for the latest Rust news, summarize it, and email the summary to user@example.com")
    .await?;
```

## MCP 통합

```rust
use rig::mcp::{McpClient, McpTool};

// MCP 서버 연결
let mcp_client = McpClient::connect("stdio", "npx", &["-y", "@modelcontextprotocol/server-filesystem"]).await?;

// MCP 도구 가져오기
let tools = mcp_client.list_tools().await?;

// 에이전트에 MCP 도구 등록
let mut agent_builder = client.agent("gpt-4o");

for tool in tools {
    agent_builder = agent_builder.mcp_tool(mcp_client.clone(), tool);
}

let agent = agent_builder.build();
```

## 에러 처리

```rust
impl Tool for SafeTool {
    // ...

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        // 입력 검증
        if input.value.is_empty() {
            return Err(anyhow::anyhow!("Input value cannot be empty"));
        }

        // 타임아웃 적용
        let result = tokio::time::timeout(
            Duration::from_secs(30),
            self.do_work(input)
        )
        .await
        .map_err(|_| anyhow::anyhow!("Tool execution timed out"))??;

        Ok(result)
    }
}
```

## 체크리스트

- [ ] Tool trait 구현
- [ ] 입출력 타입 정의 (Serialize/Deserialize)
- [ ] JSON Schema 정확히 작성
- [ ] 에러 처리 구현
- [ ] 타임아웃 설정
- [ ] 입력 검증
- [ ] 보안 고려 (SQL 인젝션, 경로 탈출 등)
