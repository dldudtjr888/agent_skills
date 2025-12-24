# Agent Mapping Rules

태스크 내용을 분석하여 최적의 서브에이전트를 자동 선택하는 규칙.

## 매핑 우선순위

1. **파일 경로 기반** (가장 높은 우선순위)
2. **작업 키워드 기반**
3. **완료 조건 기반**
4. **기본값** (매칭 없을 때)

## 파일 경로 기반 매핑

| 파일 패턴 | 에이전트 | 근거 |
|----------|---------|------|
| `**/test/**`, `**/*.spec.*`, `**/*.test.*` | `test-automator` | 테스트 파일 |
| `**/components/**`, `**/*.tsx`, `**/*.vue` | `frontend-architect` | UI 컴포넌트 |
| `**/api/**`, `**/routes/**`, `**/controllers/**` | `backend-architect` | API 레이어 |
| `**/migrations/**`, `**/schema/**` | `backend-architect` | DB 스키마 |
| `**/docs/**`, `**/*.md` | `technical-writer` | 문서 |
| `**/security/**`, `**/auth/**` | `security-auditor` | 보안 관련 |

## 작업 키워드 기반 매핑

### 테스트 관련 → `test-automator`
```
테스트, test, spec, jest, pytest, vitest,
unit test, integration test, e2e,
커버리지, coverage, mock, stub
```

### 리팩토링 관련 → `refactoring-expert`
```
리팩토링, refactor, 구조 개선, 코드 정리,
추출, extract, 분리, split, 통합, merge,
SOLID, DRY, 중복 제거, 클린 코드
```

### 성능 관련 → `performance-engineer`
```
성능, performance, 최적화, optimize,
캐시, cache, 병목, bottleneck,
프로파일링, profiling, 메모리, memory
```

### 보안 관련 → `security-auditor`
```
보안, security, 인증, authentication,
권한, authorization, 취약점, vulnerability,
XSS, SQL injection, CSRF, 암호화
```

### API/백엔드 관련 → `backend-architect`
```
API, endpoint, 라우터, router, 컨트롤러,
REST, GraphQL, DB, 스키마, migration
```

### 프론트엔드 관련 → `frontend-architect`
```
컴포넌트, component, UI, 프론트,
React, Vue, CSS, 스타일, 레이아웃
```

### 문서 관련 → `technical-writer`
```
문서, documentation, README, docs, 주석
```

## 복합 키워드 우선순위

여러 카테고리 해당 시:
1. **테스트** > 다른 모든 것
2. **보안** > 일반 백엔드
3. **성능** > 일반 구현

## 오버라이드

`@agent:` 태그로 자동 매핑 무시:

```markdown
- [ ] **T-007**: API 문서 작성 @agent:backend-architect
```

## 폴백

매핑 실패 시 `general-purpose` 사용.
