---
name: rs-graph-llm-builder
description: >-
  rs-graph-llm 크레이트 기반 워크플로우 에이전트 빌더. LangGraph 스타일 StateGraph, add_node(),
  add_conditional_edges(), CompiledGraph, State 구조체 설계, 조건부 분기, 순환 그래프,
  human-in-the-loop 체크포인트 패턴을 Rust에서 네이티브 구현.
  MUST USE: rs-graph-llm 사용, LangGraph 패턴 Rust 구현, 워크플로우 기반 에이전트, StateGraph 설계,
  조건부 라우팅, 그래프 기반 LLM 파이프라인 구축 시 반드시 사용.
  러스트 워크플로우 에이전트, 그래프 기반 LLM, LangGraph Rust 버전 구현 시 반드시 활성화.
version: 1.0.0
category: ai-agent
user-invocable: true
triggers:
  keywords:
    - rs-graph-llm
    - graph
    - workflow
    - 워크플로우
    - stategraph
  intentPatterns:
    - "(만들|구현).*(워크플로우|graph|그래프)"
    - "(rs-graph|langgraph).*(rust|러스트)"
---

## Core Rules

1. Python langgraph 문법 금지 — Rust 네이티브 `rs_graph_llm` API 사용
2. `.unwrap()` 금지 — `?` 사용
3. `StateGraph::<T>::new()` 로 그래프 생성
4. `add_node()` + `add_conditional_edge()` 로 워크플로우 구성
5. State 구조체는 `Clone + Default` derive 필수
6. 순환 그래프에는 max_iterations 가드 필수

# rs-graph-llm Builder

rs-graph-llm을 사용한 워크플로우 기반 에이전트 개발 가이드.

LangGraph의 철학을 따르는 Rust 네이티브 프레임워크입니다.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | State Design | [modules/state-design.md](modules/state-design.md) | State 구조체 설계, 타입 안전성 |
| 2 | Conditional Routing | [modules/conditional-routing.md](modules/conditional-routing.md) | 조건부 엣지, 분기 패턴 |
| 3 | Error Handling | [modules/error-handling.md](modules/error-handling.md) | 노드 에러, 재시도 전략 |

## 핵심 개념

### StateGraph

```rust
use rs_graph_llm::{StateGraph, State, Node};

#[derive(Clone, Default)]
struct AgentState {
    messages: Vec<Message>,
    next_action: Option<String>,
}

let mut graph = StateGraph::<AgentState>::new();

// 노드 추가
graph.add_node("agent", agent_node);
graph.add_node("tools", tools_node);

// 엣지 추가
graph.add_edge("agent", "tools");
graph.add_conditional_edge("tools", |state| {
    if state.next_action == Some("end".into()) {
        "end"
    } else {
        "agent"
    }
});

// 진입점
graph.set_entry_point("agent");

// 컴파일 & 실행
let app = graph.compile();
let result = app.invoke(initial_state).await?;
```

### 노드 정의

```rust
async fn agent_node(state: AgentState) -> AgentState {
    // LLM 호출
    let response = llm.invoke(&state.messages).await?;

    AgentState {
        messages: {
            let mut msgs = state.messages.clone();
            msgs.push(Message::assistant(response));
            msgs
        },
        next_action: determine_action(&response),
    }
}
```

### 조건부 라우팅

```rust
graph.add_conditional_edge("router", |state| {
    match state.intent.as_str() {
        "search" => "search_node",
        "calculate" => "calc_node",
        _ => "default_node",
    }
});
```

## 참고

- [rs-graph-llm GitHub](https://github.com/a-agmon/rs-graph-llm)
