---
name: skill-eval
description: >-
  스킬을 eval 기반으로 검증하고 최적화하는 스킬. 대상 스킬의 SKILL.md를 읽고, negative-first assertion을 설계하고,
  모호한 eval 프롬프트를 생성하여, with-skill vs baseline 비교 실험을 수행한다.
  '/optimize-skill', '스킬 검증해줘', '스킬 테스트', '스킬 최적화', 'eval 돌려줘', 'skill eval', 'skill benchmark',
  '이 스킬 효과 있어?', '스킬 성능 측정' 등의 요청 시 반드시 트리거.
  스킬을 새로 만든 후 검증할 때, 기존 스킬의 효과를 측정할 때, 스킬을 개선할 때 사용.
metadata:
  version: 1.3.0
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
7. **스킬 예시 코드가 assertion을 위반하면 역효과** — with-skill 에이전트가 예시를 복사하여 오히려 baseline보다 낮은 점수를 받음. Phase 1에서 assertion 설계 후, 대상 스킬의 모듈/레퍼런스 예시 코드를 grep하여 위반이 있으면 **스킬 예시를 먼저 수정**하라.
8. **니치 라이브러리명은 해법 힌트와 동등** — `rs-graph-llm`, `rig-core` 같은 니치 크레이트명을 프롬프트에 넣으면 baseline도 API를 유추함. 니치 크레이트 스킬은 "hallucinated API" 감지 assertion이 더 효과적.
9. **Baseline이 통과하는 assertion은 Delta에 기여하지 않는다** — "Python 문법 쓰지 마라"처럼 Opus가 당연히 아는 것을 assertion으로 만들면 with_skill과 baseline 모두 100% 통과하여 Delta=0%. assertion 설계 시 반드시 **난이도 보정**을 수행하라 (Phase 1.2 참조).

> 이 규칙은 2026-03-19 rust-backend 12개 스킬 실험(72개 에이전트, 144개 출력) + 52개 스킬 실험(92개 에이전트, 313개 출력) + 동일 12개 스킬 iteration-2 검증(36개 에이전트)에서 검증됨.

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

대상 스킬의 SKILL.md와 modules/, references/ 전체를 읽어라. 이때 **두 가지 목록**을 만들어라:

**A. 스킬이 가르치는 것 목록** — 다음 키워드로 추출:
- "하지 마라", "deprecated", "anti-pattern", "금지", "대신 사용"
- "~~old~~ → new" 형태의 마이그레이션 패턴
- Core Rules 또는 금지 사항 목록

**B. "Opus가 이걸 틀릴까?" 판단** — 목록 A의 각 항목에 대해:

| 질문 | 답변 | 판정 |
|------|------|------|
| Opus 학습 데이터에 있는 보편적 지식인가? | Yes | ❌ assertion 후보 아님 |
| Opus가 이 도메인에서 자연스럽게 할 실수인가? | Yes | ✅ 좋은 assertion 후보 |
| 이 스킬만 알려주는 비표준/최신 패턴인가? | Yes | ✅✅ 최고의 assertion 후보 |

### 1.2 Assertion 난이도 보정 (가장 중요)

**Assertion의 가치 = baseline이 틀리는 빈도.** Baseline도 100% 통과하는 assertion은 Delta에 기여하지 않아 eval이 무의미해진다.

#### 난이도 분류

| Level | baseline 통과율 | 예시 | 판정 |
|-------|:---------:|------|------|
| L1: 무의미 | ~100% | "Rust 코드에 Python import 쓰지 마라" | ❌ **절대 사용 금지** |
| L2: 너무 쉬움 | 80%+ | "axum에서 Server::bind 쓰지 마라" (이미 주류) | ⚠️ 단독 사용 금지, 보조용만 |
| L3: 적절 | 30~70% | ".unwrap() 쓰지 마라" (Opus가 종종 사용) | ✅ 핵심 assertion |
| L4: 차별화 | 0~30% | "format! + SQL 쓰지 마라" (보안 anti-pattern) | ✅✅ 최고 |

**최소 L3 이상 assertion 2개 이상** 포함해야 Delta가 유의미하다.

#### "Opus가 이걸 틀릴까?" 체크리스트

각 assertion 후보에 대해 순서대로 검증:

1. **언어/프레임워크 혼동인가?**
   - "Rust 코드에 Python 쓰지 마라" → Opus는 혼동 안 함 → **L1, 버림**
   - "rig-core에서 Python OpenAI SDK 쓰지 마라" → 같은 이유 → **L1, 버림**

2. **이미 주류가 된 마이그레이션인가?**
   - axum 0.7의 `serve` 패턴 → 2024년 이후 주류 → **L2, 보조용만**
   - Next.js 16의 `proxy.ts` → 아직 최신 → **L3-L4, 사용**

3. **Opus가 "편의상" 자주 쓰는 anti-pattern인가?**
   - `.unwrap()`, `println!`, `String` 대신 `&str` → 자주 씀 → **L3, 좋음**
   - `format!("SELECT {} ...")` (SQL injection) → 종종 씀 → **L4, 최고**

4. **스킬만 아는 비표준 패턴인가?**
   - 존재하지 않는 클래스명 (hallucinated API) → **L4, 최고**
   - 스킬 고유 컨벤션 (T-001 ID 형식) → **L4, 최고**

#### 실패 사례 → 개선 사례 (실험 데이터)

```
❌ BEFORE (Delta 0% — L1 assertion만 사용):
  axum: "No Python syntax" (w=5), "No Python OpenAI SDK" (w=5)
  → Opus는 Rust를 요청하면 당연히 Rust로 씀. 양쪽 100% 통과.

✅ AFTER (Delta 기대 — L3-L4 assertion으로 교체):
  axum: "No Arc<Mutex<HashMap>> 대신 State 추출자" (w=3)
  axum: "핸들러에서 impl IntoResponse 미반환 시 감점" (w=3)
  → Opus가 실제로 Arc<Mutex> 패턴을 자주 사용, IntoResponse를 빠뜨림

❌ BEFORE (Delta 0% — L1 assertion만 사용):
  rig-builder: "No Python syntax" (w=5), "No .unwrap()" (w=3)
  → "No Python"은 무의미, ".unwrap()"만으로 차별화 부족

✅ AFTER (Delta 기대 — 니치 API 오류 감지):
  rig-builder: "agent() 아닌 존재하지 않는 메서드 사용 감지" (w=5)
  rig-builder: "embeddings에 잘못된 모델명 사용" (w=3)
  → Baseline이 rig-core API를 hallucinate할 확률 높음
```

### 1.3 Assertion 유형별 설계 가이드

#### A. Negative Assertion (3-5개, L3 이상만)

```json
{"text": "설명", "check_type": "grep_negative", "pattern": "잘못된패턴", "weight": 3}
```

**유형 1: 흔한 anti-pattern** (L3) — Opus가 편의상 자주 쓰는 것
- `.unwrap()` (Rust), `println!` 대신 tracing (Rust), `any` 타입 (TypeScript)
- `format!("SELECT {}")` (SQL injection), `std::sync::Mutex` (async 코드)

**유형 2: deprecated 함정** (L3-L4) — 아직 학습 데이터에 old 패턴이 많은 것
- `@app.on_event` (FastAPI, deprecated 2023), `create_react_agent` (LangGraph, deprecated)
- `load_steps` (Godot 4.6), `middleware.ts` → `proxy.ts` (Next.js 16)

**유형 3: 존재하지 않는 API (hallucinated)** (L4) — 니치 라이브러리 전용
- baseline이 API를 추측하여 존재하지 않는 메서드/클래스를 사용
- `ChatOpenRouter` (존재 안 함), `Graph.add_tool_node()` (존재 안 함)
- **니치 크레이트 스킬에서 가장 효과적** — baseline의 hallucination 비율 높음

**유형 4: 구조적 anti-pattern** (L3-L4) — 동작은 하지만 나쁜 설계
- `Arc<Mutex<Vec>>` 대신 채널 사용 (Rust async)
- 모든 필드가 `pub` (가시성 설계)
- God object, 순환 의존

weight 기준:
- 5: 치명적 (존재하지 않는 API, 런타임 에러, 보안 취약점)
- 3: 중요 (deprecated API, 구조적 anti-pattern)
- 1: 경미 (컨벤션 위반)

#### B. Positive Assertion (0-2개, 최소화)

baseline이 **절대 모를** 스킬 고유 구조 패턴만. 라이브러리명/API명 금지.

