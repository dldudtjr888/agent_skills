# oh-my-claudecode

> Multi-agent orchestration system for Claude Code (93K LoC TypeScript)

## 통계
| 구성 요소 | 수량 |
|-----------|------|
| Skills | 37 |
| Agents | 32 |
| Commands | 31 |
| Hooks | 33 |
| Execution Modes | 8 (5 primary + 3 support) |

## 1. 스킬 전체 목록 (37)

| 이름 | 설명 | 트리거 키워드 |
|------|------|---------------|
| analyze | Deep analysis/investigation | analyze, investigate |
| autopilot | Idea to working code | autopilot, ap, fullsend |
| build-fix | Fix build/TS errors | build-fix |
| cancel | Cancel active OMC mode | cancel, stop |
| code-review | Comprehensive code review | code-review |
| deepinit | Hierarchical AGENTS.md init | deepinit |
| deepsearch | Thorough codebase search | deepsearch |
| doctor | Diagnose OMC install issues | doctor |
| ecomode | Token-efficient execution | eco, budget, save-tokens |
| frontend-ui-ux | Stunning UI/UX creation | frontend, ui, ux |
| git-master | Git expert, atomic commits | git-master |
| help | OMC usage guide | help |
| hud | HUD display config | hud |
| learn-about-omc | Usage pattern analysis | learn-about-omc |
| learner | Extract learned skill | learner |
| local-skills-setup | Local skills management | local-skills-setup |
| mcp-setup | Configure MCP servers | mcp-setup |
| note | Save notes (compaction-safe) | note |
| omc-setup | One-time OMC setup | omc-setup |
| orchestrate | Multi-agent orchestration | orchestrate |
| pipeline | Sequential agent chaining | pipeline, pipe, chain |
| plan | Strategic planning interview | plan |
| project-session-manager | Worktree/tmux sessions | psm, worktree, session |
| ralph | Loop until task complete | ralph |
| ralph-init | PRD creation for ralph | ralph-init |
| ralplan | Iterative planning consensus | ralplan, rp, planloop |
| release | Automated release workflow | release |
| research | Parallel scientist research | research |
| review | Plan review with Critic | review |
| security-review | Security vulnerability scan | security-review |
| skill | Manage local skills CRUD | skill |
| swarm | N agents, SQLite claiming | swarm, swarm-agents |
| tdd | Test-Driven Development | tdd |
| ultrapilot | Parallel autopilot + ownership | ultrapilot, up, ultraauto |
| ultraqa | QA cycle until quality met | ultraqa |
| ultrawork | Max parallel orchestration | ultrawork, ulw, uw, turbo |
| writer-memory | Agentic memory for writers | writer-memory |

## 2. 에이전트 전체 목록 (32)

### Planning & Strategy
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| planner | opus | HIGH | Strategic planning with interview |
| analyst | opus | HIGH | Pre-planning requirements analysis |
| critic | opus | HIGH | Work plan review expert |

### Architecture & Analysis
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| architect | opus | HIGH | Architecture & debugging advisor |
| architect-medium | sonnet | MED | Moderate architecture analysis |
| architect-low | haiku | LOW | Quick code questions |

### Implementation
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| executor | sonnet | MED | Focused task executor |
| executor-high | opus | HIGH | Complex multi-file tasks |
| executor-low | haiku | LOW | Simple single-file tasks |

### Search & Research
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| explore | haiku | LOW | Fast codebase search |
| explore-medium | sonnet | MED | Thorough search with reasoning |
| explore-high | opus | HIGH | Complex architectural search |
| researcher | sonnet | MED | External docs/reference research |
| researcher-low | haiku | LOW | Quick documentation lookups |

### Design & UI
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| designer | sonnet | MED | UI/UX designer-developer |
| designer-high | opus | HIGH | Complex UI architecture |
| designer-low | haiku | LOW | Simple styling tweaks |

### Quality & Security
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| code-reviewer | opus | HIGH | Expert code review |
| code-reviewer-low | haiku | LOW | Quick code quality check |
| security-reviewer | opus | HIGH | Security vulnerability detection |
| security-reviewer-low | haiku | LOW | Quick security scan |
| qa-tester | sonnet | MED | Interactive CLI testing (tmux) |
| qa-tester-high | opus | HIGH | Comprehensive production QA |
| build-fixer | sonnet | MED | Build error resolution |
| build-fixer-low | haiku | LOW | Simple build error fixer |
| tdd-guide | sonnet | MED | TDD workflow specialist |
| tdd-guide-low | haiku | LOW | Quick test suggestions |

