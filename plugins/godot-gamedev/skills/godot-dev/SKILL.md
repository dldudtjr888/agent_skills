---
name: godot-dev
description: >
  Godot 4.x(4.3~4.6) 개발 어시스턴트 — .tscn/.tres 파일을 4.6 표준 형식으로 정확히 생성(load_steps 생략, uid 생략, [connection] 시그널), GDScript 타입 힌트/컨벤션 가이드, 4.3+ breaking API(TileMapLayer, Jolt Physics, 타입 딕셔너리, @export_tool_button, 가변 인자, 추상 클래스) 자동 감지 후 WebFetch 확인, Autoload 싱글턴/시그널 버스/상태 머신/씬 합성/Resource 패턴 아키텍처 가이드, .gdshader 셰이더 지원.
  Use when writing GDScript, creating/editing .tscn scenes, working with .tres resources, configuring project.godot, building Godot game architecture, or debugging Godot 4.x API changes.
  'Godot', 'GDScript', '.tscn 편집', '.tres 생성', '씬 파일', '노드 구조', 'Godot 게임', 'project.godot', 'TileMapLayer', 'Godot 4', '고도 엔진', 'gdshader' 요청 시 반드시 트리거. *.gd, *.tscn, *.tres, *.gdshader, project.godot 파일 작업 시 자동 활성화.
metadata:
  author: youngseoklee
  version: "1.0.0"
  filePattern:
    - "*.gd"
    - "*.tscn"
    - "*.tres"
    - "*.gdshader"
    - "project.godot"
    - "export_presets.cfg"
  bashPattern:
    - "godot"
---

# Godot 4.x 개발 어시스턴트

이 스킬의 핵심 가치는 Claude의 내장 지식만으로는 틀리기 쉬운 두 가지를 정확하게 만드는 것이다:
1. **.tscn/.tres 파일** — 4.6 표준 형식으로 생성 (load_steps 생략, [connection] 활용, 올바른 parent 경로)
2. **4.3+ 변경 API** — breaking-changes.md에 해당하면 WebFetch로 확인 (타입 딕셔너리, TileMapLayer 등)

부가적으로 아키텍처 패턴과 GDScript 컨벤션도 가이드한다.

---

## 1. API 문서 조회 규칙

모든 API를 매번 조회하지 않는다. **변경 리스트에 해당하는 API만** WebFetch한다.

### 조회 흐름

```
사용하려는 API가 references/breaking-changes.md에 있는가?
├── YES → WebFetch 필수
├── NO → 내장 지식으로 작성
│         └── 확신 없는가?
│             ├── YES → WebFetch
│             └── NO → 그대로 진행
└── 사용자가 "문서 확인해줘"라고 요청 → WebFetch
```

### WebFetch 방법

1. 먼저 `project.godot`을 Read하여 Godot 버전 확인 (`config/features`)
2. 공식 문서 URL (2단계 fallback):
   ```
   1차: https://docs.godotengine.org/en/stable/classes/class_{소문자클래스명}.html
   2차: https://raw.githubusercontent.com/godotengine/godot-docs/master/classes/class_{소문자클래스명}.rst
   ```
   1차 URL에서 내용이 잘리면 2차(GitHub raw RST)를 사용. RST는 항상 전체 내용을 반환한다.
3. 확인 항목: 메서드 시그니처, deprecated 여부, 시그널 목록, 상속 계층

### 주요 변경 API (상세: references/breaking-changes.md)

| 버전 | 주요 변경 |
|------|----------|
| 4.3 | TileMap→TileMapLayer, Parallax2D 신규, @export_storage/@export_custom |
| 4.4 | Jolt Physics 통합, 타입 딕셔너리, @export_tool_button, SkeletonIK3D deprecated |
| 4.5 | 가변 인자, 추상 클래스, 전용 2D NavigationServer, FoldableContainer |
| 4.6 | Jolt 기본값, IK 프레임워크(6종), D3D12 기본, TileMap 회전 씬 타일 |

### 특히 주의: 4.4+ 신규 GDScript 문법

Claude 내장 지식에 없을 가능성이 높은 문법들. 사용할 때 breaking-changes.md 확인:
- **타입 딕셔너리** (4.4+): `var slots: Dictionary[String, int] = {}` — `Dictionary = {}`로 쓰지 말 것
- **@export_tool_button** (4.4+): `@export_tool_button("Run") var btn = my_func`
- **가변 인자** (4.5+): `func f(a: int, ...args) -> void:`
- **추상 클래스** (4.5+): `@abstract class Shape:`

### 404 대응
- 이름 변경 확인 (breaking-changes.md 참조)
- `_2d`/`_3d` 접미사 변형 시도
- 상위 클래스에서 메서드 찾기

---

## 2. 파일 생성/편집 규칙

Godot의 .tscn, .tres, .gd, project.godot은 모두 텍스트 기반이라 파일 도구로 직접 다룬다.

### .tscn/.tres 파일

**생성 전 반드시 references/tscn-format.md를 읽어라.** 형식이 정확해야 Godot 에디터가 파일을 열 수 있다.

핵심 규칙 (검증으로 확인된 가장 중요한 차이점):

**load_steps 절대 쓰지 말 것** — Godot 4.6에서는 생략이 표준. 에디터가 자동 계산. `load_steps=N`을 넣으면 틀린 4.6 파일이 된다.

