# Implementation Plan: [Change Name]

## Summary

| 항목 | 값 |
|------|-----|
| **Type** | Feature / Refactor / Bugfix / Modification |
| **Risk** | 🟢 Low / 🟡 Medium / 🔴 High |
| **Effort** | [X hours/days] |
| **Affected Files** | [N files] |

---

## Analysis Summary

### Tech Stack
- **Language**:
- **Framework**:
- **Database**:
- **Testing**:

### Key Files

| File | Purpose | Action |
|------|---------|--------|
| `path/to/file.ts` | [역할 설명] | Create / Modify / Review |
| `path/to/another.ts` | [역할 설명] | Modify |

### Dependencies

**Upstream (우리가 의존하는 것):**
- `module/path` - [용도]

**Downstream (우리에게 의존하는 것 - 검증 필요):**
- `module/path` - [사용 방식]

**Shared Resources:**
- Database: `table_name`
- External API: `service_name`
- Environment: `ENV_VAR_NAME`

### Patterns to Follow

| 패턴 | 컨벤션 |
|------|--------|
| **Naming** | camelCase / snake_case / PascalCase |
| **Error handling** | try-catch / Result type / Error boundary |
| **Data fetching** | useQuery / fetch / axios |
| **State management** | useState / Redux / Context |
| **File location** | `src/features/[feature]/` |

---

## Tasks

### Phase 1: Preparation [Xh]
- [ ] 관련 코드 읽고 이해
- [ ] 테스트 환경 설정
- [ ] 실패하는 테스트 먼저 작성 (TDD인 경우)

### Phase 2: Foundation [Xh]
- [ ] 타입/인터페이스 정의 (`path/to/types.ts`)
- [ ] 스키마/모델 정의 (`path/to/schema.ts`)
- [ ] DB 마이그레이션 (필요시)

Parallel tasks marked with (P)

### Phase 3: Implementation [Xh]
- [ ] 핵심 로직 구현 (depends on: 2.x)
- [ ] API 레이어 구현 (depends on: 2.x)
- [ ] UI 컴포넌트 구현 (depends on: 3.x)

### Phase 4: Integration [Xh]
- [ ] 컴포넌트 연결
- [ ] 라우팅/네비게이션 업데이트
- [ ] 권한/인증 연동

### Phase 5: Verification [Xh]
- [ ] 단위 테스트 작성/통과
- [ ] 통합 테스트 작성/통과
- [ ] 수동 테스트 시나리오 실행
- [ ] 문서 업데이트

**테스트 커버리지 목표:**
| 영역 | 최소 목표 | 권장 목표 |
|------|----------|----------|
| 핵심 비즈니스 로직 | 80% | 90%+ |
| 유틸리티 함수 | 70% | 85% |
| API 엔드포인트 | 80% | 90% |
| UI 컴포넌트 | 60% | 75% |

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| [무엇이 잘못될 수 있는가] | 🔴 High / 🟡 Medium / 🟢 Low | High / Medium / Low | [예방/복구 방법] |

### Security Checklist (High-Risk 변경 시)

auth/payment/data 관련 변경 시 반드시 확인:

- [ ] **입력 검증**: 모든 사용자 입력에 validation 적용
- [ ] **인증/인가**: 적절한 권한 체크 로직 포함
- [ ] **민감 데이터**: 로그에 PII/비밀번호 노출 금지
- [ ] **SQL Injection**: parameterized query 사용
- [ ] **XSS 방지**: 사용자 입력 이스케이프 처리
- [ ] **CSRF 토큰**: 상태 변경 요청에 CSRF 보호
- [ ] **Rate Limiting**: API 남용 방지 설정
- [ ] **에러 메시지**: 내부 정보 노출하지 않음
- [ ] **의존성 보안**: 취약한 패키지 여부 확인 (`npm audit` / `pip-audit`)

---

## Rollback Plan

배포 실패 시 복구 방법:

1. **즉시 롤백**: `git revert [commit]` 또는 이전 배포로 복원
2. **DB 롤백**: 마이그레이션 롤백 스크립트 (`migration down`)
3. **기능 플래그**: Feature flag OFF로 비활성화
4. **데이터 복구**: 백업에서 복원 (필요시)

---

## Handoff Notes

### task-decomposer 입력용

이 계획의 Tasks 섹션을 task-decomposer에 전달하면:
- 각 Task가 실행 가능한 세부 태스크로 분해됨
- 의존성 기반 웨이브 그룹핑
- 체크박스 마크다운 형식 출력

### 추가 컨텍스트

- [특이사항, 결정 사항, 논의 필요 사항 등]
