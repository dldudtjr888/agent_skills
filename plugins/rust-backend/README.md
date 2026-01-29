# rust-backend

러스트 백엔드: Rust 패턴, Axum, Tokio, AI 에이전트 (Rig, langchain-rust)

## Skills

### 백엔드 패턴

| Skill | Description |
|-------|-------------|
| rust-patterns | Rust 개발 패턴 및 베스트 프랙티스 |
| axum-backend-pattern | Axum 라우터, 미들웨어, State, 에러 핸들링 |
| tokio-async-patterns | Tokio 비동기 (JoinSet, channels, select!, shutdown) |
| rust-db-patterns | SQLx/Diesel/SeaORM 패턴, 트랜잭션 |
| rust-testing-guide | cargo test, mockall, proptest, criterion |
| rust-error-handling | thiserror/anyhow 심화, 에러 전파 패턴 |
| rust-crate-ecosystem | 주요 크레이트 (serde, tracing, tower) |
| rust-workspace-patterns | 워크스페이스, 모듈 구조 |

### 에이전트 빌드

| Skill | Description |
|-------|-------------|
| rig-builder | Rig LLM 에이전트 빌더, RAG, 도구 사용 |
| langchain-rust-builder | LangChain Rust 빌더, 체인, 메모리 |
| rs-graph-llm-builder | rs-graph-llm 워크플로우, StateGraph |
| rust-agent-infra-builder | 에이전트 인프라 (메모리, 프롬프트, MCP) |

## Agents

### 백엔드 개발

| Agent | Description |
|-------|-------------|
| rust-axum-architect | Axum 백엔드 아키텍처 설계 |
| rust-diff-reviewer | git diff 기반 Rust 코드 리뷰 (clippy, audit) |
| rust-refactor-master | 모듈 분리, 트레이트 추출, 의존성 정리 |
| rust-refactor-cleaner | clippy 경고 수정, 포맷팅 |
| rust-route-tester | Axum 라우트 테스트 (axum-test) |
| rust-route-debugger | Axum 라우트 디버깅 (tracing, tower) |
| rust-crate-builder | 새 크레이트 생성, Cargo.toml 최적화 |
| rust-perf-analyzer | 성능 분석 (criterion, flamegraph) |

### 에이전트 빌드

| Agent | Description |
|-------|-------------|
| rust-agent-builder | Rust AI 에이전트 빌더 (Rig/langchain-rust 선택) |
| rust-agent-infra-builder | 에이전트 인프라 설계 (메모리, MCP) |

## Hooks

| Hook | 트리거 | 설명 |
|------|--------|------|
| protect-sensitive.sh | PreToolUse (Edit/Write) | 민감 파일 보호 |
| rust-lint.sh | PostToolUse (Edit/Write) | cargo fmt + clippy 자동 실행 |
| suggest-agent.sh | PostToolUse (Edit/Write) | Rust 에이전트/스킬 추천 |

## Usage

```bash
/plugin install rust-backend@hibye-plugins

# common-backend, common-dev-workflow와 함께 사용 권장
/plugin install common-backend@hibye-plugins
/plugin install common-dev-workflow@hibye-plugins
```

## 연동

### common-backend

- `database-design` → `rust-db-patterns`에서 참조
- `auth-patterns` → `axum-backend-pattern`에서 참조
- `api-design` → `axum-backend-pattern`에서 참조

### common-dev-workflow

- `code-reviewer` → `rust-diff-reviewer`가 확장
- `tdd-fundamentals` → `rust-testing-guide`에서 참조
