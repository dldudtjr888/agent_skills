---
name: unity-prototype
description: "Unity 게임 프로토타입 워크플로우. 사용 시점: (1) planning 완료 후 프로토타입 시작 시, (2) Unity MCP로 실제 구현 진행 시, (3) '프로토타입 만들어줘' 요청 시, (4) 그레이박스 레벨/플레이어 컨트롤러 구현 시"
---

# Unity Prototype

기획 문서 기반으로 Unity MCP를 사용해 프로토타입을 구현한다.

## Workflow

```
Step 0: 태스크 문서 확인 → Step 1: 기획 문서 확인 → Step 2: 현재 상태 확인 → Step 3: 범위 결정 → Step 4: 구현
```

---

## Step 0: 태스크 문서 확인 (권장)

tasks/ 폴더의 태스크 문서 존재 여부 확인:

```
tasks/
├── technical-decisions.md  → 기술 결정
├── phase1-setup.md         → Phase 1 태스크
├── phase2-core.md          → Phase 2 태스크
```

**tasks/ 있으면:**
- 태스크 문서의 Wave 순서대로 진행
- 체크박스 따라 작업
- 완료 시 체크 표시 업데이트

**tasks/ 없으면:**
- Step 1부터 기존 워크플로우 진행
- 또는 `unity-task-decomposer` 스킬로 태스크 문서 먼저 생성

---

## Step 1: 기획 문서 확인

planning/ 폴더에서 필수 문서 확인:

| 문서 | 확인 항목 |
|------|----------|
| 01-concept.md | 장르, 시점, 플랫폼 |
| 04-mechanics.md | 핵심 메카닉 |
| 07-levels.md | 레벨 설계 |
| 09-metrics.md | 메트릭 기준 |
| 10-tech-stack.md | 기술 스택 |
| 11-folder-structure.md | 폴더 구조 |

**planning/ 없으면:**
- 사용자에게 기본 정보 질문
- 또는 `unity-planning` 스킬 먼저 실행 권유

---

## Step 2: 현재 프로젝트 상태 확인

```
MCP 도구:
- manage_scene → get_active: 현재 씬
- manage_scene → get_hierarchy: 기존 오브젝트
- read_console: 에러 확인
```

사용자에게 보고:
- 어떤 씬이 열려있는지
- 이미 만들어진 것이 있는지
- 에러가 있는지

---

## Step 3: 프로토타입 범위 결정

사용자에게 범위 질문:

```
프로토타입에서 뭘 먼저 만들까요?
1. 프로젝트 초기 설정 (폴더, 패키지, 태그/레이어)
2. 플레이어 컨트롤러 (이동, 카메라)
3. 그레이박스 레벨 (테스트 맵)
4. 핵심 메카닉 (게임별로 다름)
5. 전부 다
```

선택한 부분만 진행.

---

## Step 4: 모듈별 구현

각 모듈 구현 가이드는 [module-guides.md](references/module-guides.md) 참조.

### 기본 MCP 순서

```
1. 스크립트 작성 후 → read_console (컴파일 확인)
2. 컴포넌트 추가 전 → 스크립트 컴파일 완료 확인
3. 플레이 테스트 전 → 씬 저장
```

---

## 태스크 기반 진행

tasks/ 폴더에 태스크 문서가 있을 때:

### Wave별 실행
1. 현재 Wave 태스크 목록 확인
2. 병렬 가능한 태스크는 동시 진행
3. 체크박스 순서대로 수행
4. 검증 항목 확인
5. 완료 시 체크박스 업데이트
6. Wave 완료 후 다음 Wave로

### 블로커 처리
- `blocked by` 있으면 선행 태스크 먼저 완료
- 의존성 그래프 위반 금지

---

## 원칙

1. **태스크 문서 우선**: tasks/ 있으면 해당 순서대로
2. **planning 문서 참조**: 기획에 정의된 내용 따름
3. **하나씩 진행**: 한 모듈 완료 후 다음으로
4. **테스트 필수**: 각 단계 후 플레이 테스트
5. **에러 확인**: 스크립트 작성 후 read_console 필수
6. **사용자 확인**: 주요 결정 전 사용자 확인

---

## 완료 보고

각 Wave/모듈 완료 시:

```
✅ 완료된 항목:
- T-001: 폴더 구조 생성
- T-002: 태그 설정

🔄 진행 중:
- T-006: Input Actions 설정

⏳ 남은 항목:
- Wave 3: 스크립트 생성

다음으로 뭘 진행할까요?
```

---

## 다음 단계

프로토타입 완료 후:
- 펀팩터 검증
- 핵심 메카닉 테스트
- 피드백 수집

이후:
- `unity-task-decomposer`로 Phase 2 태스크 생성
- `unity-production` 스킬로 본격 개발

---

## Resources

### references/
- [module-guides.md](references/module-guides.md) - 모듈별 구현 가이드
