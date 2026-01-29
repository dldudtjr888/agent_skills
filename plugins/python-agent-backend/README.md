# python-agent-backend

파이썬 에이전트 백엔드: FastAPI, LangGraph, Pydantic AI, OpenAI Agents SDK

## Skills

| Skill | Description |
|-------|-------------|
| pydantic-ai-builder | Pydantic AI 에이전트 빌더 |
| langgraph-builder | LangGraph 워크플로우 빌더 |
| agents-sdk-builder | OpenAI Agents SDK 빌더 |
| deep-agents-builder | LangChain Deep Agents 빌더 |
| langchain-openrouter | LangChain + OpenRouter |
| google-adk-builder | Google ADK 에이전트 빌더 |
| agent-infra-builder | 에이전트 인프라 (Guardrails, MCP, Memory, Prompts) |
| python-agent-backend-pattern | FastAPI 백엔드 패턴 |

## Agents

| Agent | Description |
|-------|-------------|
| python-diff-reviewer | 파이썬 Diff 코드 리뷰 |
| python-fastapi-architect | FastAPI 아키텍처 설계 |
| python-agent-builder | 에이전트 빌더 |
| python-agent-infra-builder | 에이전트 인프라 빌더 |
| python-refactor-cleaner | 코드 정리/클린업 |
| python-refactor-master | 고급 리팩토링 |
| python-route-tester | 라우팅 테스트 |
| python-route-debugger | 라우팅 디버깅 |

## Hooks

| Hook | Trigger | Description |
|------|---------|-------------|
| protect-sensitive | PreToolUse | 민감 파일 보호 |
| python-lint | PostToolUse | Python 린팅 |
| suggest-agent | PostToolUse | 에이전트 제안 |

## Usage

```bash
/plugin install python-agent-backend@hibye-plugins

# common-dev-workflow와 함께 사용 권장
/plugin install common-dev-workflow@hibye-plugins
```
