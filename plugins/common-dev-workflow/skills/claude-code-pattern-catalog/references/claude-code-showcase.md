# claude-code-showcase

> Production-level Claude Code 설정 (스코어링 시스템 + GitHub Actions 자동화)

## 통계

| 구성 요소 | 수량 |
|-----------|------|
| Skills | 6 |
| Agents | 2 |
| Commands | 6 |
| Hook Events | 4 types |
| GitHub Actions | 4 workflows |
| MCP Servers | 8 |
| Skill Rules | 20+ definitions |

## 스킬 상세

### testing-patterns (priority 9)
- **설명**: Jest testing patterns, factory functions, mocking strategies, TDD workflow
- **핵심 트리거**: `test`, `jest`, `spec`, `tdd`, `mock`, `factory`
- **pathPatterns**: `**/*.test.ts`, `**/*.test.tsx`, `**/*.spec.ts`, `**/__mocks__/**`
- **contentPatterns**: `describe(`, `it(`, `expect(`, `jest.mock`, `getMock`
- **excludePatterns**: `e2e`, `maestro`, `end-to-end`
- **핵심 원칙**: TDD red-green-refactor, behavior-driven testing, factory pattern `getMockX(overrides)`

### systematic-debugging (priority 9)
- **설명**: Four-phase debugging methodology with root cause analysis
- **핵심 트리거**: `bug`, `debug`, `fix`, `error`, `issue`, `broken`, `crash`, `failing`
- **intentPatterns**: `(?:fix|debug|resolve|investigate).*(?:bug|error|issue|problem)`
- **excludePatterns**: `fix typo`, `fix formatting`, `fix lint`
- **4 phases**: Root Cause Investigation -> Pattern Analysis -> Hypothesis Testing -> Implementation
- **Rule**: 3회 연속 수정 실패 시 중단, 아키텍처 문제 논의 필요

### graphql-schema (priority 8)
- **설명**: GraphQL queries, mutations, code generation patterns
- **핵심 트리거**: `graphql`, `query`, `mutation`, `gql`, `apollo`, `fragment`
- **pathPatterns**: `**/*.gql`, `**/graphql/**`, `**/*.generated.ts`
- **contentPatterns**: `gql\``, `useQuery`, `useMutation`, `useLazyQuery`
- **relatedSkills**: `react-ui-patterns`
- **핵심 규칙**: Never inline gql, always run codegen, always add onError

### core-components (priority 7)
- **설명**: Core component library and design system patterns
- **핵심 트리거**: `component`, `ui`, `button`, `text`, `box`, `hstack`, `vstack`, `token`
- **pathPatterns**: `**/components/core/**`, `**/components/**/*.tsx`
- **contentPatterns**: `from 'components/core`, `Box`, `HStack`, `VStack`, `Text`
- **excludePatterns**: `storybook`, `test`
- **핵심 규칙**: Never hard-code values, always use design tokens ($1~$8 spacing, $textPrimary etc.)

### formik-patterns (priority 7)
- **설명**: Formik form handling with validation patterns
- **핵심 트리거**: `form`, `formik`, `validation`, `yup`, `input field`
- **pathPatterns**: `**/*Form.tsx`, `**/*Form/**`, `**/forms/**`
- **contentPatterns**: `useFormik`, `Formik`, `FormikProvider`, `yup.`
- **excludePatterns**: `format`, `transform`, `platform`
- **핵심 규칙**: Show errors only when touched, disable button when invalid/submitting

### react-ui-patterns (priority 6)
- **설명**: Modern React UI patterns for loading states, error handling, data fetching
- **핵심 트리거**: `react`, `hook`, `useeffect`, `usestate`, `loading`, `suspense`
- **pathPatterns**: `**/hooks/**`, `**/use*.ts`, `**/use*.tsx`
- **contentPatterns**: `useState`, `useEffect`, `useCallback`, `useMemo`
- **excludePatterns**: `test`, `jest`
- **Golden Rule**: `if (loading && !data)` -- loading은 데이터가 없을 때만

## 에이전트

### code-reviewer (model: opus)
- **용도**: 코드 작성/수정 후 자동 리뷰
- **피드백 분류**: Critical (security, breaking) / Warning (conventions, perf) / Suggestion (naming, docs)
- **체크리스트**: Logic & Flow, TypeScript strict, Immutability, Loading/Empty states, Error handling, Mutation UI, Testing, Security
- **핵심 패턴**: `if (error) -> if (loading && !data) -> if (!data?.items.length) -> return data`
- **Mutation UI**: Button must be `isDisabled` + `isLoading` during mutation

### github-workflow (model: sonnet)
- **용도**: Git workflow (commits, branches, PRs)
- **Branch naming**: `{initials}/{description}`
- **Commit format**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- **PR checklist**: branch convention, conventional commits, tests pass, no lint errors, single concern

## 커맨드 (6개)

