# JSON 스키마 레퍼런스

## eval-config.json

예시 (rust-error-handling 스킬):

```json
{
  "skill_name": "rust-error-handling",
  "skill_path": "plugins/rust-backend/skills/rust-error-handling",
  "exclude_patterns": ["#\\[cfg\\(test\\)\\]", "mod tests"],
  "assertions": [
    {
      "text": "No .unwrap() in production code",
      "check_type": "grep_negative",
      "pattern": "\\.unwrap\\(\\)",
      "weight": 3
    },
    {
      "text": "No panic!() in production code",
      "check_type": "grep_negative",
      "pattern": "panic!\\(",
      "weight": 3,
      "evals": ["e1", "e3"]
    },
    {
      "text": "Uses .context() for error propagation",
      "check_type": "grep",
      "pattern": "\\.context\\(|with_context",
      "weight": 2
    }
  ],
  "evals": [
    {
      "id": "e1",
      "name": "핵심 기능",
      "prompt": "Rust 프로젝트에서 에러 처리 전략을 설계하세요. 라이브러리와 앱이 분리되어 있습니다."
    },
    {
      "id": "e2",
      "name": "deprecated 함정",
      "prompt": "Rust HTTP 서버에서 DB 에러, 외부 API 에러, 입력 검증 에러를 통합 처리하세요."
    },
    {
      "id": "e3",
      "name": "미묘한 규칙",
      "prompt": "Rust 라이브러리 크레이트의 공개 API에서 에러 타입을 설계하세요. 다운스트림에서 매칭 가능해야 합니다."
    }
  ]
}
```

> assertion에 라이브러리명/API명이 들어가면 안 된다 (Positive grep 금지 원칙).
> 위 예시에서 `.unwrap()`, `panic!()`, `.context()` 는 라이브러리명이 아니라 코드 패턴이므로 OK.

### exclude_patterns 필드 (선택)

테스트 코드 등 특정 블록을 채점에서 제외한다. `grep_negative` assertion이 테스트 코드의 `.unwrap()` 등을 잡는 false positive를 방지:

```json
"exclude_patterns": ["#\\[cfg\\(test\\)\\]", "mod tests"]
```

매칭된 라인 이후 `{}` 블록 깊이를 추적하여 해당 블록 전체를 채점 대상에서 제외한다.

### 코멘트 자동 제거 (grade.py 내장)

grade.py는 채점 전에 **코멘트 라인을 자동 제거**한다. 설정 불필요.

Core Rules를 SKILL.md에 추가하면 에이전트가 규칙을 주석으로 복사함:
```rust
// .unwrap() 금지 — ? + .context() 사용
// Server::bind 대신 axum::serve 사용
```
이 주석이 `grep_negative`에 잡혀 false positive가 발생하므로, 다음을 자동 제거:
- `//`, `///`, `//!` 로 시작하는 라인
- `/* ... */` 블록 코멘트
- 숫자 목록 (`1. `, `2. ` 등) — 에이전트가 Core Rules를 번호 목록으로 쓰는 경우

> iteration-2 실험에서 코멘트 제거 전 8건의 false positive 발생, 실제 코드 위반 0건. 이 기능으로 전부 해소됨.

### assertion 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| text | string | ✅ | assertion 설명 (사람이 읽는 용도) |
| check_type | string | ✅ | `grep_negative` (없어야 통과) 또는 `grep` (있어야 통과) |
| pattern | string | ✅ | regex 패턴 (`|`로 OR 조건) |
| weight | number | ✅ | 1=경미, 3=중요, 5=치명적 |
| evals | string[] | ❌ | 이 assertion이 적용될 eval ID 목록. 없으면 모든 eval에 적용. |

### eval 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| id | string | ✅ | `e1`, `e2`, `e3` |
| name | string | ✅ | eval 이름 (한국어 OK) |
| prompt | string | ✅ | 도메인 특정어 허용, 해법 힌트 금지 |

## grading.json

```json
{
  "evals": {
    "e1": {
      "with_skill": {
        "passed": 3,
        "failed": 0,
        "total": 3,
        "weighted_rate": 100.0,
        "failures": []
      },
      "baseline": {
        "passed": 1,
        "failed": 2,
        "total": 3,
        "weighted_rate": 25.0,
        "failures": [
          "❌ No .unwrap() in production code (w=3)",
          "❌ No panic!() in production code (w=3)"
        ]
      }
    },
    "e2": { "..." : "..." },
    "e3": { "..." : "..." }
  },
  "summary": {
    "with_skill": {"weighted_rate": 90.0},
    "baseline": {"weighted_rate": 37.5},
    "delta": 52.5
  },
  "diagnosis": {
    "baseline_already_knows": ["error propagation with ?"],
    "baseline_misses": [".unwrap() 남용", "panic!() 사용"],
    "assertion_too_lenient": [],
    "prompt_leaks_hint": false,
    "recommendation": "스킬 효과 확인됨"
  }
}
```

> `diagnosis` 필드는 Delta < +10%일 때 필수. Phase 3 진단 절차 결과를 기록한다.

## report.md

`references/phases.md`의 Phase 6 섹션에 템플릿 있음.
