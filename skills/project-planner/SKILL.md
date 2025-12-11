---
name: project-planner
description: Deep project analysis and implementation planning for feature additions, refactoring, bug fixes, and modifications. Use when user asks to add features, refactor code, fix bugs, modify functionality, or create implementation plans for existing projects.
---

# Project Planner

사용자의 아이디어나 요청을 분석하여 구체적인 구현 계획을 수립한다.
이 계획은 task-decomposer의 입력으로 사용된다.

## Workflow

```
1. Route → 2. Clarify → 3. Analyze → 4. Plan → (handoff) → task-decomposer
```

---

## Route: Quick vs Full Mode

**먼저 복잡도 판단:**

| 조건 | Mode | 예상 토큰 |
|------|------|----------|
| Single file + < 50 lines 변경 | Quick | ~1,500 |
| 2-3 files + isolated 변경 | Quick | ~2,500 |
| 5+ files 또는 cross-cutting | Full | ~5,000+ |
| 아키텍처 변경 | Full | ~7,000+ |

### Quick Mode (단순 변경)

Phase 2의 Step 1-2, 4, 6 생략. 핵심만:

```
1. Read: [target_file]
2. Grep: "[similar_pattern]" (유사 코드 1-2개만)
3. 리스크 신호 확인: Grep: "TODO|FIXME"
4. → 바로 Plan 작성 (assets/plan_simple.md)
```

### Full Mode (복잡한 변경)

아래 Phase 1-3 전체 수행.

---

## MCP 서버 활성화

```
mcp__serena__activate_project
  project: "[project_path]"
mcp__serena__check_onboarding_performed
```

| 서버 | 용도 | 사용 시점 |
|------|------|----------|
| **Serena** | 심볼 분석, 참조 찾기 | 의존성 매핑 시 |
| **Context7** | 공식 문서 조회 | 프레임워크 패턴 확인 시 |

**Context7 사용 시점:**
- 프레임워크 best practice 확인 필요 시
- 라이브러리 API 사용법 불명확 시
- 버전별 breaking change 확인 시

```
mcp__context7__resolve-library-id
  libraryName: "next.js"
mcp__context7__get-library-docs
  context7CompatibleLibraryID: "/vercel/next.js"
  topic: "app-router"
```

---

## Phase 1: Clarify Requirements

### 필수 확인 항목

| 항목 | 질문 | 모호 시 대응 |
|------|------|-------------|
| **Type** | Feature / Refactor / Bugfix / Modification? | 증상 기반 제안 |
| **Scope** | 특정 파일? 모듈? 프로젝트 전체? | Phase 2 후 재질문 |
| **Constraints** | 하위 호환성, 마감일, 외부 제약? | 일반 제약 가정 |
| **Success criteria** | 완료 기준? | 측정 가능 기준 제안 |

### Phase 1 완료 조건

다음 중 하나 충족 시 Phase 2 진행:
- 4개 항목 모두 확인됨
- 3개 확인 + 나머지는 코드 분석으로 파악 가능
- 사용자가 "분석 진행해도 됨" 명시

**정보 부족 시:**
1. 프로젝트 컨텍스트 없음 → Phase 2 진행 후 재질문
2. 요구사항 모호 → 유사 기능 찾아 제안
3. 기술 스택 불명 → 설정 파일로 추론

---

## Phase 2: Project Analysis

### 분석 깊이 결정

| 변경 규모 | 의존성 depth | 유사 기능 탐색 | Step 수행 |
|----------|-------------|---------------|----------|
| Single file | 1 depth | 같은 폴더 | 3, 5만 |
| Module | 2 depth | 같은 도메인 | 1, 3, 4, 5 |
| Cross-cutting | 3 depth | 프로젝트 전체 | 전체 |

### 분석 우선순위

여러 파일 발견 시 순서:
1. 사용자가 명시한 파일
2. 변경 요청과 이름 유사도 높은 파일
3. downstream 참조 가장 많은 파일
4. 최근 수정된 파일

---

### Step 1: Project Overview (Cross-cutting만)

```
Glob: **/*
Read: package.json | requirements.txt | go.mod
```

**식별**: Tech stack, Project structure, Build scripts

> **프레임워크별 상세 필요 시만**: `Read: references/framework-analysis.md`