### Data & Documentation
| 이름 | 모델 | 티어 | 역할 |
|------|------|------|------|
| scientist | sonnet | MED | Data analysis/research (python) |
| scientist-high | opus | HIGH | Complex research & ML |
| scientist-low | haiku | LOW | Quick data inspection |
| writer | haiku | LOW | Technical documentation |
| vision | sonnet | MED | Visual/media file analyzer |

## 3. 커맨드 전체 목록 (31)

| 이름 | 별칭 | 설명 |
|------|------|------|
| analyze | - | Deep analysis and investigation |
| autopilot | ap, autonomous, fullsend | Full autonomous execution |
| build-fix | - | Fix build/TypeScript errors |
| cancel | - | Cancel active OMC mode |
| code-review | - | Comprehensive code review |
| deepinit | - | Hierarchical AGENTS.md docs |
| deepsearch | - | Thorough codebase search |
| doctor | - | Diagnose OMC install issues |
| ecomode | eco, efficient, budget | Token-efficient parallel execution |
| help | - | OMC usage guide |
| hud | - | Configure HUD display |
| learn-about-omc | - | Usage pattern analysis |
| learner | - | Extract learned skill |
| mcp-setup | - | Configure MCP servers |
| note | - | Save notes to notepad.md |
| omc-setup | - | One-time setup and configure |
| pipeline | pipe, chain | Sequential agent chaining |
| plan | - | Planning session with Planner |
| psm | worktree, session | Project Session Manager |
| ralph | - | Persistence loop until complete |
| ralph-init | - | Initialize PRD for ralph |
| ralplan | rp, planloop | Iterative planning consensus |
| release | - | Automated release workflow |
| research | - | Parallel scientist orchestration |
| review | - | Plan review with Critic |
| security-review | - | Security vulnerability review |
| swarm | swarm-agents | N coordinated agents (SQLite) |
| tdd | - | Test-Driven Development workflow |
| ultrapilot | up, ultraauto, parallelauto | Parallel autopilot + file ownership |
| ultraqa | - | QA cycling workflow |
| ultrawork | ulw, uw, turbo | Max performance parallel mode |

## 4. 훅 전체 목록 (33)

### Hook Events (hooks.json - 13 entries)
| 이벤트 | 스크립트 | 목적 |
|--------|----------|------|
| UserPromptSubmit | keyword-detector.mjs | Magic keyword detection |
| UserPromptSubmit | skill-injector.mjs | Local skill auto-matching |
| SessionStart | session-start.mjs | Session initialization |
| Setup (init) | setup-init.mjs | Directory/config setup |
| Setup (maint) | setup-maintenance.mjs | State cleanup/vacuum |
| PreToolUse | pre-tool-enforcer.mjs | Tool use enforcement |
| PermissionRequest | permission-handler.mjs | Auto-approve safe commands |
| PostToolUse | post-tool-verifier.mjs | Post-tool verification |
| SubagentStart | subagent-tracker.mjs | Subagent tracking start |
| SubagentStop | subagent-tracker.mjs | Subagent tracking stop |
| PreCompact | pre-compact.mjs | Checkpoint before compaction |
| Stop | persistent-mode.mjs | Persistent mode continuation |
| SessionEnd | session-end.mjs | Metrics/cleanup on end |

### Hook Modules (src/hooks/ - 31 modules)
| 모듈 | 목적 |
|------|------|
| agent-usage-reminder | Remind to delegate to agents |
| auto-slash-command | Auto-detect slash commands |
| autopilot | 5-phase autonomous workflow state |
| background-notification | Background task notifications |
| comment-checker | Comment quality checker |
| directory-readme-injector | Inject directory AGENTS.md |
| empty-message-sanitizer | Sanitize empty messages |
| keyword-detector | Magic keyword detection |
| learner | Skill extraction/matching |
| mode-registry | Centralized mode state mgmt |
| non-interactive-env | Non-interactive shell support |
| notepad | Compaction-resilient memory |
| omc-orchestrator | Delegation enforcement |
| permission-handler | Safe command auto-approval |
| persistent-mode | Unified stop handler |
| plugin-patterns | Formatter/linter integration |
| pre-compact | Pre-compaction checkpointing |
| preemptive-compaction | Context window monitoring |
| ralph | Persistence loop/PRD/verifier |
| recovery | Edit/context/session recovery |
| rules-injector | Rule file auto-injection |
| session-end | Session metrics/cleanup |
| setup | Directory structure/config init |
| subagent-tracker | Active subagent tracking |
| swarm | SQLite-based task coordination |
| think-mode | Think/ultrathink switching |
| thinking-block-validator | Thinking block validation |
| todo-continuation | Incomplete todo continuation |
| ultrapilot | Parallel worker coordination |
| ultraqa | QA cycling state |
| ultrawork | Ultrawork state persistence |

