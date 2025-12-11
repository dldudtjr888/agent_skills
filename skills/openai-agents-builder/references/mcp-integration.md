# MCP Integration

Connect Model Context Protocol servers to your agents.

## Overview

MCP allows agents to access external tools through standardized servers:
- Filesystem operations
- Web fetching
- Database queries
- IDE integrations
- Custom tool servers

## Server Types

### 1. Stdio Servers (Local)

```python
from agents import Agent
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
    }
) as server:
    agent = Agent(
        name="File Agent",
        mcp_servers=[server],
    )
    
    result = await Runner.run(agent, "List files in the directory")
```

### 2. SSE Servers (Remote)

```python
from agents.mcp import MCPServerSse

async with MCPServerSse(
    name="Remote Server",
    params={
        "url": "https://api.example.com/mcp/sse",
        "headers": {"Authorization": "Bearer token"},
    },
    cache_tools_list=True,
) as server:
    agent = Agent(
        name="API Agent",
        mcp_servers=[server],
    )
```

### 3. Hosted MCP (OpenAI)

```python
from agents.hosted_tools import HostedMCPTool

agent = Agent(
    name="Git Agent",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "github",
                "server_url": "https://mcp.github.com/api",
            }
        )
    ],
)
```

## Tool Filtering

```python
# Allow-list
async with MCPServerStdio(
    params={...},
    allowed_tool_names=["read_file", "write_file"],
) as server:
    pass

# Block-list
async with MCPServerStdio(
    params={...},
    blocked_tool_names=["delete_file"],
) as server:
    pass

# Custom filter
async def filter_tools(context, tool) -> bool:
    if context.agent.name == "ReadOnly":
        return "read" in tool.name.lower()
    return True

async with MCPServerStdio(
    params={...},
    tool_filter=filter_tools,
) as server:
    pass
```

## Tool Approval

```python
from agents import MCPToolApprovalRequest, MCPToolApprovalFunctionResult

def approve_tool(request: MCPToolApprovalRequest) -> MCPToolApprovalFunctionResult:
    if request.data.name in SAFE_TOOLS:
        return {"approve": True}
    return {"approve": False, "reason": "Requires human approval"}

agent = Agent(
    name="Cautious Agent",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_url": "...",
                "require_approval": "always",
            },
            on_approval_request=approve_tool,
        )
    ],
)
```

## Common MCP Servers

```bash
# Filesystem
npx -y @modelcontextprotocol/server-filesystem /path

# Web fetch
npx -y @modelcontextprotocol/server-fetch

# GitHub
npx -y @modelcontextprotocol/server-github

# PostgreSQL
npx -y @modelcontextprotocol/server-postgres
```

## Resources

- [MCP Documentation](https://openai.github.io/openai-agents-python/mcp/)
- [MCP Specification](https://modelcontextprotocol.io)
