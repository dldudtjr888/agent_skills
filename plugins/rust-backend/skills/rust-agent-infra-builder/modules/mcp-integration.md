# MCP Integration

Model Context Protocol (MCP) 서버 연동 패턴.

## MCP 개요

MCP(Model Context Protocol)는 LLM과 외부 도구/리소스를 연결하는 표준 프로토콜입니다.

```
┌─────────────────┐     JSON-RPC     ┌─────────────────┐
│   LLM Agent     │ ←────────────→  │   MCP Server    │
│                 │     (stdio)      │                 │
│  - Tool calls   │                  │  - Tools        │
│  - Resources    │                  │  - Resources    │
│  - Prompts      │                  │  - Prompts      │
└─────────────────┘                  └─────────────────┘
```

## MCP 클라이언트

### 기본 클라이언트

```rust
use tokio::process::{Command, Child};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader, BufWriter};
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub struct McpClient {
    child: Child,
    stdin: BufWriter<tokio::process::ChildStdin>,
    stdout: BufReader<tokio::process::ChildStdout>,
    request_id: u64,
}

#[derive(Debug, Serialize)]
struct JsonRpcRequest {
    jsonrpc: &'static str,
    id: u64,
    method: String,
    params: Option<Value>,
}

#[derive(Debug, Deserialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    id: u64,
    result: Option<Value>,
    error: Option<JsonRpcError>,
}

#[derive(Debug, Deserialize)]
struct JsonRpcError {
    code: i32,
    message: String,
    data: Option<Value>,
}

impl McpClient {
    pub async fn spawn(command: &str, args: &[&str]) -> anyhow::Result<Self> {
        let mut child = Command::new(command)
            .args(args)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::inherit())
            .spawn()?;

        let stdin = BufWriter::new(child.stdin.take().unwrap());
        let stdout = BufReader::new(child.stdout.take().unwrap());

        let mut client = Self {
            child,
            stdin,
            stdout,
            request_id: 0,
        };

        // 초기화
        client.initialize().await?;

        Ok(client)
    }

    async fn send_request(&mut self, method: &str, params: Option<Value>) -> anyhow::Result<Value> {
        self.request_id += 1;

        let request = JsonRpcRequest {
            jsonrpc: "2.0",
            id: self.request_id,
            method: method.to_string(),
            params,
        };

        let request_str = serde_json::to_string(&request)?;
        self.stdin.write_all(request_str.as_bytes()).await?;
        self.stdin.write_all(b"\n").await?;
        self.stdin.flush().await?;

        let mut response_str = String::new();
        self.stdout.read_line(&mut response_str).await?;

        let response: JsonRpcResponse = serde_json::from_str(&response_str)?;

        if let Some(error) = response.error {
            anyhow::bail!("MCP error {}: {}", error.code, error.message);
        }

        Ok(response.result.unwrap_or(Value::Null))
    }

    async fn initialize(&mut self) -> anyhow::Result<()> {
        let params = serde_json::json!({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": { "listChanged": true },
                "sampling": {}
            },
            "clientInfo": {
                "name": "rust-mcp-client",
                "version": "1.0.0"
            }
        });

        self.send_request("initialize", Some(params)).await?;
        self.send_request("initialized", None).await?;

        Ok(())
    }
}
```

### 도구 디스커버리

```rust
#[derive(Debug, Deserialize)]
pub struct ToolInfo {
    pub name: String,
    pub description: Option<String>,
    pub input_schema: Value,
}

impl McpClient {
    pub async fn list_tools(&mut self) -> anyhow::Result<Vec<ToolInfo>> {
        let result = self.send_request("tools/list", None).await?;

        let tools: Vec<ToolInfo> = serde_json::from_value(result["tools"].clone())?;
        Ok(tools)
    }

    pub async fn call_tool(&mut self, name: &str, arguments: Value) -> anyhow::Result<Value> {
        let params = serde_json::json!({
            "name": name,
            "arguments": arguments
        });

        let result = self.send_request("tools/call", Some(params)).await?;
        Ok(result)
    }
}
```

### 리소스 접근

```rust
#[derive(Debug, Deserialize)]
pub struct ResourceInfo {
    pub uri: String,
    pub name: String,
    pub description: Option<String>,
    pub mime_type: Option<String>,
}

impl McpClient {
    pub async fn list_resources(&mut self) -> anyhow::Result<Vec<ResourceInfo>> {
        let result = self.send_request("resources/list", None).await?;

        let resources: Vec<ResourceInfo> = serde_json::from_value(result["resources"].clone())?;
        Ok(resources)
    }

    pub async fn read_resource(&mut self, uri: &str) -> anyhow::Result<Value> {
        let params = serde_json::json!({
            "uri": uri
        });

        let result = self.send_request("resources/read", Some(params)).await?;
        Ok(result)
    }
}
```

