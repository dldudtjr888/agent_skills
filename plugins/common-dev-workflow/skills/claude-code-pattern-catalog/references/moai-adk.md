# moai-adk

## EARS (Easy Approach to Requirements Specification) 5가지 패턴

### Pattern 1: Ubiquitous (보편적)
```
구문: "The system SHALL [action]."
예시: The system SHALL register users with email and password validation.
```

### Pattern 2: Event-Driven (이벤트 기반)
```
구문: "WHEN [event], the system SHALL [action]."
예시: WHEN a user successfully authenticates, the system SHALL generate a JWT token with 1-hour expiry.
```

### Pattern 3: State-Driven (상태 기반)
```
구문: "WHILE [state], the system SHALL [action]."
예시: WHILE a request includes Authorization header, the system SHALL validate JWT token before processing.
```

### Pattern 4: Unwanted (방지)
```
구문: "The system SHALL NOT [action]."
예시: The system SHALL NOT allow passwords from common password lists (top 10K).
```

### Pattern 5: Optional (선택적)
```
구문: "WHERE [condition], the system SHOULD [action]."
예시: WHERE user chooses, the system SHOULD support OAuth2 authentication via Google and GitHub.
```

### 복합 패턴 예시 (Event + State):
```
Statement:
  - WHEN a user attempts login with MFA enabled (Event)
  - WHILE the MFA verification is pending (State)
  - The system SHALL send TOTP code and require verification within 5 minutes

Test Scenarios:
  - Happy path: 유효 코드 시간 내 제출
  - Expired code: 5분 후 제출
  - Invalid code: 잘못된 코드
  - Rate limit: 3회 실패 → 15분 잠금
```

## SPEC 파일 형식

**디렉토리 구조**:
```
.moai/specs/SPEC-{DOMAIN}-{NUMBER}/
├── spec.md           # EARS 형식 요구사항 (필수)
├── plan.md           # 구현 계획 (필수)
└── acceptance.md     # 인수 기준 (필수)
```

**spec.md 템플릿**:
```yaml
---
spec_id: SPEC-001
title: User Authentication System
version: 1.0.0
status: draft
created: 2026-01-28
updated: 2026-01-28
author: Claude
priority: HIGH
---

## HISTORY
- v1.0.0 (2026-01-28): Initial specification created

## Requirements

### SPEC-001-REQ-01: User Registration (Ubiquitous)
Pattern: Ubiquitous
Statement: The system SHALL register users with email and password validation.
Acceptance Criteria:
- Email format validated (RFC 5322)
- Password strength: ≥8 chars, mixed case, numbers, symbols
Test Coverage Target: ≥90%
```

**SPEC ID 형식**: `SPEC-{DOMAIN}-{NUMBER}` (예: `SPEC-AUTH-001`)
- 유효 도메인: AUTH, AUTHZ, SSO, MFA, API, BACKEND, SERVICE, UI, FRONTEND, DB, DATA, INFRA, DEVOPS, REFACTOR, FIX, UPDATE, PERF, TEST, DOCS
- 복합 도메인: 최대 3개 (예: `SPEC-UPDATE-REFACTOR-FIX-001`)
- NUMBER: 3자리 제로패딩 (001, 002, ...)

## DDD ANALYZE-PRESERVE-IMPROVE 사이클

```
ANALYZE Phase (분석):
  - 기존 코드와 동작 이해
  - 현재 테스트 커버리지 문서화
  - 의존성과 부작용 매핑

PRESERVE Phase (보존):
  - 특성화 테스트(Characterization Tests) 생성
  - 기존 동작을 테스트로 고정
  - 성공/실패/엣지 케이스 모두 포함

IMPROVE Phase (개선):
  - 동작 보존하면서 리팩터링
  - SPEC 요구사항 구현
  - 모든 특성화 테스트 통과 유지
```

**3-Phase DDD 워크플로우**:
```
Phase 1: SPEC → spec-builder → .moai/specs/SPEC-XXX/spec.md
Phase 2: DDD → ddd-implementer → Code + Tests (≥85% coverage)
Phase 3: Docs → docs-manager → API docs + diagrams
```

## 다국어 자동 라우팅

**multilingual-triggers.yaml 구조**:
```yaml
expert-backend:
  triggers:
    en: ["backend", "API", "server", "authentication", "database"]
    ko: ["백엔드", "API", "서버", "인증", "데이터베이스"]
    ja: ["バックエンド", "API", "サーバー", "認証", "データベース"]
    zh: ["后端", "API", "服务器", "认证", "数据库"]

manager-ddd:
  triggers:
    en: ["DDD", "ANALYZE-PRESERVE-IMPROVE", "domain-driven"]
    ko: ["DDD", "분석-보존-개선", "도메인주도개발"]
    ja: ["DDD", "分析-保存-改善", "ドメイン駆動開発"]
    zh: ["DDD", "分析-保存-改进", "领域驱动开发"]

manager-spec:
  triggers:
    en: ["SPEC", "requirement", "specification", "EARS"]
    ko: ["SPEC", "요구사항", "명세서", "EARS"]
    ja: ["SPEC", "要件", "仕様書", "EARS"]
    zh: ["SPEC", "需求", "规格书", "EARS"]
```

**라우팅 메커니즘**:
1. 사용자 입력을 해당 언어의 트리거 키워드와 매칭
2. `conversation_language` 설정에서 언어 코드 결정
3. 키워드 매칭 기반으로 적절한 에이전트 라우팅
4. 응답도 사용자 언어로 유지

