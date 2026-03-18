# Godot 아키텍처 패턴 & 베스트 프랙티스

> 출처 표기: [공식] = Godot 공식 문서 기반, [커뮤니티] = 공식 문서에 없는 커뮤니티 패턴

---

## 1. Autoload 싱글턴 [공식]

> 출처: docs.godotengine.org — Best practices > Autoloads versus regular nodes

Autoload는 **세 가지 조건을 모두 충족**할 때만 사용한다:
1. 데이터를 내부적으로 관리한다
2. 전역 접근이 필요하다
3. 독립적으로 동작한다

다른 시스템의 데이터를 수정하는 시스템은 Autoload가 아닌 별도 스크립트/씬으로 만들어야 한다.

### project.godot 등록
```ini
[autoload]

GameManager="*res://autoloads/game_manager.gd"
```
`*` 접두사: 싱글턴으로 접근 가능 (`GameManager.current_level`)

### 대표 사용 사례: 오디오 끊김 방지
씬 전환 시 배경 음악이 끊기는 문제 → AudioStreamPlayer를 Autoload로 분리하면 씬과 무관하게 음악 유지.

### GameManager 예시
```gdscript
extends Node

enum GameState { MENU, PLAYING, PAUSED, GAME_OVER }

var current_state: GameState = GameState.MENU
var score: int = 0
var current_level: int = 1

signal game_state_changed(new_state: GameState)

func change_state(new_state: GameState) -> void:
	current_state = new_state
	game_state_changed.emit(new_state)

func reset() -> void:
	score = 0
	current_level = 1
	change_state(GameState.MENU)
```

---

## 2. 씬 구조와 의존성 주입 [공식]

> 출처: docs.godotengine.org — Best practices > Scene organization

### 핵심 원칙
- 씬은 **최소 의존성**으로 설계한다 (loose coupling)
- SceneTree는 **공간적이 아닌 관계적**으로 사고한다
- 부모를 제거했을 때 자식도 논리적으로 제거되어야 할 때만 부모-자식 관계를 쓴다
- 형제 노드 간 직접 통신은 피하고, 상위 노드가 중재한다

### 의존성 주입 5가지 방법

**1. 시그널 연결** — 가장 안전. 과거형 이벤트에 적합.
```gdscript
# 부모가 자식의 시그널에 연결
func _ready() -> void:
	$Child.item_collected.connect(_on_item_collected)
```

**2. 메서드 호출** — 부모가 자식에게 실행할 메서드명을 지정.
```gdscript
# 자식에게 콜백 메서드명을 전달
child.callback_method = "_on_child_event"
```

**3. Callable 프로퍼티** — 메서드 호출보다 안전. 자식이 메서드를 소유할 필요 없음.
```gdscript
# 부모가 Callable을 주입
child.on_complete = func(): print("완료!")
```

**4. 노드/오브젝트 참조** — 부모가 직접 참조를 전달.
```gdscript
child.target_node = $OtherChild
```

**5. NodePath 초기화** — 부모가 경로 문자열을 전달, 자식이 런타임에 해석.
```gdscript
@export var target_path: NodePath
@onready var _target := get_node(target_path)
```

### 권장 씬 트리 구조
```
Main (main.gd)      # 게임 진입점, 전체 시스템 조감
├── World (Node2D)   # 게임 월드
└── GUI (Control)    # UI
```

### 의존성 경고 시스템
외부 컨텍스트에 의존하는 씬은 `@tool`과 `_get_configuration_warnings()`로 자체 문서화:
```gdscript
@tool
extends Node

@export var required_node: NodePath

func _get_configuration_warnings() -> PackedStringArray:
	var warnings: PackedStringArray = []
	if required_node.is_empty():
		warnings.append("required_node를 설정해야 합니다.")
	return warnings
```

---

## 3. 시그널 패턴 [공식]

> 출처: docs.godotengine.org — Step by step > Using signals

### 커스텀 시그널 정의
```gdscript
signal health_depleted
signal health_changed(old_value: int, new_value: int)
```

### 시그널 발신
```gdscript
func take_damage(amount: int) -> void:
	var old_health := health
	health -= amount
	health_changed.emit(old_health, health)
	if health <= 0:
		health_depleted.emit()
```

### 시그널 연결 (코드)
```gdscript
func _ready() -> void:
	var timer := get_node("Timer")
	timer.timeout.connect(_on_timer_timeout)

func _on_timer_timeout() -> void:
	visible = not visible
```

### await 패턴
```gdscript
await get_tree().create_timer(1.0).timeout
$AnimationPlayer.play(&"attack")
await $AnimationPlayer.animation_finished
```

---

## 4. 시그널 버스 (EventBus) [커뮤니티]

> **공식 문서에 없는 커뮤니티 패턴**. 공식 문서의 의존성 주입 방법(섹션 2)으로 대체 가능.
> 편의상 널리 사용되지만, Autoload 조건(섹션 1)을 충족하는지 먼저 검토할 것.

