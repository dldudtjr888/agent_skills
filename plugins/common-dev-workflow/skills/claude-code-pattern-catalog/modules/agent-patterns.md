# Agent 공통 패턴

## 파일 구조

```
.claude/agents/
├── agent-name.md           # 단일 파일 에이전트
├── templates/              # 에이전트 템플릿 (선택)
│   └── base-agent.md
```

## Agent 마크다운 구조

```markdown
---
name: agent-name
description: 에이전트 설명
model: sonnet | opus | haiku
tools: Read, Grep, Glob, Bash, Edit, Write
---

# Agent Name

## Role
[역할 설명]

## Tools
Read, Grep, Glob, Bash(git *), Edit, Write

## Model
sonnet (기본) | opus (복잡한 추론) | haiku (간단한 작업)

## 워크플로우
1. 단계 1
2. 단계 2
3. 단계 3

## Verification Before Completion
1. **IDENTIFY**: 완료를 증명하는 명령어는?
2. **RUN**: 검증 실행 (test, build, lint)
3. **READ**: 출력 확인 - 실제 통과했는가?
4. **ONLY THEN**: 증거와 함께 완료 주장

## 금지 사항
- "should", "probably", "seems to" 사용 금지
- 검증 없이 완료 주장 금지
- 서브에이전트 생성 금지 (Worker Preamble Protocol)
```

## Tiered Agent System (계층형 에이전트)

oh-my-claudecode에서 발견된 비용 최적화 패턴:

| 티어 | 모델 | 용도 | 비용 |
|-----|------|------|------|
| **LOW** | Haiku | 간단한 조회, 패턴 매칭 | 최저 |
| **MEDIUM** | Sonnet | 일반 기능 구현, 중간 복잡도 | 중간 |
| **HIGH** | Opus | 복잡한 추론, 아키텍처, 디버깅 | 최고 |

## 에이전트 역할 분류 (공통)

모든 주요 레포에서 발견되는 에이전트 유형:

| 역할 | 목적 | 모델 추천 |
|------|------|----------|
| **planner** | 구현 계획 수립 | opus |
| **code-reviewer** | 코드 품질 검토 | opus |
| **security-reviewer** | 보안 취약점 분석 | opus |
| **architect** | 시스템 설계 결정 | opus |
| **executor** | 직접 구현 실행 | sonnet |
| **explorer** | 코드베이스 탐색 | sonnet |
| **build-fixer** | 빌드 에러 해결 | sonnet |
| **tdd-guide** | TDD 방법론 적용 | sonnet |
| **doc-updater** | 문서 동기화 | haiku |
| **researcher** | 외부 문서/정보 조사 | sonnet |

## Multi-Agent Orchestration Pattern

plugins-for-claude-natives와 oh-my-claudecode에서 발견:

```
Phase 1: 병렬 실행 (4-5 에이전트)
  ├── Agent 1 (Task call)
  ├── Agent 2 (Task call)
  ├── Agent 3 (Task call)
  └── Agent 4 (Task call)
         ↓
Phase 2: 검증/합성 (순차 처리)
  └── Validation Agent (Phase 1 결과 처리)
         ↓
Phase 3: 사용자 선택
  └── AskUserQuestion으로 선택 요청
         ↓
Phase 4: 실행 (선택된 액션 수행)
```

## Worker Preamble Protocol

oh-my-claudecode에서 발견된 서브에이전트 제어 패턴:

```
오케스트레이터가 워커 에이전트에 위임할 때:
1. 서브에이전트 생성 방지
2. 도구 직접 사용 강제 (Read, Write, Edit, Bash 등)
3. 절대 경로로 결과 보고
```

## Agent 메타데이터 확장 (moai-adk)

고급 에이전트 정의에서 발견된 확장 필드:

```yaml
name: expert-backend
description: |
  EN: Backend API specialist
  KO: 백엔드 API 전문가
  JA: バックエンドAPI専門家
tools: [Bash, Read, Write, Edit, Grep, Glob, TodoWrite, Task]
skills: [moai-domain-backend, moai-lang-typescript]
hooks:
  PostToolUse: [code-formatter, linter]
can_resume: true
typical_chain_position: middle
token_budget: medium
context_retention: medium
checkpoint_strategy: enabled
memory_management: context_trimming (adaptive)
```

## Builder Agent 패턴 (메타 에이전트)

moai-adk에서 발견된 에이전트/스킬/커맨드 생성 전문 에이전트:

| Builder Agent | 목적 |
|--------------|------|
| `builder-agent` | 새 에이전트 정의 파일 생성 |
| `builder-command` | 새 슬래시 명령어 생성 |
| `builder-skill` | 새 스킬 생성 |
| `builder-plugin` | 새 플러그인 생성 |

## Delegation Categories (oh-my-claudecode)

작업 유형별 자동 모델/파라미터 라우팅:

| 카테고리 | 모델 티어 | Temperature | Thinking Budget |
|---------|----------|-------------|----------------|
| `visual-engineering` | HIGH (Opus) | 0.7 | high |
| `ultrabrain` | HIGH (Opus) | 0.3 | max |
| `artistry` | MEDIUM (Sonnet) | 0.9 | medium |
| `quick` | LOW (Haiku) | 0.1 | low |
| `writing` | MEDIUM (Sonnet) | 0.5 | medium |
