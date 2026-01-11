# 모듈별 구현 가이드

## A. 프로젝트 초기 설정

planning/11-folder-structure.md 기반:

### 1. 폴더 구조 생성
```
MCP: manage_asset → create_folder
```

### 2. 필수 패키지 확인
- planning/10-tech-stack.md 참조
- manifest.json 확인
- 없는 패키지 설치 안내

### 3. 태그 & 레이어 설정
```
MCP: manage_editor → add_tag, add_layer
```

### 4. 메트릭 프리팹 생성
- planning/09-metrics.md 기반
```
MCP: manage_gameobject → create
```

---

## B. 플레이어 컨트롤러

planning/01-concept.md 시점 정보 기반:

### 1. 캐릭터 생성
- planning/09-metrics.md 캐릭터 크기 참조
```
MCP: manage_gameobject → create
MCP: manage_gameobject → add_component (CharacterController 또는 Rigidbody)
```

### 2. 입력 시스템 설정
- planning/04-mechanics.md 조작 메카닉 참조
```
MCP: manage_asset → create (InputActions)
```

### 3. 이동 구현
시점별 이동 방식:
- 1인칭: 카메라 기준 직접 이동
- 3인칭: 카메라 기준 이동 + 캐릭터 회전
- 탑다운: 클릭 이동 또는 직접 이동

```
MCP: create_script (PlayerController.cs)
MCP: read_console (컴파일 확인)
```

### 4. 카메라 설정
시점별 Cinemachine 카메라:
- 1인칭: Virtual Camera + POV
- 3인칭: FreeLook 또는 Third Person Follow
- 탑다운: 고정 각도 Virtual Camera

### 5. 테스트
```
MCP: manage_editor → play
MCP: read_console (런타임 에러)
MCP: manage_editor → stop
```

---

## C. 그레이박스 레벨

planning/07-levels.md 기반:

### 1. 레벨 레이아웃 계획
- planning 문서 레벨 설계 참조
- 없으면 사용자에게 기본 레이아웃 질문

### 2. 기본 지형 생성
```
MCP: manage_gameobject → create (Floor, Wall, Obstacle)
```
- planning/09-metrics.md 크기 기준 적용
- 그레이박스 머티리얼 적용

### 3. 콜라이더 & 조명
```
MCP: manage_gameobject → add_component (Collider)
MCP: manage_gameobject → create (Directional Light)
```

### 4. 플레이어 스폰 포인트
```
MCP: manage_gameobject → create (SpawnPoint)
```

### 5. 씬 저장
```
MCP: manage_scene → save
```

---

## D. 핵심 메카닉

planning/04-mechanics.md 기반:

### 1. 게임 매니저
```
MCP: create_script (GameManager.cs)
```
- 싱글톤 패턴
- 게임 상태 관리

### 2. 핵심 메카닉 구현
- planning 문서 우선순위대로
- 각 메카닉 하나씩 구현 & 테스트
```
MCP: create_script
MCP: read_console
MCP: manage_editor → play
```

### 3. 상호작용 시스템 (필요시)
```
MCP: create_script (IInteractable.cs)
MCP: create_script (InteractionController.cs)
```

---

## MCP 도구 시퀀스

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
4. manage_gameobject → create (Floor)
5. manage_material → assign_material_to_renderer
6. manage_scene → save
```

### 검증 시퀀스
```
1. manage_scene → save
2. manage_editor → play
3. read_console (types: ["error", "warning"])
4. manage_editor → stop
```
