# claude-code-infrastructure-showcase

## skill-rules.json 전체 5개 스킬 정의

### Skill 1: skill-developer
```json
{
  "type": "domain", "enforcement": "suggest", "priority": "high",
  "promptTriggers": {
    "keywords": ["skill system", "create skill", "add skill", "skill triggers", "skill rules", "hook system", "skill development", "skill-rules.json"],
    "intentPatterns": ["(how do|how does|explain).*?skill", "(create|add|modify|build).*?skill", "skill.*?(work|trigger|activate|system)"]
  }
}
```

### Skill 2: backend-dev-guidelines
```json
{
  "type": "domain", "enforcement": "suggest", "priority": "high",
  "promptTriggers": {
    "keywords": ["backend", "microservice", "controller", "service", "repository", "express", "API", "endpoint", "middleware", "validation", "Zod", "Prisma", "BaseController", "dependency injection", "unifiedConfig"],
    "intentPatterns": ["(create|add|implement|build).*?(route|endpoint|API|controller|service|repository)", "(fix|handle|debug).*?(error|exception|backend)"]
  },
  "fileTriggers": {
    "pathPatterns": ["blog-api/src/**/*.ts", "auth-service/src/**/*.ts", "backend/**/*.ts", "api/**/*.ts", "server/**/*.ts", "services/**/*.ts"],
    "contentPatterns": ["router.", "app.(get|post|put|delete|patch)", "export.*Controller", "export.*Service", "prisma."]
  }
}
```

### Skill 3: frontend-dev-guidelines
```json
{
  "type": "guardrail", "enforcement": "block", "priority": "high",
  "promptTriggers": {
    "keywords": ["component", "react component", "UI", "interface", "page", "modal", "dialog", "form", "MUI", "Material-UI", "Grid", "styling", "frontend", "React"],
    "intentPatterns": ["(create|add|make|build|update|modify|edit).*?(component|UI|page|modal|dialog|form)", "(how to|best practice).*?(component|react|MUI)"]
  },
  "fileTriggers": {
    "pathPatterns": ["frontend/src/**/*.tsx", "frontend/src/**/*.ts", "client/src/**/*.tsx", "src/**/*.tsx"],
    "contentPatterns": ["import.*@mui", "import.*React", "export.*function.*Component"]
  },
  "blockMessage": "frontend-dev-guidelines 스킬 사용 전까지 진행 차단",
  "skipConditions": {
    "sessionSkillUsed": true,
    "fileMarkers": ["@skip-validation"],
    "envOverride": "SKIP_FRONTEND_GUIDELINES"
  }
}
```

### Skill 4: route-tester
```json
{
  "type": "domain", "enforcement": "suggest", "priority": "high",
  "promptTriggers": {
    "keywords": ["test route", "test endpoint", "test API", "route testing", "API testing", "authenticated route", "JWT testing", "cookie auth"],
    "intentPatterns": ["(test|debug|verify).*?(route|endpoint|API)", "test.*?(authenticated|auth|JWT|cookie)"]
  },
  "fileTriggers": {
    "pathPatterns": ["**/routes/**/*.ts", "**/test-*.js", "**/test-*.ts"],
    "contentPatterns": ["router.(get|post|put|delete|patch)", "app.(get|post|put|delete|patch)"]
  }
}
```

### Skill 5: error-tracking
```json
{
  "type": "domain", "enforcement": "suggest", "priority": "high",
  "promptTriggers": {
    "keywords": ["error handling", "exception", "sentry", "error tracking", "captureException", "monitoring", "performance tracking"],
    "intentPatterns": ["(add|create|implement|setup).*?(error handling|sentry|error tracking)", "(how to|best practice).*?(error|sentry|monitoring)"]
  },
  "fileTriggers": {
    "pathPatterns": ["**/instrument.ts", "**/sentry*.ts", "**/*Controller.ts", "**/*Service.ts"],
    "contentPatterns": ["@sentry", "Sentry.", "captureException", "captureMessage"]
  }
}
```

## 500줄 규칙과 Progressive Disclosure 실제 구현

**Frontend-dev-guidelines 구조**:
```
SKILL.md (~400줄) <- 메인 파일, Quick Reference + 네비게이션 가이드
├── resources/component-patterns.md     # React.FC, lazy loading, SuspenseLoader
├── resources/data-fetching.md          # useSuspenseQuery, API 서비스 레이어
├── resources/file-organization.md      # features/ vs components/ 구조
├── resources/styling-guide.md          # MUI v7 Grid 문법
├── resources/routing-guide.md          # TanStack Router 폴더 기반
├── resources/loading-and-error-states.md
├── resources/performance.md            # useMemo, useCallback, React.memo
├── resources/typescript-standards.md
├── resources/common-patterns.md        # React Hook Form, DataGrid, Dialog
└── resources/complete-examples.md      # 전체 작동 예제
```

**Backend-dev-guidelines 구조**:
```
SKILL.md (~300줄) <- "Line Count: < 500, Progressive Disclosure: 11 resource files"
├── resources/architecture-overview.md
├── resources/routing-and-controllers.md
├── resources/services-and-repositories.md
├── resources/validation-patterns.md
├── resources/sentry-and-monitoring.md
├── resources/middleware-guide.md
├── resources/database-patterns.md
├── resources/configuration.md
├── resources/async-and-errors.md
├── resources/testing-guide.md
└── resources/complete-examples.md
```

