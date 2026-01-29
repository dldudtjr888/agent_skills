# ralph-playbook

## AGENTS.md 운영 가이드 형식

```markdown
## Build & Run

Succinct rules for how to BUILD the project:

## Validation

Run these after implementing to get immediate feedback:

- Tests: `[test command]`
- Typecheck: `[typecheck command]`
- Lint: `[lint command]`

## Operational Notes

Succinct learnings about how to RUN the project:
...

### Codebase Patterns
...
```

**핵심 원칙**: ~60줄로 유지. 상태 업데이트나 진행 노트 금지 (그것은 IMPLEMENTATION_PLAN.md에). 운영 학습 발견 시에만 업데이트.

## PROMPT_plan.md 전체 내용

```markdown
0a. Study `specs/*` with up to 250 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md (if present) to understand the plan so far.
0c. Study `src/lib/*` with up to 250 parallel Sonnet subagents to understand shared utilities & components.
0d. For reference, the application source code is in `src/*`.

1. Study @IMPLEMENTATION_PLAN.md (if present; it may be incorrect) and use up to 500 Sonnet
   subagents to study existing source code in `src/*` and compare it against `specs/*`. Use
   an Opus subagent to analyze findings, prioritize tasks, and create/update @IMPLEMENTATION_PLAN.md
   as a bullet point list sorted in priority of items yet to be implemented. Ultrathink.
   Consider searching for TODO, minimal implementations, placeholders, skipped/flaky tests,
   and inconsistent patterns.

IMPORTANT: Plan only. Do NOT implement anything. Do NOT assume functionality is missing;
confirm with code search first. Treat `src/lib` as the project's standard library for shared
utilities and components.

ULTIMATE GOAL: We want to achieve [project-specific goal]. Consider missing elements and plan
accordingly. If an element is missing, search first to confirm it doesn't exist, then if needed
author the specification at specs/FILENAME.md.
```

## PROMPT_build.md 전체 내용

```markdown
0a. Study `specs/*` with up to 500 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md.
0c. For reference, the application source code is in `src/*`.

1. Your task is to implement functionality per the specifications using parallel subagents.
   Follow @IMPLEMENTATION_PLAN.md and choose the most important item to address. Before making
   changes, search the codebase (don't assume not implemented) using Sonnet subagents. You may
   use up to 500 parallel Sonnet subagents for searches/reads and only 1 Sonnet subagent for
   build/tests. Use Opus subagents when complex reasoning is needed.

2. After implementing functionality or resolving problems, run the tests for that unit of code.
   If functionality is missing then it's your job to add it. Ultrathink.

3. When you discover issues, immediately update @IMPLEMENTATION_PLAN.md using a subagent.

4. When the tests pass, update @IMPLEMENTATION_PLAN.md, then `git add -A` then `git commit`
   with a message describing the changes. After the commit, `git push`.

99999. When authoring documentation, capture the why.
999999. Single sources of truth, no migrations/adapters. If unrelated tests fail, resolve them.
9999999. As soon as there are no build or test errors create a git tag (start at 0.0.0).
99999999. You may add extra logging to debug issues.
999999999. Keep @IMPLEMENTATION_PLAN.md current with learnings using a subagent.
9999999999. Update @AGENTS.md when you learn operational knowledge (keep brief).
99999999999. For bugs you notice, resolve them or document in @IMPLEMENTATION_PLAN.md.
999999999999. Implement functionality completely. Placeholders waste efforts.
9999999999999. Periodically clean completed items from @IMPLEMENTATION_PLAN.md.
99999999999999. If specs/* have inconsistencies, use Opus 4.5 subagent with 'ultrathink'.
999999999999999. IMPORTANT: Keep @AGENTS.md operational only -- bloated AGENTS.md pollutes context.
```

## loop.sh 전체 내용

```bash
#!/bin/bash
# Usage: ./loop.sh [plan] [max_iterations]
# Examples:
#   ./loop.sh              # Build mode, unlimited
#   ./loop.sh 20           # Build mode, max 20
#   ./loop.sh plan         # Plan mode, unlimited
#   ./loop.sh plan 5       # Plan mode, max 5

# Parse arguments
if [ "$1" = "plan" ]; then
    MODE="plan"
    PROMPT_FILE="PROMPT_plan.md"
    MAX_ITERATIONS=${2:-0}
elif [[ "$1" =~ ^[0-9]+$ ]]; then
    MODE="build"
    PROMPT_FILE="PROMPT_build.md"
    MAX_ITERATIONS=$1
else
    MODE="build"
    PROMPT_FILE="PROMPT_build.md"
    MAX_ITERATIONS=0
fi

ITERATION=0
CURRENT_BRANCH=$(git branch --show-current)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Mode:   $MODE"
echo "Prompt: $PROMPT_FILE"
echo "Branch: $CURRENT_BRANCH"
[ $MAX_ITERATIONS -gt 0 ] && echo "Max:    $MAX_ITERATIONS iterations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: $PROMPT_FILE not found"
    exit 1
fi

while true; do
    if [ $MAX_ITERATIONS -gt 0 ] && [ $ITERATION -ge $MAX_ITERATIONS ]; then
        echo "Reached max iterations: $MAX_ITERATIONS"
        break
    fi

    cat "$PROMPT_FILE" | claude -p \
        --dangerously-skip-permissions \
        --output-format=stream-json \
        --model opus \
        --verbose

    git push origin "$CURRENT_BRANCH" || {
        echo "Failed to push. Creating remote branch..."
        git push -u origin "$CURRENT_BRANCH"
    }

    ITERATION=$((ITERATION + 1))
    echo -e "\n\n======================== LOOP $ITERATION ========================\n"
done
```

## IMPLEMENTATION_PLAN.md

```markdown
<!-- Generated by LLM with content and structure it deems most appropriate -->
```

**특징**:
- 우선순위 정렬된 불릿 포인트 태스크 목록
- PLANNING 모드에서 갭 분석으로 생성
- BUILDING 모드에서 업데이트 (완료 마킹, 발견 추가, 버그 기록)
- 자기 수정 가능 - 언제든 재생성
- 고정 템플릿 없음 - LLM이 최적 구조 결정
- 반복 간 유일한 공유 상태

## 용어 및 관계

| 용어 | 정의 |
|------|------|
| **JTBD** | Job to Be Done (고수준 사용자 니즈) |
| **Topic of Concern** | JTBD 내 개별 측면/컴포넌트 |
| **Spec** | 하나의 토픽에 대한 요구사항 문서 (`specs/FILENAME.md`) |
| **Task** | specs와 코드 비교에서 나온 작업 단위 |

**관계**: 1 JTBD -> N topics -> N specs -> N tasks

**범위 테스트**: "'and' 없이 한 문장" = 적절한 토픽 범위

## 핵심 설계 원칙

1. **결정론적 설정**: 매 반복마다 동일 파일 로드 -> 일관된 시작 상태
2. **최종 일관성**: 첫 시도에 완벽하지 않아도 반복으로 자기 수정
3. **공유 상태로서의 계획**: IMPLEMENTATION_PLAN.md가 디스크에서 반복 간 브릿지
4. **백프레셔의 핵심**: 테스트가 "치팅"과 잘못된 구현 방지
5. **단일 진실 소스**: 마이그레이션/어댑터 없이, `src/lib/`에 관용적 코드
6. **샌드박스 보안**: 항상 최소 접근, 격리된 네트워크
