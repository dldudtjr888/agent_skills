# hibye-plugins

Production-ready plugins for Claude Code - skills, agents, and hooks for development workflows.

**Version**: 2.0.0

## Quick Start

### 1. Add Marketplace

```bash
/plugin marketplace add hibye-ys/hibye-plugins
```

### 2. Install Plugins

```bash
# 공통 워크플로우 (태스크 계획/분해/실행, 문서 관리)
/plugin install common-dev-workflow@hibye-plugins

# 웹 프론트엔드 (React, TypeScript, Next.js)
/plugin install web-frontend@hibye-plugins

# 파이썬 에이전트 백엔드 (FastAPI, LangGraph, Pydantic AI)
/plugin install python-agent-backend@hibye-plugins

# 러스트 백엔드 (Rust 패턴)
/plugin install rust-backend@hibye-plugins

# 유니티 게임 개발 (맵 빌더, 기획)
/plugin install unity-gamedev@hibye-plugins

# 개발 훅 (PreToolUse, Stop)
/plugin install dev-hooks@hibye-plugins
```

## Available Plugins

### common-dev-workflow

공통 개발 워크플로우: 태스크 계획/분해/실행, 문서 관리, 코드 분석

| Type | Name | Description |
|------|------|-------------|
| Skill | task-planner | 요구사항 구체화 및 계획 문서 작성 |
| Skill | task-decomposer | 계획을 실행 가능한 태스크로 분해 |
| Skill | task-executor | 태스크 순차 실행, 에이전트 위임 |
| Skill | project-docs-manager | 프로젝트 문서 관리 |
| Skill | code-refactoring-analysis | 5차원 코드 리팩토링 분석 |
| Skill | sql-production-analyzer | SQL 쿼리 및 프로덕션 분석 |
| Skill | claude-code-pattern-catalog | Claude Code 패턴 카탈로그 |
| Agent | architect, analyst, explore... | 10개 공통 에이전트 |

### web-frontend

웹 프론트엔드 개발: React, TypeScript, Next.js

| Type | Name | Description |
|------|------|-------------|
| Skill | frontend-coding-standards | TypeScript/React 코딩 표준 |
| Agent | code-reviewer | 코드 리뷰 |
| Agent | build-error-resolver | 빌드 에러 해결 |
| Agent | e2e-runner | E2E 테스트 실행 |
| Agent | ... | 총 13개 에이전트 |

### python-agent-backend

파이썬 에이전트 백엔드: FastAPI, LangGraph, Pydantic AI, OpenAI Agents SDK

| Type | Name | Description |
|------|------|-------------|
| Skill | pydantic-ai-builder | Pydantic AI 에이전트 빌더 |
| Skill | langgraph-builder | LangGraph 워크플로우 빌더 |
| Skill | agents-sdk-builder | OpenAI Agents SDK 빌더 |
| Skill | deep-agents-builder | LangChain Deep Agents 빌더 |
| Skill | langchain-openrouter | LangChain + OpenRouter |
| Skill | python-agent-backend-patterns | FastAPI 백엔드 패턴 |
| Skill | google-adk-builder | Google ADK 에이전트 빌더 |
| Agent | py-error-resolver, py-langgraph-builder... | 총 15개 에이전트 |

### rust-backend

러스트 백엔드: Rust 패턴, 시스템 프로그래밍

| Type | Name | Description |
|------|------|-------------|
| Skill | rust-patterns | Rust 개발 패턴 및 베스트 프랙티스 |

### unity-gamedev

유니티 게임 개발: 맵 빌더, 게임 기획, 프로토타입

| Type | Name | Description |
|------|------|-------------|
| Skill | unity-map-builder | ProBuilder 기반 맵 자동 생성 |
| Skill | unity-planning | 게임 기획 문서 작성 |
| Skill | unity-prototype | 프로토타입 구현 |
| Skill | unity-task-decomposer | 기획 → 태스크 분해 |

### dev-hooks

개발 훅: 코드 수정 전 컨텍스트 수집, 작업 완료 전 검증

| Hook | Event | Description |
|------|-------|-------------|
| PreToolUse | Write/Edit 전 | 파일 읽기 확인, 유사 구현 검색 |
| Stop | 작업 완료 전 | 테스트 실행, 타입 검사 |

## Rules (수동 복사)

플러그인과 별도로, 프로젝트별 규칙 파일을 제공합니다.

```bash
# 파이썬 에이전트 프로젝트
cp -r rules/python_agent_rules/ your-project/.claude/rules/

# 웹 프론트엔드 프로젝트
cp -r rules/web_frontend_rules/ your-project/.claude/rules/

# 러스트 프로젝트
cp -r rules/rust_backend_rules/ your-project/.claude/rules/

# 유니티 프로젝트
cp -r rules/unity_rules/ your-project/.claude/rules/
```

## Project Structure

```
hibye-plugins/
├── plugins/
│   ├── common-dev-workflow/    # 7 skills, 10 agents
│   ├── web-frontend/           # 1 skill, 13 agents
│   ├── python-agent-backend/   # 7 skills, 15 agents
│   ├── rust-backend/           # 1 skill
│   ├── unity-gamedev/          # 4 skills
│   └── dev-hooks/              # hooks
├── rules/                      # 프로젝트별 규칙 (수동 복사)
├── docs/                       # 문서
└── ref_datas/                  # 참조 데이터
```

## Contributing

1. Fork this repository
2. Create your plugin in `plugins/your-plugin-name/`
3. Add `.claude-plugin/plugin.json` with proper configuration
4. Update `.claude-plugin/marketplace.json`
5. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Resources

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins.md)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces.md)
