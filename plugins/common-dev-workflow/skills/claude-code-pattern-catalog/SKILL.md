---
name: claude-code-pattern-catalog
description: "9개 레포에서 추출한 Claude Code 스킬/에이전트/커맨드/훅 패턴 카탈로그"
version: 1.0.0
category: foundation
user-invocable: true
triggers:
  keywords: [skill, agent, command, hook, 하네스, 스킬, 에이전트, 커맨드, 훅, pattern, 패턴]
  intentPatterns:
    - "(만들|생성|작성|구현).*(스킬|에이전트|커맨드|훅|하네스)"
    - "(create|build|implement).*(skill|agent|command|hook|harness)"
---

# Claude Code Skill/Agent/Command/Hook Pattern Catalog

9개 레포지토리에서 추출한 Claude Code 확장 패턴 카탈로그.
나만의 Claude Code 스킬, 에이전트, 커맨드, 훅을 만들 때 참조한다.

---

## 1. 전체 통계

| 구성 요소 | 총 수 | 주요 출처 |
|-----------|-------|----------|
| **Skills** | ~130+ | moai-adk(53), oh-my-claudecode(40), everything-claude-code(16), plugins(11), showcase(6+20 defined), infrastructure(5) |
| **Agents** | ~85+ | oh-my-claudecode(32), moai-adk(19+4 builder), everything-claude-code(12), infrastructure(10), plugins(10), showcase(2) |
| **Commands** | ~80+ | oh-my-claudecode(31+aliases), everything-claude-code(23), moai-adk(9), showcase(6), infrastructure(3), power-users(3), hud(2), plugins(1) |
| **Rules** | ~29+ | moai-adk(21), everything-claude-code(8) |
| **Hooks** | ~55+ | moai-adk(41), infrastructure(8), oh-my-claudecode(9 types), everything-claude-code(10+), plugins(2) |
| **Contexts** | ~6+ | everything-claude-code(3), moai-adk(3) |
| **MCP Configs** | ~22+ | everything-claude-code(14+), showcase(8) |
| **GitHub Actions** | 4 | claude-code-showcase(4 workflows) |

---

## 2. 모듈 인덱스

모듈 파일은 `modules/` 디렉토리에 위치하며, 각 패턴 영역을 상세히 다룬다.

| # | 파일 | 설명 |
|---|------|------|
| 1 | `modules/skill-patterns.md` | Skill 공통 패턴 (파일구조, frontmatter, 트리거, Progressive Disclosure) |
| 2 | `modules/agent-patterns.md` | Agent 공통 패턴 (.md 구조, 티어링, Worker Preamble, Verification) |
| 3 | `modules/command-rule-patterns.md` | Command/Rule/CLAUDE.md 공통 패턴 |
| 4 | `modules/hook-patterns.md` | Hook 공통 패턴 (11 이벤트, settings.json, 스크립트 언어) |
| 5 | `modules/methodology-patterns.md` | 방법론 패턴 (Ralph, SPEC-First DDD, 실행 모드, Model Routing) |
| 6 | `modules/plugin-mcp-integration.md` | Plugin Manifest, MCP Configuration, Contexts System |
| 7 | `modules/advanced-features.md` | GitHub Actions, Extended Thinking, State Management, 스코어링 |

---

## 3. 레포 인덱스

레퍼런스 파일은 `references/` 디렉토리에 위치하며, 각 레포별 상세 분석을 포함한다.

| # | 파일 | 설명 |
|---|------|------|
| 1 | `references/oh-my-claudecode.md` | 37 스킬, 32 에이전트, 31 커맨드, 5 실행 모드, Model Routing |
| 2 | `references/claude-code-showcase.md` | 6 스킬, 스코어링 v2.0, 4 GitHub Actions, MCP 8개 |
| 3 | `references/plugins-for-claude-natives.md` | 6개 플러그인 상세 (clarify, doubt, dev, agent-council 등) |
| 4 | `references/claude-hud.md` | 실시간 상태 표시, 컨텍스트 추적, 사용량 모니터링 |
| 5 | `references/infrastructure-showcase.md` | skill-rules.json 5개, 500줄 규칙, 10 에이전트 |
| 6 | `references/moai-adk.md` | EARS 5패턴, SPEC 형식, DDD 사이클, 다국어 라우팅 |
| 7 | `references/ralph-playbook.md` | 자율형 코딩 루프, loop.sh, PROMPT 파일 |
| 8 | `references/everything-claude-code.md` | 17+ 커맨드, 11 에이전트, Continuous Learning v2 |
| 9 | `references/power-users.md` | 환경변수, CLI 플래그, TDD, Extended Thinking |

---

## 4. 스킬 생성 템플릿

### 4.1 최소 스킬 구조

```
.claude/skills/my-skill/
└── SKILL.md
```

SKILL.md 하나만으로 스킬이 동작한다.

### 4.2 SKILL.md 템플릿