| 커맨드 | 설명 | allowed-tools |
|--------|------|---------------|
| `/onboard` | Task onboarding, codebase exploration, `.claude/tasks/[ID]/onboarding.md` 생성 | (all) |
| `/ticket` | JIRA/Linear ticket end-to-end workflow | Read, Write, Edit, Glob, Grep, Bash(git/gh/npm), mcp__jira/github/linear |
| `/pr-review` | PR review using code-reviewer agent standards | Read, Glob, Grep, Bash(git/gh) |
| `/pr-summary` | Branch changes summary 생성 (git log/diff) | Bash(git) |
| `/code-quality` | Directory code quality checks (lint, typecheck, manual) | Read, Glob, Grep, Bash(npm/npx) |
| `/docs-sync` | Documentation-code sync verification (30-day window) | Read, Glob, Grep, Bash(git) |

## Hook 구현

### UserPromptSubmit: Skill Evaluation (timeout: 5s)
- **실행**: `skill-eval.sh` -> `skill-eval.js` (Node.js engine)
- **동작**: stdin으로 prompt JSON 수신 -> keyword/pattern/path/intent/content/context 매칭 -> 스킬 추천 출력
- **출력 형식**: `<user-prompt-submit-hook>` 태그 내 ranked skill list + confidence level (HIGH/MEDIUM/LOW)
- **후속 지시**: EVALUATE (YES/NO) -> ACTIVATE (Skill tool invoke) -> IMPLEMENT

### PreToolUse: Main Branch Protection (timeout: 5s)
- **매처**: `Edit|MultiEdit|Write`
- **동작**: `git branch --show-current`가 `main`이면 block + "Create a feature branch first" 메시지
- **exit code 2**: blocking error

### PostToolUse: 4개 Hook (매처: `Edit|MultiEdit|Write`)

| Hook | Trigger 조건 | Command | Timeout |
|------|-------------|---------|---------|
| Code Formatting | `.js/.jsx/.ts/.tsx` 파일 수정 | `npx prettier --write` | 30s |
| NPM Install | `package.json` 수정 | `npm install` | 60s |
| Test Runner | `.test.(js\|jsx\|ts\|tsx)` 수정 | `npm test -- --findRelatedTests` | 90s |
| TypeScript Check | `.ts/.tsx` 수정 | `npx tsc --noEmit` | 30s |

**Hook Response Format**: `{"feedback": "...", "suppressOutput": true, "block": true, "continue": false}`
**Hook 환경 변수**: `$CLAUDE_TOOL_INPUT_FILE_PATH`, `$CLAUDE_TOOL_NAME`, `$CLAUDE_PROJECT_DIR`
**Exit codes**: 0 (success), 1 (non-blocking error), 2 (blocking error, PreToolUse only)

## 스코어링 시스템 v2.0

### 7 Trigger Types with Weights

| Trigger Type | Weight | 설명 |
|-------------|--------|------|
| keyword | 2 | 단순 키워드 매칭 (case-insensitive) |
| keywordPattern | 3 | Regex 패턴 매칭 |
| contentPattern | 3 | 코드 스니펫 내 패턴 매칭 |
| pathPattern | 4 | 파일 경로 glob 매칭 |
| intentPattern | 4 | 사용자 의도 감지 regex |
| contextPattern | 2 | 대화 컨텍스트 phrase 매칭 |
| directoryMatch | 5 | 디렉토리 매핑 직접 매칭 (최고 가중치) |

### Configuration
- **minConfidenceScore**: 3 (이 점수 이상일 때만 스킬 추천)
- **maxSkillsToShow**: 5 (최대 추천 스킬 수)
- **showMatchReasons**: true (매칭 이유 표시)
- **Confidence levels**: HIGH (score >= 9), MEDIUM (score >= 6), LOW (score >= 3)

### Directory Mappings

| Directory | Mapped Skill |
|-----------|-------------|
| `src/components/core` | core-components |
| `src/components` | core-components |
| `src/screens` | navigation-architecture |
| `src/navigation` | navigation-architecture |
| `src/hooks` | react-ui-patterns |
| `src/graphql` | graphql-schema |
| `src/localization` | i18n-translations |
| `src/state`, `src/contexts` | state-management |
| `.maestro` | maestro-e2e |
| `.github/workflows` | github-actions |
| `src/utils/sentry`, `src/datadog` | analytics-tracking |

### 20+ Skill Definitions (skill-rules.json)
storybook, testing-patterns, formik-patterns, graphql-schema, navigation-architecture, i18n-translations, core-components, systematic-debugging, state-management, github-actions, analytics-tracking, list-pagination, modal-actionsheet, maestro-e2e, react-ui-patterns, receiving-code-review, documentation, typescript-conventions, verification-before-completion, defense-in-depth

### 스코어링 알고리즘 흐름
1. excludePatterns 체크 (해당 시 즉시 제외)
2. 7개 trigger type 순회하며 점수 합산
3. `minConfidenceScore` 이상 필터링
4. score 내림차순 정렬 (동점 시 priority 내림차순)
5. `maxSkillsToShow` 개 만큼 상위 추출
6. relatedSkills 추가 추천

## GitHub Actions (4 Workflows)

