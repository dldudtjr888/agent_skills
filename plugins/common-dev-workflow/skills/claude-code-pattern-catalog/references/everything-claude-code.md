# everything-claude-code

## 전체 17+ 슬래시 명령어

| 명령어 | 목적 |
|--------|------|
| `/build-fix` | 빌드 에러 자동 감지/해결 |
| `/checkpoint` | Git 스테이징으로 프로젝트 스냅샷 생성 |
| `/code-review` | 최근 변경 코드 품질/보안/유지보수성 리뷰 |
| `/e2e` | E2E 테스팅 (핵심 사용자 여정) |
| `/eval` | 코드 품질, 테스트 커버리지, 성능 메트릭 평가 |
| `/evolve` | 본능 클러스터링 → 스킬/커맨드/에이전트 진화 |
| `/go-build` | Go 빌드/컴파일 |
| `/go-review` | Go 코드 리뷰 (Go-specific 검사) |
| `/go-test` | Go 테스트 실행/품질 검증 |
| `/instinct-export` | 모든 본능 파일 내보내기 |
| `/instinct-import` | 파일/URL에서 본능 가져오기 |
| `/instinct-status` | 본능 상태 표시 (도메인별, 신뢰도 막대) |
| `/learn` | 관찰에서 패턴 추출 → 본능 생성 |
| `/orchestrate` | 다중 에이전트 순차/병렬 실행 |
| `/plan` | 기능 구현 상세 계획 생성 |
| `/refactor-clean` | 데드코드 정리/통합 (knip, depcheck, ts-prune) |
| `/setup-pm` | 패키지 매니저 감지/설정 |
| `/skill-create` | 코드 패턴/본능에서 새 스킬 생성 |
| `/tdd` | TDD 워크플로우 (테스트 먼저 작성 강제) |
| `/test-coverage` | 코드 커버리지 분석/리포팅 |
| `/update-codemaps` | 코드 아키텍처 맵 재생성 |
| `/update-docs` | 코드와 문서 동기화 |
| `/verify` | 배포 전 종합 체크 |

## 전체 11개 에이전트

| 에이전트 | 모델 | 핵심 역할 |
|----------|------|----------|
| `architect` | Opus | 시스템 설계/아키텍처, 리팩터링 제안 |
| `build-error-resolver` | Opus | 컴파일 에러 분석, 최소 수술적 수정 |
| `code-reviewer` | Opus | 가독성, 중복, 에러 핸들링, 보안, 입력 검증, 테스트 커버리지, 성능 |
| `database-reviewer` | Opus | PostgreSQL 쿼리 최적화, 스키마 설계, RLS, JSONB, 인덱스 전략 |
| `doc-updater` | Opus | AST 분석(ts-morph), 의존성 매핑, JSDoc 추출 |
| `e2e-runner` | Opus | Vercel Agent Browser (주) + Playwright (보조), 테스트 아티팩트 캡처 |
| `go-build-resolver` | Opus | Go 컴파일 에러, go vet, staticcheck, golangci-lint |
| `go-reviewer` | Opus | Go 관용적 코드, SQL/Command injection, race condition, goroutine leak |
| `planner` | Opus | 구현 계획, 단계 분해, 리스크 평가, 테스트 전략 |
| `refactor-cleaner` | Opus | knip, depcheck, ts-prune, ESLint → DELETION_LOG.md |
| `security-reviewer` | Opus | OWASP Top 10, 하드코딩된 시크릿, SQL/XSS/SSRF, race condition |
| `tdd-guide` | Opus | TDD 방법론 강제, 80%+ 커버리지, 유닛/통합/E2E |

## Hook 설정 상세

### PreToolUse (4개)

| 매처 | 액션 |
|------|------|
| `npm run dev` 등 | tmux 밖 dev 서버 차단 |
| `npm install/test`, `pnpm`, `yarn`, `cargo`, `docker`, `pytest`, `playwright` | tmux 세션 지속성 리마인더 |
| `git push` | 푸시 전 변경사항 리뷰 리마인더 |
| Write (`.md`/`.txt` 파일) | 불필요한 문서 파일 생성 차단 |
| Edit/Write | suggest-compact.js: 논리적 간격에서 수동 압축 제안 |

