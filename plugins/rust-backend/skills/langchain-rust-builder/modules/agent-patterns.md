# Agent Patterns

LangChain Rust에서 에이전트 구현 패턴.

## ReAct Agent

추론(Reasoning)과 행동(Acting)을 반복.

```rust
use langchain_rust::agent::{Agent, AgentExecutor, Tool};
use langchain_rust::llm::openai::OpenAI;

pub struct ReActAgent {
    executor: AgentExecutor,
}

impl ReActAgent {
    pub async fn new(llm: OpenAI, tools: Vec<Box<dyn Tool>>) -> Result<Self, Error> {
        let agent = Agent::new(
            llm,
            tools.clone(),
            react_prompt(),
        );

        let executor = AgentExecutor::new(agent, tools)
            .with_max_iterations(10)
            .with_return_intermediate_steps(true);

        Ok(Self { executor })
    }

    pub async fn run(&self, input: &str) -> Result<AgentResult, Error> {
        self.executor.invoke(input).await
    }
}

fn react_prompt() -> PromptTemplate {
    PromptTemplate::new(r#"
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:"#)
}
```

## Tool 정의

```rust
use async_trait::async_trait;
use langchain_rust::agent::Tool;

pub struct SearchTool {
    client: reqwest::Client,
    api_key: String,
}

#[async_trait]
impl Tool for SearchTool {
    fn name(&self) -> &str {
        "search"
    }

    fn description(&self) -> &str {
        "Search the web for information. Input should be a search query."
    }

    async fn run(&self, input: &str) -> Result<String, Error> {
        let response = self.client
            .get("https://api.search.com/search")
            .query(&[("q", input), ("key", &self.api_key)])
            .send()
            .await?
            .json::<SearchResponse>()
            .await?;

        Ok(response.results.first()
            .map(|r| r.snippet.clone())
            .unwrap_or_else(|| "No results found".into()))
    }
}

pub struct CalculatorTool;

#[async_trait]
impl Tool for CalculatorTool {
    fn name(&self) -> &str {
        "calculator"
    }

    fn description(&self) -> &str {
        "Perform mathematical calculations. Input should be a math expression."
    }

    async fn run(&self, input: &str) -> Result<String, Error> {
        let result = meval::eval_str(input)
            .map_err(|e| Error::ToolError(e.to_string()))?;
        Ok(result.to_string())
    }
}
```

## Plan-and-Execute Agent

먼저 계획하고 실행.

```rust
pub struct PlanAndExecuteAgent {
    planner: LLMChain,
    executor: AgentExecutor,
}

impl PlanAndExecuteAgent {
    pub async fn new(
        llm: OpenAI,
        tools: Vec<Box<dyn Tool>>,
    ) -> Result<Self, Error> {
        let planner = LLMChain::new(
            llm.clone(),
            planner_prompt(),
        );

        let executor_agent = Agent::new(llm, tools.clone(), executor_prompt());
        let executor = AgentExecutor::new(executor_agent, tools);

        Ok(Self { planner, executor })
    }

    pub async fn run(&self, input: &str) -> Result<String, Error> {
        // 1. 계획 수립
        let plan = self.planner.invoke(hashmap! {
            "input" => input
        }).await?;

        let steps: Vec<&str> = plan.lines()
            .filter(|l| l.starts_with("- "))
            .collect();

        // 2. 단계별 실행
        let mut results = Vec::new();
        for step in steps {
            let result = self.executor.invoke(step).await?;
            results.push(result);
        }

        // 3. 결과 종합
        Ok(results.join("\n\n"))
    }
}

fn planner_prompt() -> PromptTemplate {
    PromptTemplate::new(r#"
Create a step-by-step plan to accomplish the following task.
Each step should be a clear, actionable item.

Task: {input}

Plan (list each step with "- "):
"#)
}
```

## 도구 기반 에이전트 (OpenAI Functions)

```rust
use langchain_rust::agent::OpenAIFunctionsAgent;

pub async fn create_functions_agent(
    llm: OpenAI,
    tools: Vec<Box<dyn Tool>>,
) -> Result<AgentExecutor, Error> {
    // 도구를 OpenAI functions 형식으로 변환
    let functions: Vec<Function> = tools.iter()
        .map(|t| Function {
            name: t.name().to_string(),
            description: t.description().to_string(),
            parameters: t.parameters_schema(),
        })
        .collect();

    let agent = OpenAIFunctionsAgent::new(llm, functions);
    let executor = AgentExecutor::new(agent, tools);

    Ok(executor)
}
```

## 대화형 에이전트

```rust
pub struct ConversationalAgent {
    executor: AgentExecutor,
    memory: ConversationBufferMemory,
}

impl ConversationalAgent {
    pub async fn chat(&mut self, input: &str) -> Result<String, Error> {
        let history = self.memory.load_memory_variables().await?;

        let result = self.executor.invoke_with_context(
            input,
            hashmap! {
                "chat_history" => history.get("history").unwrap_or(&String::new())
            }
        ).await?;

        self.memory.save_context(
            hashmap! { "input" => input.to_string() },
            hashmap! { "output" => result.output.clone() },
        ).await?;

        Ok(result.output)
    }
}
```

## 에이전트 실행 제어

```rust
pub struct ControlledAgent {
    executor: AgentExecutor,
}

impl ControlledAgent {
    pub fn new(executor: AgentExecutor) -> Self {
        Self {
            executor: executor
                .with_max_iterations(15)
                .with_max_execution_time(Duration::from_secs(60))
                .with_early_stopping_method(EarlyStoppingMethod::Force)
                .with_handle_parsing_errors(true),
        }
    }

    pub async fn run_with_callbacks(
        &self,
        input: &str,
        on_step: impl Fn(&AgentStep),
    ) -> Result<AgentResult, Error> {
        let mut result = self.executor.start(input).await?;

        while !result.is_finished() {
            let step = result.next_step().await?;
            on_step(&step);
        }

        Ok(result.finalize())
    }
}
```

## 에러 핸들링

```rust
impl ReActAgent {
    pub async fn run_safe(&self, input: &str) -> AgentResult {
        match self.executor.invoke(input).await {
            Ok(result) => result,
            Err(Error::MaxIterationsReached) => {
                AgentResult {
                    output: "I couldn't complete the task within the allowed steps.".into(),
                    intermediate_steps: vec![],
                }
            }
            Err(Error::ToolError(msg)) => {
                AgentResult {
                    output: format!("A tool encountered an error: {}", msg),
                    intermediate_steps: vec![],
                }
            }
            Err(e) => {
                tracing::error!("Agent error: {}", e);
                AgentResult {
                    output: "An unexpected error occurred.".into(),
                    intermediate_steps: vec![],
                }
            }
        }
    }
}
```

## 체크리스트

- [ ] 적절한 에이전트 타입 선택 (ReAct vs Plan-and-Execute)
- [ ] 도구 설명 명확히 작성
- [ ] 최대 반복 횟수 설정
- [ ] 실행 시간 제한 설정
- [ ] 파싱 에러 핸들링
- [ ] 중간 단계 로깅
- [ ] 대화형일 경우 메모리 통합
