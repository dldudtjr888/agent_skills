# .tscn / .tres / project.godot 텍스트 형식 가이드

> Godot 4.x의 씬, 리소스, 프로젝트 설정 파일은 모두 텍스트 기반이다.
> 이 문서는 Claude가 파일을 직접 생성/편집할 때 참조하는 형식 스펙이다.

---

## 1. .tscn (씬 파일)

### 헤더
```
[gd_scene format=3 uid="uid://qwikou0mfxua"]
```
- `format=3`: Godot 4.x 형식 (Godot 3.x는 format=2)
- `uid`: 에디터가 자동 생성. 수동 생성 시 생략 가능.
- `load_steps`: Godot 4.6에서는 **생략하는 것이 표준**. 에디터가 자동 계산. 수동 생성 시 넣지 않아도 됨.

### ext_resource (외부 리소스 참조)
```
[ext_resource type="Script" uid="uid://j2aqmoj8l8aj" path="res://scripts/player.gd" id="1_wdwmd"]
[ext_resource type="Texture2D" uid="uid://b50b6aopyneu1" path="res://sprites/idle.png" id="1_wsdg4"]
[ext_resource type="PackedScene" uid="uid://jj3fblwvh20d" path="res://scenes/bg.tscn" id="3_s6a02"]
[ext_resource type="FontFile" uid="uid://dyfgkwafvomrf" path="res://fonts/main.ttf" id="1_wohm3"]
```
- `type`: Script, Texture2D, PackedScene, FontFile, AudioStream 등
- `uid`: 에디터 자동 생성. 수동 생성 시 생략 가능.
- `path`: `res://`로 시작하는 프로젝트 내 경로
- `id`: 이 파일 내에서의 고유 식별자. `"숫자_문자열"` 형식. 기존 파일 편집 시 절대 변경하지 말 것.

### sub_resource (인라인 리소스)
```
[sub_resource type="RectangleShape2D" id="RectangleShape2D_abc"]
size = Vector2(32, 16)

[sub_resource type="LabelSettings" id="LabelSettings_miotl"]
font = ExtResource("1_wohm3")
font_size = 50
font_color = Color(0.26, 0.69, 1, 1)
outline_size = 5

[sub_resource type="AtlasTexture" id="AtlasTexture_xaqfc"]
atlas = ExtResource("1_wsdg4")
region = Rect2(0, 0, 32, 32)
```
- 씬 파일 안에 직접 정의되는 리소스
- `id`: 문자열 형식. 이 파일 내 고유.
- 프로퍼티는 다음 줄부터 `key = value` 형식

### node (노드 정의)
```
[node name="Root" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="."]
script = ExtResource("1_wdwmd")

[node name="Sprite" type="AnimatedSprite2D" parent="Player"]
sprite_frames = SubResource("SpriteFrames_gypvn")
animation = &"idle"

[node name="Collision" type="CollisionShape2D" parent="Player"]
shape = SubResource("RectangleShape2D_abc")
```

**parent 규칙:**
- 루트 노드: `parent` 속성 없음
- 루트의 직접 자식: `parent="."`
- 중첩 자식: `parent="Player"` 또는 `parent="Player/Sprite"`

**특수 속성:**
- `unique_id=786229062` — Unique Node ID. Godot 4.6에서는 **거의 모든 노드에 자동 부여**. 수동 생성 시 생략 가능 (에디터가 할당).
- `groups=["enemy", "damageable"]` — 그룹 배열
- `instance=ExtResource("3_s6a02")` — 다른 씬의 인스턴스

**인스턴스 프로퍼티 오버라이드:**
다른 씬을 인스턴스할 때, 원본 씬의 `@export` 변수를 오버라이드할 수 있다.
오버라이드할 프로퍼티명은 **따옴표로 감싸서** 작성:
```
[node name="배경" parent="." instance=ExtResource("3_s6a02")]
"배경화면" = ExtResource("4_fk14r")
```
여기서 `"배경화면"`은 원본 씬 스크립트의 `@export var 배경화면:CompressedTexture2D`에 해당.

**프로퍼티 할당:**
```
position = Vector2(100, 200)
scale = Vector2(2, 2)
rotation = 1.5708
visible = false
z_index = 5
texture = ExtResource("1_miciu")
script = ExtResource("1_wdwmd")
motion_mirroring = Vector2(256, 256)
layout_mode = 1
anchors_preset = 8
text = "게임 시작"
```

