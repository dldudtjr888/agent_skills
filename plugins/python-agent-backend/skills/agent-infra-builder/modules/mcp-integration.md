# MCP Integration

MCP 서버를 통합하고 관리하는 가이드.
서버 풀, 도구 디스커버리, 라이프사이클 관리, OpenAI Agents SDK 연동 전문.

## Core Responsibilities

1. **Server Pool Management** - MCP 서버 풀 관리 (싱글톤, 네임스페이스)
2. **Lifecycle Management** - 서버 시작, 워밍, 헬스체크, 종료
3. **Tool Discovery** - 도구 목록 조회 및 로드
4. **Agent Integration** - OpenAI Agents SDK와 연동
5. **Error Recovery** - 서버 장애 복구

---

## MCP 개요

### Model Context Protocol

MCP는 LLM 에이전트가 외부 도구(DB, API, 파일시스템 등)와 통신하는 표준 프로토콜.

```
Agent ←→ MCP Server ←→ External Resource
         (stdio/sse)     (MySQL, API, etc.)
```

### 핵심 컴포넌트

```python
# OpenAI Agents SDK의 MCP 지원
from agents.mcp import MCPServerStdio, MCPServerSse

# Stdio 기반 (로컬 프로세스)
server = MCPServerStdio(
    name="mysql",
    params={
        "command": sys.executable,
        "args": ["-m", "mcp_servers.mysql"],
        "env": {"DB_HOST": "localhost"},
    },
)

# SSE 기반 (원격 서버)
server = MCPServerSse(
    name="remote_api",
    params={
        "url": "http://localhost:8080/sse",
        "headers": {"Authorization": "Bearer token"},
    },
)
```

---

## MCP 서버 풀

### MCPServerPool 구현

```python
import asyncio
import sys
from typing import Dict, Optional, Any

try:
    from agents.mcp import MCPServerStdio
    MCP_AVAILABLE = True
except ImportError:
    MCPServerStdio = None
    MCP_AVAILABLE = False


class MCPServerPool:
    """네임스페이스 인식 MCP 서버 풀

    Features:
    - 네임스페이스 격리 (멀티테넌트)
    - 서버 사전 워밍 (cold start 제거)
    - 헬스체크 및 자동 복구
    - 그레이스풀 셧다운

    Usage:
        await MCPServerPool.register_config("mysql", {...})
        await MCPServerPool.warmup(["mysql"])
        server = await MCPServerPool.get("mysql")
        await MCPServerPool.shutdown()
    """

    _instances: Dict[str, "MCPServerPool"] = {}
    _lock = asyncio.Lock()

    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self._servers: Dict[str, Any] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._contexts: Dict[str, Any] = {}
        self._healthy: Dict[str, bool] = {}
        self._initialized = False
        self._enabled = MCP_AVAILABLE

    @classmethod
    async def _get_instance(cls, namespace: str = "default") -> "MCPServerPool":
        """네임스페이스별 싱글톤 인스턴스"""
        if namespace not in cls._instances:
            async with cls._lock:
                if namespace not in cls._instances:
                    cls._instances[namespace] = MCPServerPool(namespace)
        return cls._instances[namespace]

    @classmethod
    async def register_config(
        cls,
        name: str,
        config: Dict[str, Any],
        namespace: str = "default",
    ) -> None:
        """MCP 서버 설정 등록"""
        instance = await cls._get_instance(namespace)
        instance._configs[name] = config

    @classmethod
    async def warmup(
        cls,
        server_names: list[str],
        namespace: str = "default",
    ) -> Dict[str, bool]:
        """서버 사전 워밍 (cold start 제거)"""
        instance = await cls._get_instance(namespace)

        if not MCP_AVAILABLE:
            return {name: False for name in server_names}

        results = {}

        for name in server_names:
            if name not in instance._configs:
                results[name] = False
                continue

            try:
                if name in instance._servers:
                    await cls._cleanup_server(instance, name)

                config = instance._configs[name]

                server = MCPServerStdio(
                    name=f"pool-{name}",
                    params={
                        "command": config.get("command", sys.executable),
                        "args": config.get("args", []),
                        "env": config.get("env", {}),
                    },
                    client_session_timeout_seconds=config.get("timeout", 300),
                )

                context = await server.__aenter__()

                instance._servers[name] = server
                instance._contexts[name] = context
                instance._healthy[name] = True
                results[name] = True

            except Exception as e:
                instance._healthy[name] = False
                results[name] = False

        instance._initialized = True
        return results

    @classmethod
    async def get(
        cls,
        name: str,
        namespace: str = "default",
    ) -> Optional[Any]:
        """워밍된 서버 획득"""
        if not MCP_AVAILABLE:
            return None

        instance = await cls._get_instance(namespace)

        if name not in instance._servers:
            return None

        if not instance._healthy.get(name, False):
            try:
                await cls._recover_server(instance, name)
            except Exception:
                return None

        return instance._servers.get(name)

    @classmethod
    async def _cleanup_server(cls, instance: "MCPServerPool", name: str) -> None:
        """서버 정리"""
        if name in instance._servers:
            try:
                await instance._servers[name].__aexit__(None, None, None)
            except Exception:
                pass
            instance._servers.pop(name, None)
            instance._contexts.pop(name, None)
            instance._healthy.pop(name, None)

    @classmethod
    async def _recover_server(cls, instance: "MCPServerPool", name: str) -> None:
        """서버 복구"""
        await cls._cleanup_server(instance, name)

        config = instance._configs[name]
        server = MCPServerStdio(
            name=f"pool-{name}",
            params={
                "command": config.get("command", sys.executable),
                "args": config.get("args", []),
                "env": config.get("env", {}),
            },
            client_session_timeout_seconds=config.get("timeout", 300),
        )

        context = await server.__aenter__()
        instance._servers[name] = server
        instance._contexts[name] = context
        instance._healthy[name] = True

    @classmethod
    async def shutdown(cls, namespace: Optional[str] = None) -> None:
        """그레이스풀 셧다운"""
        namespaces = [namespace] if namespace else list(cls._instances.keys())

        for ns in namespaces:
            if ns not in cls._instances:
                continue

            instance = cls._instances[ns]

            for name, server in instance._servers.items():
                try:
                    await server.__aexit__(None, None, None)
                except Exception:
                    pass

            instance._servers.clear()
            instance._contexts.clear()
            instance._healthy.clear()
            instance._initialized = False

            if namespace:
                del cls._instances[ns]

    @classmethod
    async def get_stats(cls, namespace: str = "default") -> Dict[str, Any]:
        """풀 통계"""
        instance = await cls._get_instance(namespace)
        return {
            "namespace": namespace,
            "registered_servers": list(instance._configs.keys()),
            "active_servers": list(instance._servers.keys()),
            "health_status": dict(instance._healthy),
            "initialized": instance._initialized,
        }
```

