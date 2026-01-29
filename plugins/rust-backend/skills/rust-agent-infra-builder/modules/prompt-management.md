# Prompt Management

Rust AI 에이전트의 프롬프트 관리 패턴.

## 템플릿 시스템

### Handlebars 기반

```rust
use handlebars::Handlebars;
use serde::Serialize;
use std::collections::HashMap;

pub struct PromptManager {
    handlebars: Handlebars<'static>,
    versions: HashMap<String, Vec<PromptVersion>>,
}

#[derive(Debug, Clone)]
struct PromptVersion {
    version: String,
    template: String,
    active: bool,
}

impl PromptManager {
    pub fn new() -> Self {
        let mut handlebars = Handlebars::new();
        handlebars.set_strict_mode(true);

        Self {
            handlebars,
            versions: HashMap::new(),
        }
    }

    pub fn register(&mut self, name: &str, template: &str) -> anyhow::Result<()> {
        self.handlebars.register_template_string(name, template)?;
        Ok(())
    }

    pub fn register_versioned(
        &mut self,
        name: &str,
        version: &str,
        template: &str,
        active: bool,
    ) -> anyhow::Result<()> {
        let full_name = format!("{}:{}", name, version);
        self.handlebars.register_template_string(&full_name, template)?;

        self.versions
            .entry(name.to_string())
            .or_default()
            .push(PromptVersion {
                version: version.to_string(),
                template: template.to_string(),
                active,
            });

        // active 버전을 기본으로 등록
        if active {
            self.handlebars.register_template_string(name, template)?;
        }

        Ok(())
    }

    pub fn render<T: Serialize>(&self, name: &str, data: &T) -> anyhow::Result<String> {
        Ok(self.handlebars.render(name, data)?)
    }

    pub fn render_version<T: Serialize>(
        &self,
        name: &str,
        version: &str,
        data: &T,
    ) -> anyhow::Result<String> {
        let full_name = format!("{}:{}", name, version);
        Ok(self.handlebars.render(&full_name, data)?)
    }
}
```

### Tera 기반

```rust
use tera::{Tera, Context};

pub struct TeraPromptManager {
    tera: Tera,
}

impl TeraPromptManager {
    pub fn new() -> Self {
        Self {
            tera: Tera::default(),
        }
    }

    pub fn from_dir(dir: &str) -> anyhow::Result<Self> {
        let pattern = format!("{}/**/*.txt", dir);
        let tera = Tera::new(&pattern)?;
        Ok(Self { tera })
    }

    pub fn register(&mut self, name: &str, template: &str) -> anyhow::Result<()> {
        self.tera.add_raw_template(name, template)?;
        Ok(())
    }

    pub fn render(&self, name: &str, context: &Context) -> anyhow::Result<String> {
        Ok(self.tera.render(name, context)?)
    }
}
```

## 프롬프트 템플릿 패턴

### 시스템 프롬프트

```handlebars
{{! prompts/system.hbs }}
# Role
You are {{role}}, a {{expertise}} assistant.

# Capabilities
{{#each capabilities}}
- {{this}}
{{/each}}

# Guidelines
{{#each guidelines}}
{{@index}}. {{this}}
{{/each}}

{{#if context}}
# Context
{{context}}
{{/if}}

# Output Format
{{output_format}}
```

### 사용자 프롬프트

```handlebars
{{! prompts/user.hbs }}
{{#if conversation_history}}
## Previous Conversation
{{#each conversation_history}}
**{{role}}**: {{content}}
{{/each}}
{{/if}}

{{#if retrieved_context}}
## Relevant Information
{{#each retrieved_context}}
---
{{content}}
---
{{/each}}
{{/if}}

## User Question
{{user_message}}
```

### 도구 사용 프롬프트

```handlebars
{{! prompts/tool_use.hbs }}
You have access to the following tools:

{{#each tools}}
### {{name}}
{{description}}

Parameters:
```json
{{parameters}}
```
{{/each}}

To use a tool, respond with a JSON object:
```json
{
  "tool": "tool_name",
  "arguments": { ... }
}
```

User request: {{user_message}}
```

## 동적 조합

### 컨텍스트 빌더