### pr-claude-code-review
- **트리거**: `pull_request` (opened/synchronize/reopened) + `issue_comment` (@claude 멘션)
- **model**: claude-opus-4-5-20251101
- **max-turns**: 10
- **allowedTools**: Read, Glob, Grep, Bash(git), Bash(gh pr comment/diff/view)
- **동작**: code-reviewer.md 체크리스트 기반 PR 리뷰, severity별 피드백

### scheduled-claude-code-docs-sync
- **트리거**: monthly (매월 1일 09:00 UTC) + workflow_dispatch
- **model**: claude-opus-4-5-20251101
- **max-turns**: 30
- **동작**: 30일간 변경 코드 파일 분석 -> 관련 docs 검색 -> 실제 오류만 수정 -> PR 생성
- **원칙**: "WRONG인 것만 수정, 없는 것은 추가하지 않음"

### scheduled-claude-code-quality
- **트리거**: weekly (매주 일요일 08:00 UTC) + workflow_dispatch
- **model**: claude-opus-4-5-20251101
- **max-turns**: 35
- **max-parallel**: 3 (matrix strategy, fail-fast: false)
- **동작**: src/ 하위 랜덤 3개 디렉토리 선택 -> 각 디렉토리별 병렬 review -> 이슈 직접 수정 -> PR 생성

### scheduled-claude-code-dependency-audit
- **트리거**: biweekly (매월 1일, 15일 10:00 UTC) + workflow_dispatch
- **model**: claude-opus-4-5-20251101
- **max-turns**: 40
- **동작**: `npm outdated` + `npm audit` -> 안전한 업데이트만 수행 -> lint/test 검증 -> PR 생성
- **원칙**: "Be CONSERVATIVE - when in doubt, don't update"

## MCP 서버 (8개)

| Server | Package | 필수 환경 변수 |
|--------|---------|---------------|
| jira | `@anthropic/mcp-jira` | JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN |
| github | `@anthropic/mcp-github` | GITHUB_TOKEN |
| linear | `@anthropic/mcp-linear` | LINEAR_API_KEY |
| sentry | `@anthropic/mcp-sentry` | SENTRY_AUTH_TOKEN, SENTRY_ORG |
| postgres | `@anthropic/mcp-postgres` | DATABASE_URL |
| slack | `@anthropic/mcp-slack` | SLACK_BOT_TOKEN, SLACK_TEAM_ID |
| notion | `@anthropic/mcp-notion` | NOTION_API_KEY |
| memory | `@anthropic/mcp-memory` | (없음) |

모든 서버는 `stdio` type, `npx -y` 으로 실행.

## settings.json 구조

```json
{
  "includeCoAuthoredBy": true,
  "env": {
    "INSIDE_CLAUDE_CODE": "1",
    "BASH_DEFAULT_TIMEOUT_MS": "420000",
    "BASH_MAX_TIMEOUT_MS": "420000"
  },
  "hooks": {
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "skill-eval.sh", "timeout": 5 }] }],
    "PreToolUse": [{ "matcher": "Edit|MultiEdit|Write", "hooks": [{ "type": "command", "command": "main branch check", "timeout": 5 }] }],
    "PostToolUse": [
      { "matcher": "Edit|MultiEdit|Write", "hooks": [{ "command": "prettier", "timeout": 30 }] },
      { "matcher": "Edit|MultiEdit|Write", "hooks": [{ "command": "npm install", "timeout": 60 }] },
      { "matcher": "Edit|MultiEdit|Write", "hooks": [{ "command": "test runner", "timeout": 90 }] },
      { "matcher": "Edit|MultiEdit|Write", "hooks": [{ "command": "tsc --noEmit", "timeout": 30 }] }
    ]
  }
}
```

**BASH timeout**: 420000ms (7분) -- default 및 max 동일 설정
**includeCoAuthoredBy**: commit 메시지에 Co-Authored-By 자동 추가

## 프로젝트 구조 요약

```
.claude/
  settings.json          # hooks, env vars
  settings.md            # hook documentation
  agents/
    code-reviewer.md     # opus model, review checklist
    github-workflow.md   # sonnet model, git conventions
  commands/
    onboard.md           # task onboarding
    ticket.md            # JIRA/Linear workflow
    pr-review.md         # PR review
    pr-summary.md        # branch changes summary
    code-quality.md      # directory quality check
    docs-sync.md         # documentation sync
  hooks/
    skill-eval.sh        # bash wrapper
    skill-eval.js        # Node.js scoring engine (v2.0)
    skill-rules.json     # 20+ skill definitions + scoring config
    skill-rules.schema.json  # JSON Schema validation
  skills/
    testing-patterns/    # priority 9
    systematic-debugging/ # priority 9
    graphql-schema/      # priority 8
    core-components/     # priority 7
    formik-patterns/     # priority 7
    react-ui-patterns/   # priority 6
.github/workflows/
  pr-claude-code-review.yml
  scheduled-claude-code-docs-sync.yml
  scheduled-claude-code-quality.yml
  scheduled-claude-code-dependency-audit.yml
.mcp.json                # 8 MCP servers
CLAUDE.md                # project rules + skill activation guide
```