### PostToolUse (5개)

| 매처 | 액션 |
|------|------|
| Bash | PR URL 추출 → 리뷰 커맨드 제공 |
| `npm/pnpm/yarn build` | 비동기 완료 알림 (30초 타임아웃) |
| Edit (`.ts/.tsx/.js/.jsx`) | Prettier 자동 포맷 |
| Edit (`.ts/.tsx`) | TypeScript 컴파일러 체크 (파일당 처음 10개 에러) |
| Edit (JS/TS 파일) | console.log 경고 (최대 5개 표시) |

### SessionStart (1개)

- `*` 매처: 이전 컨텍스트 로드 + 패키지 매니저 감지

### PreCompact (1개)

- `*` 매처: pre-compact.js → 압축 전 상태 저장

### Stop (1개)

- `*` 매처: check-console-log.js → 수정된 파일에서 console.log 감사

### SessionEnd (2개)

- session-end.js: 세션 상태 영속화
- evaluate-session.js: 추출 가능한 패턴 평가

## Contexts 시스템

### dev.md (개발 모드)

```
우선순위: 동작하게 → 올바르게 → 깔끔하게
행동: 코드 먼저, 설명 후 / 완벽보다 동작 / 변경 후 테스트 / 원자적 커밋
선호 도구: Edit, Write, Bash, Grep, Glob
```

### research.md (리서치 모드)

```
프로세스: 이해 → 탐색 → 가설 → 검증 → 요약
행동: 넓게 읽고 결론 / 명확화 질문 / 발견 기록 / 이해 전 코드 금지
선호 도구: Read, Grep/Glob, WebSearch/WebFetch, Task(Explore)
출력: 발견사항 먼저, 권고사항 두 번째
```

### review.md (리뷰 모드)

```
우선순위: critical > high > medium > low
체크리스트: 로직 에러, 엣지케이스, 에러 핸들링, 보안(injection, auth, secrets), 성능, 가독성, 커버리지
행동: 문제 지적만 하지 말고 수정 제안 / 파일별 그룹화, 심각도 우선
```

## Instinct CLI 상세 (instinct-cli.py)

**4개 명령어**:

```bash
# 상태 표시 (도메인별 그룹, 신뢰도 프로그레스 바)
instinct-cli.py status

# 가져오기 (파일/URL)
instinct-cli.py import <source> [--dry-run] [--force] [--min-confidence 0.5]

# 내보내기 (YAML 형식)
instinct-cli.py export [--output file.yaml] [--domain workflow] [--min-confidence 0.5]

# 진화 (스킬/커맨드/에이전트 후보 분석)
instinct-cli.py evolve [--generate]
# - 스킬 후보: 3+ 유사 트리거 본능
# - 커맨드 후보: 70%+ 신뢰도 워크플로우 본능
# - 에이전트 후보: 3+ 본능, 75%+ 평균 신뢰도
```

## Observer 에이전트 상세

**실행 조건**: 20+ 도구 호출 후 / `/analyze-patterns` / 5분 간격 / SIGUSR1

**패턴 감지 유형**:
1. **User Corrections**: 사용자 교정 감지 ("No, use X instead of Y")
2. **Error Resolutions**: 동일 에러 유형의 반복 해결 패턴
3. **Repeated Workflows**: 반복되는 도구 시퀀스, 함께 변경되는 파일
4. **Tool Preferences**: Grep→Edit 등 도구 사용 선호도

**Observer 루프**:

```bash
start-observer.sh           # 백그라운드 시작
start-observer.sh stop      # 중지
start-observer.sh status    # 상태 확인

# 내부 루프:
1. 10+ 관찰 존재 확인
2. Claude Haiku로 패턴 분석
3. 명확한 패턴에서 본능 생성
4. 처리된 관찰 아카이빙
5. 5분 대기 → 반복
```

**가이드라인**: 보수적 (3+ 관찰), 구체적 (좁은 트리거), 증거 추적, 프라이버시 (코드 스니펫 제외), 유사 본능 머지

## 패키지 매니저 설정

```json
{
  "packageManager": "bun",
  "setAt": "2026-01-23T02:09:58.819Z"
}
```

SessionStart 훅에서 감지, 이후 빌드/테스트 명령에 활용.
