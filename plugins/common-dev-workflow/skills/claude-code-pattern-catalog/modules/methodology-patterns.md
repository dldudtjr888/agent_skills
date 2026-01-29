# 방법론 패턴

## Ralph 방법론 (ralph-playbook)

```
Phase 1: 정의 (LLM과 대화로 요구사항/스펙 작성)
    ↓
Phase 2: PLANNING 모드
    - PROMPT_plan.md로 "현재 코드 vs 스펙" 비교
    - IMPLEMENTATION_PLAN.md 생성
    ↓
Phase 3: BUILDING 모드 (무한 루프)
    - PROMPT_build.md로 계획 실행
    - 테스트 검증 (백프레셔)
    - git commit & push
    - IMPLEMENTATION_PLAN.md 업데이트
    → 반복
```

핵심: `loop.sh`가 매 반복마다 fresh context로 claude CLI 실행. IMPLEMENTATION_PLAN.md가 공유 상태.

## SPEC-First DDD (moai-adk)

```
Plan Phase (30K tokens): /moai:1-plan
    - SPEC 문서 작성 (EARS 형식)
    - /clear 후 다음 단계
    ↓
Run Phase (180K tokens): /moai:2-run
    - DDD 구현 (ANALYZE → PRESERVE → IMPROVE)
    - TRUST 5 품질 게이트
    ↓
Sync Phase (40K tokens): /moai:3-sync
    - 문서 동기화
    - PR 생성
```

## Continuous Learning v2 (everything-claude-code)

```
Session Activity
    → Hooks 관찰 (PreToolUse/PostToolUse)
    → Instincts 생성 (신뢰도 0.3-0.9)
    → 패턴 클러스터링
    → Skills/Commands/Agents로 진화
```

### 디렉토리 구조

```
~/.claude/homunculus/
├── observations.jsonl        # 현재 세션 관찰 기록
├── observations.archive/     # 처리된 관찰 기록
├── instincts/
│   ├── personal/            # 자동 학습된 본능
│   └── inherited/           # 다른 사용자로부터 임포트
└── evolved/
    ├── agents/              # 생성된 전문 에이전트
    ├── skills/              # 생성된 스킬
    └── commands/            # 생성된 명령어
```

### Observer Agent

Haiku 모델, 백그라운드 실행:
- 트리거: 20+ 도구 호출 후, 5분 간격, `/analyze-patterns` 명령
- 패턴 감지 유형: user_corrections, error_resolutions, repeated_workflows, tool_preferences, file_patterns

### 신뢰도 점수 시스템

```
관찰 1-2회:  0.3 (잠정)
관찰 3-5회:  0.5 (보통)
관찰 6-10회: 0.7 (강함)
관찰 11+회:  0.85 (매우 강함)

보정: 확인 관찰 +0.05 / 반박 관찰 -0.1 / 주당 감쇠 -0.02
```

### Instinct 파일 형식

```yaml
---
id: prefer-grep-before-edit
trigger: "when searching for code to modify"
confidence: 0.65
domain: "workflow"
source: "session-observation"
---

# Prefer Grep Before Edit
## Action
Always use Grep to find the exact location before using Edit.
## Evidence
- Observed 8 times in session abc123
- Pattern: Grep → Read → Edit sequence
```

### Instinct CLI 및 진화 파이프라인

CLI 명령어: `/instinct-status`, `/instinct-import`, `/instinct-export`, `/evolve`

진화 파이프라인: 3+ 관련 본능 클러스터링 → Commands (명시적 요청), Skills (자동 행동), Agents (다단계 워크플로우)

## Execution Modes (oh-my-claudecode)

7가지 실행 모드와 각각의 특징:

| 모드 | 핵심 특징 | 에이전트 수 | 모델 기본값 |
|------|----------|------------|-----------|
| **Autopilot** | 5단계 자율 실행 (Expansion→Planning→Execution→QA→Validation) | 4-5 병렬 | Opus (분석), Sonnet (실행) |
| **Ultrapilot** | 파일 소유권 분할 병렬 (최대 5x 속도) | 최대 5 워커 | 혼합 |
| **Ultrawork** | 최대 성능, 공격적 위임, 백그라운드 실행 | 무제한 | 티어 기반 |
| **Ralph** | 자기 참조 루프, Architect 검증까지 멈추지 않음 | 2+ | Opus (검증) |
| **Ecomode** | 토큰 절약, Haiku/Sonnet만 사용 | 3-5 | Haiku 우선 |
| **Swarm** | SQLite 기반 원자적 태스크 클레이밍, 하트비트 모니터링 | N 에이전트 | 혼합 |
| **Pipeline** | 순차 에이전트 체이닝, 데이터 전달 | 스테이지별 1 | 스테이지별 |

### Ultrapilot 파일 파티셔닝 예시

