---
name: rust-agent-infra-builder
description: "Rust AI 에이전트 인프라 빌더. 메모리 스토어, 프롬프트 관리, MCP 통합을 종합적으로 가이드."
version: 1.0.0
category: infrastructure
user-invocable: true
triggers:
  keywords:
    - memory
    - 메모리
    - mcp
    - model context protocol
    - prompt manager
    - 프롬프트 관리
    - context
    - 컨텍스트
    - infra
    - 인프라
  intentPatterns:
    - "(만들|생성|구현|빌드).*(메모리|MCP|프롬프트|인프라)"
    - "(구축|설계).*(에이전트.*인프라|인프라.*에이전트)"
---

# Rust Agent Infrastructure Builder

Rust AI 에이전트 인프라를 종합적으로 구축하는 스킬.
Memory Store, Prompt Management, MCP Integration 3개 영역을 통합합니다.

## 모듈 참조

| # | 모듈 | 파일 | 설명 |
|---|------|------|------|
| 1 | Memory Store | [modules/memory-store.md](modules/memory-store.md) | 대화 메모리, 벡터 메모리, 지속성 |
| 2 | Prompt Management | [modules/prompt-management.md](modules/prompt-management.md) | 프롬프트 템플릿, 버전 관리, 동적 조합 |
| 3 | MCP Integration | [modules/mcp-integration.md](modules/mcp-integration.md) | MCP 서버 연동, 도구 디스커버리, 프로토콜 |

## 사용 시점

### When to Use
- Rust AI 에이전트 백엔드 인프라 구축
- 대화 히스토리 및 컨텍스트 관리 필요시
- 프롬프트 템플릿 시스템 구현
- MCP 서버와 연동 필요시

### When NOT to Use
- 단순 LLM API 호출 (인프라 불필요)
- 특정 프레임워크 전용 작업:
  - Rig 에이전트 → `rig-builder`
  - LangChain Rust → `langchain-rust-builder`

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────┐
│                   Agent Application                  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐│
│  │              Prompt Manager                      ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐        ││
│  │  │Templates│  │Variables│  │Versioning│        ││
│  │  └─────────┘  └─────────┘  └─────────┘        ││
│  └─────────────────────────────────────────────────┘│
│                        ↓                             │
│  ┌─────────────────────────────────────────────────┐│
│  │              Memory Store                        ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐        ││
│  │  │Convo Mem│  │Vector Mem│  │Persist  │        ││
│  │  └─────────┘  └─────────┘  └─────────┘        ││
│  └─────────────────────────────────────────────────┘│
│                        ↓                             │
│  ┌─────────────────────────────────────────────────┐│
│  │              MCP Integration                     ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐        ││
│  │  │ Servers │  │  Tools  │  │Resources│        ││
│  │  └─────────┘  └─────────┘  └─────────┘        ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

## 컴포넌트 선택 가이드

| 요구사항 | 필요 컴포넌트 |
|----------|--------------|
| 기본 채팅 | Memory Store (대화) |
| RAG 시스템 | Memory Store (벡터) |
| 프롬프트 관리 | Prompt Manager |
| 외부 도구 연동 | MCP Integration |
| 전체 통합 | 3개 전체 |

## Quick Start

### Memory Store

```rust
use std::collections::VecDeque;

pub struct ConversationMemory {
    messages: VecDeque<Message>,
    max_messages: usize,
}

impl ConversationMemory {
    pub fn new(max_messages: usize) -> Self {
        Self {
            messages: VecDeque::new(),
            max_messages,
        }
    }

    pub fn add(&mut self, message: Message) {
        if self.messages.len() >= self.max_messages {
            self.messages.pop_front();
        }
        self.messages.push_back(message);
    }

    pub fn get_context(&self) -> Vec<&Message> {
        self.messages.iter().collect()
    }
}
```

### Prompt Manager

