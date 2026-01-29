# Skill 공통 패턴

> ⚠️ **공식 스펙 vs 커뮤니티 확장**: 이 문서는 Claude Code 공식 스펙과 커뮤니티 레포에서 발견된 확장 패턴을 모두 포함합니다. 공식 스펙은 ✅로, 커뮤니티 확장은 🔧로 표시합니다.

## 파일 구조

```
.claude/skills/skill-name/
├── SKILL.md              # 메인 파일 (YAML frontmatter + 내용)
├── references/           # 참조 문서 (선택)
│   ├── overview.md
│   └── examples.md
├── scripts/              # 헬퍼 스크립트 (선택)
│   └── helper.sh
└── modules/              # 모듈화된 섹션 (대규모 스킬용)
    ├── module-a.md
    └── module-b.md
```

## SKILL.md YAML Frontmatter

### ✅ 공식 지원 필드 (Claude Code 공식 스펙)

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | No | 스킬 표시명 (생략시 디렉토리명). 소문자, 숫자, 하이픈만 (최대 64자) |
| `description` | Recommended | 스킬 기능과 **사용 시점**. Claude가 자동 로드 결정에 사용 |
| `argument-hint` | No | 자동완성 시 인자 힌트. 예: `[issue-number]` |
| `disable-model-invocation` | No | `true`면 수동 `/name` 트리거만 허용 |
| `user-invocable` | No | `false`면 `/` 메뉴에서 숨김 (배경 지식용) |
| `allowed-tools` | No | 스킬 활성화 시 허용 도구. 예: `Read, Grep, Glob` |
| `model` | No | 스킬 활성화 시 사용 모델 |
| `context` | No | `fork`로 설정하면 격리된 서브에이전트에서 실행 |
| `agent` | No | `context: fork` 시 사용할 서브에이전트 유형 |
| `hooks` | No | 스킬 생명주기에 범위 지정된 훅 |

```yaml
---
name: my-skill
description: 스킬 기능 설명과 사용 시점. Use when [trigger conditions].
user-invocable: true
allowed-tools: Read, Grep, Glob
---
```

### 🔧 커뮤니티 확장 필드 (moai-adk, oh-my-claudecode 등)

> ⚠️ 아래 필드들은 커뮤니티 레포에서 사용하는 확장 패턴이며, Claude Code가 직접 해석하지 않습니다. 별도의 훅/스크립트를 통해 처리해야 합니다.

| 필드 | 출처 | 설명 |
|------|------|------|
| `version` | moai-adk | 스킬 버전 관리 |
| `category` | moai-adk | 스킬 분류 (domain, workflow 등) |
| `triggers` | infrastructure-showcase | 자동 활성화 키워드/패턴 |
| `references` | 여러 레포 | 참조 파일 목록 |

```yaml
# 커뮤니티 확장 예시 (별도 훅 필요)
---
name: skill-name
description: 스킬 설명
version: 1.0.0
category: domain
triggers:
  - "키워드1"
  - "키워드2"
---
```

## SKILL.md 본문 구조

모든 레포에서 공통적으로 발견되는 패턴:

```markdown
# Skill Name

## 개요
[무엇을 하는 스킬인지 1-3줄 설명]

## 사용 시점 (When to Use)
- 조건 1
- 조건 2

## 워크플로우
1. 단계 1: [설명]
2. 단계 2: [설명]
3. 단계 3: [설명]

## 핵심 규칙 / 패턴
- 규칙 1
- 규칙 2

## 안티패턴 (하지 말 것)
- 안티패턴 1
- 안티패턴 2

## 예제
[코드/사용 예제]
```

## 🔧 스킬 카테고리 분류 (moai-adk 커뮤니티 패턴)

