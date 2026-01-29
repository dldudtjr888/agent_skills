# web-frontend

웹 프론트엔드 개발 전문 플러그인 - React, Next.js, TypeScript, Tailwind CSS

## Vercel 스킬과 함께 사용하기 (권장)

이 플러그인은 **Vercel 공식 스킬과 보완적으로 설계**되었습니다. 최상의 경험을 위해 함께 설치하세요.

```bash
# Vercel 공식 스킬 설치 (React/Next.js 성능, UI 가이드라인, 컴포지션 패턴)
npx skills add vercel-labs/agent-skills

# 이 플러그인 설치
/plugin install web-frontend@hibye-plugins
```

### 역할 분담

| 영역 | Vercel 스킬 | web-frontend |
|------|------------|--------------|
| React/Next.js 성능 최적화 | react-best-practices | - |
| UI/UX, 접근성 가이드 | web-design-guidelines | - |
| 컴포넌트 조합 패턴 | composition-patterns | - |
| 상태 관리 패턴 | - | state-management |
| Tailwind CSS 가이드 | - | tailwind-styling |
| TypeScript 심화 | - | typescript-advanced |
| 테스팅 가이드 | - | testing-guide |
| 프론트엔드 보안 | - | frontend-security |
| 에이전트 (리뷰/에러/성능) | - | 전담 |

---

## 언제 무엇을 사용하나요? (상세 시나리오)

### 시나리오 1: 새 컴포넌트 작성

```
"버튼 컴포넌트 만들어줘"
```

| 단계 | 사용 스킬/에이전트 | 역할 |
|------|-------------------|------|
| 1. 컴포넌트 구조 설계 | Vercel `composition-patterns` | 확장 가능한 API 설계 |
| 2. 스타일링 | web-frontend `tailwind-styling` | CVA variants, cn() 사용 |
| 3. 타입 정의 | web-frontend `typescript-advanced` | Props 제네릭, HTML 확장 |
| 4. 성능 검증 | Vercel `react-best-practices` | memo, useCallback 적용 |
| 5. 테스트 작성 | web-frontend `testing-guide` | Testing Library 테스트 |

**워크플로우 예시:**
```bash
# 1단계: 컴포넌트 구조 (Vercel)
"compound component 패턴으로 Select 컴포넌트 설계해줘"

# 2단계: 스타일링 (web-frontend)
"CVA로 Select variants 만들어줘"

# 3단계: 타입 (web-frontend)
"Select Props에 제네릭 적용해줘"

# 4단계: 테스트 (web-frontend)
"Select 컴포넌트 테스트 작성해줘"
```

---

### 시나리오 2: 기존 코드 리팩토링

```
"이 컴포넌트 리팩토링해줘"
```

| 상황 | 사용 스킬/에이전트 | 언제 |
|------|-------------------|------|
| Props가 10개 이상 | Vercel `composition-patterns` | boolean prop proliferation 해결 |
| 성능 문제 (리렌더) | Vercel `react-best-practices` | memo, useMemo, useCallback |
| 상태 로직 복잡 | web-frontend `state-management` | Zustand/Jotai로 분리 |
| 타입 안전성 부족 | web-frontend `typescript-advanced` | 타입 가드, 브랜드 타입 |
| 전반적 코드 품질 | web-frontend `refactorer` | 데드코드, 파일 정리 |

**결정 가이드:**
```
컴포넌트 구조/패턴 문제? → Vercel composition-patterns
렌더링 성능 문제? → Vercel react-best-practices
상태 관리 문제? → web-frontend state-management
타입 문제? → web-frontend typescript-advanced
전체 코드 정리? → web-frontend refactorer 에이전트
```

---

### 시나리오 3: 페이지 데이터 페칭

```
"API에서 데이터 가져오는 페이지 만들어줘"
```

| 단계 | 사용 스킬/에이전트 | 역할 |
|------|-------------------|------|
| Next.js RSC/SSR 결정 | Vercel `react-best-practices` | 서버/클라이언트 분리 |
| 클라이언트 캐싱 | web-frontend `state-management` | TanStack Query 패턴 |
| 로딩/에러 UI | Vercel `web-design-guidelines` | Skeleton, 에러 바운더리 |
| 타입 안전 API | web-frontend `typescript-advanced` | Zod 스키마, 타입 추론 |

**데이터 페칭 결정 트리:**
```
서버에서 한 번만 필요? → Next.js RSC (Vercel react-best-practices)
클라이언트에서 실시간 동기화? → TanStack Query (web-frontend state-management)
URL 상태로 공유 필요? → nuqs (web-frontend state-management)
전역 클라이언트 상태? → Zustand (web-frontend state-management)
```

---

### 시나리오 4: UI 디자인 & 접근성

```
"대시보드 UI 디자인해줘"
```

| 관심사 | 사용 스킬/에이전트 | 역할 |
|--------|-------------------|------|
| 접근성 (a11y) | Vercel `web-design-guidelines` | WCAG, 키보드 내비게이션 |
| 시각 디자인 | web-frontend `designer` | 타이포그래피, 색상, 애니메이션 |
| 반응형 레이아웃 | web-frontend `tailwind-styling` | 브레이크포인트, 컨테이너 쿼리 |
| 다크 모드 | web-frontend `tailwind-styling` | CSS 변수, next-themes |

**디자인 체크리스트:**
```
☐ 접근성 검토 필요? → Vercel web-design-guidelines
☐ 시각적으로 돋보여야 함? → web-frontend designer 에이전트
☐ Tailwind 스타일링? → web-frontend tailwind-styling
☐ 컴포넌트 상호작용? → Vercel composition-patterns
```

---

### 시나리오 5: 보안 & 테스트

