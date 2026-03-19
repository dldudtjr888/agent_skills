---
name: task-planner
description: "모호한 요청을 Clarify→Analyze→Plan 3단계 대화로 구체화하여 구현 계획 문서를 작성하는 스킬 — Serena/Grep/WebSearch로 코드베이스 분석, 변경 대상 파일/심볼 식별, 의존성 매핑, 리스크 평가 포함. task-decomposer의 입력을 생성. Use when planning new features, designing refactoring strategies, scoping bugfix approaches, creating implementation plans, or analyzing project impact before coding. '계획 세워줘', '설계해줘', '구현 방향 잡아줘', '이거 어떻게 만들지', '기능 추가 전에 분석해줘', '리팩토링 계획', 'plan this feature', 'design the implementation' 요청 시 반드시 트리거."
---

# Task Planner

**목적**: 모호한 요청 → 대화로 구체화 → 분석 → 계획 문서

## Workflow

```
Clarify (대화) → Analyze (분석) → Plan (문서화)
```

---

## Phase 1: Clarify

사용자의 모호한 요청을 구체화. **가장 중요한 단계**.

| 항목 | 질문 예시 |
|------|----------|
| **What** | "구체적으로 어떤 기능이 필요한가요?" |
| **Why** | "이 기능이 해결하려는 문제가 뭔가요?" |
| **Where** | "특정 파일/모듈이 있나요?" |
| **Constraints** | "기존 API 호환? 성능 요구사항?" |
| **Done** | "어떻게 되면 완료인가요?" |

**완료 조건**: 5개 항목 중 4개 이상 확인 또는 사용자가 "분석 진행해" 명시

---

## Phase 2: Analyze

Serena, Grep, WebSearch 등으로 코드베이스 분석:
- 변경 대상 파일/심볼 식별
- 의존성 매핑
- 리스크 평가

---

## Phase 3: Plan Output

아래 템플릿으로 계획서 작성 후 `task-decomposer`로 전달.

```markdown
# Implementation Plan: [Change Name]

## Summary
| 항목 | 값 |
|------|-----|
| **Type** | Feature / Refactor / Bugfix |
| **Risk** | 🟢 Low / 🟡 Medium / 🔴 High |
| **Affected Files** | N개 |

## Key Files
| File | Purpose | Action |
|------|---------|--------|
| `path/to/file.ts` | 역할 | Create / Modify |

## Dependencies
- **Upstream**: 우리가 의존하는 모듈
- **Downstream**: 우리에게 의존하는 모듈 (검증 필요)
- **Shared**: DB 테이블, 외부 API, 환경변수

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| [위험 요소] | 🔴/🟡/🟢 | [예방/복구 방법] |

## Rollback
1. `git revert [commit]`
2. DB 마이그레이션 롤백
3. Feature flag OFF
```