| 카테고리 | 설명 | 예시 |
|---------|------|------|
| **foundation** | 프레임워크 핵심 원칙 | core, context, memory, quality |
| **domain** | 기술 도메인 전문 지식 | backend, frontend, database, uiux |
| **workflow** | 작업 흐름 정의 | ddd, spec, testing, loop |
| **language** | 프로그래밍 언어별 패턴 | python, typescript, go, rust |
| **platform** | 플랫폼/서비스 통합 | supabase, vercel, firebase |
| **library** | 라이브러리별 패턴 | mermaid, shadcn, nextra |
| **tool** | 외부 도구 통합 | ast-grep, svg |
| **framework** | 프레임워크별 패턴 | electron |

## ✅ Progressive Disclosure (점진적 공개) 패턴

공식 스펙에서 권장하는 토큰 최적화 패턴 (moai-adk, infrastructure-showcase에서도 활용):

```
Level 1 (메타데이터): ~100 토큰 → 항상 로드
Level 2 (본문): ~5K 토큰 → 트리거 매칭 시 로드
Level 3 (번들): 가변 → Claude가 필요 시 on-demand 로드
```

**핵심 규칙**: SKILL.md 본문은 500줄 미만으로 유지. 대규모 스킬은 modules/ 디렉토리로 분할.

## 🔧 Skill Composition Layer (oh-my-claudecode 커뮤니티 패턴)

> ⚠️ Claude Code 공식 기능이 아닙니다. oh-my-claudecode에서 구현한 다중 스킬 합성 패턴입니다.

```
┌──────────────────────────────────────┐
│ GUARANTEE LAYER (선택)               │
│ ralph: "검증될 때까지 멈출 수 없음"   │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ ENHANCEMENT LAYER (0-N 스킬)         │
│ ultrawork | git-master | frontend-ui │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ EXECUTION LAYER (주요 스킬)          │
│ default | orchestrate | planner      │
└──────────────────────────────────────┘
```

## 🔧 skill-rules.json (커뮤니티 자동 활성화 시스템)

> ⚠️ Claude Code 공식 기능이 아닙니다. infrastructure-showcase와 claude-code-showcase에서 사용하는 커뮤니티 패턴입니다.

```json
{
  "version": "1.0",
  "skills": {
    "skill-name": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "high",
      "promptTriggers": {
        "keywords": ["keyword1", "keyword2"],
        "intentPatterns": ["regex.*pattern"]
      },
      "fileTriggers": {
        "pathPatterns": ["src/**/*.ts"],
        "contentPatterns": ["import.*from"]
      },
      "skipConditions": {
        "sessionSkillUsed": true,
        "fileMarkers": ["@skip-validation"]
      }
    }
  }
}
```

**enforcement 유형**:
- `suggest`: 스킬 추천 (비차단)
- `block`: 스킬 사용 전까지 차단 (가드레일)
- `warn`: 경고 표시, 진행 허용

## 🔧 Scoring System (claude-code-showcase 커뮤니티 패턴)

> ⚠️ Claude Code 공식 기능이 아닙니다. claude-code-showcase에서 구현한 skill-eval.js 기반 커뮤니티 패턴입니다.

```json
{
  "version": "2.0",
  "config": {
    "minConfidenceScore": 3,
    "showMatchReasons": true,
    "maxSkillsToShow": 5
  },
  "scoring": {
    "keyword": 2,
    "keywordPattern": 3,
    "pathPattern": 4,
    "directoryMatch": 5,
    "intentPattern": 4,
    "contentPattern": 3,
    "contextPattern": 2
  },
  "directoryMappings": {
    "src/components/core": "core-components",
    "src/hooks": "react-ui-patterns",
    "src/graphql": "graphql-schema"
  }
}
```

**Skill 정의 확장 필드** (showcase 20개 스킬 기준):
```json
{
  "skill-name": {
    "priority": 9,
    "keywords": ["test", "jest", "spec"],
    "keywordPatterns": ["\\.test\\.(js|tsx)"],
    "intentPatterns": ["write.*test", "red.green.refactor"],
    "contentPatterns": ["useFormik", "FormikProvider"],
    "contextPatterns": ["before claiming", "double check"],
    "excludePatterns": ["fix typo", "fix formatting"],
    "relatedSkills": ["systematic-debugging"]
  }
}
```
