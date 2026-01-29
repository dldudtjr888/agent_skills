# Command, Rule, CLAUDE.md 공통 패턴

## Command 공통 패턴

### 파일 구조

```
.claude/commands/
├── command-name.md         # 단일 파일 명령어
```

### Command 마크다운 구조

```markdown
---
description: 명령어 설명 (간결하게)
allowed-tools: Read, Write, Edit, Bash(git *), Glob, Grep, Task, AskUserQuestion
argument-hint: "선택적 인수 힌트"
---

# Command Name

## 사용법
- `/command-name` - 기본 실행
- `/command-name [arg]` - 인수와 함께 실행

## 워크플로우
1. [첫 번째 단계]
2. [두 번째 단계]
3. [세 번째 단계]

## 출력 형식
[결과 포맷 설명]
```

### 공통 명령어 유형

| 유형 | 예시 | 특징 |
|------|------|------|
| **워크플로우 명령어** | /plan, /build, /sync, /tdd | 복잡한 다단계 워크플로우 |
| **검증 명령어** | /code-review, /verify, /test-coverage | 코드 품질/보안 검증 |
| **유틸리티 명령어** | /build-fix, /refactor-clean, /update-docs | 단일 목적 유틸리티 |
| **설정 명령어** | /setup, /configure, /omc-setup | 초기화/구성 |
| **학습 명령어** | /learn, /evolve, /instinct-status | 패턴 추출/학습 |
| **티켓 연동 명령어** | /ticket, /pr-review, /pr-summary | JIRA/Linear/GitHub 연동 |
| **피드백 명령어** | /9-feedback, /instinct-export | 사용자 피드백/공유 |

### Command Alias 패턴 (oh-my-claudecode)

```yaml
---
description: Full autonomous execution
aliases: [ap, autonomous]
---
```

`/oh-my-claudecode:autopilot` = `/oh-my-claudecode:ap` = `/oh-my-claudecode:autonomous`

---

## Rules 공통 패턴

### 파일 구조

```
.claude/rules/
├── core/
│   └── constitution.md       # 핵심 불변 규칙
├── development/
│   ├── coding-standards.md   # 코딩 표준
│   └── skill-authoring.md    # 스킬 작성 가이드
├── languages/
│   └── typescript.md         # 언어별 규칙
└── workflow/
    └── spec-workflow.md      # 워크플로우 규칙
```

### Rule 마크다운 구조

```markdown
# Rule Name

## 항상 따라야 할 규칙
- 규칙 1: [설명]
- 규칙 2: [설명]

## 금지 사항
- 절대 하지 말 것 1
- 절대 하지 말 것 2

## 예외
- [규칙이 적용되지 않는 경우]
```

---

## CLAUDE.md 공통 패턴

### 구조

```markdown
# Project Name

## Quick Facts
- Stack: [기술 스택]
- Test: `npm test`
- Build: `npm run build`
- Lint: `npm run lint`

## 프로젝트 구조
[디렉토리 트리]

## 코드 스타일
[컨벤션 규칙]

## Git 규칙
[브랜치 네이밍, 커밋 포맷]

## 핵심 규칙
[절대 위반 불가 규칙]

## 스킬 매핑
[어떤 작업 → 어떤 스킬 사용]
```
