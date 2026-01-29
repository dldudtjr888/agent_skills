# Conditional Routing

rs-graph-llm에서 조건부 라우팅 및 분기 패턴.

## 기본 조건부 엣지

```rust
use rs_graph_llm::prelude::*;

pub fn build_conditional_graph() -> Graph<AgentState> {
    let mut graph = Graph::new();

    // 노드 추가
    graph.add_node("classifier", classifier_node);
    graph.add_node("tech_handler", tech_handler_node);
    graph.add_node("general_handler", general_handler_node);
    graph.add_node("output", output_node);

    // 조건부 엣지
    graph.add_conditional_edge(
        "classifier",
        |state: &AgentState| {
            match state.classification.as_deref() {
                Some("tech") => "tech_handler",
                Some("general") => "general_handler",
                _ => "general_handler",
            }
        },
        vec!["tech_handler", "general_handler"],
    );

    // 일반 엣지
    graph.add_edge("tech_handler", "output");
    graph.add_edge("general_handler", "output");

    graph.set_entry_point("classifier");
    graph.set_finish_point("output");

    graph
}
```

## 다중 분기

```rust
pub fn build_multi_branch_graph() -> Graph<WorkflowState> {
    let mut graph = Graph::new();

    graph.add_node("analyzer", analyze_input);
    graph.add_node("simple_path", handle_simple);
    graph.add_node("medium_path", handle_medium);
    graph.add_node("complex_path", handle_complex);
    graph.add_node("error_path", handle_error);
    graph.add_node("merger", merge_results);

    // 복잡도 기반 라우팅
    graph.add_conditional_edge(
        "analyzer",
        |state: &WorkflowState| {
            match state.complexity {
                Complexity::Simple => "simple_path",
                Complexity::Medium => "medium_path",
                Complexity::Complex => "complex_path",
                Complexity::Unknown => "error_path",
            }
        },
        vec!["simple_path", "medium_path", "complex_path", "error_path"],
    );

    // 모든 경로가 merger로
    for path in ["simple_path", "medium_path", "complex_path"] {
        graph.add_edge(path, "merger");
    }

    graph.set_entry_point("analyzer");
    graph.set_finish_point("merger");

    graph
}
```

## 루프 라우팅

```rust
pub fn build_loop_graph() -> Graph<AgentState> {
    let mut graph = Graph::new();

    graph.add_node("process", process_node);
    graph.add_node("check", check_node);
    graph.add_node("refine", refine_node);
    graph.add_node("finish", finish_node);

    graph.add_edge("process", "check");

    // 조건부 루프
    graph.add_conditional_edge(
        "check",
        |state: &AgentState| {
            if state.quality_score >= 0.9 {
                "finish"
            } else if state.iteration >= 5 {
                "finish"  // 최대 반복 도달
            } else {
                "refine"  // 다시 개선
            }
        },
        vec!["finish", "refine"],
    );

    graph.add_edge("refine", "process");  // 루프백

    graph.set_entry_point("process");
    graph.set_finish_point("finish");

    graph
}
```

## 동적 라우팅

```rust
pub fn build_dynamic_router_graph() -> Graph<AgentState> {
    let mut graph = Graph::new();

    graph.add_node("router", router_node);
    graph.add_node("fallback", fallback_node);

    // 동적으로 노드 추가 (런타임)
    let handlers = vec!["handler_a", "handler_b", "handler_c"];
    for handler in &handlers {
        graph.add_node(handler, create_handler(handler));
    }

    // LLM 기반 라우팅
    graph.add_conditional_edge(
        "router",
        move |state: &AgentState| {
            state.next_node.as_deref().unwrap_or("fallback")
        },
        handlers.iter().map(|s| *s).chain(std::iter::once("fallback")).collect(),
    );

    graph.set_entry_point("router");

    graph
}

async fn router_node(state: AgentState) -> AgentState {
    let llm = OpenAI::default();

    let prompt = format!(
        "Given the input: {}\nWhich handler should process this? Options: handler_a, handler_b, handler_c",
        state.input
    );

    let response = llm.invoke(&prompt).await.unwrap();

    AgentState {
        next_node: Some(response.trim().to_string()),
        ..state
    }
}
```

## 병렬 분기 후 합류

```rust
pub fn build_parallel_branch_graph() -> Graph<ParallelState> {
    let mut graph = Graph::new();

    graph.add_node("splitter", split_input);
    graph.add_node("branch_a", process_branch_a);
    graph.add_node("branch_b", process_branch_b);
    graph.add_node("branch_c", process_branch_c);
    graph.add_node("joiner", join_results);

    // 분기 (조건 없이 모두 실행)
    graph.add_edge("splitter", "branch_a");
    graph.add_edge("splitter", "branch_b");
    graph.add_edge("splitter", "branch_c");

    // 합류
    graph.add_edge("branch_a", "joiner");
    graph.add_edge("branch_b", "joiner");
    graph.add_edge("branch_c", "joiner");

    // joiner는 모든 브랜치 완료 후 실행
    graph.set_join_node("joiner", 3);

    graph.set_entry_point("splitter");
    graph.set_finish_point("joiner");

    graph
}

async fn join_results(state: ParallelState) -> ParallelState {
    // 모든 브랜치 결과 합치기
    let combined = state.branch_results
        .values()
        .cloned()
        .collect::<Vec<_>>()
        .join("\n");

    ParallelState {
        output: Some(combined),
        ..state
    }
}
```

## 조건 함수 패턴

### Enum 기반

```rust
pub enum RouteDecision {
    Continue(String),
    Finish,
    Error(String),
}

fn routing_condition(state: &AgentState) -> RouteDecision {
    if let Some(error) = &state.error {
        return RouteDecision::Error(error.clone());
    }

    if state.is_complete() {
        return RouteDecision::Finish;
    }

    let next = determine_next_step(state);
    RouteDecision::Continue(next)
}
```

### 클로저 팩토리

```rust
fn create_threshold_router(threshold: f64) -> impl Fn(&AgentState) -> &'static str {
    move |state: &AgentState| {
        if state.confidence >= threshold {
            "high_confidence_path"
        } else {
            "low_confidence_path"
        }
    }
}

// 사용
graph.add_conditional_edge(
    "analyzer",
    create_threshold_router(0.8),
    vec!["high_confidence_path", "low_confidence_path"],
);
```

## 체크리스트

- [ ] 모든 가능한 분기 경로 정의
- [ ] 기본/폴백 경로 설정
- [ ] 무한 루프 방지 (최대 반복)
- [ ] 터미널 노드 명확히 설정
- [ ] 조건 함수 테스트
- [ ] 병렬 분기 시 합류 조건 정의