**uid도 생략** — 에디터가 다음 열기 시 자동 할당. 수동으로 `uid="uid://xxx"`를 만들지 말 것.

추가 규칙:
- 기존 프로젝트에 .tscn이 있으면 **먼저 Read해서 실제 형식을 파악**
- `ext_resource`/`sub_resource`의 `id`는 **절대 변경하지 말 것** (다른 곳에서 참조 중)
- 시그널 연결은 **[connection] 섹션**을 활용 (코드에서 `.connect()` 하는 것보다 .tscn의 [connection]이 Godot 표준)
- 새 씬은 최소 구조부터 시작:

```
[gd_scene format=3]

[node name="Root" type="Node2D"]
```

시그널 연결이 있으면 파일 끝에:
```
[connection signal="pressed" from="Button" to="." method="_on_button_pressed"]
```

### .gd 파일 (GDScript)

```gdscript
extends CharacterBody2D

@export var speed: float = 200.0
@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D

func _ready() -> void:
    pass

func _physics_process(delta: float) -> void:
    var direction := Input.get_axis(&"move_left", &"move_right")
    velocity.x = direction * speed
    move_and_slide()
```

컨벤션 (공식 스타일 가이드 기반):
- `snake_case`: 함수, 변수, 시그널, 파일명
- `PascalCase`: 클래스명, 노드명, enum 이름
- `CONSTANT_CASE`: 상수, enum 멤버
- `_접두사`: 프라이빗 함수/변수 (`var _counter`, `func _recalculate():`)
- 시그널은 **과거형**: `signal door_opened` (not `door_open`)
- 들여쓰기: **탭** 사용 (스페이스 아님)
- 불리언: `and`, `or`, `not` 사용 (`&&`, `||`, `!` 아님)
- 타입 힌트 항상 사용: `var x: float = 0.0`, `func f() -> void:`
- 코드 순서: signals → enums → constants → @export → 변수 → @onready → 메서드

### project.godot

INI 형식. 주요 편집 대상:
- `[autoload]`: 싱글턴 등록
- `[input]`: 입력 매핑
- `[application]`: 메인 씬, 이름, 아이콘

---

## 3. Godot 아키텍처 패턴

코드 작성 시 아래 패턴을 따른다. 상세: references/godot-patterns.md

### 패턴 선택 가이드

| 상황 | 패턴 | 출처 |
|------|------|------|
| 노드 간 통신 | **의존성 주입 5가지** (시그널, Callable, 참조 등) | 공식 |
| 전역 상태 관리 (점수, 게임 상태) | **Autoload 싱글턴** (3가지 조건 충족 시만) | 공식 |
| 재사용 가능한 게임 요소 | **씬 합성** (PackedScene) | 공식 |
| 정적 게임 데이터 (아이템, 스탯) | **Resource 패턴** (.tres) | 공식 부분 |
| 키보드/게임패드 입력 | **InputMap 액션** (project.godot [input]) | 공식 |
| 캐릭터/적 행동 분기 | **상태 머신** (enum + match) | 커뮤니티 |
| 다수 노드 → 글로벌 이벤트 | **시그널 버스** (EventBus Autoload) | 커뮤니티 |
| 화면 전환 효과 | **씬 전환** + 트랜지션 Autoload | 커뮤니티 |

### 프로젝트 폴더 구조 (권장)

```
res://
├── autoloads/          # Autoload 싱글턴 스크립트
├── scenes/             # .tscn 씬 파일
│   ├── ui/
│   ├── levels/
│   └── characters/
├── scripts/            # .gd 스크립트 (씬과 분리할 때)
├── resources/          # .tres 커스텀 리소스
├── assets/             # 이미지, 오디오, 폰트
│   ├── sprites/
│   ├── audio/
│   ├── fonts/
│   └── ui/
├── shaders/            # .gdshader 셰이더
└── project.godot
```

---

## 4. 검증 규칙

### 코드 작성 후
1. **참조 검증**: ext_resource의 `path`가 실제 파일과 일치하는지 Glob으로 확인
2. **파일 검증**: 작성한 .tscn을 다시 Read해서 형식 오류 확인
3. **문법 검증** (가능할 때):
   ```bash
   godot --headless --check-only --path {프로젝트경로}
   ```

### 흔한 실수
- `load_steps` 숫자가 실제 리소스 수와 불일치
- `parent` 경로 오류 (루트 자식은 `"."`, 중첩은 `"ParentName"`)
- ext_resource `id` 변경 (기존 참조 깨짐)
- `format=2` 사용 (Godot 3.x 형식, 4.x에서는 `format=3`)

---

## 5. .gdshader 파일

GLSL ES 3.0 유사 문법. 셰이더 타입: `spatial`(3D), `canvas_item`(2D), `particles`, `sky`, `fog`.

```glsl
shader_type canvas_item;

uniform vec4 color : source_color = vec4(1.0);
uniform float intensity : hint_range(0.0, 1.0) = 0.5;

void fragment() {
	COLOR = texture(TEXTURE, UV) * color * intensity;
}
```

셰이더 API에 확신이 없으면 WebFetch:
```
https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/shaders/shader_reference/shading_language.rst
```