전역 시그널 허브로 노드 간 느슨한 결합. 직접 참조 없이 이벤트 통신.

```gdscript
# autoloads/event_bus.gd
extends Node

signal game_state_changed(new_state: int)
signal player_damaged(amount: int)
signal score_updated(new_score: int)
signal level_completed
signal item_collected(item_id: String)
```

발신: `EventBus.player_damaged.emit(10)`
수신: `EventBus.player_damaged.connect(_on_player_damaged)`

---

## 5. 씬 합성 [공식]

> 출처: docs.godotengine.org — Best practices > Scene organization

Godot 철학: "씬이 곧 컴포넌트". 작은 씬을 조합해 복잡한 씬 구성.

### PackedScene 인스턴스화
```gdscript
var bullet_scene: PackedScene = preload("res://scenes/bullet.tscn")

func shoot() -> void:
	var bullet: Node2D = bullet_scene.instantiate()
	bullet.position = global_position
	get_tree().current_scene.add_child(bullet)
```

### @export로 에디터에서 씬 할당
```gdscript
@export var enemy_scene: PackedScene

func spawn_enemy(pos: Vector2) -> void:
	var enemy := enemy_scene.instantiate()
	enemy.position = pos
	add_child(enemy)
```

### 동적 노드 관리
```gdscript
var label := Label.new()
label.text = "Hello"
add_child(label)

child_node.queue_free()  # 안전한 제거 (프레임 끝에 실행)
```

---

## 6. Resource 데이터 패턴 [공식 부분]

> 출처: Resource 클래스는 공식 문서에 있지만, "데이터 패턴"이라는 명칭은 커뮤니티 관례.
> 데이터 구조 선택: docs.godotengine.org — Best practices > Data preferences

게임 데이터를 .tres 파일로 관리.

### 커스텀 리소스 정의
```gdscript
class_name ItemData
extends Resource

@export var id: String
@export var display_name: String
@export var description: String
@export var icon: Texture2D
@export var value: int = 0
@export var stackable: bool = true
@export var max_stack: int = 99
```

### 저장/로드
```gdscript
# 저장
var item := ItemData.new()
item.id = "potion_hp"
item.display_name = "HP 포션"
ResourceSaver.save(item, "res://data/items/potion_hp.tres")

# 로드
var item: ItemData = load("res://data/items/potion_hp.tres")
```

### 데이터 구조 선택 기준 [공식]
| 주요 연산 | 추천 구조 | 이유 |
|-----------|----------|------|
| 순차 접근, 반복 | Array | 연속 메모리, 가장 빠른 반복 |
| 키 기반 조회 | Dictionary | 해시맵, 상수 시간 접근 |
| 복잡한 추상화, 시그널 | Object (커스텀 클래스) | 캡슐화, 시그널 지원 |

---

## 7. 상태 머신 [커뮤니티]

> **공식 문서에 없는 커뮤니티 패턴**. 널리 사용되지만 공식 권장은 아님.

enum + match 패턴으로 캐릭터/게임 상태 관리.

```gdscript
extends CharacterBody2D

enum State { IDLE, RUN, JUMP, FALL, ATTACK }
var _current_state: State = State.IDLE

func _physics_process(delta: float) -> void:
	match _current_state:
		State.IDLE:
			_state_idle(delta)
		State.RUN:
			_state_run(delta)
		State.JUMP:
			_state_jump(delta)
		State.FALL:
			_state_fall(delta)
		State.ATTACK:
			_state_attack(delta)

func _change_state(new_state: State) -> void:
	if _current_state == new_state:
		return
	_current_state = new_state
	match new_state:
		State.IDLE:
			$AnimatedSprite2D.play(&"idle")
		State.RUN:
			$AnimatedSprite2D.play(&"run")
		State.JUMP:
			velocity.y = -_jump_speed
			$AnimatedSprite2D.play(&"jump")
```

---

## 8. 입력 처리 [공식]

### InputMap 기반 (권장)
```gdscript
func _physics_process(_delta: float) -> void:
	var direction := Input.get_axis(&"move_left", &"move_right")
	velocity.x = direction * speed

	if Input.is_action_just_pressed(&"jump") and is_on_floor():
		velocity.y = -jump_speed

	move_and_slide()
```

### _unhandled_input vs _input [공식]
```gdscript
# _unhandled_input: UI가 처리하지 않은 입력만 받음 (게임 내 입력에 적합)
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"interact"):
		_interact()

# _input: 모든 입력을 받음 (UI 처리 포함)
func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		pass
```

---

## 9. 씬 전환 [공식 부분]

### 기본 전환 [공식]
```gdscript
get_tree().change_scene_to_file("res://scenes/level_2.tscn")

var next_scene: PackedScene = load("res://scenes/level_2.tscn")
get_tree().change_scene_to_packed(next_scene)
```

