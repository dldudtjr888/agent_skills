---
name: unity-task-decomposer
description: "Unity 프로젝트 기획 문서를 MCP 기반 실행 가능한 태스크 목록으로 분해. 사용 시점: (1) planning 폴더의 기획 문서를 구현 태스크로 변환할 때, (2) 태스크 분해해줘 또는 구현 계획 세워줘 요청 시, (3) 대규모 Unity 기능을 단계별로 나눌 때"
---

# Unity Task Decomposer

기획 문서를 Unity MCP 도구로 실행 가능한 구체적 태스크 목록으로 변환한다.

## Workflow

```
Step 1: 기획 분석 → Step 2: Phase 분리 → Step 3: 태스크 분해 → Step 4: Wave 구성 → Step 5: MCP 매핑 → Step 6: 문서 생성
```

---

## Step 1: 기획 문서 분석

planning/ 폴더에서 핵심 정보 추출:

| 문서 | 추출 항목 |
|------|----------|
| concept.md | 장르, 시점, 플랫폼 |
| mechanics.md | 구현할 메카닉 목록 |
| levels.md | 맵/레벨 설계 |
| metrics.md | 수치 기준 |
| tech-stack.md | 패키지, 기술 결정 |
| folder-structure.md | 폴더/네이밍 규칙 |

---

## Step 2: Phase 분리

대규모 프로젝트는 Phase로 분리 (각 20개 태스크 이하):

```
Phase 1: 프로젝트 설정 + 기본 이동
Phase 2: 핵심 메카닉
Phase 3: 게임 루프 + UI
Phase 4: 멀티플레이어 (해당 시)
Phase 5: 폴리싱
```

---

## Step 3: 태스크 분해

재귀적 분해:
```
메카닉 → 시스템 → 스크립트 → 함수 → atomic 작업
```

**분해 기준:**
- 30분 이내 완료 가능
- 단일 스크립트/컴포넌트 수준
- 명확한 완료 조건

**예시:**
```
이동 시스템
├── Input Actions 에셋 생성
├── PlayerController.cs 생성
├── CharacterController 설정
└── 이동 테스트
```

---

## Step 4: Wave 구성

의존성 기반 병렬 실행 그룹:

```
Wave 1: 의존성 없음 (폴더, 설정, 유틸리티)
Wave 2: Wave 1 의존 (기본 스크립트)
Wave 3: Wave 2 의존 (프리팹)
Wave 4: Wave 3 의존 (씬 구성)
Wave 5: 통합 테스트
```

---

## Step 5: MCP 도구 매핑

각 태스크에 MCP 도구 지정. 상세 매핑은 [references/mcp-mapping.md](references/mcp-mapping.md) 참조.

**핵심 매핑:**

| 태스크 유형 | MCP 도구 |
|------------|---------|
| 폴더 생성 | `manage_asset` action="create_folder" |
| 태그/레이어 | `manage_editor` action="add_tag/add_layer" |
| 스크립트 생성 | `create_script` |
| 게임오브젝트 | `manage_gameobject` action="create" |
| 컴포넌트 추가 | `manage_gameobject` action="add_component" |
| 프리팹 저장 | `manage_gameobject` save_as_prefab=true |
| 머티리얼 | `manage_material` |
| 씬 관리 | `manage_scene` |
| 에러 확인 | `read_console` |
| 플레이 테스트 | `manage_editor` action="play" |

**필수 순서:**
1. 스크립트 작성 후 → `read_console` (컴파일 확인)
2. 컴포넌트 추가 전 → 스크립트 컴파일 완료 확인
3. 플레이 테스트 전 → 씬 저장

---

## Step 6: 문서 생성

`tasks/` 폴더에 Phase별 문서 생성:

```
tasks/
├── technical-decisions.md
├── phase1-setup.md
├── phase2-core.md
└── ...
```

---

## 태스크 문서 형식

각 태스크 항목:

```markdown
- [ ] **T-001**: [태스크명] ⏱️ [시간]
  - 파일: [대상 파일/폴더]
  - MCP 도구: [사용할 도구]
  - 작업:
    - [ ] 세부 작업 1
    - [ ] 세부 작업 2
  - 검증:
    - [ ] 검증 항목
  - blocked by: [선행 태스크] (있는 경우)
```

---

## 검증 규칙

| 태스크 유형 | 검증 방법 |
|------------|----------|
| 스크립트 | `read_console` 에러 0개 |
| 프리팹 | 파일 존재 + 컴포넌트 확인 |
| 씬 | `get_hierarchy` + 플레이 가능 |

---

## 맵 구현

맵/레벨 구현은 `unity-map-builder` 스킬 사용.
태스크 분해 시 맵 관련 태스크는 해당 스킬로 위임.

---

## Resources

### references/
- [mcp-mapping.md](references/mcp-mapping.md) - MCP 도구 상세 매핑 및 시퀀스
