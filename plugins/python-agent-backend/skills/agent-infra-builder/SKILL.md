---
name: agent-infra-builder
description: "Python AI 에이전트 인프라 빌더. Guardrails, Handler 패턴, MCP 통합, Memory Store, Prompt 관리, LangGraph 워크플로우를 종합적으로 가이드."
version: 1.0.0
category: infrastructure
user-invocable: true
triggers:
  keywords:
    - guardrail
    - 가드레일
    - pii
    - prompt injection
    - handler
    - sse
    - streaming
    - 스트리밍
    - mcp
    - model context protocol
    - memory
    - 메모리
    - 3-tier
    - context assembly
    - prompt manager
    - yaml prompt
    - 프롬프트 관리
    - langgraph
    - stategraph
    - 워크플로우
  intentPatterns:
    - "(만들|생성|구현|빌드).*(가드레일|핸들러|MCP|메모리|프롬프트|워크플로우)"
    - "(구축|설계).*(에이전트.*인프라|인프라.*에이전트)"
---

# Agent Infrastructure Builder

Python AI 에이전트 인프라를 종합적으로 구축하는 스킬.
Guardrails, Handler, MCP, Memory, Prompt, LangGraph 6개 영역을 통합한다.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Guardrails | [modules/guardrails.md](modules/guardrails.md) | 입력/출력 검증, Prompt Injection 방지, PII 마스킹 |
| 2 | Handler 패턴 | [modules/handler-patterns.md](modules/handler-patterns.md) | SSE 스트리밍, 템플릿 메서드, 라이프사이클 |
| 3 | MCP 통합 | [modules/mcp-integration.md](modules/mcp-integration.md) | MCP 서버 풀, 도구 디스커버리, 에이전트 연동 |
| 4 | Memory Store | [modules/memory-store.md](modules/memory-store.md) | 3-Tier 메모리, Context Assembly, 벡터 검색 |
| 5 | Prompt 관리 | [modules/prompt-management.md](modules/prompt-management.md) | YAML 프롬프트, 버전 관리, A/B 테스트 |
| 6 | LangGraph | [modules/langgraph-workflows.md](modules/langgraph-workflows.md) | StateGraph, 병렬 실행, 조건부 라우팅 |

## 사용 시점

### When to Use
- Python AI 에이전트 백엔드 인프라를 처음 구축할 때
- 기존 에이전트 시스템에 가드레일, 메모리, MCP 등을 추가할 때
- LangGraph 기반 워크플로우를 설계할 때
- SSE 스트리밍 핸들러를 구현할 때

### When NOT to Use
- 프론트엔드 전용 작업
- 단순 LLM API 호출 (인프라 불필요)
- 특정 프레임워크 전용 작업:
  - Google ADK → `google-adk-builder`
  - OpenAI Agents SDK → `agents-sdk-builder`
  - Deep Agents → `deep-agents-builder`
  - PydanticAI → `pydantic-ai-builder`

## 아키텍처 개요

```
사용자 요청
    ↓
FastAPI Endpoint
    ↓
Handler (BaseHandler) ← Guardrails (입력 검증)
    ↓
Memory Manager (컨텍스트 조합)
    ↓
Prompt Manager (버전별 프롬프트)
    ↓
LangGraph Workflow (오케스트레이션)
    ↓
MCP Server Pool (외부 도구)
    ↓
응답 스트리밍 (SSE) ← Guardrails (출력 검증)
```

## 컴포넌트 선택 가이드

| 요구사항 | 필요 컴포넌트 |
|----------|--------------|
| 기본 채팅 | Handler |
| 보안 필요 | Handler + Guardrails |
| 외부 도구 | Handler + MCP |
| 대화 기억 | Handler + Memory |
| 프롬프트 관리 | Handler + Prompt Manager |
| 복잡한 워크플로우 | LangGraph + (선택) |
| 전체 통합 | 6개 전체 |

## 워크플로우

### Phase 1: 분석
1. 에이전트 목적 파악
2. 필요한 컴포넌트 식별
3. 통합 순서 계획

### Phase 2: 구현
1. Core 구현 (Memory, Prompt, MCP)
2. Handler 구현 (BaseHandler 확장)
3. Guardrail 연결
4. Workflow 구현 (필요시)

### Phase 3: 통합
1. FastAPI 연동
2. 테스트

## 빠른 참조

[references/quick-reference.md](references/quick-reference.md) - 핵심 API 및 체크리스트