**네비게이션 패턴**:
```markdown
## Navigation Guide
| Need to... | Read this resource |
|---|---|
| Create a component | [component-patterns.md](resources/component-patterns.md) |
| Fetch data | [data-fetching.md](resources/data-fetching.md) |
```

**컨텍스트 절감**: 전체 3000+ 토큰 대비, 메인(400) + 선택 리소스(300-500) = 평균 700-900 토큰 (70% 절감)

## 전체 10개 에이전트 목록

| 에이전트 | 모델 | 도구 | 핵심 역할 |
|----------|------|------|----------|
| `code-architecture-reviewer` | Sonnet | Read, Grep, Glob | 아키텍처 일관성 리뷰, TypeScript strict, 에러 핸들링, 서비스 통합 |
| `code-refactor-master` | Opus | Read, Write, Edit, Grep, Glob | 파일 구성, 의존성 추적, 컴포넌트 리팩터링, <300줄/컴포넌트 |
| `documentation-architect` | inherit | Read, Write, Grep, Glob | 개발자 가이드, README, API 문서, 데이터 흐름 다이어그램 |
| `frontend-error-fixer` | - | Read, Write, Edit, Grep, Glob, browser-tools MCP | 프론트엔드 에러 분류(빌드/런타임/네트워크/스타일링), 스크린샷 진단 |
| `plan-reviewer` | Opus | Read, Grep, Glob | 구현 전 계획 리뷰, DB 영향 평가, 의존성 매핑, 대안 평가 |
| `refactor-planner` | - | Read, Grep, Glob | 코드 구조 분석, 리팩터링 기회 식별, 단계별 계획 생성 |
| `web-research-specialist` | Sonnet | Read, WebSearch, WebFetch | 5-10개 검색 변형, GitHub/Reddit/SO 우선, 기술 리서치 |
| `auth-route-tester` | Sonnet | Read, Write, Edit, Bash | JWT 쿠키 인증 라우트 테스트, test-auth-route.js 활용, DB 검증 |
| `auth-route-debugger` | - | Read, Grep, Glob, Bash | PM2 로그 분석, 라우트 등록 확인, 쿠키/JWT 이슈 조사 |
| `auto-error-resolver` | - | Read, Write, Edit, Bash | TSC 에러 캐시에서 자동 수정, import -> 타입 -> 나머지 순서 |

## 전체 3개 슬래시 명령어

### /dev-docs
```
목적: 전략적 구현 계획 + 구조화된 태스크 분해
출력 디렉토리: dev/active/[task-name]/
├── [task-name]-plan.md       # Executive Summary, 현재/미래 상태, 구현 단계, 리스크
├── [task-name]-context.md    # 핵심 파일, 결정, 의존성
└── [task-name]-tasks.md      # 체크리스트 형식 태스크
```

### /dev-docs-update
```
목적: 컨텍스트 압축 전 문서 업데이트
트리거: 컨텍스트 한계 접근 시
업데이트 대상:
  - [task-name]-context.md: 현재 구현 상태, 결정, 수정 파일, 차단요소
  - [task-name]-tasks.md: 완료/진행 중/새 태스크 마킹
  - 핸드오프 노트: 편집 중인 파일/줄, 변경 목표, 테스트 명령
핵심: "코드만으로 재발견하기 어려운 정보 캡처에 집중"
```

### /route-research-for-testing
```
인수: [/extra/path ...]
허용 도구: Bash (cat, awk, grep, sort, xargs, sed)
모델: Sonnet
동작:
  1. 자동 생성된 라우트 목록(edited-files.log) + 사용자 지정 경로 결합
  2. 각 라우트에 대해 JSON 레코드 출력 (path, method, request/response shapes, payload 예제)
  3. auth-route-tester 서브에이전트로 스모크 테스트 실행
```

## 전체 Hook 스크립트

### skill-activation-prompt.sh + .ts (UserPromptSubmit)
```
1. skill-rules.json 로드
2. 사용자 프롬프트와 모든 스킬 트리거 매칭 (대소문자 무시)
3. 키워드 매칭 + 의도 패턴(정규식) 매칭
4. 우선순위별 그룹화: critical > high > medium > low
5. 포맷된 제안 출력:
   CRITICAL SKILLS (REQUIRED) -> RECOMMENDED -> SUGGESTED -> OPTIONAL
```

### post-tool-use-tracker.sh (PostToolUse - Edit/MultiEdit/Write)
```
1. 파일->레포 매핑 감지 (frontend, backend, packages/X 등)
2. 패키지 매니저 자동 감지 (pnpm > npm > yarn)
3. TSC 명령 감지 (tsconfig.app.json vs tsconfig.json)
4. 캐시 생성:
   - .claude/tsc-cache/{session_id}/edited-files.log
   - .claude/tsc-cache/{session_id}/affected-repos.txt
   - .claude/tsc-cache/{session_id}/commands.txt
```

### tsc-check.sh (PreToolUse)
```
1. 레포별 TypeScript 컴파일 체크
2. 에러 캐시에 저장 (last-errors.txt, affected-repos.txt, tsc-commands.txt)
3. 7일 초과 캐시 자동 정리
4. 출력: OK / Errors found + auto-error-resolver 에이전트 사용 권장
```

### stop-build-check-enhanced.sh (Stop)
```
1. affected-repos.txt에서 변경된 레포 읽기
2. 각 레포 TSC 실행
3. 에러 5개 이상 -> auto-error-resolver 추천
4. 에러 5개 미만 -> 직접 표시
5. Exit 0: 클린 / Exit 2: 에러 피드백
```