### 트랜지션 Autoload [커뮤니티]
```gdscript
# autoloads/scene_transition.gd
extends CanvasLayer

@onready var _animation_player: AnimationPlayer = $AnimationPlayer

func change_scene(target_scene: String) -> void:
	_animation_player.play(&"fade_out")
	await _animation_player.animation_finished
	get_tree().change_scene_to_file(target_scene)
	_animation_player.play(&"fade_in")
	await _animation_player.animation_finished
```

---

## 10. GDScript 컨벤션 [공식]

> 출처: docs.godotengine.org — GDScript style guide

### 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| 파일명 | snake_case | `yaml_parser.gd` |
| 클래스명 | PascalCase | `class_name YAMLParser` |
| 노드명 | PascalCase | `Camera3D`, `Player` |
| 함수 | snake_case | `func load_level():` |
| 변수 | snake_case | `var particle_effect` |
| 시그널 | snake_case, **과거형** | `signal door_opened`, `signal score_changed` |
| 상수 | CONSTANT_CASE | `const MAX_SPEED = 200` |
| enum 이름 | PascalCase | `enum Element` |
| enum 멤버 | CONSTANT_CASE | `{EARTH, WATER, AIR, FIRE}` |
| 프라이빗 | `_` 접두사 | `var _counter`, `func _recalculate():` |

### 스크립트 내 코드 순서 (공식 권장)

```
01. @tool, @icon, @static_unload
02. class_name
03. extends
04. ## 문서 주석

05. signals
06. enums
07. constants
08. static variables
09. @export variables
10. 일반 변수
11. @onready variables

12. _static_init()
13. static 메서드
14. 빌트인 가상 메서드 순서:
    _init() → _enter_tree() → _ready() →
    _process() → _physics_process() → 나머지 가상 메서드
15. 오버라이드 메서드
16. 나머지 메서드 (public → private 순)
17. inner class
```

### 포매팅 규칙
- **들여쓰기**: 탭 사용 (스페이스 아님)
- **줄 길이**: 100자 이하 권장, 80자 목표
- **불리언 연산자**: `and`, `or`, `not` 사용 (`&&`, `||`, `!` 아님)
- **빈 줄**: 함수/클래스 정의 앞뒤에 2줄, 함수 내 논리 구분에 1줄
- **따옴표**: 기본 쌍따옴표, 이스케이프 줄이려면 홑따옴표
- **숫자**: 앞뒤 0 포함 (`0.234`, `13.0`), 큰 숫자 밑줄 (`1_234_567`)
- **문장 당 하나의 구문** (삼항은 예외: `x = "a" if cond else "b"`)

### 주요 @export 변형

```gdscript
@export var speed: float = 200.0                    # 기본
@export_range(0, 100, 1) var hp: int = 100           # 범위
@export_range(0, 360, 0.1, "radians_as_degrees") var angle: float  # 라디안→도
@export_enum("Warrior", "Magician", "Thief") var job: int  # 열거
@export_file("*.tscn") var scene_path: String        # 파일 선택
@export_dir var save_dir: String                     # 디렉토리
@export_multiline var text: String                   # 멀티라인
@export_color_no_alpha var color: Color              # 알파 없는 색상
@export_node_path("Button") var btn_path: NodePath   # 노드 경로
@export_flags("Fire", "Water", "Earth") var elements: int = 0  # 비트 플래그
@export_exp_easing var ease_val: float               # 이징 커브
@export_group("Movement")                            # 그룹
@export_subgroup("Ground")                           # 서브그룹
@export_category("Main")                             # 카테고리
@export_storage var _internal: int                   # 저장만, 에디터 미표시
@export_tool_button("Run", "Callable") var btn = my_func  # 인스펙터 버튼 (4.4+)
```

### 타입 힌트
```gdscript
var speed: float = 200.0
var items: Array[ItemData] = []
var stats: Dictionary[String, int] = {}   # 4.4+ 타입 딕셔너리

func take_damage(amount: int) -> void:
	health -= amount

# 타입 추론 (:=) — 같은 줄에서 타입이 명확할 때
var direction := Vector3(1, 2, 3)

# 명시적 타입 — 타입이 모호할 때
@onready var health_bar: ProgressBar = get_node("UI/LifeBar")
```

### GDScript 4.5+ 신규 문법

```gdscript
# 가변 인자
func my_func(a: int, b: int = 0, ...args) -> void:
	prints(a, b, args)

# 추상 클래스/메서드
@abstract class Shape:
	@abstract func draw() -> void

class Circle extends Shape:
	func draw() -> void:
		print("Drawing a circle.")
```

### 문서 주석 [공식]
```gdscript
## 플레이어 캐릭터.
##
## 이동, 점프, 공격을 처리한다.
## @deprecated: 새 PlayerController를 사용하세요.
class_name Player
extends CharacterBody2D

## 이동 속도 (pixels/sec).
@export var speed: float = 200.0
```