```
"프로덕션 배포 전 점검해줘"
```

| 관심사 | 사용 에이전트 | 역할 |
|--------|--------------|------|
| 보안 취약점 | `security-reviewer` | XSS, CSRF, 인젝션 검토 |
| 코드 품질 | `code-reviewer` | 패턴, 안티패턴, 성능 |
| 유닛 테스트 | `tdd-guide` | 테스트 커버리지 확보 |
| E2E 테스트 | `e2e-runner` | 핵심 플로우 검증 |
| 번들 크기 | `bundle-analyzer` | 코드 스플리팅, 트리쉐이킹 |
| 성능 지표 | `performance-optimizer` | Core Web Vitals |

**배포 전 체크 순서:**
```bash
# 1. 보안 검토
"보안 취약점 검토해줘" → security-reviewer

# 2. 코드 리뷰
"코드 품질 점검해줘" → code-reviewer

# 3. 테스트 확인
"테스트 커버리지 확인하고 부족한 테스트 추가해줘" → tdd-guide

# 4. E2E 테스트
"핵심 유저 플로우 E2E 테스트 실행해줘" → e2e-runner

# 5. 성능 분석
"번들 크기 분석해줘" → bundle-analyzer
"Core Web Vitals 점검해줘" → performance-optimizer
```

---

### 시나리오 6: 에러 해결

```
"빌드 에러 고쳐줘" / "TypeScript 에러 해결해줘"
```

| 에러 유형 | 사용 | 역할 |
|----------|------|------|
| TypeScript 에러 | `error-resolver` | 타입 오류 진단 및 수정 |
| 빌드 에러 | `error-resolver` | Webpack/Vite/Next.js 에러 |
| 런타임 에러 | `error-resolver` | React 에러 바운더리, 예외 처리 |
| 성능 에러 (hydration) | Vercel `react-best-practices` | SSR/CSR 불일치 해결 |

---

## Vercel 스킬 vs web-frontend 빠른 참조

| 질문 | 답변 |
|------|------|
| "memo 써야 해?" | Vercel `react-best-practices` |
| "Zustand vs Context?" | web-frontend `state-management` |
| "compound component가 뭐야?" | Vercel `composition-patterns` |
| "CVA variants 어떻게?" | web-frontend `tailwind-styling` |
| "접근성 체크해줘" | Vercel `web-design-guidelines` |
| "XSS 방어 어떻게?" | web-frontend `frontend-security` |
| "제네릭 타입 어떻게?" | web-frontend `typescript-advanced` |
| "Vitest 설정해줘" | web-frontend `testing-guide` |
| "RSC vs 클라이언트?" | Vercel `react-best-practices` |
| "TanStack Query 캐싱?" | web-frontend `state-management` |

---

## Skills

| Skill | Description |
|-------|-------------|
| state-management | Zustand, Jotai, TanStack Query 상태 관리 패턴 |
| tailwind-styling | Tailwind CSS, CVA, cn() 스타일링 가이드 |
| typescript-advanced | 고급 TypeScript 패턴, 제네릭, 유틸리티 타입 |
| testing-guide | Vitest, Testing Library, Playwright 테스팅 |
| frontend-security | XSS, CSRF, CSP 등 프론트엔드 보안 |

## Agents

### 코드 품질

| Agent | Description |
|-------|-------------|
| code-reviewer | 코드 리뷰 (품질, 보안, 성능, 아키텍처) |
| security-reviewer | 보안 취약점 검토 (OWASP Top 10) |
| refactorer | 리팩토링, 데드코드 제거, 파일 정리 |

### 에러 해결

| Agent | Description |
|-------|-------------|
| error-resolver | TypeScript/빌드/런타임 에러 통합 해결 |

### 성능

| Agent | Description |
|-------|-------------|
| performance-optimizer | Core Web Vitals, 렌더링 최적화 |
| bundle-analyzer | 번들 분석, 크기 최적화 |

### 디자인 & 테스트

| Agent | Description |
|-------|-------------|
| designer | UI/UX 디자인, 프레임워크별 컴포넌트 |
| tdd-guide | TDD 가이드, 테스트 작성 |
| e2e-runner | Playwright E2E 테스트 |

## Usage

```bash
# 기본 설치
/plugin install web-frontend@hibye-plugins

# Vercel 스킬과 함께 (권장)
npx skills add vercel-labs/agent-skills
/plugin install web-frontend@hibye-plugins

# common-dev-workflow와 함께 사용
/plugin install common-dev-workflow@hibye-plugins
```

## 스킬 트리거 예시

```
# 상태 관리
"zustand로 전역 상태 만들어줘"
"TanStack Query 캐싱 전략 알려줘"

# Tailwind
"CVA로 버튼 variants 만들어줘"
"Tailwind dark mode 설정해줘"

# TypeScript
"제네릭 컴포넌트 타입 어떻게 해?"
"Zod로 타입 검증하는 법"

# 테스팅
"Vitest로 컴포넌트 테스트 작성해줘"
"MSW 목킹 설정해줘"

# 보안
"XSS 방어 어떻게 해?"
"CSP 설정 도와줘"
```

## 에이전트 사용 예시

```
# 코드 리뷰
"방금 작성한 코드 리뷰해줘" → code-reviewer

# 에러 해결
"빌드 에러 고쳐줘" → error-resolver
"TypeScript 에러 해결해줘" → error-resolver

# 성능
"성능 분석해줘" → performance-optimizer
"번들 크기 줄여줘" → bundle-analyzer

# 리팩토링
"데드코드 정리해줘" → refactorer
"컴포넌트 분리해줘" → refactorer
```

## Version

- **2.0.0** - Vercel 스킬 연계, 에이전트 통합/정리, 새 스킬 추가
