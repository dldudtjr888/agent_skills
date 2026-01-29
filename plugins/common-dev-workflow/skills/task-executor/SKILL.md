---
name: task-executor
description: "task-decomposer가 생성한 태스크 마크다운을 실행하는 스킬. Wave별 병렬 실행, 스킬 활용, 의존성 존중, 진행 상태 실시간 업데이트. 사용 시점: (1) 태스크 파일 실행 요청 시, (2) '태스크 실행해줘' 요청 시, (3) Wave 단위 자동 실행이 필요할 때"
---

# Task Executor

task-decomposer가 생성한 마크다운 태스크 파일을 입력받아 실제 실행한다.

## 핵심 기능

- **Wave 기반 병렬 실행**: 같은 Wave의 태스크를 `Task` 도구로 병렬 실행
- **스킬 활용**: 태스크 유형에 맞는 스킬(`Skill` 도구)을 자동 호출
- **스마트 에이전트 매핑**: 스킬이 없는 경우 최적 서브에이전트 선택
- **의존성 존중**: `blocked by` 관계 추적, 선행 완료 후 실행
- **실시간 상태 동기화**: 마크다운 체크박스 자동 업데이트
- **Resume (재개)**: 중단된 지점부터 이어서 실행 (자동 감지)
- **미리보기**: 실행 전 계획 분석 (사용자 요청 시)
- **참조 컨텍스트**: 참조 파일을 에이전트에게 자동 제공
- **동적 타임아웃**: ⏱️ 예상 시간 기반 타임아웃 설정
- **실행 리포트**: 완료 후 상세 보고서 생성

## 실행 방식 (자연어 기반)

Flag 없이 자연어로 요청:

```
# 기본 실행
"docs/tasks/인증-tasks.md 실행해줘"
"/task-executor docs/tasks/인증-tasks.md"

# 미리보기 (Dry-run)
"태스크 파일 미리보기만 해줘"
"실행하기 전에 분석부터 보여줘"

# 재개 (Resume) - 자동 감지
"이어서 실행해줘"
→ 파일에 [x], [!], [~] 있으면 자동으로 Resume 모드
```

### 자동 모드 감지

| 파일 상태 | 감지 모드 | 동작 |
|----------|----------|------|
| 모두 `[ ]` | 새로 시작 | Wave 1부터 실행 |
| 일부 `[x]` 존재 | Resume | 미완료 태스크부터 실행 |
| `[!]` 존재 | Resume + 확인 | 실패 태스크 재시도 여부 질문 |
| `[~]` 존재 | Resume | 진행 중이던 태스크 재시작 |

## 스킬 활용 (핵심!)

**하이브리드 방식**: task-decomposer가 제안한 스킬 우선 사용, 없으면 동적 탐색.

### 하이브리드 스킬 결정 로직

```
태스크에 `스킬:` 필드 있음?
    │
    Yes → 해당 스킬 사용 (검증 후)
    │       ↓
    │     available_skills에 존재?
    │       ├─ Yes → Skill 도구로 호출
    │       └─ No → 경고 후 동적 탐색으로 폴백
    │
    No → 동적 스킬 탐색
          ↓
        태스크 키워드 추출
          ↓
        available_skills description 매칭
          ↓
        매칭 스킬 발견? → Skill 도구로 호출
          ↓
        없으면 → 에이전트만 사용
```

### 스킬 필드 우선순위

1. **명시적 스킬 (최우선)**: 태스크의 `스킬:` 필드에 지정된 스킬
2. **동적 탐색 (폴백)**: 스킬 필드 없을 때 available_skills에서 매칭
3. **에이전트만 (최후)**: 스킬 없이 서브에이전트로 직접 실행

### 동적 스킬 탐색 (하드코딩 금지!)

**실행 시점에 사용 가능한 스킬 목록을 확인**:

```
1. Skill 도구의 available_skills 섹션 확인
2. 각 스킬의 description 파싱
3. 태스크 키워드와 description 매칭
4. 매칭되는 스킬 호출
```

### 스킬 매칭 알고리즘

```
태스크 제목/작업 내용에서 키워드 추출
    ↓
available_skills의 각 스킬 description과 비교
    ↓
관련도 높은 스킬 발견? ─Yes→ Skill 도구로 해당 스킬 호출
    │                        (스킬이 전문 지식 제공)
    No
    ↓
에이전트 키워드 매칭? ─Yes→ Task 도구로 서브에이전트 실행
    │
    No
    ↓
general-purpose 에이전트 사용
```

### 스킬 description 기반 매칭 예시

```
태스크: "UserService 리팩토링"
    ↓
available_skills 스캔:
  - code-refactoring: "리팩토링, 코드 품질 개선..."  ← 매칭!
  - sql-production-analyzer: "SQL 분석, 쿼리..."
  - task-planner: "계획, 설계..."
    ↓
Skill("code-refactoring") 호출
```