예시:
- `task-decomposer`: `T-\d{3}` ID 형식 (w=2, 스킬 고유)
- `unity-map-builder`: `wall_owner` 시스템 (w=2, 스킬 고유)

### 1.4 Eval별 assertion 매핑 (권장)

모든 assertion이 모든 eval에 해당하지 않을 수 있다. **프롬프트와 assertion의 불일치는 false positive/negative의 주요 원인이므로**, assertion에 `evals` 필드를 추가하여 해당 eval만 지정하라:

> 예: 직렬화 프롬프트에 로깅 assertion이 적용되거나, 가시성 설계 프롬프트에 workspace 설정 assertion이 적용되면 결과가 왜곡됨.

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

### 1.6 Assertion 사전 검증

eval-config.json 작성 후, **에이전트 실행 전에** 대상 스킬의 예시 코드에 assertion을 돌려 false positive를 확인하라:

```bash
# 스킬 모듈/레퍼런스에서 assertion 패턴 검색
grep -rn "\.unwrap()" plugins/rust-backend/skills/axum-backend-pattern/modules/
```

스킬 예시 코드가 assertion을 위반하면:
1. **스킬 예시 코드를 먼저 수정** (production 예시에서 anti-pattern 제거)
2. 테스트 코드(`#[cfg(test)]`, `mod tests` 등) 내 사용은 허용
3. "BAD 예시"로 명시적 표시된 것은 허용

### 1.7 eval-config.json 저장

`references/schemas.md`의 eval-config 스키마를 따라 저장하라.

---

## Phase 2: 에이전트 실행

eval-config.json 저장 후, 6개 에이전트를 **한 턴에** 동시 spawn.

**배치 실행** (여러 스킬을 한꺼번에 eval할 때): 스킬당 6개씩 묶어 배치 실행. 한 턴에 최대 24개 에이전트(4 스킬) 권장. 배치 간 의존성 없으므로 전부 background로 실행 가능:

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

Delta가 낮다고 바로 "효과 없음"으로 판정하지 마라. **대부분 assertion 난이도 문제**다.

#### 진단 절차

1. **baseline 출력을 직접 읽어라** — 스킬이 가르치는 것 중 baseline이 이미 맞힌 것 vs 놓친 것 분류
2. **assertion 난이도 재판정** — 각 assertion의 난이도 Level 확인 (1.2절 참조). L1-L2만 있으면 assertion 재설계 필수
3. **baseline 출력에서 실제 실수 찾기** — baseline이 실제로 쓴 anti-pattern을 grep으로 확인. 이것이 새 assertion 후보
4. **프롬프트가 힌트를 주고 있는지 확인** — 프롬프트에 해법이 들어있으면 프롬프트 재설계
5. **스킬의 진짜 차별화 포인트 재탐색** — 스킬에만 있고 baseline이 모르는 것이 정말 없는지

#### Delta 0%의 근본 원인 분류

| 원인 | 빈도 | 해결 |
|------|:----:|------|
| Assertion이 L1-L2 (너무 쉬움) | **60%** | assertion을 L3-L4로 교체 |
| Baseline이 이미 도메인 전문가 | 20% | 스킬 차별화 재탐색 또는 삭제 검토 |
| 프롬프트가 힌트를 줌 | 15% | 프롬프트 재설계 |
| eval-assertion 미스매치 | 5% | eval별 매핑 추가 |

> 12개 Rust 스킬 실험에서 Delta 0%인 4개 스킬 중 3개가 L1 assertion만 사용한 것이 원인이었음 (axum, langchain, rig).

#### assertion 재설계 절차 (Delta 0% 시)

1. baseline 출력 3개를 모두 읽는다
2. 스킬이 가르치는 것 중 baseline이 **실제로 틀린 부분**을 찾는다
3. 그 부분을 grep 가능한 패턴으로 변환한다
4. 새 assertion의 난이도가 L3 이상인지 확인한다
5. eval-config.json 교체 후 재실행한다

진단 결과를 grading.json의 `diagnosis` 필드에 기록:
```json
"diagnosis": {
  "baseline_already_knows": ["패턴 A", "패턴 B"],
  "baseline_misses": ["패턴 C"],
  "assertion_too_lenient": ["assertion X: L1 — baseline도 100% 통과"],
  "assertion_levels": {"L1": 2, "L2": 1, "L3": 1, "L4": 0},
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
