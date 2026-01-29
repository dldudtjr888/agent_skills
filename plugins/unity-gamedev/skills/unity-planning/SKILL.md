---
name: unity-planning
description: "Unity 게임 기획 워크플로우. 사용 시점: (1) 새 Unity 게임 프로젝트 시작 시, (2) 게임 아이디어를 기획 문서로 정리할 때, (3) '기획해줘' 또는 'GDD 만들어줘' 요청 시, (4) planning 폴더에 문서 생성이 필요할 때"
---

# Unity Planning

게임 아이디어를 체계적인 기획 문서로 변환한다.

## Workflow

```
Step 1: 아이디어 수집 → Step 2: Reference 분석 → Step 3: 내용 정리 → Step 4: 부족한 부분 질문 → Step 5: 문서 생성 → Step 6: CLAUDE.md 업데이트 → Step 7: Self Reflection
```

---

## Step 1: 아이디어 수집

사용자가 자유롭게 게임 아이디어 설명하도록 안내.
- 어떤 형식이든 OK
- 기존 기획 문서 있으면 공유받기

## Step 2: Reference 분석

Reference/ 폴더 활용 안내:
```
Reference/ 폴더에 참고 자료를 넣어주시면 분석해서 기획에 반영합니다:
- 문서, 이미지, 영상 링크 등
```

폴더 있으면 Glob → Read로 분석 후 기획에 반영.

## Step 3: 내용 정리

수집된 정보를 구조화해서 보여주기:
```
## 현재까지 정리된 내용
- 게임 컨셉: ...
- 핵심 메카닉: ...
- 레퍼런스: ...
```

## Step 4: 부족한 부분 파악

필수 카테고리 체크리스트로 미정의 항목 파악.
상세 체크리스트는 [planning-checklist.md](references/planning-checklist.md) 참조.

**질문 가이드라인:**
- 2-3개씩 끊어서 진행
- "나중에", "스킵" 응답 시 해당 항목 제외
- 필수 카테고리 먼저, 선택 카테고리는 간단히

## Step 5: 문서 생성

`planning/` 폴더에 주제별 문서 생성:

```
planning/
├── 01-concept.md           # 게임 컨셉
├── 02-references.md        # 레퍼런스 분석
├── 03-core-loop.md         # 코어 루프
├── 04-mechanics.md         # 핵심 메카닉
├── 05-win-conditions.md    # 승리/패배 조건
├── 06-characters.md        # 캐릭터/역할
├── 07-levels.md            # 레벨/맵 설계
├── 08-ui-flow.md           # UI 플로우 (선택)
├── 09-metrics.md           # 밸런스 수치
├── 10-tech-stack.md        # 기술 스택
├── 11-folder-structure.md  # 폴더 구조
├── 12-multiplayer.md       # 멀티플레이어 (해당 시)
├── 13-mobile-ux.md         # 모바일 UX (해당 시)
├── 14-audio-feedback.md    # 사운드 (선택)
├── 15-onboarding.md        # 온보딩 (선택)
├── 16-settings.md          # 설정 (선택)
└── 17-meta-systems.md      # 메타 시스템 (선택)
```

스킵한 항목은 문서 생성하지 않음.

## Step 6: CLAUDE.md 업데이트

프로젝트 루트 CLAUDE.md에 반영:
- 프로젝트 개요 (01-concept 기반)
- 핵심 메카닉 요약
- 폴더 구조, 네이밍 컨벤션
- 메트릭 기준
- 개발 단계
- MCP 사용 가이드

## Step 7: Self Reflection

문서 생성 후 필수 확인:

```
## Self Reflection

### 확인 완료 항목
- [x] ...

### 미정의 항목 (의도적 스킵)
- [ ] ...

### 보완 필요 항목
- ...

### 다음 단계에서 결정 필요
- ...
```

---

## 원칙

1. **사용자 주도**: 사용자가 먼저 설명, Claude는 정리/보완
2. **유연한 진행**: 스킵 요청 시 제외
3. **세분화된 문서**: 하나의 큰 GDD 대신 주제별 분리
4. **점진적 완성**: 나중에 추가 가능
5. **Self Reflection 필수**: 누락/보완 항목 확인

---

## 다음 단계

기획 완료 후 `unity-prototype` 스킬로 프로토타입 진행.

---

## Resources

### references/
- [planning-checklist.md](references/planning-checklist.md) - 기획 필수/선택 항목 체크리스트
