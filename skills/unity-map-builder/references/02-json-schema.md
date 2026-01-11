# Map Builder Agent - JSON Schema

> 그레이박싱용 맵 명세 JSON 스키마 정의

---

## 설계 원칙

| 항목 | 결정 |
|------|------|
| 좌표 체계 | 혼합 (방=절대, 하위=상대) |
| 좌표 기준점 | 바닥 중심 (bottom center) |
| 벽 표현 | 방에 내장 |
| 공유 벽 | **한쪽만 생성** (wall_owner 명시) |
| 인접 벽 중복 | **빌드 시 자동 감지** (좌표 기반) |
| 방 생성 방식 | 바닥 + 벽 4개 + 천장 (개별 생성) |
| 개구부 위치 | 상대 위치 (0.0~1.0) |
| 개구부 정의 | **openings[]에서만 상세 정의** |
| 문/창문 | 구멍 + placeholder |
| Placeholder 소속 | **wall_owner 방의 하위로 생성** |

---

## 전체 구조

```
map_spec.json
├── meta              # 메타 정보
├── config            # 설정 (스케일, 네이밍 등)
├── hierarchy         # 오브젝트 계층 구조
├── floors[]          # 층 목록
├── rooms[]           # 방 목록
├── openings[]        # 개구부 목록 (상세 정의는 여기서만)
├── connections[]     # 연결 관계 (공유 벽 owner 명시)
├── structures[]      # 특수 구조물 (기둥, 칸막이 등)
└── props[]           # 배치물 (선택)
```

---

## 상세 스키마

### 1. meta