**값 타입 형식:**
- Vector2: `Vector2(x, y)`
- Vector2i: `Vector2i(x, y)` (정수)
- Vector3: `Vector3(x, y, z)`
- Color: `Color(r, g, b, a)` (0.0~1.0)
- Rect2: `Rect2(x, y, w, h)`
- bool: `true` / `false`
- int: `5`
- float: `1.5708`
- String: `"텍스트"`
- StringName: `&"animation_name"`
- ExtResource: `ExtResource("id")`
- SubResource: `SubResource("id")`
- PackedStringArray: `PackedStringArray("a", "b", "c")`
- null: `null`
- 배열: `[value1, value2, ...]`
- 딕셔너리 배열 (복잡한 프로퍼티, 여러 줄):
  ```
  animations = [{
  "frames": [{
  "duration": 1.0,
  "texture": SubResource("AtlasTexture_xaqfc")
  }],
  "loop": true,
  "name": &"idle",
  "speed": 5.0
  }]
  ```

### connection (시그널 연결)
```
[connection signal="body_entered" from="Area2D" to="." method="_on_area_2d_body_entered"]
[connection signal="pressed" from="StartButton" to="." method="_on_start_pressed"]
[connection signal="timeout" from="Timer" to="." method="_on_timer_timeout"]
```
- 파일 맨 끝에 위치
- `from`: 시그널 발신 노드 경로
- `to`: 수신 노드 경로 ("." = 루트)
- `method`: 호출할 메서드명

---

## 2. .tres (리소스 파일)

```
[gd_resource type="TileSet" format=3 uid="uid://..."]

[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_abc"]
texture = ExtResource("1_tex")
texture_region_size = Vector2i(16, 16)

[resource]
tile_shape = 0
tile_size = Vector2i(16, 16)
```
- 헤더: `[gd_resource type="..." format=3]`
- `[resource]` 블록이 메인 리소스의 프로퍼티
- sub_resource와 ext_resource는 .tscn과 동일 문법

---

## 3. project.godot

INI 스타일 설정 파일. `;`로 주석 작성. 섹션 헤더 뒤에 빈 줄 하나.

```ini
; Godot 프로젝트 설정
config_version=5

[application]

config/name="MyGame"
config/features=PackedStringArray("4.6", "Forward Plus")
config/icon="res://icon.svg"
run/main_scene="res://scenes/main.tscn"

[autoload]
GameManager="*res://autoloads/game_manager.gd"
EventBus="*res://autoloads/event_bus.gd"

[input]
move_left={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194319,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}

[display]
window/size/viewport_width=1280
window/size/viewport_height=720

[rendering]
rendering_device/driver.windows="d3d12"

[physics]
3d/physics_engine="Jolt Physics"
```

**주요 섹션:**
- `[application]`: 게임 이름, 아이콘, 메인 씬, Godot 버전
- `[autoload]`: 자동 로드 스크립트 (`*` 접두사 = 싱글턴)
- `[input]`: 입력 액션 매핑
- `[display]`: 해상도, 창 모드
- `[rendering]`: 렌더링 설정
- `[physics]`: 물리 엔진 설정

---

## 4. 편집 시 주의사항

1. **ID 보존**: ext_resource/sub_resource의 `id`를 절대 변경하지 말 것. 다른 곳에서 참조 중.
2. **uid/unique_id 생략 가능**: 수동 생성 시 uid, unique_id 없어도 Godot 에디터가 다음 열기 시 자동 할당.
3. **load_steps 생략**: Godot 4.6에서는 생략이 표준. 에디터가 자동 계산.
4. **빈 줄**: ext_resource 간에는 빈 줄 없이 연속 작성. 섹션(ext_resource → sub_resource → node → connection) 사이에 빈 줄.
5. **인코딩**: UTF-8. 한글 노드명/변수명 사용 가능.
6. **parent 경로**: 루트의 자식은 ".", 그 아래는 "ParentName" 또는 "A/B/C".
7. **에디터 상태 프로퍼티**: `frame`, `frame_progress` 등은 에디터가 저장하는 런타임 상태. 수동 생성 시 설정 불필요.
