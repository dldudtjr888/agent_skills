# Phase 상세 가이드

## Phase 2 상세: Workspace 구조

```
<skill-name>-workspace/
├── eval-config.json
│   {
│     "skill_name": "...",
│     "skill_path": "...",
│     "assertions": [
│       {"text": "...", "check_type": "grep_negative", "pattern": "...", "weight": 3},
│       {"text": "...", "check_type": "grep", "pattern": "...", "weight": 2}
│     ],
│     "evals": [
│       {"id": "e1", "name": "...", "prompt": "..."},
│       {"id": "e2", "name": "...", "prompt": "..."},
│       {"id": "e3", "name": "...", "prompt": "..."}
│     ]
│   }
├── iteration-1/
│   ├── e1/
│   │   ├── with_skill/outputs/output.py
│   │   └── baseline/outputs/output.py
│   ├── e2/ (동일)
│   ├── e3/ (동일)
│   └── grading.json
├── iteration-2/ (검증 시)
│   └── grading.json
└── report.md
```

## Phase 3 상세: Grading

### 채점 로직

```python
for each eval output:
    for each assertion:
        if check_type == "grep_negative":
            passed = pattern NOT found in content
        elif check_type == "grep":
            passed = pattern found in content

        if passed:
            weighted_score += weight

    weighted_rate = weighted_score / total_weight * 100
```

### grading.json 스키마

```json
{
  "evals": {
    "e1": {
      "with_skill": {
        "passed": 4, "total": 5, "weighted_rate": 80,
        "failures": ["❌ No .unwrap() (w=3)"]
      },
      "baseline": {
        "passed": 2, "total": 5, "weighted_rate": 40,
        "failures": ["❌ No .unwrap() (w=3)", "❌ No varchar(255) (w=3)"]
      }
    },
    "e2": { ... },
    "e3": { ... }
  },
  "summary": {
    "with_skill": {"weighted_rate": 90},
    "baseline":   {"weighted_rate": 50},
    "delta": 40
  }
}
```

### scripts/grade.py 사용

```bash
python <skill-eval-path>/scripts/grade.py <workspace-path>/iteration-1
```

이 스크립트는 eval-config.json의 assertions를 읽고, 각 출력 파일에 대해 자동 채점하여 grading.json을 생성한다.

## Phase 4 상세: 최적화 규칙

### Core Rules 작성 가이드

SKILL.md 최상단에 10줄 이내로 추가. **금지 사항 위주**:

```markdown
## Core Rules
1. `.unwrap()` 금지 — `?` 연산자 + `.context()` 사용
2. `pub` 대신 `pub(crate)` 기본
3. 파라미터에 `String` 대신 `&str` 수용
4. `thiserror`(라이브러리) vs `anyhow`(앱) 분리
5. ...
```

이렇게 하면 에이전트가 스킬을 읽을 때 핵심 규칙을 먼저 보게 되어 역효과를 방지한다.

### Description 강화 가이드

구체적 트리거 시나리오 포함. "반드시 트리거" 문구:

```yaml
description: >-
  Rust 에러 처리 전략. thiserror(라이브러리)와 anyhow(앱) 분리, .context() 전파,
  retry/circuit breaker 복구 패턴. *.rs 파일 작성/리뷰 시, Cargo.toml 편집 시,
  "에러 처리", "error handling", "thiserror", "anyhow" 관련 요청 시 반드시 트리거.
```

## Phase 5 상세: 검증

1. 최적화된 스킬로 with-skill 3개만 재실행
2. baseline은 iteration-1에서 복사
3. grading → Delta 비교
4. 판정:
   - iteration-2 >= iteration-1: **확정**
   - < iteration-1 - 5%p: **롤백** (git checkout으로 SKILL.md 복원)
   - -5%p 이내: **허용** (크기 감소 이점 인정)

## Phase 6 상세: 리포트

### report.md 템플릿

```markdown
# [skill-name] 최적화 리포트

## 스킬 정보
- 경로: [path]
- 플러그인: [plugin]
- 줄 수: Before XX줄 → After XX줄

## Eval 결과
| Eval | With | Base | Delta | 실패 항목 |
|------|------|------|-------|----------|
| e1   |  XX% |  XX% | +XX%  | ...      |
| e2   |  XX% |  XX% | +XX%  | ...      |
| e3   |  XX% |  XX% | +XX%  | ...      |
| 합계 |  XX% |  XX% | +XX%  |          |

## 적용된 최적화
- [변경 1]
- [변경 2]

## iteration-2 검증
- Before Delta: +XX%
- After Delta: +XX%
- 판정: 확정/롤백/허용

## 최종 상태
✅ 최적화 / ⚠️ 효과 낮음 / 💀 삭제 권고
```

### 정리

iteration 디렉토리의 출력 파일(outputs/)은 삭제. 남기는 파일:
- `eval-config.json` (재현용)
- `grading.json` (결과 데이터)
- `report.md` (사람이 읽는 요약)