## 언어 설정 (language.yaml)

```yaml
language:
  conversation_language: en            # 사용자 대면 (ko, en, ja, es, zh, fr, de)
  conversation_language_name: English  # 표시 이름 (자동 갱신)
  agent_prompt_language: en            # 내부 에이전트 지시
  git_commit_messages: en              # Git 커밋 메시지
  code_comments: en                    # 소스 코드 주석
  documentation: en                    # 문서 파일
  error_messages: en                   # 에러 메시지
```

## Plan-Run-Sync 워크플로우 상세

**Phase 1: PLAN (`/moai:1-plan`)**
```
토큰 예산: 30,000
후속 조치: /clear 실행 (필수) → 45-50K 토큰 절약

워크플로우:
1. 사용자 기능 요청 → Explore 에이전트 (선택)
2. manager-spec 에이전트 → SPEC 후보 분석/제안
3. 사용자 승인 → AskUserQuestion
4. SPEC 파일 생성 → spec.md, plan.md, acceptance.md
5. 브랜치/worktree 생성 (선택)
6. /clear 실행 → 다음 단계를 위한 깨끗한 컨텍스트
```

**Phase 2: RUN (`/moai:2-run SPEC-ID`)**
```
토큰 예산: 180,000 (70% 더 큰 구현 가능)

워크플로우 (순차):
1. PHASE 1: 분석 & 계획 (manager-strategy)
2. PHASE 1.5: 태스크 분해 (SDD 2025)
3. PHASE 2: DDD 구현 (manager-ddd)
   ├── ANALYZE → PRESERVE → IMPROVE
4. PHASE 2.5: 품질 검증 (manager-quality)
   ├── TRUST 5 평가, 동작 보존 검증, ≥85% 커버리지
5. PHASE 3: Git 작업 (manager-git)
6. PHASE 4: 완료 & 안내 → /moai:3-sync 실행 제안

성공 기준: 모든 SPEC 요구사항 구현, ≥85% 커버리지, TRUST 5 통과, 회귀 없음
```

**Phase 3: SYNC (`/moai:3-sync [mode] [target]`)**
```
토큰 예산: 40,000 (60% 적은 중복 파일 읽기)

실행 모드:
- auto (기본): 변경 파일 선택적 동기화
- force: 전체 프로젝트 재동기화
- status: 읽기 전용 상태 체크
- project: 통합 프로젝트 동기화

워크플로우:
1. 변경 파일 분석 (manager-docs)
2. 문서 생성/업데이트 (manager-docs + manager-quality)
3. Git & PR (manager-git) → PR 생성/업데이트
```

## Token Budget 최적화

```
Plan:  30,000 tokens  → /clear 후 45-50K 절약
Run:   180,000 tokens → 70% 더 큰 구현 가능
Sync:  40,000 tokens  → 60% 적은 중복 읽기
TOTAL: 250,000 tokens
```

**Progressive Disclosure 3-Level**:
```
Level 1 (메타데이터): ~100-1,000 tokens
  ├── Quick Reference (30초 읽기)
  └── 항상 로드

Level 2 (본문): ~3,000-5,000 tokens
  ├── Implementation Guide (5분 읽기)
  └── 트리거 조건 매칭 시 로드

Level 3 (번들): ~5,000+ tokens
  ├── modules/*.md, examples.md, reference.md
  └── On-demand: Claude가 필요 시 접근
```

**SKILL.md 라인 예산 (Hard Limit: 500줄)**:
```
Frontmatter:         4-6줄
Quick Reference:     80-120줄
Implementation Guide: 180-250줄
Advanced Patterns:   80-140줄 (→ modules/ 링크)
Works Well With:     10-20줄
```

## Alfred Orchestrator & Manager 에이전트

**Alfred**: 전략적 오케스트레이터. 모든 작업은 전문 에이전트에게 위임.

**Hard Rules**:
- 사용자 언어로 응답 (conversation_language)
- 독립적 도구 호출은 병렬 실행
- 사용자 응답에 XML 태그 금지
- 마크다운으로 출력

**7개 Manager 에이전트**:
| 에이전트 | 역할 |
|----------|------|
| `manager-spec` | SPEC 문서 생성, EARS 형식, 요구사항 분석 |
| `manager-ddd` | DDD 개발, ANALYZE-PRESERVE-IMPROVE 사이클 |
| `manager-docs` | 문서 생성, Nextra 통합 |
| `manager-quality` | 품질 게이트, TRUST 5 검증, 코드 리뷰 |
| `manager-project` | 프로젝트 설정, 구조 관리 |
| `manager-strategy` | 시스템 설계, 아키텍처 결정 |
| `manager-git` | Git 작업, 브랜치 전략, 머지 관리 |

## 품질 설정 (quality.yaml)

```yaml
constitution:
  development_mode: ddd              # DDD만 지원
  enforce_quality: true
  test_coverage_target: 85

  ddd_settings:
    require_existing_tests: true
    characterization_tests: true
    behavior_snapshots: true
    max_transformation_size: small

  lsp_quality_gates:
    enabled: true
    plan:
      require_baseline: true
    run:
      max_errors: 0
      max_type_errors: 0
      max_lint_errors: 0
      allow_regression: false
    sync:
      max_errors: 0
      max_warnings: 10
      require_clean_lsp: true
    cache_ttl_seconds: 5
    timeout_seconds: 3
```