```json
{
  "meta": {
    "name": "School_Level_01",
    "description": "학교 1층 - 교실 3개와 복도",
    "schema_version": "1.0.0",
    "created": "2024-01-15T10:30:00Z",
    "modified": "2024-01-15T10:30:00Z",
    "author": "map_builder_agent"
  }
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | ✅ | 맵 이름 (영문, 언더스코어) |
| description | string | | 맵 설명 |
| schema_version | string | ✅ | 스키마 버전 |
| created | datetime | ✅ | 생성 일시 |
| modified | datetime | | 수정 일시 |
| author | string | | 생성 주체 |

---

### 2. config

```json
{
  "config": {
    "unit": 1.0,
    "grid_size": 0.5,
    "wall_thickness": 0.2,
    "default_ceiling_height": 3.0,
    "default_door_size": [1.5, 2.2],
    "default_window_size": [1.2, 1.0],

    "position_anchor": "bottom_center",

    "adjacency_detection": {
      "enabled": true,
      "tolerance": 0.01
    },

    "naming": {
      "root": "Map_Root",
      "floor_prefix": "Floor_",
      "room_prefix": "Room_",
      "wall_prefix": "Wall_",
      "surface_floor_prefix": "Surface_Floor_",
      "surface_ceiling_prefix": "Surface_Ceiling_",
      "opening_prefix": "Opening_",
      "placeholder_prefix": "Placeholder_",
      "structure_prefix": "Structure_",
      "prop_prefix": "Prop_"
    },

    "graybox_material": "MAT_Graybox_Default"
  }
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| unit | float | 1.0 | 1유닛 = ?미터 |
| grid_size | float | 0.5 | 스냅 그리드 크기 |
| wall_thickness | float | 0.2 | 벽 두께 |
| default_ceiling_height | float | 3.0 | 기본 천장 높이 |
| default_door_size | [w, h] | [1.5, 2.2] | 기본 문 크기 |
| default_window_size | [w, h] | [1.2, 1.0] | 기본 창문 크기 |
| position_anchor | string | "bottom_center" | 좌표 기준점 |
| adjacency_detection | object | | 인접 벽 자동 감지 설정 |
| naming | object | | 네이밍 규칙 |
| graybox_material | string | | 그레이박스 기본 머티리얼 |

#### adjacency_detection (인접 벽 자동 감지)

```json
"adjacency_detection": {
  "enabled": true,
  "tolerance": 0.01
}
```

| 필드 | 설명 |
|------|------|
| enabled | 활성화 여부 |
| tolerance | 인접 판정 허용 오차 (미터) |

**동작 방식:**
```
빌드 시 각 벽에 대해:
1. 다른 방의 벽과 좌표 비교
2. 거리 < tolerance 이면 인접으로 판정
3. connection이 없는 인접 벽:
   - 좌표가 더 작은 방이 owner (일관성)
   - owner만 벽 생성
```

---

### 3. hierarchy

```json
{
  "hierarchy": {
    "root": "Map_Root",
    "structure": [
      {
        "name": "Floor_01",
        "children": ["Room_Classroom_01", "Room_Classroom_02", "Room_Hallway_01"]
      },
      {
        "name": "Floor_02",
        "children": ["Room_Office_01"]
      }
    ]
  }
}
```

**Unity 계층 구조 결과:**
```
Map_Root
├── Floor_01
│   ├── Room_Classroom_01
│   │   ├── Surface_Floor_Classroom_01
│   │   ├── Surface_Ceiling_Classroom_01
│   │   ├── Wall_Classroom_01_North
│   │   ├── Wall_Classroom_01_East
│   │   ├── Wall_Classroom_01_South
│   │   │   └── Placeholder_Door_01  ← opening placeholder는 벽 하위
│   │   └── Wall_Classroom_01_West
│   ├── Room_Classroom_02
│   └── Room_Hallway_01
└── Floor_02
    └── Room_Office_01
```

---

### 4. floors[]

```json
{
  "floors": [
    {
      "floor_id": "floor_01",
      "floor_number": 1,
      "base_height": 0,
      "ceiling_height": 3.0,
      "rooms": ["room_classroom_01", "room_classroom_02", "room_hallway_01"]
    },
    {
      "floor_id": "floor_02",
      "floor_number": 2,
      "base_height": 3.0,
      "ceiling_height": 3.0,
      "rooms": ["room_office_01"]
    }
  ]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| floor_id | string | ✅ | 층 고유 ID |
| floor_number | int | ✅ | 층 번호 (1, 2, 3...) |
| base_height | float | ✅ | 이 층 바닥의 Y 좌표 |
| ceiling_height | float | | 천장 높이 (기본값 사용 가능) |
| rooms | string[] | ✅ | 이 층에 속한 방 ID 목록 |

---

### 5. rooms[]

#### 5.1 Box 형태 (사각형 방)

```json
{
  "rooms": [
    {
      "room_id": "room_classroom_01",
      "name": "Classroom_01",
      "floor_id": "floor_01",

      "shape": "box",
      "position": [0, 0, 0],
      "size": [8, 3, 6],

      "surfaces": {
        "floor": true,
        "ceiling": true
      },

      "walls": {
        "north": { "exists": true },
        "east": { "exists": true },
        "south": { "exists": true },
        "west": { "exists": true }
      }
    }
  ]
}
```

**중요**: `walls`에서는 `exists` 여부만 정의. 개구부 정보는 `openings[]`에서 정의.

#### 5.2 Polygon 형태 (비정형 방)

```json
{
  "room_id": "room_l_shaped",
  "name": "L_Shaped_Room",
  "floor_id": "floor_01",

  "shape": "polygon",
  "position": [10, 0, 0],
  "height": 3,
  "floor_points": [
    [0, 0], [6, 0], [6, 4], [3, 4], [3, 6], [0, 6]
  ],

  "surfaces": {
    "floor": true,
    "ceiling": true
  },

  "walls": {
    "segments": [
      { "index": 0, "exists": true },
      { "index": 1, "exists": true },
      { "index": 2, "exists": true },
      { "index": 3, "exists": true },
      { "index": 4, "exists": true },
      { "index": 5, "exists": true }
    ]
  }
}
```

**Polygon 시각화:**
```
floor_points 인덱스:

    0───────────1
    │           │
    │       2───┘
    │       │
    5───────4,3

segment 0: point 0 → point 1
segment 1: point 1 → point 2
segment 2: point 2 → point 3
...
```

#### Room 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| room_id | string | ✅ | 방 고유 ID |
| name | string | ✅ | 표시 이름 (Unity 오브젝트 이름) |
| floor_id | string | ✅ | 소속 층 ID |
| shape | "box" \| "polygon" | ✅ | 방 형태 |
| position | [x, y, z] | ✅ | 위치 (bottom center 기준, 절대 좌표) |
| size | [w, h, d] | box일 때 | 크기 [가로, 높이, 세로] |
| height | float | polygon일 때 | 높이 |
| floor_points | [[x,z], ...] | polygon일 때 | 바닥 꼭지점 (시계방향) |
| surfaces | object | ✅ | 바닥/천장 생성 여부 |
| walls | object | ✅ | 벽 존재 여부 (exists만) |

---

### 6. openings[]

**개구부의 모든 상세 정보는 여기서만 정의**

```json
{
  "openings": [
    {
      "opening_id": "opening_door_01",
      "type": "door",
      "connection_id": "conn_01",

      "position_on_wall": 0.5,
      "size": [1.5, 2.2],
      "bottom_offset": 0,

      "placeholder": true
    },
    {
      "opening_id": "opening_window_01",
      "type": "window",
      "room_id": "room_classroom_01",
      "wall_direction": "east",

      "position_on_wall": 0.5,
      "size": [1.2, 1.0],
      "bottom_offset": 1.0,

      "placeholder": true
    },
    {
      "opening_id": "opening_archway_01",
      "type": "archway",
      "connection_id": "conn_02",

      "position_on_wall": 0.5,
      "size": [2.0, 2.5],
      "bottom_offset": 0,

      "placeholder": false
    }
  ]
}
```

#### Opening 위치 지정 방식

**A. 연결된 개구부 (두 방 사이)** → `connection_id` 사용
```json
{
  "opening_id": "opening_door_01",
  "type": "door",
  "connection_id": "conn_01",  // connection에서 위치 정보 가져옴
  ...
}
```

**B. 단독 개구부 (외벽 창문 등)** → `room_id` + `wall_direction` 또는 `wall_segment_index`
```json
// Box 방일 때
{
  "opening_id": "opening_window_01",
  "type": "window",
  "room_id": "room_classroom_01",
  "wall_direction": "east",
  ...
}

// Polygon 방일 때
{
  "opening_id": "opening_window_02",
  "type": "window",
  "room_id": "room_l_shaped",
  "wall_segment_index": 2,
  ...
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| opening_id | string | ✅ | 개구부 고유 ID |
| type | "door" \| "window" \| "archway" | ✅ | 개구부 타입 |
| connection_id | string | 연결 시 | 소속 connection ID |
| room_id | string | 단독 시 | 소속 방 ID |
| wall_direction | string | 단독+box | 벽 방향 (north/east/south/west) |
| wall_segment_index | int | 단독+polygon | 벽 segment 인덱스 |
| position_on_wall | float | ✅ | 벽 내 위치 (0.0~1.0, 0.5=중앙) |
| size | [w, h] | ✅ | 크기 [너비, 높이] |
| bottom_offset | float | ✅ | 바닥에서 높이 (문=0, 창문=1.0 등) |
| placeholder | bool | | placeholder 박스 생성 여부 (기본: true) |

**타입별 특징:**
| 타입 | 설명 | placeholder |
|------|------|-------------|
| door | 문 | 생성 (단순 박스) |
| window | 창문 | 생성 (단순 박스) |
| archway | 열린 통로 | 생성 안함 |

**Placeholder 소속:**
- connection 개구부: **wall_owner 방의 해당 벽 하위**에 생성
- 단독 개구부: **해당 방의 해당 벽 하위**에 생성

---

### 7. connections[]

**공유 벽 처리: owner만 벽 생성**

```json
{
  "connections": [
    {
      "connection_id": "conn_01",
      "type": "door",

      "room_a": {
        "room_id": "room_classroom_01",
        "wall_direction": "south",
        "wall_segment_index": null
      },
      "room_b": {
        "room_id": "room_hallway_01",
        "wall_direction": "north",
        "wall_segment_index": null
      },

      "wall_owner": "room_a",

      "opening_id": "opening_door_01"
    },
    {
      "connection_id": "conn_02",
      "type": "archway",

      "room_a": {
        "room_id": "room_l_shaped",
        "wall_direction": null,
        "wall_segment_index": 3
      },
      "room_b": {
        "room_id": "room_lobby_01",
        "wall_direction": "west",
        "wall_segment_index": null
      },

      "wall_owner": "room_b",

      "opening_id": "opening_archway_01"
    },
    {
      "connection_id": "conn_03",
      "type": "stairs",

      "room_a": {
        "room_id": "room_hallway_01",
        "wall_direction": null,
        "wall_segment_index": null
      },
      "room_b": {
        "room_id": "room_hallway_02",
        "wall_direction": null,
        "wall_segment_index": null
      },

      "wall_owner": null,

      "structure_id": "stairs_01"
    }
  ]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| connection_id | string | ✅ | 연결 고유 ID |
| type | "door" \| "archway" \| "open" \| "stairs" \| "ladder" | ✅ | 연결 타입 |
| room_a | object | ✅ | 연결된 방 A 정보 |
| room_a.room_id | string | ✅ | 방 ID |
| room_a.wall_direction | string \| null | | Box 방의 벽 방향 |
| room_a.wall_segment_index | int \| null | | Polygon 방의 벽 segment 인덱스 |
| room_b | object | ✅ | 연결된 방 B 정보 |
| wall_owner | "room_a" \| "room_b" \| null | ✅ | **공유 벽의 owner** |
| opening_id | string | door/archway | 개구부 ID |
| structure_id | string | stairs/ladder | 구조물 ID |

#### wall_direction vs wall_segment_index

| 방 형태 | 사용 필드 | 예시 |
|--------|----------|------|
| box | wall_direction | "north", "south", "east", "west" |
| polygon | wall_segment_index | 0, 1, 2, ... |

**규칙:** 하나만 사용, 다른 하나는 null

#### wall_owner 규칙

```
wall_owner = "room_a" 일 때:
  - room_a의 해당 벽: 생성 (opening 포함)
  - room_b의 해당 벽: 생성 안함
  - placeholder: room_a의 벽 하위에 생성

wall_owner = "room_b" 일 때:
  - room_a의 해당 벽: 생성 안함
  - room_b의 해당 벽: 생성 (opening 포함)
  - placeholder: room_b의 벽 하위에 생성

wall_owner = null 일 때:
  - 계단, 사다리 등 벽이 없는 연결
  - 양쪽 모두 해당 벽 없음
```

---

### 8. structures[]

```json
{
  "structures": [
    {
      "structure_id": "pillar_01",
      "type": "pillar",
      "room_id": "room_hallway_01",
      "position": [5, 0, 2.5],
      "size": [0.5, 3, 0.5]
    },
    {
      "structure_id": "partition_01",
      "type": "partition",
      "room_id": "room_office_01",
      "start": [2, 0, 0],
      "end": [2, 0, 4],
      "height": 1.5,
      "thickness": 0.1
    },
    {
      "structure_id": "stairs_01",
      "type": "stairs",
      "position": [15, 0, 5],
      "direction": "north",
      "width": 2,
      "height": 3,
      "depth": 4,
      "step_count": 15
    },
    {
      "structure_id": "ramp_01",
      "type": "ramp",
      "position": [20, 0, 5],
      "direction": "east",
      "width": 2,
      "height": 1,
      "depth": 4
    }
  ]
}
```

**구조물 타입:**

| type | 설명 | 필요 필드 |
|------|------|----------|
| pillar | 기둥 | room_id, position, size |
| partition | 칸막이/반벽 | room_id, start, end, height, thickness |
| stairs | 계단 | position, direction, width, height, depth, step_count |
| ramp | 경사로 | position, direction, width, height, depth |

---

### 9. props[] (선택)

```json
{
  "props": [
    {
      "prop_id": "prop_desk_01",
      "room_id": "room_classroom_01",
      "type": "placeholder",
      "name": "desk",
      "position": [2, 0, 1.5],
      "rotation": [0, 0, 0],
      "size": [1.2, 0.75, 0.6]
    }
  ]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| prop_id | string | ✅ | Prop 고유 ID |
| room_id | string | ✅ | 소속 방 ID |
| type | "placeholder" | ✅ | 그레이박싱에서는 placeholder만 |
| name | string | ✅ | Prop 이름 (나중에 교체 시 참조) |
| position | [x, y, z] | ✅ | 방 내 상대 위치 |
| rotation | [x, y, z] | | 회전 (기본: [0,0,0]) |
| size | [w, h, d] | ✅ | 대략적 크기 |

**Position 기준:**
- rooms[].position → **절대 좌표** (월드 기준)
- props[].position → **상대 좌표** (소속 방의 중심 기준)
- structures[].position → **절대 좌표** (월드 기준)

---

## 전체 예시

```json
{
  "meta": {
    "name": "School_Level_01",
    "description": "학교 1층 - 교실 2개와 복도, L자형 방 포함",
    "schema_version": "1.0.0",
    "created": "2024-01-15T10:30:00Z",
    "author": "map_builder_agent"
  },

  "config": {
    "unit": 1.0,
    "grid_size": 0.5,
    "wall_thickness": 0.2,
    "default_ceiling_height": 3.0,
    "default_door_size": [1.5, 2.2],
    "position_anchor": "bottom_center",
    "adjacency_detection": {
      "enabled": true,
      "tolerance": 0.01
    },
    "naming": {
      "root": "Map_Root",
      "floor_prefix": "Floor_",
      "room_prefix": "Room_",
      "wall_prefix": "Wall_",
      "surface_floor_prefix": "Surface_Floor_",
      "surface_ceiling_prefix": "Surface_Ceiling_",
      "placeholder_prefix": "Placeholder_"
    }
  },

  "hierarchy": {
    "root": "Map_Root",
    "structure": [
      {
        "name": "Floor_01",
        "children": ["Room_Classroom_01", "Room_Classroom_02", "Room_Hallway_01", "Room_L_Shaped"]
      }
    ]
  },

  "floors": [
    {
      "floor_id": "floor_01",
      "floor_number": 1,
      "base_height": 0,
      "ceiling_height": 3.0,
      "rooms": ["room_classroom_01", "room_classroom_02", "room_hallway_01", "room_l_shaped"]
    }
  ],

  "rooms": [
    {
      "room_id": "room_classroom_01",
      "name": "Classroom_01",
      "floor_id": "floor_01",
      "shape": "box",
      "position": [4, 0, 8],
      "size": [8, 3, 6],
      "surfaces": { "floor": true, "ceiling": true },
      "walls": {
        "north": { "exists": true },
        "east": { "exists": true },
        "south": { "exists": true },
        "west": { "exists": true }
      }
    },
    {
      "room_id": "room_classroom_02",
      "name": "Classroom_02",
      "floor_id": "floor_01",
      "shape": "box",
      "position": [14, 0, 8],
      "size": [8, 3, 6],
      "surfaces": { "floor": true, "ceiling": true },
      "walls": {
        "north": { "exists": true },
        "east": { "exists": true },
        "south": { "exists": true },
        "west": { "exists": true }
      }
    },
    {
      "room_id": "room_hallway_01",
      "name": "Hallway_01",
      "floor_id": "floor_01",
      "shape": "box",
      "position": [9, 0, 2.5],
      "size": [18, 3, 3],
      "surfaces": { "floor": true, "ceiling": true },
      "walls": {
        "north": { "exists": true },
        "east": { "exists": true },
        "south": { "exists": true },
        "west": { "exists": true }
      }
    },
    {
      "room_id": "room_l_shaped",
      "name": "L_Shaped_Room",
      "floor_id": "floor_01",
      "shape": "polygon",
      "position": [25, 0, 5],
      "height": 3,
      "floor_points": [
        [0, 0], [6, 0], [6, 4], [3, 4], [3, 6], [0, 6]
      ],
      "surfaces": { "floor": true, "ceiling": true },
      "walls": {
        "segments": [
          { "index": 0, "exists": true },
          { "index": 1, "exists": true },
          { "index": 2, "exists": true },
          { "index": 3, "exists": true },
          { "index": 4, "exists": true },
          { "index": 5, "exists": true }
        ]
      }
    }
  ],

  "openings": [
    {
      "opening_id": "opening_door_01",
      "type": "door",
      "connection_id": "conn_01",
      "position_on_wall": 0.3,
      "size": [1.5, 2.2],
      "bottom_offset": 0,
      "placeholder": true
    },
    {
      "opening_id": "opening_door_02",
      "type": "door",
      "connection_id": "conn_02",
      "position_on_wall": 0.7,
      "size": [1.5, 2.2],
      "bottom_offset": 0,
      "placeholder": true
    },
    {
      "opening_id": "opening_window_01",
      "type": "window",
      "room_id": "room_classroom_01",
      "wall_direction": "north",
      "position_on_wall": 0.5,
      "size": [2.0, 1.2],
      "bottom_offset": 1.0,
      "placeholder": true
    },
    {
      "opening_id": "opening_door_03",
      "type": "door",
      "connection_id": "conn_03",
      "position_on_wall": 0.5,
      "size": [1.5, 2.2],
      "bottom_offset": 0,
      "placeholder": true
    }
  ],

  "connections": [
    {
      "connection_id": "conn_01",
      "type": "door",
      "room_a": {
        "room_id": "room_classroom_01",
        "wall_direction": "south",
        "wall_segment_index": null
      },
      "room_b": {
        "room_id": "room_hallway_01",
        "wall_direction": "north",
        "wall_segment_index": null
      },
      "wall_owner": "room_a",
      "opening_id": "opening_door_01"
    },
    {
      "connection_id": "conn_02",
      "type": "door",
      "room_a": {
        "room_id": "room_classroom_02",
        "wall_direction": "south",
        "wall_segment_index": null
      },
      "room_b": {
        "room_id": "room_hallway_01",
        "wall_direction": "north",
        "wall_segment_index": null
      },
      "wall_owner": "room_a",
      "opening_id": "opening_door_02"
    },
    {
      "connection_id": "conn_03",
      "type": "door",
      "room_a": {
        "room_id": "room_hallway_01",
        "wall_direction": "east",
        "wall_segment_index": null
      },
      "room_b": {
        "room_id": "room_l_shaped",
        "wall_direction": null,
        "wall_segment_index": 5
      },
      "wall_owner": "room_a",
      "opening_id": "opening_door_03"
    }
  ],

  "structures": [],

  "props": []
}
```

---

## 맵 시각화

```
        N
        ↑
     ┌─[W]─┐
     │     │
┌────┴─────┴────┬────────────────┐          ┌───────────┐
│               │                │          │           │
│  Classroom_01 │  Classroom_02  │          │   L형 방   │
│    (8x6m)     │    (8x6m)      │          │           │
│               │                │          │       ┌───┘
│               │                │          │       │
└──────[D]──────┴───────[D]──────┘          └───────┘
       │                 │                      │
       │    (공유 벽)     │                      │
       │   wall_owner    │                      │
       │   = room_a      │                      │
       ▼                 ▼                      │
┌────────────────────────────────────────[D]───┘
│
│                   Hallway_01
│                    (18x3m)
│
└──────────────────────────────────────────────

[D] = Door
[W] = Window

연결 규칙:
- conn_01: Classroom_01(south) ↔ Hallway(north), owner=room_a
- conn_02: Classroom_02(south) ↔ Hallway(north), owner=room_a
- conn_03: Hallway(east) ↔ L형방(segment 5), owner=room_a
```

---

## 빌드 순서

```
1. Map_Root 생성

2. Floor_01 생성 (Map_Root 하위)

3. 각 Room 생성:
   a. Room 컨테이너 생성
   b. Surface_Floor 생성
   c. Surface_Ceiling 생성
   d. 각 벽 생성:
      - connection 있으면: wall_owner인지 체크
        - owner면: 벽 생성 + opening 구멍
        - owner 아니면: 스킵
      - connection 없으면: adjacency_detection으로 인접 체크
        - 인접 벽 있으면: 좌표 비교로 owner 결정
        - owner면: 벽 생성
        - owner 아니면: 스킵
      - 인접 없으면: 벽 생성
   e. Opening placeholder 생성 (벽 하위)

4. Structures 생성

5. Props 생성
```

---

## 참고 문서

- [00-overview.md](00-overview.md) - 전체 개요
- [01-outputs.md](01-outputs.md) - 산출물 정의
- [03-validation-rules.md](03-validation-rules.md) - 검증 규칙
- [04-md-spec.md](04-md-spec.md) - MD 명세
- [05-image-spec.md](05-image-spec.md) - 이미지 명세
