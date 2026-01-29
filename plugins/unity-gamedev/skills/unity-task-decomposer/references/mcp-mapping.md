# MCP 도구 상세 매핑

## 태스크 유형별 MCP 도구

| 태스크 유형 | 주요 MCP 도구 | 파라미터 예시 |
|------------|--------------|--------------|
| **폴더 생성** | `manage_asset` | `action: "create_folder", path: "Scripts/Player"` |
| **태그 추가** | `manage_editor` | `action: "add_tag", tag_name: "Player"` |
| **레이어 추가** | `manage_editor` | `action: "add_layer", layer_name: "Ground"` |
| **스크립트 생성** | `create_script` | `path: "Assets/.../MyScript.cs", contents: "..."` |
| **스크립트 수정** | `script_apply_edits` | `name, path, edits: [...]` |
| **게임오브젝트 생성** | `manage_gameobject` | `action: "create", name, primitive_type, position, scale` |
| **컴포넌트 추가** | `manage_gameobject` | `action: "add_component", target, component_name` |
| **컴포넌트 설정** | `manage_gameobject` | `action: "set_component_property", target, component_name, component_properties` |
| **프리팹 저장** | `manage_gameobject` | `action: "create", save_as_prefab: true, prefab_path: "..."` |
| **프리팹 열기** | `manage_prefabs` | `action: "open_stage", prefab_path: "..."` |
| **머티리얼 생성** | `manage_asset` | `action: "create", asset_type: "Material", path: "..."` |
| **머티리얼 색상** | `manage_material` | `action: "set_material_color", material_path, color: [r,g,b,a]` |
| **머티리얼 적용** | `manage_material` | `action: "assign_material_to_renderer", target, material_path` |
| **씬 생성** | `manage_scene` | `action: "create", name: "SCN_Test"` |
| **씬 로드** | `manage_scene` | `action: "load", path: "..."` |
| **씬 저장** | `manage_scene` | `action: "save"` |
| **씬 계층 확인** | `manage_scene` | `action: "get_hierarchy"` |
| **콘솔 확인** | `read_console` | `types: ["error", "warning"]` |
| **플레이 모드** | `manage_editor` | `action: "play"` |
| **플레이 중지** | `manage_editor` | `action: "stop"` |

---

## MCP 도구 호출 순서 규칙

```
1. 스크립트 작성 후 → 반드시 read_console (컴파일 확인)
2. 컴포넌트 추가 전 → 스크립트 컴파일 완료 확인
3. 프리팹 저장 전 → 모든 컴포넌트 설정 완료
4. 플레이 테스트 전 → 씬 저장
5. 씬 저장 전 → 에러 없음 확인
```

---

## 복합 작업 MCP 시퀀스

### 플레이어 프리팹 생성

```
1. manage_gameobject → create (Capsule)
2. manage_gameobject → add_component (CharacterController)
3. manage_gameobject → set_component_property (height, radius)
4. manage_gameobject → add_component (PlayerController) ← 커스텀 스크립트
5. manage_material → assign_material_to_renderer
6. manage_gameobject → create (save_as_prefab: true)
```

### 씬 기본 구성

```
1. manage_scene → create
2. manage_gameobject → create (Directional Light)
3. manage_gameobject → set_component_property (Light 설정)
4. manage_gameobject → create (Floor - Plane/Cube)
5. manage_material → assign_material_to_renderer
6. manage_scene → save
```

### 방(Room) 생성

```
1. manage_gameobject → create (Floor - Cube, scale 기반 크기)
2. manage_gameobject → create (Wall_North - Cube)
3. manage_gameobject → create (Wall_South - Cube)
4. manage_gameobject → create (Wall_East - Cube)
5. manage_gameobject → create (Wall_West - Cube)
6. manage_material → assign (각 오브젝트)
7. manage_gameobject → modify (Layer 설정)
```

### 오브젝트 배치

```
1. manage_gameobject → create (prefab_path 사용)
   - position: [x, y, z]
   - rotation: [rx, ry, rz]
   - scale: [sx, sy, sz]
2. manage_gameobject → modify (tag, layer 설정)
```

---

## 검증용 MCP 시퀀스

### 스크립트 검증
```
1. create_script (스크립트 작성)
2. read_console (types: ["error"]) → 에러 0개 확인
```

### 씬 구조 검증
```
1. manage_scene → get_hierarchy
2. 필수 오브젝트 존재 확인 (Light, Camera, Floor 등)
```

### 플레이 테스트 검증
```
1. manage_scene → save
2. manage_editor → play
3. read_console (types: ["error", "warning"])
4. manage_editor → stop
```
