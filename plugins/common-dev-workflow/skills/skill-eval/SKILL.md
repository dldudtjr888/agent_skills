---
name: skill-eval
description: >-
  스킬을 eval 기반으로 검증하고 최적화하는 스킬. 대상 스킬의 SKILL.md를 읽고, negative-first assertion을 설계하고,
  모호한 eval 프롬프트를 생성하여, with-skill vs baseline 비교 실험을 수행한다.
  '/optimize-skill', '스킬 검증해줘', '스킬 테스트', '스킬 최적화', 'eval 돌려줘', 'skill eval', 'skill benchmark',
  '이 스킬 효과 있어?', '스킬 성능 측정' 등의 요청 시 반드시 트리거.
  스킬을 새로 만든 후 검증할 때, 기존 스킬의 효과를 측정할 때, 스킬을 개선할 때 사용.
metadata:
  version: 1.1.0
  author: youngseoklee
  filePattern: ["**/skills/*/SKILL.md"]
  bashPattern: ["optimize-skill", "skill-eval"]
---

## 입력

대상 스킬 경로를 사용자에게 확인하라. 예: `plugins/rust-backend/skills/axum-backend-pattern`
명시하지 않으면 현재 대화 컨텍스트에서 추론하거나 물어봐라.

---

## Core Rules (가장 중요 — 위반 시 eval 무의미)

1. **Positive grep assertion 금지** — "라이브러리명이 출력에 있는가"는 Opus에게 무조건 통과됨
2. **프롬프트에서 해법 힌트 제거** — 도메인 특정어(Godot, FastAPI)는 OK, 해법(load_steps 생략, lifespan 사용)은 금지
3. **Negative-first assertion** — 스킬 가치 = "잘못된 것을 안 쓰게 하는 것"
4. **baseline에게 힌트 주지 마라** — evals.json, assertion, 스킬 경로 일체 미제공
5. **1 에이전트 = 1 스킬** — 여러 스킬 합치면 뒤쪽 품질 저하
6. **스킬이 너무 길면 역효과** — Core Rules 10줄 요약이 없으면 에이전트가 핵심을 놓침

> 이 규칙은 2026-03-19 전체 52개 스킬 실험(92개 에이전트, 313개 출력)에서 검증됨.

---

## 실행 흐름

```
Phase 1: 분석 + Eval 설계 → eval-config.json
Phase 2: 에이전트 실행 (6개 병렬) → 출력 파일 6개
Phase 3: Grading + 진단 → grading.json
Phase 4: 최적화 → SKILL.md 수정
Phase 5: 검증 (iteration-2) → 확정/롤백
Phase 6: 마무리 → report.md
```

각 Phase의 상세는 `references/phases.md`를 참조하라.

---

## Phase 1: Eval 설계

### 1.1 스킬 분석

대상 스킬의 SKILL.md와 references/ 전체를 읽어라. 이때 찾아야 할 것:
- "하지 마라", "deprecated", "anti-pattern", "금지", "대신 사용" 키워드
- "~~old~~ → new" 형태의 마이그레이션 패턴
- 스킬 없이 Claude가 자연스럽게 할 실수

### 1.2 Negative Assertion 생성 (3-5개)

```json
{"text": "설명", "check_type": "grep_negative", "pattern": "잘못된패턴", "weight": 3}
```

weight 기준:
- 5: 치명적 (존재하지 않는 클래스, 런타임 에러)
- 3: 중요 (deprecated API, anti-pattern)
- 1: 경미 (컨벤션 위반)

예시:
- `langchain-openrouter`: `ChatOpenRouter` 미사용 (w=5, 존재하지 않는 클래스)
- `godot-dev`: `load_steps` 미포함 (w=5, Godot 4.6 표준)
- `langgraph-builder`: `create_react_agent` 미사용 (w=5, deprecated)
- `rust-patterns`: `.unwrap()` 미사용 (w=3)
- `python-agent-backend-pattern`: `@app.on_event` 미사용 (w=4, deprecated)

### 1.3 Positive Assertion (0-2개, 최소화)

baseline이 **절대 모를** 스킬 고유 구조 패턴만. 라이브러리명/API명 금지.

예시:
- `task-decomposer`: `T-\d{3}` ID 형식 (w=2, 스킬 고유)
- `unity-map-builder`: `wall_owner` 시스템 (w=2, 스킬 고유)

### 1.4 Eval별 assertion 매핑 (선택)

모든 assertion이 모든 eval에 해당하지 않을 수 있다. assertion에 `evals` 필드를 추가하여 해당 eval만 지정할 수 있다:

```json
{"text": "No .unwrap()", "check_type": "grep_negative", "pattern": "\\.unwrap\\(\\)", "weight": 3, "evals": ["e1", "e3"]}
```

`evals` 필드가 없으면 모든 eval에 적용 (기본값).

### 1.5 Eval 프롬프트 3개

**도메인 특정어는 허용, 해법 힌트는 금지:**

| eval | 목적 | 프롬프트 스타일 |
|------|------|--------------|
| e1 | 핵심 기능 | 도메인 컨텍스트 제공, 구현 방법은 에이전트 판단 |
| e2 | deprecated 함정 | baseline이 deprecated API를 쓰기 쉬운 상황 설정 |
| e3 | 미묘한 규칙 | 스킬 없이는 놓치기 쉬운 컨벤션/구조 |

