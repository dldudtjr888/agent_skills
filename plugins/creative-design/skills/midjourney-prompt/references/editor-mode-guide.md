---
title: Editor 모드 상세 가이드
category: reference
tags: editor, inpaint, erase, retexture, layers, smart select
---

# Editor 모드 상세 가이드

기존 이미지를 부분 수정하거나 스타일을 변환할 때 사용하는 미드저니 웹 Editor의 상세 가이드.
Editor는 파라미터(`--ar`, `--stylize`, `--cref`, `--sref`, `--oref` 등) 없이 **텍스트 프롬프트만**으로 결과를 제어한다.

---

## Editor 도구 6가지 상세

### 1. Erase / Restore

| 항목 | 내용 |
|------|------|
| **용도** | 이미지의 특정 부분을 지워서 AI가 재생성하도록 마킹 |
| **UI 조작** | 브러시로 영역 칠하기, 브러시 크기 슬라이더로 조절 |
| **Restore** | 실수로 지운 부분을 되돌리는 복원 도구 |
| **프롬프트 역할** | 지운 영역에 **무엇을 채울지** 텍스트로 지시 |

**프롬프트 팁:**
- 마스킹 영역에 나타날 내용만 구체적으로 묘사
- 주변 이미지와의 스타일/조명 일관성 키워드 포함
- 넓은 영역일수록 더 상세한 묘사 필요
- 좁은 영역은 간결한 키워드만으로도 충분

### 2. Smart Select

| 항목 | 내용 |
|------|------|
| **용도** | 포함/제외 포인트를 찍어 AI가 자동으로 마스크 생성 |
| **Erase Selection** | 선택한 영역만 지우기 |
| **Erase Background** | 선택 영역 외 배경 전체 제거 |
| **정확도** | AI 기반 경계 인식으로 높은 정확도 |

**활용 팁:**
- 복잡한 형태(머리카락, 나뭇잎 등)의 마스킹에 유리
- Erase Background로 피사체 분리 후 새 배경 프롬프트 작성
- 포함/제외 포인트를 여러 개 찍어 정밀도 향상

### 3. Layers

| 항목 | 내용 |
|------|------|
| **용도** | 여러 이미지를 레이어로 추가하여 합성 |
| **기능** | 순서 변경, 활성 레이어 선택 편집, 개별 Erase |
| **제한** | Submit 시 레이어가 **평탄화(flatten)** — 비파괴 편집 아님 |

**프롬프트 팁:**
- 합성 후 경계면이 어색하면 해당 영역을 Erase하고 블렌딩 프롬프트 작성
- 프롬프트에 전체적인 통일감 키워드 포함: `cohesive scene`, `unified lighting`, `seamless blend`

### 4. Move / Resize

| 항목 | 내용 |
|------|------|
| **용도** | 캔버스에서 이미지 위치/크기 조정, 리프레이밍 |
| **커스텀 종횡비** | 수동으로 원하는 비율 입력 가능 |
| **Outpainting** | 이미지를 작게 만들면 주변을 AI가 창의적으로 확장 |

**프롬프트 팁:**
- 확장될 영역에 대한 묘사를 프롬프트에 포함
- 예: 위로 확장 시 `clear blue sky with scattered clouds`
- 예: 아래로 확장 시 `stone cobblestone street, matching perspective`

### 5. Retexture

| 항목 | 내용 |
|------|------|
| **용도** | 이미지의 **구조/구도는 유지**하면서 스타일/질감/분위기를 완전 변경 |
| **작동 원리** | 지오메트리, 재질, 조명을 추론하여 새 프롬프트에 맞게 리스타일링 |
| **결과** | 4개 옵션 제공, 선택 후 Upscale 가능 |

**프롬프트 팁:**
- 구조/구도 묘사 불필요 (자동 유지됨)
- **스타일, 질감, 색감, 분위기**에 집중
- 구체적인 미술 매체/화풍 명시가 효과적
- 50단어 이내 권장

### 6. Export

| 항목 | 내용 |
|------|------|
| **Upscale to Gallery** | 고해상도 업스케일 후 갤러리 저장 |
| **Download Image** | 디바이스에 직접 다운로드 |
| **Save Current Edit** | Erase한 영역을 **투명 PNG**로 저장 가능 |

> **주의:** 업스케일하지 않으면 Create/Organize 페이지에 나타나지 않는다. 편집 결과는 반드시 Upscale하거나 Download할 것.

---

## Erase/Inpaint 프롬프트 전략 심화

### 배경 교체

원본 이미지의 피사체는 유지하고 배경만 변경할 때.

**전략:**
- Smart Select로 피사체 선택 → Erase Background
- 또는 Erase 브러시로 배경 영역만 직접 마킹
- 프롬프트에 새 배경만 묘사 (피사체 묘사 불필요)
- 원본의 조명 방향/색온도와 일관된 키워드 포함

**프롬프트 예시:**
```
lush enchanted forest with soft dappled sunlight filtering through leaves, mystical atmosphere, matching warm lighting from the left
```

### 오브젝트 추가

기존 장면에 새로운 요소를 삽입할 때.

**전략:**
- 추가할 위치의 빈 공간을 Erase로 마킹
- 프롬프트에 추가할 오브젝트를 구체적으로 묘사
- 기존 이미지의 스타일/질감과 매칭되는 키워드 포함

**프롬프트 예시:**
```
a small fluffy black cat sitting calmly on the ledge, matching the existing warm lighting and watercolor art style
```

### 오브젝트 제거

불필요한 요소를 자연스럽게 제거할 때.