---

## 도구 디스커버리

### 서버에서 도구 목록 조회

```python
async def discover_tools(server) -> list[dict]:
    """MCP 서버에서 도구 목록 조회"""
    tools = await server.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }
        for tool in tools
    ]


# 사용 예시
server = await MCPServerPool.get("mysql")
if server:
    tools = await discover_tools(server)
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")
```

### 도구 호출

```python
async def call_tool(server, tool_name: str, arguments: dict) -> Any:
    """MCP 도구 호출"""
    result = await server.call_tool(tool_name, arguments)
    return result.content


# 사용 예시
result = await call_tool(
    server,
    "execute_query",
    {"query": "SELECT * FROM users LIMIT 10"},
)
```

---

## Agent 통합

### OpenAI Agents SDK 연동

```python
from agents import Agent, Runner

async def create_mysql_agent():
    """MCP 서버와 연동된 에이전트 생성"""

    mysql_server = await MCPServerPool.get("mysql")
    if not mysql_server:
        raise RuntimeError("MySQL MCP server not available")

    agent = Agent(
        name="mysql_agent",
        instructions="You are a MySQL database assistant.",
        model="gpt-4o",
        mcp_servers=[mysql_server],
    )

    return agent


async def run_query(query: str):
    """에이전트를 통한 쿼리 실행"""
    agent = await create_mysql_agent()

    result = await Runner.run(
        agent,
        input=f"Execute this query and explain the results: {query}",
    )

    return result.final_output
```

### 다중 MCP 서버

```python
async def create_multi_server_agent():
    """여러 MCP 서버와 연동된 에이전트"""

    mysql_server = await MCPServerPool.get("mysql")
    search_server = await MCPServerPool.get("web_search")

    servers = [s for s in [mysql_server, search_server] if s]

    return Agent(
        name="research_agent",
        instructions="Use database and web search to answer questions.",
        mcp_servers=servers,
    )
```

---

## 설정 관리

### YAML 기반 설정

```yaml
# config/mcp_servers.yaml
servers:
  mysql:
    command: python
    args:
      - -m
      - mcp_servers.mysql
    env:
      DB_HOST: ${DB_HOST}
      DB_PORT: ${DB_PORT}
      DB_NAME: ${DB_NAME}
    timeout: 300

  web_search:
    command: python
    args:
      - -m
      - mcp_servers.search
    env:
      SEARCH_API_KEY: ${SEARCH_API_KEY}
    timeout: 60
```

### 설정 로더

```python
import yaml
import os
from pathlib import Path

def load_mcp_config(config_path: str = "config/mcp_servers.yaml") -> dict:
    """MCP 설정 로드 (환경 변수 치환)"""

    with open(config_path) as f:
        config = yaml.safe_load(f)

    def substitute_env(obj):
        if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.environ.get(env_var, "")
        elif isinstance(obj, dict):
            return {k: substitute_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [substitute_env(item) for item in obj]
        return obj

    return substitute_env(config)


async def initialize_mcp_pool(config_path: str = "config/mcp_servers.yaml"):
    """설정 파일로 MCP 풀 초기화"""
    config = load_mcp_config(config_path)

    for name, server_config in config.get("servers", {}).items():
        await MCPServerPool.register_config(name, server_config)

    server_names = list(config.get("servers", {}).keys())
    results = await MCPServerPool.warmup(server_names)

    return results
```

---

## 라이프사이클 통합

### FastAPI 연동

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클"""

    # Startup: MCP 풀 초기화
    results = await initialize_mcp_pool()
    print(f"MCP servers initialized: {results}")

    yield

    # Shutdown: MCP 풀 정리
    await MCPServerPool.shutdown()
    print("MCP servers shut down")


app = FastAPI(lifespan=lifespan)


@app.get("/mcp/stats")
async def mcp_stats():
    """MCP 풀 상태 조회"""
    return await MCPServerPool.get_stats()


@app.post("/mcp/warmup/{server_name}")
async def warmup_server(server_name: str):
    """특정 서버 워밍"""
    results = await MCPServerPool.warmup([server_name])
    return results
```

---

## 검증 체크리스트

| 항목 | 확인 |
|------|------|
| 서버 풀 싱글톤 | 네임스페이스별 격리 |
| 워밍 | cold start 제거 |
| 헬스체크 | 자동 복구 |
| 그레이스풀 셧다운 | 리소스 정리 |
| 환경 변수 | 설정 치환 |
| SDK 옵션 | 없어도 동작 |

**Remember**: 풀에서 획득한 서버는 직접 close하지 마세요. 풀이 라이프사이클을 관리합니다.
