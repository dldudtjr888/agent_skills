# Map Builder Agent - Validation Rules

> JSON 스키마 검증 규칙

---

## 검증 단계

```
1. 구문 검증 (Syntax)     - JSON 파싱 가능 여부
2. 구조 검증 (Structure)  - 필수 필드 존재 여부
3. 타입 검증 (Type)       - 필드 타입 일치 여부
4. 참조 검증 (Reference)  - ID 참조 유효성
5. 논리 검증 (Logic)      - 비즈니스 규칙 준수
6. 기하 검증 (Geometry)   - 공간적 유효성
```

---

## 1. 구문 검증 (Syntax)

| 규칙 | 설명 |
|------|------|
| JSON_VALID | 유효한 JSON 형식 |

---

## 2. 구조 검증 (Structure)

### 필수 섹션

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| STRUCT_001 | meta | 존재해야 함 |
| STRUCT_002 | config | 존재해야 함 |
| STRUCT_003 | floors | 존재해야 함, 최소 1개 |
| STRUCT_004 | rooms | 존재해야 함, 최소 1개 |
| STRUCT_005 | openings | 존재해야 함 (빈 배열 가능) |
| STRUCT_006 | connections | 존재해야 함 (빈 배열 가능) |

### 필수 필드 - meta

| 규칙 ID | 필드 | 조건 |
|---------|------|------|
| META_001 | name | 필수, 비어있지 않음 |
| META_002 | schema_version | 필수, 형식: "x.y.z" |
| META_003 | created | 필수, ISO 8601 형식 |

### 필수 필드 - config

| 규칙 ID | 필드 | 조건 |
|---------|------|------|
| CONF_001 | unit | 필수, > 0 |
| CONF_002 | wall_thickness | 필수, > 0 |
| CONF_003 | default_ceiling_height | 필수, > 0 |

### 필수 필드 - floor

| 규칙 ID | 필드 | 조건 |
|---------|------|------|
| FLOOR_001 | floor_id | 필수, 고유 |
| FLOOR_002 | floor_number | 필수, 정수 |
| FLOOR_003 | base_height | 필수, 숫자 |
| FLOOR_004 | rooms | 필수, 배열 |

### 필수 필드 - room

| 규칙 ID | 필드 | 조건 |
|---------|------|------|
| ROOM_001 | room_id | 필수, 고유 |
| ROOM_002 | name | 필수, 비어있지 않음 |
| ROOM_003 | floor_id | 필수 |
| ROOM_004 | shape | 필수, "box" 또는 "polygon" |
| ROOM_005 | position | 필수, [x, y, z] 배열 |
| ROOM_006 | size | shape="box"일 때 필수 |
| ROOM_007 | height | shape="polygon"일 때 필수 |
| ROOM_008 | floor_points | shape="polygon"일 때 필수 |
| ROOM_009 | surfaces | 필수 |
| ROOM_010 | walls | 필수 |

### 필수 필드 - opening

| 규칙 ID | 필드 | 조건 |
|---------|------|------|
| OPEN_001 | opening_id | 필수, 고유 |
| OPEN_002 | type | 필수, "door"/"window"/"archway" |
| OPEN_003 | position_on_wall | 필수, 0.0~1.0 |
| OPEN_004 | size | 필수, [w, h] 배열 |
| OPEN_005 | bottom_offset | 필수, >= 0 |

### 필수 필드 - connection

| 규칙 ID | 필드 | 조건 |
|---------|------|------|
| CONN_001 | connection_id | 필수, 고유 |
| CONN_002 | type | 필수 |
| CONN_003 | room_a | 필수 |
| CONN_004 | room_b | 필수 |
| CONN_005 | wall_owner | 필수, "room_a"/"room_b"/null |

---

## 3. 타입 검증 (Type)

| 규칙 ID | 필드 | 예상 타입 |
|---------|------|----------|
| TYPE_001 | position | [number, number, number] |
| TYPE_002 | size | [number, number, number] (room) 또는 [number, number] (opening) |
| TYPE_003 | floor_points | [[number, number], ...] |
| TYPE_004 | exists | boolean |
| TYPE_005 | placeholder | boolean |
| TYPE_006 | wall_direction | string 또는 null |
| TYPE_007 | wall_segment_index | integer 또는 null |

---

## 4. 참조 검증 (Reference)

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| REF_001 | room.floor_id | floors[].floor_id에 존재해야 함 |
| REF_002 | floor.rooms[] | rooms[].room_id에 존재해야 함 |
| REF_003 | opening.connection_id | connections[].connection_id에 존재해야 함 |
| REF_004 | opening.room_id | rooms[].room_id에 존재해야 함 |
| REF_005 | connection.room_a.room_id | rooms[].room_id에 존재해야 함 |
| REF_006 | connection.room_b.room_id | rooms[].room_id에 존재해야 함 |
| REF_007 | connection.opening_id | openings[].opening_id에 존재해야 함 |
| REF_008 | connection.structure_id | structures[].structure_id에 존재해야 함 |
| REF_009 | structure.room_id | rooms[].room_id에 존재해야 함 (있는 경우) |
| REF_010 | prop.room_id | rooms[].room_id에 존재해야 함 |
| REF_011 | hierarchy.structure[].children | rooms[].name에 존재해야 함 |

---

## 5. 논리 검증 (Logic)