```rust
use std::collections::HashMap;
use handlebars::Handlebars;

pub struct PromptManager {
    templates: HashMap<String, String>,
    handlebars: Handlebars<'static>,
}

impl PromptManager {
    pub fn new() -> Self {
        Self {
            templates: HashMap::new(),
            handlebars: Handlebars::new(),
        }
    }

    pub fn register(&mut self, name: &str, template: &str) -> anyhow::Result<()> {
        self.handlebars.register_template_string(name, template)?;
        self.templates.insert(name.into(), template.into());
        Ok(())
    }

    pub fn render(&self, name: &str, data: &serde_json::Value) -> anyhow::Result<String> {
        Ok(self.handlebars.render(name, data)?)
    }
}
```

### MCP Client

```rust
use tokio::process::{Command, Child};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

pub struct McpClient {
    child: Child,
    // ...
}

impl McpClient {
    pub async fn spawn(command: &str, args: &[&str]) -> anyhow::Result<Self> {
        let child = Command::new(command)
            .args(args)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .spawn()?;

        Ok(Self { child })
    }

    pub async fn list_tools(&mut self) -> anyhow::Result<Vec<ToolInfo>> {
        // MCP 프로토콜로 도구 목록 요청
        todo!()
    }

    pub async fn call_tool(&mut self, name: &str, args: serde_json::Value) -> anyhow::Result<serde_json::Value> {
        // MCP 프로토콜로 도구 호출
        todo!()
    }
}
```

## 통합 예제

```rust
pub struct AgentInfra {
    memory: ConversationMemory,
    prompt_manager: PromptManager,
    mcp_clients: HashMap<String, McpClient>,
}

impl AgentInfra {
    pub async fn new() -> anyhow::Result<Self> {
        let mut prompt_manager = PromptManager::new();

        // 프롬프트 템플릿 등록
        prompt_manager.register("system", include_str!("prompts/system.hbs"))?;
        prompt_manager.register("user", include_str!("prompts/user.hbs"))?;

        Ok(Self {
            memory: ConversationMemory::new(20),
            prompt_manager,
            mcp_clients: HashMap::new(),
        })
    }

    pub async fn add_mcp_server(&mut self, name: &str, command: &str, args: &[&str]) -> anyhow::Result<()> {
        let client = McpClient::spawn(command, args).await?;
        self.mcp_clients.insert(name.into(), client);
        Ok(())
    }

    pub async fn process_message(&mut self, user_message: &str) -> anyhow::Result<String> {
        // 1. 메모리에서 컨텍스트 가져오기
        let context = self.memory.get_context();

        // 2. 프롬프트 렌더링
        let system_prompt = self.prompt_manager.render("system", &serde_json::json!({
            "context": context,
        }))?;

        // 3. LLM 호출 및 응답 생성
        // ...

        // 4. 메모리에 저장
        self.memory.add(Message::user(user_message));
        // self.memory.add(Message::assistant(&response));

        todo!()
    }
}
```

## 체크리스트

### Memory Store
- [ ] 대화 메모리 구현
- [ ] 메모리 크기 제한
- [ ] 벡터 메모리 (RAG용)
- [ ] 지속성 (Redis/DB)

### Prompt Manager
- [ ] 템플릿 시스템 선택 (Handlebars/Tera)
- [ ] 버전 관리
- [ ] 동적 변수 주입
- [ ] A/B 테스트 지원

### MCP Integration
- [ ] MCP 서버 연결
- [ ] 도구 디스커버리
- [ ] 에러 처리
- [ ] 연결 관리 (재연결)

## 관련 스킬

- `rig-builder` - Rig 에이전트 프레임워크
- `langchain-rust-builder` - LangChain Rust 버전
- `rs-graph-llm-builder` - 워크플로우 기반 에이전트

## common-backend 참조

- `common-backend/caching-strategies` - 캐싱 패턴
- `common-backend/message-queue-patterns` - 메시지 큐 패턴