### Step 2: Entry Points (Cross-cutting만)

| 대상 | 찾는 방법 |
|------|----------|
| Main entry | `Glob: **/main.*, **/index.*, **/app.*` |
| Routing | `Grep: "router\|route\|endpoint"` |
| Config | `Glob: **/.env*, **/config.*` |

### Step 3: Change Area Deep Dive (항상)

```
Read: [target_file]
mcp__serena__get_symbols_overview
  relative_path: "[target_file]"
```

**유사 기능**: `Grep: "[keyword]"` → 패턴 템플릿으로 활용

**데이터 흐름**: Input → Process → Output 추적

### Step 4: Dependency Mapping (Module 이상)

> **복잡한 의존성 시만**: `Read: references/dependency-tools.md`

**Upstream**: `Read` import 문
**Downstream**: `mcp__serena__find_referencing_symbols`
**Shared**: DB, External API, Global state

### Step 5: Risk Assessment (항상)

| Signal | Risk | Action |
|--------|------|--------|
| 테스트 없음 | 🔴 | 테스트 먼저 작성 |
| 의존처 5개+ | 🔴 | 점진적 마이그레이션 |
| 300+ lines | 🟡 | 리팩토링 선행 검토 |
| auth/payment/data | 🔴 | 추가 리뷰, 롤백 필수 |

```
Grep: "TODO\|FIXME\|HACK"
Bash: wc -l [target_file]
```

**복잡도 기준**: <100 🟢 | 100-300 🟡 | 300+ 🔴

### Step 6: Pattern Extraction (Full만)

| 패턴 | 확인 |
|------|------|
| Naming | 컨벤션 확인 |
| Error handling | `Grep: "try\|catch\|except"` |
| Data fetching | `Grep: "fetch\|useQuery\|axios"` |

---

### Phase 2 완료 조건

체크리스트 충족 시 Phase 3 진행:
- [ ] 영향 파일 목록 작성됨
- [ ] 핵심 의존성 파악됨 (upstream/downstream)
- [ ] 리스크 평가됨
- [ ] (Full만) 기존 패턴 문서화됨

**중단 기준**: 분석 10분 초과 시 현재까지 결과로 Plan 작성

---

## Change Type Specific

### Feature
1. 유사 기능 찾기 → 템플릿
2. 영향 레이어 식별 (DB → API → UI)

### Refactoring
1. 현재 동작 문서화
2. `mcp__serena__find_referencing_symbols` 로 사용처 식별

### Bug Fix
1. 재현 먼저
2. 실행 경로 추적 → 근본 원인

### Modification
1. 현재 구현 이유 이해
2. Breaking change → deprecation 계획

**Git 분석 (Modification 시):**
```bash
Bash: git log --oneline -10 [file]
Bash: git blame [file]
```

---

## Phase 3: Plan Output

| 변경 규모 | 템플릿 |
|----------|--------|
| Quick Mode | `assets/plan_simple.md` |
| Full Mode | `assets/plan_full.md` |

### Estimation

| Scope | Effort |
|-------|--------|
| Single file, <50 lines | <1h |
| 2-3 files, isolated | 1-3h |
| 5+ files, cross-cutting | 4-8h |
| Architecture | 1-3 days |

**Buffer**: 익숙하지 않은 코드 ×1.5, 테스트 없음 ×1.3

---

## Handoff to task-decomposer

Plan 완성 후:
1. 사용자 확인
2. 승인 시 task-decomposer 호출
3. Tasks 섹션이 입력이 됨

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| Serena 활성화 실패 | Grep/Read로 대체 분석 |
| 테스트 전혀 없음 | "테스트 작성" Phase 추가 제안 |
| 모노레포 | 사용자에게 타겟 패키지 확인 |
| 분석 막힘 | 현재까지 결과 + 불확실 영역 명시 |

---

## Quick Reference

| 목적 | 도구 |
|------|------|
| 파일 찾기 | `Glob: [pattern]` |
| 내용 검색 | `Grep: [pattern]` |
| 심볼 개요 | `mcp__serena__get_symbols_overview` |
| 참조 찾기 | `mcp__serena__find_referencing_symbols` |
| 문서 조회 | `mcp__context7__get-library-docs` |
