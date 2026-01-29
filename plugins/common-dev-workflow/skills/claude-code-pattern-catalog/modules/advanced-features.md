# GitHub Actions, Extended Thinking, State Management

## 14. GitHub Actions 자동화 (claude-code-showcase)

4개의 자동화 워크플로우:

### 14.1 PR 코드 리뷰

```yaml
trigger: PR opened/synchronized/reopened, @claude 멘션
model: claude-opus-4-5-20251101
timeout: 30분
tools: [Read, Glob, Grep, Bash(git), Bash(gh pr)]
동작: .claude/agents/code-reviewer.md 기준으로 리뷰, 심각도별 피드백
```

### 14.2 의존성 감사

```yaml
schedule: 매월 1일, 15일 10:00 UTC
model: claude-opus-4-5-20251101
timeout: 45분
tools: [Read, Write, Edit, Glob, Grep, Bash(git/gh/npm)]
동작: npm outdated + npm audit → 보수적 업데이트 → lint/test 검증 → PR 생성
```

### 14.3 문서 동기화

```yaml
schedule: 매월 1일 09:00 UTC
model: claude-opus-4-5-20251101
timeout: 60분
동작: 최근 30일 코드 변경 vs 문서 비교 → 실제 틀린 내용만 수정
핵심: "변경 로그가 아닌 살아있는 문서 - 틀린 것만 수정"
```

### 14.4 코드 품질 리뷰

```yaml
schedule: 매주 일요일 08:00 UTC
model: claude-opus-4-5-20251101
timeout: 디렉토리당 45분
동작: 3개 랜덤 디렉토리 선택 → 병렬 리뷰 → 직접 수정 → PR 생성
검사항목: TypeScript strict, React 안티패턴, 코드 스타일, 에러 핸들링, 보안, 성능
```

---

## 15. Extended Thinking & Magic Keywords

### 15.1 Extended Thinking 모드 (oh-my-claudecode)

| 키워드 | 효과 |
|--------|------|
| `ultrathink`, `think`, `reason`, `ponder` | Extended Thinking 활성화 |
| 40+ 다국어 지원 | 한국어 '생각', '고민', '검토' / 일본어 '考え', '熟考' / 중국어 '思考' 등 |

**Thinking Budget 설정**:
```typescript
// Anthropic
{ thinking: { type: 'enabled', budgetTokens: 64000 }, maxTokens: 128000 }
// Amazon Bedrock
{ reasoningConfig: { type: 'enabled', budgetTokens: 32000 }, maxTokens: 64000 }
// Google
{ providerOptions: { google: { thinkingConfig: { thinkingLevel: 'HIGH' } } } }
// OpenAI
{ reasoning_effort: 'high' }
```

### 15.2 Magic Keywords (oh-my-claudecode)

| 키워드 | 트리거 | 효과 |
|--------|--------|------|
| `ultrawork` / `ulw` / `uw` | 최대 성능 모드 | 병렬 에이전트 오케스트레이션 활성화 |
| `search` / `find` / `locate` 등 16개 | 검색 모드 | 병렬 explore + researcher 에이전트, 첫 결과에 멈추지 않음 |
| `analyze` / `investigate` / `debug` 등 20개 | 분석 모드 | 컨텍스트 수집 → 심층 분석 → 복잡 시 architect 자문 |
| `ultrathink` / `think` / `reason` | 사고 모드 | Extended Thinking, 단계별 추론, 가정 검증 |

### 15.3 Model Routing Engine (oh-my-claudecode)

3종 시그널 추출 → 복잡도 점수 → 모델 티어 결정:

**시그널 유형**:
```
Lexical:    단어 수, 파일 경로 수, 코드 블록 수, 아키텍처/디버깅/단순 키워드, 질문 깊이
Structural: 예상 서브태스크 수, 크로스파일 의존성, 테스트 요구, 도메인 특수성, 되돌림 난이도, 영향 범위
Context:    이전 실패 횟수, 대화 턴 수, 계획 복잡도, 에이전트 체인 깊이
```

**가중치 및 점수**:
```
아키텍처 키워드: +3    디버깅 키워드: +2    단순 키워드: -2
리스크 키워드: +2      'Why' 질문: +2       크로스파일: +2
시스템 전체 영향: +3   이전 실패: +2/회     보안 도메인: +2
```

**티어 결정**: Score >= 8 → HIGH (Opus) / Score >= 4 → MEDIUM (Sonnet) / Score < 4 → LOW (Haiku)

---

## 16. State Management & Analytics

### 16.1 State Management (oh-my-claudecode)

```
.omc/
├── notepad.md                  # 3-섹션 메모 시스템
├── notepads/{plan-name}/       # Plan Wisdom 시스템
│   ├── learnings.md
│   ├── decisions.md
│   ├── issues.md
│   └── problems.md
├── state/
│   └── swarm.db               # Swarm 모드 SQLite DB
├── ultrapilot-state.json       # Ultrapilot 상태
└── pipeline-state.json         # Pipeline 상태
```

**Notepad 3-섹션 시스템**:
```
Priority Context (500자 제한) → 세션 시작 시 항상 주입
Working Memory (타임스탬프) → 7일 후 자동 정리
MANUAL → 자동 정리 없음, 사용자 제어
```

**Notepad 명령어**:
```
/note <content>              # Working Memory에 추가
/note --priority <content>   # Priority Context에 추가
/note --manual <content>     # MANUAL 섹션에 추가
/note --show                 # 전체 표시
/note --prune                # 7일 초과 항목 제거
```

### 16.2 Rate Limit 자동 대기 (oh-my-claudecode)

```
1. Claude API Rate Limit 상태 모니터링 (헤더 기반)
2. tmux 패널에서 Rate Limit 차단된 Claude 세션 감지
3. 백그라운드 데몬이 리셋 대기
4. 리셋 시 자동으로 차단된 패널에 재개 시퀀스 전송
```

**명령어**: `omc wait status`, `omc wait daemon start/stop`, `omc wait detect`

### 16.3 TRUST 5 품질 프레임워크 (moai-adk)

| 기준 | 의미 | 검증 방법 |
|------|------|----------|
| **T**ested | 85%+ 커버리지, 기존 코드는 특성화 테스트 | 유닛 테스트, LSP 타입 에러 = 0 |
| **R**eadable | 명확한 네이밍, 영문 주석 | 네이밍 규칙, LSP 린트 에러 = 0 |
| **U**nified | 일관된 스타일, ruff/black 포매팅 | 문서 완성, 코드 복잡도, LSP 경고 < 임계값 |
| **S**ecured | OWASP 준수, 입력 검증 | 보안 스캔, LSP 보안 경고 = 0 |
| **T**rackable | Conventional commits, 이슈 참조 | 구조화된 로그, LSP 진단 히스토리 |

**Phase별 LSP 임계값**:
```yaml
plan:  require_baseline: true
run:   max_errors: 0, max_type_errors: 0, max_lint_errors: 0, allow_regression: false
sync:  max_errors: 0, max_warnings: 10, require_clean_lsp: true
```

### 16.4 Configuration Sections (moai-adk)

```
.moai/config/sections/
├── git-strategy.yaml    # Git 워크플로우
├── language.yaml        # 언어 설정
├── llm.yaml            # LLM 모델 설정
├── pricing.yaml        # 비용 추적
├── project.yaml        # 프로젝트 메타데이터
├── quality.yaml        # TRUST 5 품질 게이트
├── ralph.yaml          # Ralph 엔진 설정
├── system.yaml         # 시스템 설정
├── user.yaml           # 사용자 개인화
└── workflow.yaml       # 워크플로우 실행 모드
```
