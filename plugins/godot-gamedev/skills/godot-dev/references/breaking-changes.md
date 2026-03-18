# Godot 4.x 주요 변경사항 (WebFetch 트리거 기준)

> 이 리스트에 해당하는 API를 사용할 때 WebFetch로 공식 문서를 확인해야 한다.
> 리스트에 없는 API는 내장 지식으로 작성해도 된다.
>
> **출처**: 모든 항목은 Godot 공식 마이그레이션 가이드 RST 파일에서 직접 추출.
> (`github.com/godotengine/godot-docs/master/tutorials/migrating/upgrading_to_godot_4.x.rst`)

---

## 4.3 변경 (4.2 → 4.3)

### 클래스/메서드 변경
- **TileMap → TileMapLayer**: 레이어 시스템이 별도 노드로 분리. 기존 TileMap deprecated.
- **Parallax2D 신규**: ParallaxBackground/ParallaxLayer 대체.
- **SkeletonModifier3D 신규**: 골격 애니메이션 스크립팅.
- **EditorSceneFormatImporterFBX → EditorSceneFormatImporterFBX2GLTF**: 클래스명 변경.
- `Skeleton3D.add_bone()`: 반환 타입 `void` → `int32`
- `Skeleton3D`: 시그널 `bone_pose_changed` → `skeleton_updated`로 교체
- `BoneAttachment3D.on_bone_pose_update()` → `on_skeleton_update()`
- `AcceptDialog.register_text_enter()`: 파라미터 `Control` → `LineEdit`으로 축소
- `AcceptDialog.remove_button()`: 파라미터 `Control` → `Button`으로 축소
- `PhysicsShapeQueryParameters3D.motion`: `Vector2` → `Vector3`
- `AnimationMixer._post_process_key_value()`: 파라미터 `Object` → `uint64`

### GDExtension
- `close_library()`, `initialize_library()`, `open_library()` 제거
- `GDExtensionManager.load_extension`/`unload_extension` 사용

### Navigation
- `NavigationRegion2D`: `avoidance_layers`, `constrain_avoidance` 제거

### Rendering
- `RenderingDevice`: `InitialAction`/`FinalAction` enum 값 변경
- 다수 RD 메서드에서 `post_barrier` 파라미터 제거

### GDScript 신규
- `is not` 연산자, `@export_storage`, `@export_custom`
- 빌트인 함수 → `Callable` 자동 변환

### 동작 변경
- 바이너리 직렬화 형식 변경 (기존 인코딩 깨짐)
- 폰트 외곽선 기본 색상: 흰색 → 검정
- `auto_translate` deprecated → `auto_translate_mode` 사용
- Reverse Z 깊이 버퍼 (셰이더 호환 주의)
- Android 권한 자동 요청 중단

---

## 4.4 변경 (4.3 → 4.4)

### Core
- `FileAccess.store_*` 메서드들: 반환 타입 `void` → `bool`
- `FileAccess.open_encrypted`: `iv` 파라미터 추가
- `OS.read_string_from_stdin`: `buffer_size` 파라미터 추가 (GDScript 비호환)
- `RegEx.compile`/`create_from_string`: `show_error` 파라미터 추가

### 신규 노드
- `LookAtModifier3D`, `SpringBoneSimulator3D`, 애니메이션 마커
- **Jolt Physics**: 실험적 3D 물리 대안

### GUI
- `RichTextLabel.push_meta`: `tooltip` 파라미터 추가
- `GraphEdit.connect_node`: `keep_alive` 파라미터 추가
- `GraphEdit.frame_rect_changed` 시그널: `Vector2` → `Rect2`
- **@export_file**: 경로를 `uid://`로 저장 (기존 `res://`에서 변경)

### Rendering
- `RenderingDevice.draw_list_begin`: `breadcrumb` 추가, 여러 파라미터 제거
- `Shader.get_default_texture_parameter`: `Texture2D` → `Texture`
- `VisualShaderNodeCubemap.cube_map`: `Cubemap` → `TextureLayered`
- CPU/GPU 파티클: `restart()`에 `keep_seed` 추가

### GDScript 신규
- **타입 딕셔너리**: `Dictionary[KeyType, ValueType]`
- `@export_tool_button` 어노테이션

### Deprecated/제거
- **SkeletonIK3D deprecated** → LookAtModifier3D
- CSG → Manifold 라이브러리 교체 (비매니폴드 메시 미지원)
- Curve 도메인 [0,1] 범위 강제 (벗어난 포인트 조정 필요)
- .NET 6 지원 중단 → .NET 8.0 필수

### 동작 변경
- Android 센서 기본 비활성화 (프로젝트 설정에서 수동 활성화)

---

## 4.5 변경 (4.4 → 4.5)

### Core
- `JSONRPC.set_scope` → `set_method` (GDScript 비호환)
- `Node.get_rpc_config` → `get_node_rpc_config`
- `Node.set_name`: 파라미터 `String` → `StringName`
- `Resource.duplicate(true)`: 이제 내부 리소스만 복사 (외부 리소스 제외)

### Rendering
- `RenderingServer.instance_reset_physics_interpolation`, `instance_set_interpolated` **제거** (GDScript 비호환)