```rust
use serde::Serialize;

#[derive(Default, Serialize)]
pub struct PromptContext {
    role: Option<String>,
    expertise: Option<String>,
    capabilities: Vec<String>,
    guidelines: Vec<String>,
    context: Option<String>,
    output_format: Option<String>,
    conversation_history: Vec<Message>,
    retrieved_context: Vec<RetrievedDoc>,
    tools: Vec<ToolInfo>,
    user_message: String,
}

impl PromptContext {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn role(mut self, role: &str) -> Self {
        self.role = Some(role.to_string());
        self
    }

    pub fn expertise(mut self, expertise: &str) -> Self {
        self.expertise = Some(expertise.to_string());
        self
    }

    pub fn add_capability(mut self, capability: &str) -> Self {
        self.capabilities.push(capability.to_string());
        self
    }

    pub fn add_guideline(mut self, guideline: &str) -> Self {
        self.guidelines.push(guideline.to_string());
        self
    }

    pub fn context(mut self, context: &str) -> Self {
        self.context = Some(context.to_string());
        self
    }

    pub fn conversation_history(mut self, history: Vec<Message>) -> Self {
        self.conversation_history = history;
        self
    }

    pub fn retrieved_context(mut self, docs: Vec<RetrievedDoc>) -> Self {
        self.retrieved_context = docs;
        self
    }

    pub fn tools(mut self, tools: Vec<ToolInfo>) -> Self {
        self.tools = tools;
        self
    }

    pub fn user_message(mut self, message: &str) -> Self {
        self.user_message = message.to_string();
        self
    }
}
```

### 사용 예제

```rust
let context = PromptContext::new()
    .role("Rust Code Reviewer")
    .expertise("Rust programming and code review")
    .add_capability("Identify bugs and issues")
    .add_capability("Suggest improvements")
    .add_capability("Check for idiomatic patterns")
    .add_guideline("Be constructive and explain reasoning")
    .add_guideline("Prioritize safety and performance")
    .conversation_history(memory.get_messages().clone())
    .user_message("Please review this code: ...");

let system_prompt = prompt_manager.render("system", &context)?;
let user_prompt = prompt_manager.render("user", &context)?;
```

## 버전 관리

### YAML 기반 관리

```yaml
# prompts/code_review.yaml
name: code_review
description: Code review prompt
versions:
  - version: "1.0.0"
    active: false
    template: |
      Review the following code and provide feedback.
      Code: {{code}}

  - version: "1.1.0"
    active: true
    template: |
      # Code Review Task
      Review the following code for:
      - Bugs and issues
      - Performance concerns
      - Code style

      ## Code
      ```{{language}}
      {{code}}
      ```

      Provide structured feedback in JSON format.
```

### 파일 기반 로더

```rust
use std::path::Path;

impl PromptManager {
    pub fn load_from_dir(dir: &Path) -> anyhow::Result<Self> {
        let mut manager = Self::new();

        for entry in std::fs::read_dir(dir)? {
            let path = entry?.path();

            if path.extension().map_or(false, |ext| ext == "yaml" || ext == "yml") {
                let content = std::fs::read_to_string(&path)?;
                let config: PromptConfig = serde_yaml::from_str(&content)?;

                for version in config.versions {
                    manager.register_versioned(
                        &config.name,
                        &version.version,
                        &version.template,
                        version.active,
                    )?;
                }
            }
        }

        Ok(manager)
    }
}

#[derive(Deserialize)]
struct PromptConfig {
    name: String,
    description: String,
    versions: Vec<VersionConfig>,
}

#[derive(Deserialize)]
struct VersionConfig {
    version: String,
    active: bool,
    template: String,
}
```

## A/B 테스트

```rust
use rand::Rng;

impl PromptManager {
    pub fn render_ab_test<T: Serialize>(
        &self,
        name: &str,
        data: &T,
        weights: &[(String, f64)],
    ) -> anyhow::Result<(String, String)> {
        let total_weight: f64 = weights.iter().map(|(_, w)| w).sum();
        let mut rng = rand::thread_rng();
        let random = rng.gen::<f64>() * total_weight;

        let mut cumulative = 0.0;
        for (version, weight) in weights {
            cumulative += weight;
            if random <= cumulative {
                let prompt = self.render_version(name, version, data)?;
                return Ok((version.clone(), prompt));
            }
        }

        // 기본 버전
        let prompt = self.render(name, data)?;
        Ok(("default".to_string(), prompt))
    }
}

// 사용 예제
let weights = vec![
    ("1.0.0".to_string(), 0.2),  // 20%
    ("1.1.0".to_string(), 0.8),  // 80%
];

let (version_used, prompt) = prompt_manager.render_ab_test("code_review", &context, &weights)?;
tracing::info!(version = %version_used, "Using prompt version");
```

## 체크리스트

- [ ] 템플릿 엔진 선택 (Handlebars/Tera)
- [ ] 프롬프트 템플릿 파일 구조 설계
- [ ] 동적 컨텍스트 빌더 구현
- [ ] 버전 관리 전략 결정
- [ ] A/B 테스트 지원 (필요시)
- [ ] 프롬프트 로깅 및 추적
- [ ] 캐싱 (컴파일된 템플릿)