### ID 고유성

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| LOGIC_001 | floor_id | 모든 floor_id가 고유 |
| LOGIC_002 | room_id | 모든 room_id가 고유 |
| LOGIC_003 | opening_id | 모든 opening_id가 고유 |
| LOGIC_004 | connection_id | 모든 connection_id가 고유 |
| LOGIC_005 | structure_id | 모든 structure_id가 고유 |
| LOGIC_006 | prop_id | 모든 prop_id가 고유 |

### Room 관련

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| LOGIC_010 | box room | size[0] > 0, size[1] > 0, size[2] > 0 |
| LOGIC_011 | polygon room | floor_points 최소 3개 |
| LOGIC_012 | polygon room | height > 0 |
| LOGIC_013 | box walls | north, east, south, west 모두 정의 |
| LOGIC_014 | polygon walls | segments 개수 = floor_points 개수 |

### Opening 관련

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| LOGIC_020 | opening | connection_id 또는 room_id 중 하나는 필수 |
| LOGIC_021 | 단독 opening (box) | wall_direction 필수 |
| LOGIC_022 | 단독 opening (polygon) | wall_segment_index 필수 |
| LOGIC_023 | connection opening | connection_id만 있으면 됨 |
| LOGIC_024 | position_on_wall | 0.0 <= value <= 1.0 |
| LOGIC_025 | bottom_offset + size[1] | <= 벽 높이 |

### Connection 관련

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| LOGIC_030 | room_a.room_id | != room_b.room_id |
| LOGIC_031 | wall_owner | "room_a" 또는 "room_b" 또는 null |
| LOGIC_032 | door/archway connection | opening_id 필수 |
| LOGIC_033 | stairs/ladder connection | structure_id 필수 |
| LOGIC_034 | room_a (box) | wall_direction 필수, wall_segment_index = null |
| LOGIC_035 | room_a (polygon) | wall_segment_index 필수, wall_direction = null |

### Wall Direction

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| LOGIC_040 | wall_direction | "north", "east", "south", "west" 중 하나 |
| LOGIC_041 | wall_segment_index | 0 <= index < floor_points.length |

---

## 6. 기하 검증 (Geometry)

### 크기 제약

| 규칙 ID | 검증 대상 | 조건 | 권장값 |
|---------|----------|------|--------|
| GEO_001 | room size | 최소 크기 | >= 2m x 2m |
| GEO_002 | door size | 최소 크기 | >= 0.8m x 2.0m |
| GEO_003 | window size | 최소 크기 | >= 0.5m x 0.5m |
| GEO_004 | wall thickness | > 0 | 0.1m ~ 0.5m |
| GEO_005 | ceiling height | > 0 | 2.5m ~ 5m |

### Opening 위치

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| GEO_010 | opening 너비 | <= 벽 길이 |
| GEO_011 | opening 위치 | 벽 범위 내 (position_on_wall 고려) |
| GEO_012 | opening 높이 | bottom_offset + height <= ceiling_height |

### 방 배치

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| GEO_020 | connection 방들 | 실제로 인접해야 함 |
| GEO_021 | 같은 층 방들 | base_height 동일 |
| GEO_022 | room position.y | floor.base_height와 일치 |

### Polygon 유효성

| 규칙 ID | 검증 대상 | 조건 |
|---------|----------|------|
| GEO_030 | floor_points | 자기 교차 없음 (simple polygon) |
| GEO_031 | floor_points | 시계방향 순서 |
| GEO_032 | floor_points | 연속 중복점 없음 |

---

## 검증 결과 형식

```json
{
  "valid": false,
  "errors": [
    {
      "rule_id": "REF_001",
      "severity": "error",
      "message": "room 'room_classroom_01'의 floor_id 'floor_99'가 존재하지 않습니다",
      "path": "rooms[0].floor_id",
      "value": "floor_99"
    }
  ],
  "warnings": [
    {
      "rule_id": "GEO_001",
      "severity": "warning",
      "message": "room 'room_closet'의 크기가 권장 최소 크기(2m x 2m)보다 작습니다",
      "path": "rooms[3].size",
      "value": [1.5, 3, 1.5]
    }
  ]
}
```

### Severity 레벨

| 레벨 | 설명 | 빌드 가능 |
|------|------|----------|
| error | 치명적 오류, 빌드 불가 | ❌ |
| warning | 경고, 빌드 가능하나 확인 필요 | ✅ |
| info | 정보, 참고용 | ✅ |

---

## 검증 실행 순서

```
1. 구문 검증 → 실패 시 중단
2. 구조 검증 → 실패 시 중단
3. 타입 검증 → 오류 수집
4. 참조 검증 → 오류 수집
5. 논리 검증 → 오류 수집
6. 기하 검증 → 오류/경고 수집
7. 결과 반환
```

---

## 검증 규칙 요약

| 카테고리 | 규칙 수 | 주요 검증 내용 |
|----------|---------|---------------|
| 구문 | 1 | JSON 유효성 |
| 구조 | ~25 | 필수 필드 존재 |
| 타입 | ~10 | 필드 타입 일치 |
| 참조 | ~11 | ID 참조 유효성 |
| 논리 | ~20 | 비즈니스 규칙 |
| 기하 | ~10 | 공간적 유효성 |
| **총계** | **~77** | |

---

## 참고 문서

- [00-overview.md](00-overview.md) - 전체 개요
- [01-outputs.md](01-outputs.md) - 산출물 정의
- [02-json-schema.md](02-json-schema.md) - JSON 스키마
- [04-md-spec.md](04-md-spec.md) - MD 명세
- [05-image-spec.md](05-image-spec.md) - 이미지 명세
