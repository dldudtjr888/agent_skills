---
name: unity-map-builder
description: "Unity ProBuilder 기반 맵/레벨 자동 생성 워크플로우. 사용 시점: (1) '맵 만들어줘' 또는 '레벨 만들어줘' 요청 시, (2) '그레이박스 맵 만들어줘' 요청 시, (3) planning/07-levels.md 기반 맵 구현 시, (4) 이미지 기반 맵 설계 요청 시, (5) 설계도 기반 정밀 맵 구현이 필요할 때"
---

# Unity Map Builder

Unity ProBuilder 기반 맵 자동 생성 워크플로우.

## Workflow Overview

```
Phase 1: 입력 수집
    ├── "맵 이미지나 참조 자료가 있으신가요?"
    ├── Yes → 이미지 분석 후 MD 작성
    └── No  → 대화로 요구사항 수집 후 MD 작성

Phase 2: MD 작성 (핵심 단계)
    ├── AI가 MD 초안 작성
    ├── ASCII 다이어그램 필수 포함
    ├── 유저 검토 → 수정 → 반복
    └── 유저 승인 시 다음 단계로

Phase 3: Image 생성 (시각적 검증)
    ├── 이미지 생성 AI용 프롬프트 작성
    └── 유저 승인 시 다음 단계로

Phase 4: JSON 생성 (빌드 데이터)
    ├── MD + Image 기반 정밀 수치화
    ├── 스키마 준수 + 검증 통과
    └── mapbuild/outputs/map_spec.json 저장

Phase 5: MCP 빌드 (Unity ProBuilder)
    ├── 방별 순서: 바닥 → 외벽 → 개구부 → 천장
    └── 결과 검증 (구조적/기하학적/시각적)
```

## Phase 1: Input Collection

Ask: "맵 이미지나 참조 자료가 있으신가요?"

**Yes (이미지 제공):**
1. Vision으로 이미지 분석
2. 사각형/도형 인식, 텍스트 읽기, 연결 관계 추론
3. 불명확한 부분 질문 → MD 작성

**No (대화 시작):**
1. 맵 용도/컨셉 질문
2. 필요한 공간 목록 수집
3. 대략적 크기 및 연결 관계 파악 → MD 작성

## Phase 2: MD Writing

MD 템플릿 - ASCII 다이어그램 필수:

```markdown
# [맵 이름]

> [한 줄 설명]

## 설계 기준
| 항목 | 값 |
|------|-----|
| 1 유닛 | 1m |
| 벽 두께 | 0.2m |
| 천장 높이 | 3m |
| 문 크기 | 1.5m x 2.2m |

## 공간 목록
| 이름 | ID | 크기 | 용도 |
|------|-----|------|------|
| Room A | room_a | 8x6m | 설명 |

## 연결 관계
Room A ──[문]── Hallway ──[문]── Room B

## 배치도 (ASCII)
            N
            ↑
┌───────────┐   ┌───────────┐
│  Room A   │   │  Room B   │
│   8x6m    │   │   8x6m    │
└─────◠─────┘   └─────◠─────┘
      └───────┬───────┘
        ┌─────┴─────┐
        │  Hallway  │
        │  16x3m    │
        └───────────┘

Scale: ████ = 5m
```

승인 확인: "이 설계가 맞나요? 수정할 부분이 있으면 말씀해주세요."

## Phase 3: Image Generation

이미지 생성 AI (DALL-E, Midjourney 등)용 프롬프트 예시:

```
Architectural floor plan, white background, black lines.
Two rooms labeled 'Classroom A' (8x6m) and 'Classroom B' (8x6m)
connected to 'Hallway' (16x3m) via doors.
Include dimension labels, scale bar (1 unit = 5m),
north arrow pointing up.
Door symbols as arc, wall thickness 0.2m visible.
Clean technical drawing style, no shadows, no 3D effects.
```

ASCII로 충분하면 바로 JSON 생성으로 진행 가능.

## Phase 4: JSON Generation

스키마 요약 (상세: [02-json-schema.md](references/02-json-schema.md)):

```json
{
  "meta": { "name": "...", "version": "1.0.0" },
  "coordinate_system": { "origin": "center", "unit": 1.0, "up_axis": "Y" },
  "scale": {
    "grid_size": 0.5,
    "wall_thickness": 0.2,
    "ceiling_height": 3.0,
    "door_size": [1.5, 2.2]
  },
  "floors": [...],
  "rooms": [...],
  "walls": [...],
  "openings": [...],
  "connections": [...]
}
```

저장 위치: `mapbuild/outputs/map_spec.json`

## Phase 5: MCP Build

### ProBuilder Tools

| 용도 | MCP 툴 |
|------|--------|
| 바닥/천장 | `probuilder-create-shape` (Plane) |
| 벽 | `probuilder-create-shape` (Cube) 또는 `probuilder-extrude` |
| 문 구멍 | `probuilder-delete-faces` 또는 `probuilder-create-shape` (Door) |
| 위치 조정 | `manage_gameobject` → modify |
| 검증 | `manage_gameobject` → get_component (Transform) |

### Build Order

1. 루트 컨테이너: Map_[이름]
2. 층별 컨테이너: Floor_1F, Floor_2F...
3. 방별 생성:
   - 3.1 바닥 (Plane) - 앵커
   - 3.2 외벽 4면 (Cube)
   - 3.3 개구부 (문/창문)
   - 3.4 천장 (Plane)
4. 결과 검증

### Validation

| 유형 | 확인 항목 |
|------|----------|
| 구조적 | 모든 방 생성, 구성요소 완료 |
| 기하학적 | 방 간 갭 < 0.01m, 겹침 없음 |
| 시각적 | 뷰포트 스크린샷 확인 |

## Metrics (CLAUDE.md)

| 항목 | 값 |
|------|-----|
| 복도 폭 | 3m |
| 소형 방 | 5x5m ~ 8x8m |
| 중형 방 | 10x10m ~ 15x15m |
| 대형 방 | 20x20m+ |
| 문 폭 | 1.5m |
| 천장 높이 | 3m |
| 그리드 스냅 | 0.5m |

## Critical Rules

1. **순차적 진행**: 각 Phase는 유저 승인 후에만 다음으로
2. **MD 중심**: MD가 모든 산출물의 원본
3. **ProBuilder 필수**: 일반 Primitive 사용 금지
4. **위치 조회 필수**: 하드코딩 좌표 금지, Transform 조회 후 계산

## References

상세 문서 (필요 시 참조):

- [00-overview.md](references/00-overview.md) - 전체 워크플로우
- [01-outputs.md](references/01-outputs.md) - 산출물 정의
- [02-json-schema.md](references/02-json-schema.md) - JSON 스키마 (빌드 데이터)
- [03-validation-rules.md](references/03-validation-rules.md) - 검증 규칙
- [04-md-spec.md](references/04-md-spec.md) - MD 작성 규칙
- [05-image-spec.md](references/05-image-spec.md) - 이미지 생성 규칙
