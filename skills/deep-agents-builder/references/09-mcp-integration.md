# MCP 도구 통합

> **최종 업데이트**: 2026-01-23 (deepagents 0.3.8)

Deep Agents에서 **Model Context Protocol (MCP)** 도구를 사용하는 방법입니다.

---

## 개요

MCP는 Anthropic이 개발한 도구 통합 프로토콜입니다. `langchain-mcp-adapters`를 사용하여 MCP 도구를 Deep Agents에 연결할 수 있습니다.

### 장점

- MCP 서버의 도구를 자동 발견
- 여러 MCP 서버 동시 연결
- LangChain 도구로 자동 변환
- 별도 래퍼 코드 불필요

---

## 설치

```bash
pip install langchain-mcp-adapters
pip install deepagents
```

---

## 기본 사용

### 단일 MCP 서버 연결

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from deepagents import create_deep_agent

async def main():
    # MCP 서버 연결
    server_params = StdioServerParameters(
        command="python",
        args=["path/to/mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # MCP 도구를 LangChain 도구로 변환
            mcp_tools = await load_mcp_tools(session)

            # Deep Agent에 도구 추가
            agent = create_deep_agent(
                tools=mcp_tools,
                system_prompt="You have access to MCP tools."
            )

            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": "Use the tools"}]
            })

asyncio.run(main())
```

---

## 다중 MCP 서버 연결

### MultiServerMCPClient

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

async def main():
    # 여러 MCP 서버 설정
    client = MultiServerMCPClient({
        "filesystem": {
            "transport": "stdio",
            "command": "python",
            "args": ["servers/filesystem_server.py"]
        },
        "database": {
            "transport": "http",
            "url": "http://localhost:8080/mcp",
            "headers": {"Authorization": "Bearer TOKEN"}
        },
        "web_search": {
            "transport": "streamable_http",
            "url": "http://localhost:8081/mcp"
        }
    })

    # 모든 서버에서 도구 로드
    tools = await client.get_tools()

    # Deep Agent 생성
    agent = create_deep_agent(
        tools=tools,
        system_prompt="You have access to filesystem, database, and web search tools."
    )

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Search the web and save results"}]
    })

asyncio.run(main())
```

---

## Transport 옵션

| Transport | 용도 | 특징 |
|-----------|------|------|
| `stdio` | 로컬 개발 | 프로세스 직접 통신 |
| `http` | 원격 서버 | 표준 HTTP |
| `streamable_http` | 장시간 작업 | Stateless HTTP, 스트리밍 지원 |

### stdio 설정

```python
{
    "server_name": {
        "transport": "stdio",
        "command": "python",
        "args": ["server.py"],
        "env": {"API_KEY": "..."}  # 환경변수 전달
    }
}
```

### HTTP 설정

```python
{
    "server_name": {
        "transport": "http",
        "url": "http://localhost:8080/mcp",
        "headers": {
            "Authorization": "Bearer TOKEN",
            "X-Custom-Header": "value"
        }
    }
}
```

---

## 비동기 Deep Agent

MCP 도구는 비동기이므로 `async_create_deep_agent`를 사용합니다:

```python
from deepagents import async_create_deep_agent

async def main():
    client = MultiServerMCPClient({...})
    tools = await client.get_tools()

    # 비동기 버전 사용
    agent = await async_create_deep_agent(
        tools=tools,
        system_prompt="..."
    )

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "..."}]
    })
```

---

## LangGraph StateGraph 통합

MCP 도구를 LangGraph StateGraph와 함께 사용:

```python
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient

async def create_agent_graph():
    client = MultiServerMCPClient({...})
    tools = await client.get_tools()

    # ToolNode로 자동 라우팅
    tool_node = ToolNode(tools)

    workflow = StateGraph(...)
    workflow.add_node("tools", tool_node)
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", "end": "__end__"}
    )

    return workflow.compile()
```

---

## MCP 서버 예시

### FastMCP 서버 생성

```python
# servers/my_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool()
def search_database(query: str) -> str:
    """Search the database for records."""
    # 구현
    return f"Results for: {query}"

@mcp.tool()
def save_file(path: str, content: str) -> str:
    """Save content to a file."""
    # 구현
    return f"Saved to: {path}"

if __name__ == "__main__":
    mcp.run()
```

### 연결

```python
client = MultiServerMCPClient({
    "my_server": {
        "transport": "stdio",
        "command": "python",
        "args": ["servers/my_server.py"]
    }
})
```

---

## 런타임 헤더

HTTP/SSE transport에서 런타임 헤더 전달:

```python
client = MultiServerMCPClient({
    "api_server": {
        "transport": "http",
        "url": "http://api.example.com/mcp"
    }
})

# 런타임에 헤더 추가
tools = await client.get_tools(
    headers={
        "Authorization": f"Bearer {get_current_token()}",
        "X-Request-ID": generate_request_id()
    }
)
```

---

## 프로덕션 배포

### LangGraph API Server

```python
# graph.py
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

async def make_graph():
    client = MultiServerMCPClient({
        "tools": {
            "transport": "http",  # stdio는 서버 환경에서 제한적
            "url": "http://mcp-tools-service/mcp"
        }
    })
    tools = await client.get_tools()

    return create_deep_agent(tools=tools)
```

```json
// langgraph.json
{
    "graphs": {
        "agent": "graph:make_graph"
    }
}
```

> **주의**: `stdio` transport는 서버 환경에서 제한적입니다. 프로덕션에서는 `http` 또는 `streamable_http`를 사용하세요.

---

## 참고 자료

- [langchain-mcp-adapters GitHub](https://github.com/langchain-ai/langchain-mcp-adapters)
- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [DeepMCPAgent](https://github.com/cryxnet/DeepMCPAgent)