```markdown
---
name: my-skill
description: 스킬이 하는 일 (1-2줄)
version: 1.0.0
---

# My Skill

## 개요
[스킬의 목적과 핵심 기능 설명]

## 사용 시점
- [조건 1]
- [조건 2]

## 워크플로우

### Step 1: [단계명]
[상세 설명]

### Step 2: [단계명]
[상세 설명]

### Step 3: [단계명]
[상세 설명]

## 핵심 규칙
- [반드시 따라야 할 규칙]

## 안티패턴
- [하지 말아야 할 것]

## 예제
[사용 예제]
```

### 4.3 고급 스킬 구조 (모듈화)

대규모 스킬은 modules/와 references/로 분할한다.

```
.claude/skills/my-advanced-skill/
├── SKILL.md                # 메인 (500줄 미만)
├── references/
│   ├── overview.md         # 상세 설명
│   ├── examples.md         # 예제 모음
│   └── config.md           # 설정 가이드
├── scripts/
│   └── helper.sh           # 스크립트
└── modules/
    ├── module-a.md          # 하위 모듈
    └── module-b.md
```

### 4.4 에이전트 포함 스킬

```
.claude/skills/my-skill/
├── SKILL.md
├── agents/
│   ├── analyzer.md          # 분석 에이전트
│   └── executor.md          # 실행 에이전트
└── references/
    └── patterns.md
```

SKILL.md 내에서 에이전트 호출:

```markdown
## 워크플로우

### Step 1: 분석
Task 도구로 `analyzer` 에이전트 실행:
- 도구: Read, Grep, Glob
- 모델: sonnet
- 목적: 코드베이스 분석

### Step 2: 실행
Task 도구로 `executor` 에이전트 실행:
- 도구: Read, Write, Edit, Bash
- 모델: sonnet
- 목적: 구현 실행
```

### 4.5 자동 활성화를 위한 skill-rules.json

```json
{
  "version": "1.0",
  "skills": {
    "my-skill": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "medium",
      "promptTriggers": {
        "keywords": ["my-keyword", "관련-키워드"],
        "intentPatterns": ["(create|add|implement).*my-feature"]
      },
      "fileTriggers": {
        "pathPatterns": ["src/my-feature/**/*.ts"]
      }
    }
  }
}
```

---

## 5. Best Practices 요약

### Do (권장)

1. **SKILL.md 500줄 미만** 유지 -- 대규모는 modules/ 분할
2. **YAML frontmatter** 필수 (name, description, version)
3. **Verification Before Completion** 패턴 에이전트에 포함
4. **트리거 조건** 명확하게 정의 (keywords, intent, file patterns)
5. **안티패턴** 섹션으로 "하지 말 것" 명시
6. **예제** 포함하여 Claude가 패턴을 학습하도록
7. **모듈화** - 큰 스킬은 references/와 modules/ 활용
8. **Worker Preamble** - 서브에이전트가 또 서브에이전트 생성 방지

### Don't (금지)

1. 하나의 SKILL.md에 모든 것 넣지 않기
2. 모호한 트리거 키워드 사용하지 않기
3. 검증 단계 없이 "완료" 주장하지 않기
4. 모든 에이전트에 opus 모델 사용하지 않기 (비용!)
5. settings.json을 그대로 복사하지 않기 (환경별 커스터마이징 필요)
6. Stop 훅에 차단 로직 넣지 않기 (신중하게)

---

## 6. 참조 레포지토리

| # | 레포 | 경로 | 핵심 특징 |
|---|------|------|----------|
| 1 | plugins-for-claude-natives | `ref_datas/repos/1_plugins/plugins-for-claude-natives/` | 플러그인 패턴, 멀티에이전트 오케스트레이션 |
| 2 | oh-my-claudecode | `ref_datas/repos/1_plugins/oh-my-claudecode/` | 37 스킬, 계층형 에이전트, 매직 키워드 |
| 3 | claude-hud | `ref_datas/repos/1_plugins/claude-hud/` | 상태 표시 플러그인, 명령어 패턴 |
| 4 | everything-claude-code | `ref_datas/repos/2_settings/everything-claude-code/` | 18 스킬, 연속 학습 v2, 해커톤 우승 |
| 5 | claude-code-infrastructure-showcase | `ref_datas/repos/2_settings/claude-code-infrastructure-showcase/` | skill-rules.json, 자동 활성화 훅 |
| 6 | claude-code-showcase | `ref_datas/repos/2_settings/claude-code-showcase/` | 스코어링 시스템, 실전 설정 |
| 7 | claude-code-for-power-users | `ref_datas/repos/2_settings/claude-code-for-power-users/` | 1706줄 종합 가이드 |
| 8 | ralph-playbook | `ref_datas/repos/3_methodology/ralph-playbook/` | 자율형 코딩 루프, 백프레셔 |
| 9 | moai-adk | `ref_datas/repos/3_methodology/moai-adk/` | 55 스킬, TRUST 5, SPEC-First DDD |