**전략:**
- 제거할 오브젝트를 Erase로 마킹
- 프롬프트를 비워두거나, 주변 환경만 간략히 묘사
- 빈 프롬프트 시 미드저니가 주변 컨텍스트로 자연스럽게 채움

**프롬프트 예시:**
```
clean stone wall with natural texture, continuous brick pattern
```

### 의상/색상 변경

캐릭터의 의상이나 특정 요소의 색상만 변경할 때.

**전략:**
- 변경할 의상/요소만 정밀하게 Erase (브러시 크기 작게)
- 새 의상/색상을 구체적으로 묘사 + 재질감 포함
- 주변과의 자연스러운 연결을 위한 키워드 추가

**프롬프트 예시:**
```
deep royal blue silk fabric with subtle sheen, elegant draping, same fabric texture and lighting
```

---

## Retexture 프롬프트 전략 심화

### 화풍 변환

사실적 이미지를 특정 미술 매체로 변환하거나 그 반대.

**프롬프트 예시:**
```
delicate watercolor painting, soft wet-on-wet technique, muted pastel palette, visible paper texture, gentle color bleeding at edges
```
```
oil painting in the style of Dutch Golden Age, rich warm tones, dramatic chiaroscuro, visible brushstrokes, varnished finish
```

### 시대/문화 변환

동일한 구도를 다른 시대나 문화적 맥락으로 변환.

**프롬프트 예시:**
```
ancient Japanese ukiyo-e woodblock print, flat perspective, bold outlines, limited color palette of indigo and vermillion
```
```
retro 1980s synthwave aesthetic, neon pink and cyan gradients, chrome reflections, grid floor, VHS scan lines
```

### 계절/시간 변환

같은 장면의 계절이나 시간대를 변경.

**프롬프트 예시:**
```
deep winter scene, heavy snow covering surfaces, frost and ice crystals, cold blue and white palette, bare frozen branches, misty cold breath
```
```
golden hour sunset, warm orange and amber tones, long dramatic shadows, hazy atmospheric glow
```

### 분위기 변환

동일한 구도에서 전체적인 톤/무드를 변경.

**프롬프트 예시:**
```
dark gothic horror atmosphere, desaturated cold tones, ominous shadows, fog rolling in, eerie green undertones
```
```
whimsical fairy tale illustration, bright candy colors, soft rounded forms, sparkling magical particles
```

---

## Layers 활용 시 프롬프트 팁

1. **합성 후 경계 블렌딩**: 레이어 경계가 어색한 부분을 Erase → `seamless transition, natural blend, matching shadows`
2. **조명 통일**: 여러 소스 이미지의 조명이 다를 때 → Retexture로 `unified warm lighting from upper left, consistent shadow direction`
3. **스타일 통일**: 다른 화풍의 이미지를 합성했을 때 → Retexture로 하나의 스타일로 통일

---

## 흔한 실수와 해결법

### 실수 1: Editor에서 포즈 변경 시도
- **증상**: 포즈 안 바뀌고 마스킹 영역의 디테일만 변경
- **해결**: Create 페이지에서 `--cref` 또는 `--oref` 사용

### 실수 2: Erase 영역이 너무 작음
- **증상**: 새 요소가 잘리거나 어색하게 생성
- **해결**: 변경하려는 영역보다 **약간 넓게** 마스킹 (주변 컨텍스트 확보)

### 실수 3: Retexture 프롬프트에 구도/포즈 묘사
- **증상**: 구조가 이상하게 왜곡되거나 프롬프트 토큰 낭비
- **해결**: 스타일/질감/분위기만 묘사. 구조는 자동 유지됨

### 실수 4: 프롬프트 없이 Erase만 Submit
- **증상**: 미드저니가 주변 컨텍스트로 추측하여 채움 (원하지 않는 결과)
- **해결**: 제거 목적이 아니라면 반드시 프롬프트에 원하는 내용 기술

### 실수 5: Editor에서 파라미터 사용 시도
- **증상**: 파라미터가 무시되거나 오류
- **해결**: Editor는 텍스트 프롬프트만 지원. `--stylize`, `--ar` 등은 Create 페이지 전용

---

## 실전 워크플로우 시나리오

### 시나리오 1: 캐릭터 배경 교체

1. Editor에서 이미지 열기
2. **Smart Select**로 캐릭터 선택 → **Erase Background** 클릭
3. 프롬프트 입력: `ancient stone castle courtyard, ivy-covered walls, warm afternoon sunlight, fantasy RPG atmosphere`
4. Submit → 4개 결과 중 선택 → Upscale

### 시나리오 2: 3D 렌더를 일러스트로 변환

1. 3D 렌더 스크린샷 업로드
2. **Retexture** 탭 선택
3. 프롬프트 입력: `hand-painted digital illustration, vibrant colors, soft cel-shading, anime-inspired aesthetic, detailed linework`
4. Submit → 마음에 드는 결과 선택 → Upscale

### 시나리오 3: 게임 환경에 소품 추가

1. 배경 이미지에서 소품 배치할 영역을 **Erase**로 마킹
2. 프롬프트 입력: `ornate treasure chest with golden trim, slightly open with faint glow, matching the dungeon's dark stone aesthetic`
3. Submit → 결과 확인
4. 어색한 경계가 있으면 해당 부분만 다시 Erase → `seamless stone floor, natural shadow beneath chest`

### 시나리오 4: 여러 캐릭터 합성

1. 배경 이미지 로드
2. **Layers**로 캐릭터 이미지들을 추가
3. **Move/Resize**로 각 캐릭터 배치
4. 경계면을 **Erase**로 블렌딩
5. 프롬프트: `cohesive group scene, unified lighting, natural interaction between characters`
6. Submit → Retexture로 스타일 통일 가능
