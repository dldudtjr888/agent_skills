---
title: 미드저니 비디오 생성 가이드
category: reference
tags: video, animation, motion, animate
---

# 미드저니 비디오 생성 가이드

## 모델 버전 개요

| 모델 | 출시 | 생성 방식 | 최대 길이 | 해상도 |
|------|------|----------|----------|--------|
| **V1** | 2025년 6월 | Image-to-Video 전용 | 21초 (5초 + 4초×4) | 480p (기본) / 720p HD |
| **V8** | 2026년 현재 | Text-to-Video + Image-to-Video | 10초 / 60fps | 480p ~ HD |

**공통 스펙:**
- 포맷: MP4, 무음(오디오 미지원)
- 기본 생성: 5초 클립 4개 동시 생성
- GPU 비용: ~8 GPU분/생성 (이미지의 약 8배)
- 플랫폼: 웹 UI 전용 (Discord 봇 미지원)

---

## 지원 파라미터

> ⚠️ 비디오 생성 시 이미지 파라미터(`--ar`, `--stylize`, `--cref`, `--sref`, `--oref`, `--chaos` 등)는 **사용 불가**

| 파라미터 | 문법 | 효과 | 권장 상황 |
|---------|------|------|---------|
| `--motion low` | `--motion low` | 미묘하고 자연스러운 움직임, 카메라 고정 경향 | 캐릭터 걷기, 자연스러운 애니메이션 |
| `--motion high` | `--motion high` | 역동적인 큰 움직임, 카메라도 함께 움직임 | 액션 장면, 극적 효과 (왜곡 위험) |
| `--raw` | `--raw` | 미드저니 자동 스타일 최소화, 프롬프트 충실도 향상 | 정확한 동작 묘사가 필요할 때 |
| `--end [URL]` | `--end https://...` | 시작 이미지에서 종료 이미지로 전환하는 애니메이션 | A→B 상태 전환, 변신 장면 |
| `--loop` | `--loop` | 시작 프레임과 종료 프레임이 일치하는 루핑 비디오 | 반복 재생 애니메이션 |

---

## 웹 UI 모션 설정 옵션

이미지에서 Animate 버튼 클릭 시 나타나는 옵션:

| 옵션 | 설명 | 사용 시점 |
|------|------|---------|
| **Auto Low Motion** | 미드저니가 자동으로 낮은 강도 모션 생성 | 빠른 테스트 |
| **Auto High Motion** | 미드저니가 자동으로 높은 강도 모션 생성 | 역동적 결과 탐색 |
| **Manual Low Motion** | 텍스트 프롬프트로 낮은 강도 모션 제어 | 세밀한 동작 제어 |
| **Manual High Motion** | 텍스트 프롬프트로 높은 강도 모션 제어 | 역동적 정밀 제어 |
| **Loop (Low/High)** | 루핑 비디오 생성 | 게임 스프라이트, 반복 애니메이션 |

---

## Image-to-Video 워크플로우

### 기본 흐름

```
[이미지 생성 또는 업로드] → [Animate 버튼] → [모션 설정 선택] → [프롬프트 입력] → [Generate]
```

### 단계별 안내

**Step 1: 기반 이미지 준비**
- 기존 미드저니 갤러리 이미지 선택, 또는
- 외부 이미지 업로드 (프롬프트 바에 드래그앤드롭)

**Step 2: Animate 클릭**
- 이미지 호버 → **"Animate"** 버튼 클릭
- 또는 이미지 열기 → "Animate Image" 버튼

**Step 3: 모션 설정 선택**
- Manual Low/High Motion 권장 (프롬프트 제어 가능)

**Step 4: 프롬프트 입력**
- 동작, 카메라 움직임, 속도를 영어로 기술

**Step 5: 결과 확인 및 확장**
- 5초 클립 4개 생성 → 원하는 것 선택
- "Extend Video" 클릭 → 4초씩 최대 21초까지 연장

**Step 6: 다운로드**
- Download for Social: 소셜 미디어 최적화
- Download Raw Video: 원본 파일
- Download GIF: GIF 형식

---

## Text-to-Video 워크플로우 (V8)

이미지 없이 텍스트 프롬프트만으로 바로 비디오 생성 가능.

```
[Create 페이지] → [Video 모드 선택] → [텍스트 프롬프트 입력] → [Generate]
```

**프롬프트 작성 팁 (Text-to-Video):**
- 이미지-to-비디오보다 더 상세한 장면 묘사 필요
- 배경, 캐릭터, 동작을 모두 포함
- 카메라 무브먼트도 명시

---

## 캐릭터 레퍼런스 + 비디오 연동 워크플로우

`--cref`, `--sref`, `--oref`는 비디오 생성에서 **직접 사용 불가**.
아래 워크어라운드를 사용합니다:

```
1. --cref로 캐릭터 이미지 생성
2. 생성된 이미지를 Starting Frame으로 Animate
3. 비디오 프롬프트로 동작 지정
```

**예시 (CEO.png 픽셀아트 캐릭터 걷기):**

```
Step 1: 이미지 생성
pixel art chibi young male walking pose, black messy hair, round glasses, gray hoodie arms swinging freely --cref [CEO.png URL] --stylize 100 --ar 2:3

Step 2: 생성된 이미지 → Animate → Manual Low Motion

Step 3: 비디오 프롬프트
the pixel art character walks forward with a natural stride, arms swinging rhythmically at sides, smooth walking cycle animation, side view --motion low
```

---

## 카메라 무브먼트 키워드 사전

| 한국어 | 영어 키워드 |
|--------|-----------|
| 팬 왼쪽/오른쪽 | camera pans left / pans right |
| 틸트 위/아래 | camera tilts up / tilts down |
| 줌인 | slow zoom in, camera pushes in |
| 줌아웃 | camera pulls back, zoom out |
| 트래킹 샷 | tracking shot, follows the subject |
| 달리 샷 | dolly forward / dolly backward |
| 고정 카메라 | static camera, locked-off shot |
| 360도 회전 | camera circles around the subject |
| 크레인 업 | crane up, camera rises |
| 핸드헬드 | handheld, slight camera shake |
| POV | first-person view, POV shot |

---

## 동작 표현 한→영 매핑

### 캐릭터 이동

| 한국어 | 영어 키워드 |
|--------|-----------|
| 걷다 | walking, strolling, sauntering |
| 뛰다 | running, dashing, sprinting, jogging |
| 점프하다 | jumping, leaping, hopping |
| 기다 | crawling, creeping |
| 미끄러지다 | sliding, gliding |

### 몸동작

| 한국어 | 영어 키워드 |
|--------|-----------|
| 손 흔들다 | waving hand, arms swinging |
| 돌아보다 | turns head, glances back, looks over shoulder |
| 앉다 | sitting down, crouching |
| 일어서다 | stands up, rises |
| 춤추다 | dancing, swaying, spinning |
| 뻗다/스트레칭 | stretching, reaches out arm |
| 고개 끄덕이다 | nodding, head bobs |

### 속도/강도

| 한국어 | 영어 키워드 |
|--------|-----------|
| 천천히 | slowly, gently, gradually |
| 빠르게 | quickly, rapidly, swiftly |
| 부드럽게 | smoothly, fluidly |
| 갑자기 | suddenly, abruptly |
| 리듬감 있게 | rhythmically |

---

## 비디오 프롬프트 예시

### 캐릭터 걷기 (자연스러운)
```
a pixel art chibi character walks forward with a natural stride, arms swinging rhythmically at sides, smooth looping walk cycle, side view --motion low
```

### 캐릭터 달리기 (역동적)
```
a fantasy warrior running at full speed, cape flowing behind, arms pumping, feet barely touching the ground, dynamic side tracking shot --motion high
```

### 카메라 패닝 (풍경)
```
a misty fantasy landscape at dawn, the camera slowly pans from left to right revealing mountains and a glowing river --motion low --raw
```

### 캐릭터 인사
```
a cute pixel art character waves hello with a cheerful smile, arms raised and waving side to side, slight body bounce, static camera --motion low
```

### A→B 전환 (--end 활용)
```
[Starting Frame: 캐릭터 서있는 포즈 이미지]
[--end URL: 캐릭터 걷는 포즈 이미지]
the character smoothly transitions from standing to walking pose --motion low
```

---

## 비용 및 스펙 참고

| 항목 | 내용 |
|------|------|
| 기본 해상도 | 480p SD |
| HD 해상도 | 720p (Pro/Mega 플랜) |
| V8 최대 | 10초 / 60fps |
| 기본 길이 | 5초 (클립 4개 생성) |
| 최대 길이 | 21초 (4초×4회 Extend) |
| GPU 비용 | ~8 GPU분/생성 |
| 다운로드 | MP4, GIF 선택 가능 |

---

## 흔한 실수와 해결법

| 실수 | 결과 | 해결법 |
|------|------|--------|
| `--ar`, `--stylize` 포함 | 파라미터 무시됨 | 비디오 파라미터만 사용 |
| `--cref` 직접 사용 | 미지원 오류 | 이미지 먼저 생성 → Animate |
| `--motion high` 남용 | 왜곡, 비현실적 물리 | Low motion으로 먼저 테스트 |
| 프롬프트 없이 Auto 선택 | 의도와 다른 움직임 | Manual mode + 프롬프트 사용 |
| 너무 긴 비디오 한 번에 생성 | 불가 | 5초 생성 후 Extend로 연장 |
| Editor 모드에서 Animate 시도 | 기능 없음 | Create 페이지에서 Animate 사용 |