**중요**: 스킬 목록은 하드코딩하지 않음. 실행 시점에 동적으로 탐색.

### 스킬 활용 예시

#### 예시 1: 명시적 스킬 지정 (하이브리드 - 우선순위 1)

```markdown
# 태스크 (decomposer가 스킬 제안)
- [ ] **T-003**: UserService 리팩토링 ⏱️ 20분
  - 파일: `src/services/user.ts`
  - 스킬: `code-refactoring`  ← decomposer가 제안
  - 작업:
    - [ ] 중복 코드 추출
    - [ ] SOLID 원칙 적용
```

**실행 시**:
```
1. 스킬 필드 감지: "code-refactoring"
2. available_skills에서 존재 확인 ✓
3. Skill(skill: "code-refactoring") 호출 → 전문 지식 획득
4. Task(subagent_type: "refactoring-expert") 로 실제 작업 수행
```

#### 예시 2: 스킬 미지정 (동적 탐색 폴백)

```markdown
# 태스크 (스킬 필드 없음)
- [ ] **T-004**: API 엔드포인트 구현 ⏱️ 15분
  - 파일: `src/routes/users.ts`
  - 작업:
    - [ ] GET /users 구현
    - [ ] POST /users 구현
```

**실행 시**:
```
1. 스킬 필드 없음 → 동적 탐색
2. "API", "엔드포인트" 키워드 추출
3. available_skills 스캔 → "api-design-principles" 매칭
4. Skill(skill: "backend-development:api-design-principles") 호출
5. Task(subagent_type: "backend-architect") 로 실제 작업 수행
```

### 스킬 + 에이전트 조합 패턴

```
스킬 호출 (지식/가이드 획득)
    ↓
서브에이전트 실행 (실제 작업 수행)
    ↓
결과 검증
```

## 에이전트 매핑 (스킬 없을 때)

| 키워드 | 서브에이전트 타입 |
|--------|-----------------|
| 테스트, test, spec | `test-automator` |
| 성능, performance | `performance-engineer` |
| 보안, security | `security-auditor` |
| API, endpoint | `backend-architect` |
| 컴포넌트, UI | `frontend-architect` |
| 기본값 | `general-purpose` |

상세 매핑: [assets/agent-mapping.md](assets/agent-mapping.md)

## 서브에이전트 프롬프트 생성

스킬 컨텍스트를 포함한 프롬프트:

```markdown
## 태스크: {태스크 제목}

**스킬 가이드** (있는 경우):
{스킬에서 얻은 전문 지식/체크리스트}

**대상 파일**: {파일 경로} ({신규|수정})

**참조 컨텍스트**:
```{참조 파일}
{파일 내용}
```

**작업 목록**:
- [ ] {atomic 작업 1}
- [ ] {atomic 작업 2}

**검증 명령**:
- `{검증 명령}`

**수행 지침**:
1. 스킬 가이드의 패턴/체크리스트 따르기
2. 참조 컨텍스트의 기존 코드 패턴 참고
3. 각 작업 항목 순차 수행
4. 검증 명령 실행하여 확인
```

## 실행 전략

### 1. 파싱 & 모드 감지
```
태스크 파일 읽기
    ↓
상태 분석 → 모드 자동 결정 (새로시작/Resume)
    ↓
Wave/태스크/의존성 파싱
```

### 2. Wave 실행
```
Wave N 시작:
  ├── 미완료 태스크 추출
  ├── 각 태스크별:
  │   ├── 스킬 키워드 매칭 → Skill 도구 호출 (가이드 획득)
  │   ├── 에이전트 매핑
  │   ├── 참조 파일 로드
  │   └── 타임아웃 계산
  ├── 병렬 서브에이전트 실행 (최대 5개)
  │   └── Task(run_in_background=true)
  ├── 결과 수집 (TaskOutput)
  ├── 체크박스 업데이트
  └── 실패 시 롤백

모든 Wave 완료 → Verification → 리포트 생성
```

## 병렬 실행 패턴

```
Wave 2에 T-003, T-004, T-005가 있을 때:

# 1. 스킬 탐색 & 호출 (필요한 경우만)
T-003 "리팩토링" → available_skills 스캔 → 매칭 스킬 호출 → 가이드 획득
T-004 "SQL 분석" → available_skills 스캔 → 매칭 스킬 호출 → 가이드 획득
T-005 "API 구현" → 매칭 스킬 없음 → 에이전트만 사용

# 2. 에이전트 병렬 실행
Task(T-003 + 스킬가이드, run_in_background=true) → id_1
Task(T-004 + 스킬가이드, run_in_background=true) → id_2
Task(T-005, run_in_background=true) → id_3

# 3. 결과 수집
TaskOutput(id_1) → 결과1
TaskOutput(id_2) → 결과2
TaskOutput(id_3) → 결과3

# 마크다운 업데이트 → Wave 3
```