### Text/UI
- `TextServerExtension` 드로잉 메서드: `oversampling` 파라미터 추가 (GDScript/C# 비호환)
- `RichTextLabel.add_image`: `size_in_percent` → `width_in_percent` + `height_in_percent`로 분리
- `RichTextLabel.update_image`: 동일하게 분리

### GLTF
- `GLTFAccessor` 다수 프로퍼티: `int32` → `int64`
- `GLTFAccessor.component_type`: `int` → `GLTFComponentType` enum
- `GLTFBufferView` 프로퍼티들: `int64`로 변경

### GDScript 신규
- **가변 인자(Variadic arguments)** 함수 지원
- **추상 클래스/메서드** 지원 (`@abstract`)
- Release 빌드 스크립트 역추적

### 신규 노드/기능
- `FoldableContainer`, Stencil 버퍼, SMAA 1x
- **전용 2D NavigationServer** (3D 프록시 아님)
- `duplicate_deep()` (Array, Dictionary, Resource 깊은 복사)
- **AccessKit 스크린 리더** 지원

### Networking (XR)
- `OpenXRAPIExtension`: 4개 메서드 파라미터 타입 변경
- XR 에디터 관련 클래스가 Core → Editor API로 이동

### 동작 변경
- **TileMapLayer**: 물리 청크 병합 기본 활성화 → `get_coords_for_body_rid()` 반환값 변경
- Navigation region 업데이트: 기본 비동기 (프로젝트 설정으로 조정 가능)
- Jolt `Area3D`: 정적 바디와의 오버랩 항상 보고
- C# Android 내보내기: .NET 9 필요

---

## 4.6 변경 (4.5 → 4.6)

### Core
- `FileAccess.get_as_text`: `skip_cr` 파라미터 **제거**
- `FileAccess.create_temp`: `mode_flags` 타입 `int` → `FileAccess.ModeFlags`

### Animation
- `AnimationPlayer.assigned_animation/autoplay/current_animation`: `String` → `StringName`
- `AnimationPlayer.get_queue`: 반환 `PackedStringArray` → `StringName[]`
- `AnimationPlayer.current_animation_changed` 시그널: `String` → `StringName`
- `SpringBoneSimulator3D` 다수 enum: `SpringBoneSimulator3D` → `SkeletonModifier3D`로 이동

### GUI
- `Control.grab_focus`/`has_focus`: `hide_focus`/`ignore_hidden_focus` 파라미터 추가
- `FileDialog.add_filter`: `mime_type` 파라미터 추가
- `SplitContainer.clamp_split_offset`: `priority_index` 파라미터 추가

### Networking
- `StreamPeerTCP` 메서드들 → `StreamPeerSocket`으로 이동
- `TCPServer` 메서드들 → `SocketServer`로 이동

### Editor
- `EditorFileDialog.add_side_menu` **제거**
- `EditorFileDialog` 16개 메서드 + 9개 프로퍼티 → `FileDialog` 베이스 클래스로 이동

### 신규 기능
- **Jolt Physics가 새 3D 프로젝트 기본값**
- **IK 프레임워크**: `IKModifier3D`, `TwoBoneIK3D`, `SplineIK3D`, `FABRIK3D`, `CCDIK3D`, `JacobianIK3D`
- **D3D12가 Windows 기본 렌더러**
- **LibGodot**: 커스텀 앱에 Godot 엔진 임베딩
- **Unique Node IDs**: 씬 리팩토링 시 노드 추적

### 동작 변경
- **.tscn 형식**: `load_steps` 더 이상 기록 안 함, unique node ID 저장
- **Glow**: 기본 블렌드 모드 Soft Light → Screen (상당히 밝아짐)
- **Volumetric fog**: 더 물리적으로 정확한 블렌딩 (밝아짐)
- **AStar**: 시작점이 disabled/solid이면 빈 경로 반환
- `MeshInstance3D.skeleton`: 기본값 `NodePath("..")` → `NodePath("")`

---

## 항상 조회 대상 (버전 무관)

아래는 변경이 잦거나 불확실한 영역. 확신이 없을 때 WebFetch:

- TileMapLayer API (4.3 신규, 4.5에서 동작 변경)
- IK 노드 (4.6 대폭 추가)
- Jolt Physics 설정 (4.4 실험적 → 4.6 기본값)
- AnimationPlayer 타입 변경 (4.6에서 String → StringName)
- NavigationServer API (4.3~4.5 계속 변경)
- RenderingDevice/RenderingServer (매 버전 변경)
- GDScript 신규 문법 (@abstract, variadic, typed dict)
- StreamPeerTCP/TCPServer → Socket 계열 이동 (4.6)
- XR/OpenXR API
- FileAccess 메서드 시그니처

---

## WebFetch URL 패턴

### 1차: 공식 문서 HTML (내용이 잘릴 수 있음)
```
https://docs.godotengine.org/en/stable/classes/class_{소문자클래스명}.html
```

### 2차 fallback: GitHub raw RST (확실히 전체 내용 확보)
```
https://raw.githubusercontent.com/godotengine/godot-docs/master/classes/class_{소문자클래스명}.rst
```

### 마이그레이션 가이드
```
https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/migrating/upgrading_to_godot_4.3.rst
https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/migrating/upgrading_to_godot_4.4.rst
https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/migrating/upgrading_to_godot_4.5.rst
https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/migrating/upgrading_to_godot_4.6.rst
```

### 예시
```
TileMapLayer    → class_tilemaplayer.html / class_tilemaplayer.rst
CharacterBody2D → class_characterbody2d.html / class_characterbody2d.rst
AnimationPlayer → class_animationplayer.html / class_animationplayer.rst
```
