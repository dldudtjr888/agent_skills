# JSON 스키마 레퍼런스

## eval-config.json

예시 (rust-error-handling 스킬):

```json
{
  "skill_name": "rust-error-handling",
  "skill_path": "plugins/rust-backend/skills/rust-error-handling",
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