## 미리보기 (Dry-run)

"미리보기", "분석만", "실행 전에 확인" 요청 시:

```
📋 실행 계획 분석

총 태스크: 16개 | Wave: 4개 | 예상 시간: ~95분

Wave 1 (병렬 4개):
  T-001 "리팩토링" → 스킬: code-refactoring (명시) + refactoring-expert
  T-002 "UI 컴포넌트" → 스킬 없음 → frontend-architect

Wave 2 (병렬 4개):
  T-003 "API 설계" → 스킬: api-design-principles (명시) + backend-architect
  T-004 "테스트" → 동적 탐색 예정 → test-automator
  ...

스킬 활용:
  - 명시적 지정: N개
  - 동적 탐색 예정: M개
서브에이전트: K개

⚠️ 주의:
  - T-005: 롤백 명령 없음
  - T-003: 크리티컬 패스

실행할까요?
```

## Resume (재개)

파일 상태 기반 자동 감지 + 사용자 확인:

```
📂 태스크 파일 분석

상태:
  ✅ 완료: 8개
  ❌ 실패: 1개 (T-005)
  ⏭️ 스킵: 1개 (T-007, T-005 의존)
  ⏳ 대기: 6개

T-005 재시도할까요?
[1] 재시도 - 다시 실행
[2] 스킵 - 건너뛰고 계속
[3] 수동 수정 - 직접 고친 후 계속
```

상세: [references/resume-strategy.md](references/resume-strategy.md)

## 입력 형식 (새 템플릿 호환)

```markdown
- [ ] **T-001**: [태스크 제목] ⏱️ 10분
  - 파일: `path/to/file.ts` (신규)
  - 참조: `similar/file.ts`
  - 스킬: `code-refactoring` (선택, decomposer가 제안)
  - 작업:
    - [ ] 첫 번째 atomic 작업
    - [ ] 두 번째 atomic 작업
  - 검증:
    - [ ] `npm test`
  - 롤백: `git checkout -- path/to/file.ts`
  - blocked by: T-000
```

### 필드별 처리

| 필드 | 처리 방식 |
|------|----------|
| ⏱️ 시간 | 타임아웃 = 시간 × 1.5 + 2분 |
| 참조 | 에이전트 프롬프트에 포함 |
| 스킬 | 우선 사용, 없으면 동적 탐색 |
| 작업 | 개별 체크박스 업데이트 |
| 검증 | 명령 실행 후 체크 |
| 롤백 | 실패 시 자동 실행 |

## 상태 표기법

| 마커 | 의미 |
|------|------|
| `- [ ]` | 대기 중 |
| `- [x]` | 완료 |
| `- [!]` | 실패 |
| `- [-]` | 스킵됨 |
| `- [~]` | 진행 중 |

## 에러 처리

1. 롤백 명령 있으면 자동 실행
2. `- [!]`로 마킹 + 에러 메시지 추가
3. 의존 태스크 자동 스킵 (`- [-]`)
4. 사용자에게 옵션 제시

상세: [references/error-handling.md](references/error-handling.md)

## 실행 리포트

완료 후 상세 보고서:

```markdown
# 실행 리포트

## 요약
| 항목 | 값 |
|------|-----|
| 성공 | 14개 (87.5%) |
| 실패 | 1개 |
| 스킬 활용 | N회 (동적 탐색) |
| 소요 시간 | 47분 |

## 스킬 활용 통계
| 스킬 | 사용 횟수 |
|------|----------|
| [실행 중 발견된 스킬들] | N |

## 권장 조치
1. T-005 수동 수정 후 재실행
```

템플릿: [assets/report-template.md](assets/report-template.md)

## 제약 사항

| 항목 | 제한 |
|------|------|
| 동시 에이전트 | 최대 5개 |
| 기본 타임아웃 | 10분 |
| 최대 타임아웃 | 30분 |
| 재시도 | 2회 |

## Quick Start

```
# 태스크 생성
/task-decomposer "인증 기능 계획.md"

# 미리보기
"태스크 미리보기 해줘"

# 실행
/task-executor "docs/tasks/인증-tasks.md"
또는
"태스크 실행해줘"

# 중단 후 재개 (자동 감지)
"이어서 실행해줘"
```

## 관련 스킬

- **task-decomposer**: 계획 → 태스크 변환 (이 스킬의 입력 생성)
- **task-planner**: 프로젝트 분석 → 계획 생성
- **기타 모든 스킬**: 태스크 키워드에 따라 동적으로 탐색 및 활용