```
Worker 1: src/api/**     (exclusive)
Worker 2: src/ui/**      (exclusive)
Worker 3: src/db/**      (exclusive)
Worker 4: docs/**        (exclusive)
Worker 5: tests/**       (exclusive)
SHARED:   package.json, tsconfig.json (순차 처리)
```

### Swarm SQLite 스키마

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending/claimed/done/failed
  claimed_by TEXT,
  claimed_at INTEGER,
  completed_at INTEGER
);

CREATE TABLE heartbeats (
  agent_id TEXT PRIMARY KEY,
  last_heartbeat INTEGER NOT NULL,
  current_task_id TEXT
);
```

### Pipeline 빌트인 프리셋

```
review:    explore → architect → critic → executor
implement: planner → executor → tdd-guide
debug:     explore → architect → build-fixer
research:  parallel(researcher, explore) → architect → writer
refactor:  explore → architect-medium → executor-high → qa-tester
security:  explore → security-reviewer → executor → security-reviewer-low
```

## Ralph loop.sh 메커니즘 (ralph-playbook)

```bash
while true; do
    cat "$PROMPT_FILE" | claude -p \
        --dangerously-skip-permissions \
        --output-format=stream-json \
        --model opus \
        --verbose

    git push origin "$CURRENT_BRANCH" || {
        git push -u origin "$CURRENT_BRANCH"
    }

    ITERATION=$((ITERATION + 1))
done
```

**환경 변수**: `MODE` (plan/build), `PROMPT_FILE`, `MAX_ITERATIONS`, `CURRENT_BRANCH`

### Claude CLI 플래그

- `-p`: 헤드리스 모드 (비대화형, stdin에서 읽기)
- `--dangerously-skip-permissions`: 모든 도구 호출 자동 승인
- `--output-format=stream-json`: 구조화된 출력
- `--model opus`: 복잡한 추론용

### PROMPT_plan.md 핵심 지시

- 최대 500개 Sonnet 서브에이전트로 specs/* vs src/* 비교
- Opus 서브에이전트로 분석, 우선순위화
- IMPLEMENTATION_PLAN.md 생성/업데이트
- **구현 금지** - 갭 분석만

### PROMPT_build.md 핵심 지시

- IMPLEMENTATION_PLAN.md에서 가장 중요한 항목 선택
- 최대 500 Sonnet 서브에이전트(검색), 1 Sonnet 서브에이전트(빌드)
- 테스트 통과 → git commit → git push
- IMPLEMENTATION_PLAN.md를 공유 상태로 계속 업데이트

핵심 원칙: 매 반복마다 fresh context. IMPLEMENTATION_PLAN.md가 유일한 공유 상태.

## LLM-as-Judge 백프레셔 (ralph-playbook)

주관적 품질 기준 (창의성, 미학, UX)을 테스트로 검증하는 패턴:

```typescript
interface ReviewResult {
  pass: boolean;
  feedback?: string; // pass=false일 때만
}

function createReview(config: {
  criteria: string;      // 평가 기준 (행동적, 관찰 가능)
  artifact: string;      // 텍스트 또는 스크린샷 경로
  intelligence?: "fast" | "smart";  // 기본값: 'fast'
}): Promise<ReviewResult>;
```

### 사용 예시

```typescript
// 텍스트 평가
test("welcome message tone", async () => {
  const result = await createReview({
    criteria: "Message uses warm, conversational tone",
    artifact: generateWelcomeMessage(),
  });
  expect(result.pass).toBe(true);
});

// 비전 평가 (스크린샷)
test("dashboard visual hierarchy", async () => {
  await page.screenshot({ path: "./tmp/dashboard.png" });
  const result = await createReview({
    criteria: "Layout demonstrates clear visual hierarchy",
    artifact: "./tmp/dashboard.png",
  });
  expect(result.pass).toBe(true);
});
```

철학: 비결정적이지만, 루프 반복을 통한 eventual consistency 확보.

## Sandbox 환경 (ralph-playbook)

`--dangerously-skip-permissions`은 모든 안전장치 해제 → 샌드박스가 유일한 보안 경계.

> "It's not if it gets popped, it's when. And what is the blast radius?"

| 샌드박스 | 격리 방식 | 시작 시간 | 지속성 | 비용 |
|---------|----------|----------|-------|------|
| **Sprites (Fly.io)** | Firecracker VM | <1s 복원 | 무제한 | $30 무료 |
| **E2B** | Firecracker microVM | 150-200ms | 24h (Pro) | $100 크레딧 |
| **exe.dev** | SSH VM | ~2s | 영구 | $20/월 |
| **Modal** | gVisor | 2-5s | 세션 한정 | $30/월 무료 |
| **Cloudflare** | Edge 격리 | 즉시 | R2 마운트 | $5/월 |
| **Docker Local** | 컨테이너 | 즉시 | 로컬 | 무료 |

권장: 프로덕션→E2B, 장기 실행→Sprites, 로컬 개발→Docker
