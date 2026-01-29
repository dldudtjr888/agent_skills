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
# 공통 워크플로우 (태스크 계획/분해/실행, TDD, 코드 분석)
/plugin install common-dev-workflow@hibye-plugins

# 공통 백엔드 패턴 (API 설계, 인증, DB, 캐싱, 배포)
/plugin install common-backend@hibye-plugins

# 웹 프론트엔드 (React, TypeScript, Next.js)
/plugin install web-frontend@hibye-plugins

# 파이썬 에이전트 백엔드 (FastAPI, LangGraph, Pydantic AI)
/plugin install python-agent-backend@hibye-plugins

# Vector/RAG 백엔드 (Qdrant, FalkorDB, RAG 패턴)
/plugin install vector-rag-backend@hibye-plugins

# 러스트 백엔드 (Rust 패턴)
/plugin install rust-backend@hibye-plugins

# 유니티 게임 개발 (맵 빌더, 기획)
/plugin install unity-gamedev@hibye-plugins

# 디자인 시스템 생성기 (Tailwind CSS 토큰)
/plugin install design-system-generator@hibye-plugins
```

## Available Plugins

### common-dev-workflow

공통 개발 워크플로우: 태스크 계획/분해/실행, TDD, 코드 분석

| Type | Name | Description |
|------|------|-------------|
| Skill | task-planner | 요구사항 구체화 및 계획 문서 작성 |
| Skill | task-decomposer | 계획을 실행 가능한 태스크로 분해 |
| Skill | task-executor | 태스크 순차 실행, 에이전트 위임 |
| Skill | tdd-fundamentals | TDD 핵심 원칙 + 언어별 테스트 가이드 (Python/TypeScript/Rust) |
| Skill | code-refactoring-analysis | 5차원 코드 리팩토링 분석 |
| Skill | sql-production-analyzer | SQL 쿼리 및 프로덕션 분석 |
| Skill | claude-code-pattern-catalog | Claude Code 패턴 카탈로그 |
| Agent | code-reviewer | 코드 리뷰, 품질 검토 |
| Agent | critic | 비판적 리뷰, 개선점 도출 |
| Agent | docs-researcher | 문서/자료 조사 |
| Agent | rule-validator | 규칙/컨벤션 검증 |
| Agent | scientist | 실험 설계, 가설 검증 |
| Agent | tradeoff-analyzer | 기술적 트레이드오프 분석 |
| Agent | doc-sync | 문서와 코드 불일치 감지 및 동기화 |

### common-backend

공통 백엔드 패턴: API 설계, 인증/인가, DB, 캐싱, 메시지큐, 배포, CI/CD, 관측성

| Type | Name | Description |
|------|------|-------------|
| Skill | api-design | REST/GraphQL API 설계 패턴 |
| Skill | auth-patterns | OAuth2, JWT, RBAC/ABAC 패턴 |
| Skill | database-design | 스키마 설계, 정규화, 인덱싱 |
| Skill | caching-strategies | 캐시 패턴, 무효화, TTL |
| Skill | message-queue-patterns | Pub/Sub, 이벤트 드리븐, Saga |
| Skill | deployment-patterns | Docker, K8s, 12-Factor |
| Skill | cicd-patterns | 파이프라인, 테스트/배포 전략 |
| Skill | observability | 로깅, 메트릭, 트레이싱 |
| Agent | api-design-reviewer, database-reviewer... | 5개 에이전트 |

### web-frontend

웹 프론트엔드 개발: React, TypeScript, Next.js

| Type | Name | Description |
|------|------|-------------|
| Skill | state-management | Zustand, Jotai, TanStack Query 패턴 |
| Skill | tailwind-styling | Tailwind CSS, CVA, cn() 가이드 |
| Skill | typescript-advanced | 고급 TypeScript 패턴 |
| Skill | testing-guide | React/Next.js 테스트 패턴 |
| Skill | frontend-security | XSS, CSRF, CSP 보안 |
| Agent | code-reviewer, designer, e2e-runner... | 9개 에이전트 |

### python-agent-backend

파이썬 에이전트 백엔드: FastAPI, LangGraph, Pydantic AI, OpenAI Agents SDK

| Type | Name | Description |
|------|------|-------------|
| Skill | pydantic-ai-builder | Pydantic AI 에이전트 빌더 |
| Skill | langgraph-builder | LangGraph 워크플로우 빌더 |
| Skill | agents-sdk-builder | OpenAI Agents SDK 빌더 |
| Skill | deep-agents-builder | LangChain Deep Agents 빌더 |
| Skill | langchain-openrouter | LangChain + OpenRouter |
| Skill | google-adk-builder | Google ADK 에이전트 빌더 |
| Skill | agent-infra-builder | 에이전트 인프라 (Guardrails, MCP, Memory) |
| Skill | python-agent-backend-pattern | FastAPI 백엔드 패턴 |
| Agent | python-diff-reviewer, python-fastapi-architect... | 8개 에이전트 |

### vector-rag-backend

Vector/RAG 백엔드: Qdrant, FalkorDB, RAG 패턴

| Type | Name | Description |
|------|------|-------------|
| Skill | qdrant-mastery | Qdrant 벡터 DB 마스터리 |
| Skill | falkordb-graphrag | FalkorDB GraphRAG |
| Skill | rag-patterns | RAG 아키텍처 패턴 |
| Skill | semantic-search | 시맨틱 검색 구현 |
| Agent | rag-system-builder, vector-db-architect... | 4개 에이전트 |

### rust-backend

러스트 백엔드: Rust 패턴, Axum, 비동기, 에이전트 프레임워크

| Type | Name | Description |
|------|------|-------------|
| Skill | rust-patterns | Rust 개발 패턴 및 베스트 프랙티스 |
| Skill | axum-backend-pattern | Axum 웹 프레임워크 패턴 |
| Skill | tokio-async-patterns | Tokio 비동기 프로그래밍 패턴 |
| Skill | rust-db-patterns | 데이터베이스 연동 패턴 (SQLx, SeaORM) |
| Skill | rust-testing-guide | Rust 테스트 가이드 |
| Skill | rust-error-handling | 에러 처리 패턴 |
| Skill | rust-crate-ecosystem | 크레이트 생태계 가이드 |
| Skill | rust-workspace-patterns | 워크스페이스 구성 패턴 |
| Skill | rig-builder | Rig 에이전트 프레임워크 빌더 |
| Skill | langchain-rust-builder | LangChain Rust 빌더 |
| Skill | rs-graph-llm-builder | RS Graph LLM 빌더 |
| Skill | rust-agent-infra-builder | Rust 에이전트 인프라 빌더 |
| Agent | rust-axum-architect | Axum 아키텍처 설계 |
| Agent | rust-diff-reviewer | 코드 리뷰어 |
| Agent | rust-refactor-master | 리팩토링 마스터 |
| Agent | rust-refactor-cleaner | 코드 정리 전문가 |
| Agent | rust-route-tester | 라우트 테스터 |
| Agent | rust-route-debugger | 라우트 디버거 |
| Agent | rust-crate-builder | 크레이트 빌더 |
| Agent | rust-perf-analyzer | 성능 분석가 |
| Agent | rust-agent-builder | 에이전트 빌더 |
| Agent | rust-agent-infra-builder | 에이전트 인프라 빌더 |

### unity-gamedev

유니티 게임 개발: 맵 빌더, 게임 기획, 프로토타입

| Type | Name | Description |
|------|------|-------------|
| Skill | unity-map-builder | ProBuilder 기반 맵 자동 생성 |
| Skill | unity-planning | 게임 기획 문서 작성 |
| Skill | unity-prototype | 프로토타입 구현 |
| Skill | unity-task-decomposer | 기획 → 태스크 분해 |

*에이전트 추후 확장 예정*

### design-system-generator

디자인 시스템 자동 생성: Tailwind CSS 토큰

| Type | Name | Description |
|------|------|-------------|
| Skill | tailwind-tokens | Tailwind CSS v4 @theme 토큰 변환 |
| Agent | design-system-reviewer | 일관성/접근성 리뷰어 |

## Rules (수동 복사)

플러그인과 별도로, 프로젝트별 규칙 파일을 제공합니다.

```bash
# 파이썬 에이전트 프로젝트
cp -r rules/python_agent_rules/ your-project/.claude/rules/
```

## Project Structure

```
hibye-plugins/
├── plugins/
│   ├── common-dev-workflow/    # 7 skills, 7 agents
│   ├── common-backend/         # 8 skills, 5 agents
│   ├── web-frontend/           # 5 skills, 9 agents
│   ├── python-agent-backend/   # 8 skills, 8 agents
│   ├── vector-rag-backend/     # 4 skills, 4 agents
│   ├── rust-backend/           # 12 skills, 10 agents
│   ├── unity-gamedev/          # 4 skills
│   └── design-system-generator/ # 1 skill, 1 agent
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
