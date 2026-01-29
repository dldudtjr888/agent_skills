# Skill 공통 패턴

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

```yaml
---
name: skill-name
description: 스킬 설명 (1-2줄)
version: 1.0.0
category: domain | workflow | foundation | tool | platform | language
user-invocable: true | false

# 트리거 조건 (선택)
triggers:
  - "키워드1"
  - "키워드2"
  - "/slash-command"

# 참조 파일 (선택)
references:
  - references/overview.md
  - references/examples.md

# 사용 도구 (선택)
allowed-tools:
  - Read
  - Write
  - Bash(git *)
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

## 스킬 카테고리 분류 (moai-adk 기반)

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

## Progressive Disclosure (점진적 공개) 패턴

moai-adk와 infrastructure-showcase에서 발견된 토큰 최적화 패턴:

```
Level 1 (메타데이터): ~100 토큰 → 항상 로드
Level 2 (본문): ~5K 토큰 → 트리거 매칭 시 로드
Level 3 (번들): 가변 → Claude가 필요 시 on-demand 로드
```

**핵심 규칙**: SKILL.md 본문은 500줄 미만으로 유지. 대규모 스킬은 modules/ 디렉토리로 분할.

## Skill Composition Layer (스킬 합성 계층)

oh-my-claudecode에서 발견된 다중 스킬 합성 패턴:

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

## skill-rules.json (자동 활성화 시스템)

infrastructure-showcase와 claude-code-showcase에서 발견된 패턴:

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

## Scoring System (claude-code-showcase v2.0)

skill-eval.js 기반 7가지 트리거 유형과 가중치 점수 시스템:

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