## MCP 서버 풀

```rust
use std::collections::HashMap;
use tokio::sync::RwLock;

pub struct McpServerPool {
    servers: RwLock<HashMap<String, McpClient>>,
}

impl McpServerPool {
    pub fn new() -> Self {
        Self {
            servers: RwLock::new(HashMap::new()),
        }
    }

    pub async fn add_server(
        &self,
        name: &str,
        command: &str,
        args: &[&str],
    ) -> anyhow::Result<()> {
        let client = McpClient::spawn(command, args).await?;

        let mut servers = self.servers.write().await;
        servers.insert(name.to_string(), client);

        Ok(())
    }

    pub async fn get_all_tools(&self) -> anyhow::Result<Vec<(String, ToolInfo)>> {
        let mut all_tools = Vec::new();

        let mut servers = self.servers.write().await;
        for (server_name, client) in servers.iter_mut() {
            let tools = client.list_tools().await?;
            for tool in tools {
                all_tools.push((server_name.clone(), tool));
            }
        }

        Ok(all_tools)
    }

    pub async fn call_tool(
        &self,
        server_name: &str,
        tool_name: &str,
        arguments: Value,
    ) -> anyhow::Result<Value> {
        let mut servers = self.servers.write().await;
        let client = servers.get_mut(server_name)
            .ok_or_else(|| anyhow::anyhow!("Server not found: {}", server_name))?;

        client.call_tool(tool_name, arguments).await
    }
}
```

## 에이전트 연동

### Rig + MCP

```rust
use rig::tool::{Tool, ToolDescription};

pub struct McpToolWrapper {
    pool: Arc<McpServerPool>,
    server_name: String,
    tool_info: ToolInfo,
}

impl Tool for McpToolWrapper {
    const NAME: &'static str = "mcp_tool";

    type Input = Value;
    type Output = Value;
    type Error = anyhow::Error;

    fn description(&self) -> ToolDescription {
        ToolDescription {
            name: self.tool_info.name.clone(),
            description: self.tool_info.description.clone().unwrap_or_default(),
            parameters: self.tool_info.input_schema.clone(),
        }
    }

    async fn call(&self, input: Self::Input) -> Result<Self::Output, Self::Error> {
        self.pool
            .call_tool(&self.server_name, &self.tool_info.name, input)
            .await
    }
}

// 에이전트에 MCP 도구 등록
async fn create_agent_with_mcp(
    client: &openai::Client,
    pool: Arc<McpServerPool>,
) -> anyhow::Result<impl Agent> {
    let all_tools = pool.get_all_tools().await?;

    let mut agent_builder = client.agent("gpt-4o");

    for (server_name, tool_info) in all_tools {
        let wrapper = McpToolWrapper {
            pool: pool.clone(),
            server_name,
            tool_info,
        };
        // agent_builder = agent_builder.tool(wrapper);
    }

    Ok(agent_builder.build())
}
```

## 일반적인 MCP 서버

### 파일 시스템

```rust
// 파일 시스템 MCP 서버 시작
pool.add_server(
    "filesystem",
    "npx",
    &["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
).await?;
```

### GitHub

```rust
// GitHub MCP 서버 시작
pool.add_server(
    "github",
    "npx",
    &["-y", "@modelcontextprotocol/server-github"],
).await?;
```

### 데이터베이스

```rust
// PostgreSQL MCP 서버 시작
pool.add_server(
    "postgres",
    "npx",
    &["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"],
).await?;
```

## 에러 처리

```rust
impl McpClient {
    pub async fn call_tool_safe(&mut self, name: &str, arguments: Value) -> Result<Value, McpError> {
        match self.call_tool(name, arguments).await {
            Ok(result) => Ok(result),
            Err(e) => {
                let error_str = e.to_string();

                if error_str.contains("Tool not found") {
                    Err(McpError::ToolNotFound(name.to_string()))
                } else if error_str.contains("Invalid arguments") {
                    Err(McpError::InvalidArguments(error_str))
                } else if error_str.contains("timeout") {
                    Err(McpError::Timeout)
                } else {
                    Err(McpError::Internal(error_str))
                }
            }
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum McpError {
    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    #[error("Invalid arguments: {0}")]
    InvalidArguments(String),

    #[error("Request timeout")]
    Timeout,

    #[error("Internal error: {0}")]
    Internal(String),
}
```

## 체크리스트

- [ ] MCP 클라이언트 구현
- [ ] JSON-RPC 통신
- [ ] 도구 디스커버리
- [ ] 리소스 접근
- [ ] 서버 풀 관리
- [ ] 에러 처리 및 재연결
- [ ] 타임아웃 설정
- [ ] 에이전트 연동