## 5. 실행 모드

| 모드 | 방식 | 설명 |
|------|------|------|
| Autopilot | 5-phase | expand -> plan -> execute(ralph) -> QA(ultraqa) -> validate |
| Ultrapilot | 5-worker parallel | File ownership partitioning, 3-5x faster |
| Ultrawork | Aggressive delegation | Haiku default, parallel agents, zero scope reduction |
| Ecomode | Token-efficient | Haiku/Sonnet only (no Opus), 30-50% savings |
| Swarm | SQLite claiming | 1-5 coordinated agents, atomic task claiming |
| Pipeline | Sequential chain | 6 presets: review, implement, debug, research, refactor, security |
| Ralph | Persistence loop | Self-referential loop + architect verification |
| UltraQA | QA cycling | test -> verify -> fix -> repeat until met |

Mutual exclusion: autopilot/ultrapilot/swarm/pipeline. Layerable: ralph/ultrawork/ultraqa/ecomode.

## 6. Model Routing Engine

**Signal Extraction**: Lexical (wordCount, keywords, questionDepth) + Structural (subtasks, crossFile, domain, impact) + Context (failures, chainDepth)

**Scoring** (additive integer): architecture keywords +3, system-wide impact +3, subtasks>3 +3, debugging +2, cross-file +2, security +2, why-questions +2, simple keywords -2

**Tier Determination**: score >= 8 -> HIGH (Opus) | 4-7 -> MEDIUM (Sonnet) | < 4 -> LOW (Haiku)

**Confidence**: 0.5 + (min(distance_from_threshold, 4) / 4) * 0.4

## 7. Magic Keywords (4 built-in + 8 mode triggers)

| 키워드 | 트리거 | 매핑 |
|--------|--------|------|
| ultrawork | ultrawork, ulw, uw | Max parallel orchestration mode |
| ultrathink | ultrathink, think, reason, ponder | Extended thinking mode |
| search | search, find, locate, grep + 12 more | Parallel search agents |
| analyze | analyze, investigate, debug + 17 more | Context-gather analysis mode |
| autopilot | autopilot, ap, fullsend | 5-phase autonomous |
| ralph | ralph | Persistence loop |
| eco | eco, budget, save-tokens | Token-efficient |
| plan | plan | Planning interview |
| ultrapilot | up, ultraauto | Parallel autopilot |
| swarm | swarm | N-agent coordination |
| pipeline | pipeline, pipe | Sequential chaining |

Combinable: `ralph ulw: migrate database` = persistence + parallelism

## 8. Worker Preamble Protocol

Sub-agent spawning 방지. `wrapWithPreamble(task)` 함수가 모든 worker에게 표준 preamble 적용:
- WORKER agent identity (not orchestrator)
- Use tools directly, do NOT spawn sub-agents
- Do NOT call TaskCreate/TaskUpdate
- Report results with absolute file paths

## 9. State 파일 구조

### .omc/ (Project-level)
| 경로 | 용도 |
|------|------|
| state/autopilot-state.json | Autopilot phase/progress |
| state/ultrapilot-state.json | Worker coordination |
| state/ultrapilot-ownership.json | File ownership map |
| state/ultrawork-state.json | Ultrawork activation |
| state/ultraqa-state.json | QA cycling state |
| state/ralph-state.json | Ralph loop iteration |
| state/ralph-verification.json | Architect verification |
| state/ecomode-state.json | Ecomode activation |
| state/swarm.db | SQLite task database |
| state/pipeline-state.json | Pipeline stage progress |
| state/token-tracking.jsonl | Token usage log |
| plans/ | Work plans from planner |
| notepads/{plan}/ | Plan-scoped wisdom capture |
| notepad.md | Compaction-resilient notes |
| prd.json | Product Requirements Document |
| progress.txt | Ralph progress tracking |
| autopilot/spec.md | Expanded spec |

### ~/.omc/ (Global)
| 경로 | 용도 |
|------|------|
| state/ultrawork-state.json | Global ultrawork state |
| state/ralph-state.json | Global ralph state |
| state/ecomode-state.json | Global ecomode state |
| skills/ | User learned skills |