프롬프트 작성 규칙:
- **도메인 특정어 허용**: "Godot 4.6", "FastAPI", "Rust", "미드저니" 등은 OK — 이걸 안 쓰면 eval이 성립 안 됨
- **해법 힌트 금지**: "load_steps 생략", "lifespan 사용", "--oref 사용" 등은 금지 — 이걸 쓰면 baseline도 통과
- **e2 주의**: deprecated 함정은 eval의 내부 목적. 프롬프트에 "deprecated를 피해주세요"라고 쓰면 안 됨

```
❌ BAD: "LangGraph StateGraph와 PIIMiddleware를 사용하세요" (해법 힌트)
✅ GOOD: "Python으로 멀티스텝 에이전트를 만드세요. PII 필터링이 필요합니다." (도메인만)

❌ BAD: "deprecated된 @app.on_event 대신 lifespan을 사용하세요" (해법 힌트)
✅ GOOD: "FastAPI 서버의 시작/종료 시 DB 커넥션을 관리하세요" (도메인만)

❌ BAD: "Godot 4.6 .tscn에서 load_steps를 생략하세요" (해법 힌트)
✅ GOOD: "Godot 4.6으로 Player 씬 파일(.tscn)을 만드세요" (도메인만)

❌ BAD: "--oref 파라미터와 --ow 값을 설정하세요" (해법 힌트)
✅ GOOD: "캐릭터 일관성을 유지하는 미드저니 프롬프트를 만들어주세요" (도메인만)
```

### 1.6 eval-config.json 저장

`references/schemas.md`의 eval-config 스키마를 따라 저장하라.

---

## Phase 2: 에이전트 실행

eval-config.json 저장 후, 6개 에이전트를 **한 턴에** 동시 spawn:

**with-skill (3개):**
```
Eval agent. DO NOT use Skill tool.
1. Read SKILL.md + all references at: [대상 스킬 절대 경로]
2. Following skill guidance, complete: "[프롬프트 — eval-config.json에서 복사]"
3. Write complete code to: [output path]
```

**baseline (3개)** — eval-config.json, assertion, 스킬 경로 일체 미제공. 프롬프트만 직접 전달:
```
Eval agent. DO NOT use Skill tool. DO NOT read any files except to write output.
Complete using ONLY built-in knowledge: "[동일 프롬프트 — 직접 문자열로 전달]"
Write complete code to: [output path]
```

- `mode: bypassPermissions, run_in_background: true`
- agent name: `w-e1`, `w-e2`, `w-e3`, `b-e1`, `b-e2`, `b-e3`
- baseline에게는 eval-config.json 경로를 **절대 주지 마라**. 프롬프트 텍스트만 복사해서 넣어라.

---

## Phase 3: Grading + 진단

에이전트 완료 후 `scripts/grade.py`를 실행하라. 상세는 `references/phases.md` 참조.

결과 테이블을 사용자에게 표시:
```
| Eval | With  | Base  | Delta | Neg Fails (with) | Neg Fails (base) |
|------|-------|-------|-------|-----------------|-----------------|
| e1   |  80%  |  40%  | +40%  | .unwrap() 1건   | .unwrap() 3건   |
```

### Delta가 낮을 때 진단 (< +10%)

Delta가 낮다고 바로 "효과 없음"으로 판정하지 마라. 다음을 확인:

1. **baseline 출력을 직접 읽어라** — 스킬이 가르치는 것 중 baseline이 이미 맞힌 것 vs 놓친 것 분류
2. **assertion이 너무 관대한지 확인** — grep 패턴이 너무 넓어서 의도치 않게 매칭되는지
3. **프롬프트가 힌트를 주고 있는지 확인** — 프롬프트에 해법이 들어있으면 assertion 재설계
4. **스킬의 진짜 차별화 포인트 재탐색** — 스킬에만 있고 baseline이 모르는 것이 정말 없는지

진단 결과를 grading.json의 `diagnosis` 필드에 기록:
```json
"diagnosis": {
  "baseline_already_knows": ["패턴 A", "패턴 B"],
  "baseline_misses": ["패턴 C"],
  "assertion_too_lenient": ["assertion X의 패턴이 너무 넓음"],
  "prompt_leaks_hint": false,
  "recommendation": "assertion 재설계 필요 / 스킬 차별화 없음 / 스킬 효과 확인됨"
}
```

---

## Phase 4: 최적화

| Delta | 조치 |
|-------|------|
| >= +20% | baseline도 아는 내용 축소, 핵심 가치 유지 |
| +10~20% | Core Rules에 차별화 규칙 추가 |
| < +10% | 진단 결과에 따라: assertion 재설계 → 재실행 / 또는 삭제 대상 |
| < 0% (역효과) | SKILL.md를 Core Rules 10줄로 압축, 재실행 후 여전히 역효과면 삭제 권고 |

공통: description pushy 강화, Core Rules 10줄 추가, 500줄 제한, version bump.

---

## Phase 5-6: 검증 + 마무리

상세는 `references/phases.md`를 참조하라.

최종 산출물:
```
<skill-name>-workspace/
├── eval-config.json    ← 재현용
├── iteration-1/
│   └── grading.json    ← 결과 데이터 + 진단
└── report.md           ← 최종 리포트
```
