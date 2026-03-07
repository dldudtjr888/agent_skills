---
name: midjourney-prompt
description: "미드저니(Midjourney) 프롬프트 생성 스킬. 사용자가 한국어로 이미지 설명을 요청하면 미드저니 V7에 최적화된 영어 프롬프트를 생성합니다. '/midjourney', '미드저니 프롬프트', '미드저니로 만들어줘', 'MJ 프롬프트', '이미지 프롬프트 만들어줘' 등의 요청 시 트리거됩니다. 게임 캐릭터 디자인, 컨셉아트, 환경 디자인, UI/아이콘 등 게임 개발 관련 이미지 생성에도 특화되어 있습니다."
metadata:
  author: youngseoklee
  version: "1.1.0"
  date: March 2026
---

# Midjourney Prompt Generator

한국어 이미지 설명을 미드저니 V7에 최적화된 영어 프롬프트로 변환하는 스킬입니다.

## 트리거 조건

다음 요청 시 이 스킬을 사용합니다:

- `/midjourney` 슬래시 커맨드
- "미드저니 프롬프트", "MJ 프롬프트", "미드저니로 그려줘/만들어줘"
- "이미지 프롬프트 생성해줘" (미드저니 맥락)
- "캐릭터 컨셉아트 프롬프트", "환경 디자인 프롬프트"
- 한국어로 이미지 설명 후 미드저니 프롬프트를 요청할 때
- "에딧 프롬프트", "에디터 프롬프트", "인페인팅 프롬프트", "리텍스처 프롬프트"
- "부분 수정 프롬프트", "배경 교체 프롬프트", "이미지 수정 프롬프트"

---

## 프롬프트 생성 워크플로우

사용자 요청을 받으면 다음 5단계를 순서대로 수행합니다.

### Step 1: 요청 분석 (Parse)

한국어 설명에서 다음 요소를 추출합니다:

| 추출 요소 | 설명 | 예시 |
|-----------|------|------|
| **주제(Subject)** | 무엇을 그릴 것인가 | 여전사, 숲속 마을, 마법 지팡이 |
| **스타일(Style)** | 어떤 화풍/매체인가 | 수채화, 픽셀아트, 사실적 사진 |
| **용도(Purpose)** | 어디에 사용하는가 | 게임 캐릭터, 배경화면, SNS |
| **분위기(Mood)** | 어떤 느낌인가 | 몽환적, 역동적, 고요한 |
| **기술 요구(Tech)** | 특정 사양 | 종횡비, 해상도, 투명배경 |
| **레퍼런스 이미지(Ref)** | 참조할 기존 이미지가 있는가 | 캐릭터 이미지, 포즈 사진, 스타일 샘플 |

명시되지 않은 요소는 용도와 맥락에서 추론합니다.
레퍼런스 이미지가 있으면 **이미지 레퍼런스 가이드** 섹션의 워크플로우를 따릅니다.

### Step 2: 카테고리 결정 (Categorize)

| 카테고리 | 트리거 키워드 | 참조 파일 |
|----------|-------------|----------|
| 캐릭터(Character) | 캐릭터, 인물, 초상화, 전사, NPC | `references/styles-game-art.md` |
| 환경(Environment) | 배경, 풍경, 맵, 던전, 마을 | 카테고리에 따라 선택 |
| 아이템/오브젝트(Item) | 무기, 아이템, 소품, 아이콘 | `references/styles-game-art.md` |
| UI/아이콘(UI) | UI, 아이콘, 버튼, HUD | `references/styles-game-art.md` |
| 포토리얼(Photo) | 사진, 실사, 포토, 제품사진 | `references/styles-photorealistic.md` |
| 일러스트(Illustration) | 그림, 일러스트, 수채화, 만화 | `references/styles-illustration.md` |
| 애니메이션(Anime) | 애니, 만화, 일본풍, 동양풍 | `references/styles-illustration.md` + `--niji 7` |
| 3D 렌더(3D) | 3D, 렌더, 클레이, 로우폴리 | `references/styles-3d-render.md` |
| Editor(Inpaint) | 에딧, 인페인팅, 부분수정, 배경교체, 오브젝트 추가/제거 | `references/editor-mode-guide.md` |
| Editor(Retexture) | 리텍스처, 스타일변환, 질감변경, 화풍변환 | `references/editor-mode-guide.md` |

### Step 3: 프롬프트 조립 (Compose)

아래 구조 공식에 따라 영어 프롬프트를 조립합니다.
한국어 표현의 변환은 `references/korean-english-mapping.md`를 참조합니다.

### Step 4: 파라미터 결정 (Parameters)

파라미터 추천 로직에 따라 적절한 파라미터를 결정합니다.
상세 레퍼런스는 `references/params-reference.md`를 참조합니다.

### Step 5: 출력 및 변형 제안 (Output)

출력 형식에 맞춰 출력하고, 2개의 변형 제안을 함께 제공합니다.

---

## 프롬프트 구조 공식

### 기본 공식

```
[Subject & Action], [Style/Medium], [Technical Details], [Lighting], [Composition/Angle], [Mood/Atmosphere], [Quality Boosters] --parameters
```

### 요소별 작성 규칙

#### Subject & Action (필수)
- 주어를 먼저, 동작/상태를 다음에 배치
- 구체적이고 명확하게 (20단어 이내 권장)
- "a", "an" 관사를 적절히 사용
- 예: "a fierce female warrior wielding a glowing sword"

#### Style/Medium (권장)

| 한국어 | 영어 키워드 |
|--------|-----------|
| 사실적/실사 | photorealistic, hyperrealistic |
| 수채화 | watercolor painting |
| 유화 | oil painting |
| 디지털 일러스트 | digital illustration |
| 애니/만화 | anime style, manga style |
| 픽셀아트 | pixel art, 16-bit, 32-bit |
| 컨셉아트 | concept art |
| 로우폴리 | low poly |
| 셀 셰이딩 | cel-shaded |

#### Lighting (권장)

| 상황 | 키워드 |
|------|--------|
| 따뜻한 자연광 | golden hour lighting, warm sunlight |
| 차가운 분위기 | blue hour, moonlight, cold tones |
| 드라마틱 | dramatic lighting, chiaroscuro, Rembrandt lighting |
| 네온/사이버 | neon glow, cyberpunk lighting |
| 스튜디오 | studio lighting, softbox, three-point lighting |
| 역광 | backlit, rim light, silhouette lighting |
| 볼류메트릭 | volumetric lighting, god rays |

#### Composition/Angle (선택)

| 한국어 | 영어 키워드 |
|--------|-----------|
| 클로즈업 | close-up shot |
| 전신샷 | full body shot |
| 상반신 | upper body, bust shot |
| 조감도 | bird's eye view |
| 저앵글 | low angle shot |
| 아이소메트릭 | isometric view |
| 정면 | front view |
| 3/4 뷰 | three-quarter view |

#### Mood/Atmosphere (선택)

| 한국어 | 영어 키워드 |
|--------|-----------|
| 몽환적 | dreamy, ethereal, surreal |
| 역동적 | dynamic, energetic, action-packed |
| 고요한 | serene, peaceful, tranquil |
| 웅장한 | epic, majestic, grandiose |
| 아기자기한 | whimsical, cute, charming |
| 신비로운 | mystical, mysterious, enigmatic |
| 음울한 | gloomy, somber, brooding |

(상세 매핑은 `references/korean-english-mapping.md` 참조)

#### Quality Boosters (2-3개만 선택)
- `ultra-detailed, intricate details` - 디테일 강조
- `sharp focus, high resolution` - 선명도
- `masterpiece, best quality` - 품질 향상
- `award-winning, professional` - 전문적 느낌

---

## 카테고리별 생성 전략

### 캐릭터 디자인

**공식:**
```
[character description], [pose/action], [outfit/equipment], [art style], character design, [background], [lighting], [mood] --ar 2:3 --stylize 200
```

**원칙:**
- 시각적 특징 구체적으로 (헤어, 눈 색상, 체형, 의상)
- 포즈 명시 (standing, dynamic action pose, idle stance)
- 게임용: `character design, concept art` 추가
- 배경 집중: `simple background, white background`
- 여러 뷰: `character turnaround, multiple views, front and back view`

### 환경/배경 디자인

**공식:**
```
[environment description], [time of day], [weather], [art style], [composition], [lighting], environment concept art --ar 16:9 --stylize 300
```

**원칙:**
- 스케일감 전달 (vast, intimate, towering)
- 시간대/날씨로 분위기 설정
- 원근감 구도 (wide angle, panoramic)
- 게임용: `game environment, level design` 추가

### 아이템/오브젝트 디자인

**공식:**
```
[item description], [material/texture], [art style], [background], game item design, [lighting] --ar 1:1 --stylize 150
```

**원칙:**
- 재질감 상세 묘사 (metallic, wooden, crystalline)
- 아이콘용: `game icon, flat design, isolated on dark background`
- 스프라이트용: `sprite, isolated, white background, no shadow`
- 세트: `item set, collection, matching style`

### UI/아이콘 디자인

**공식:**
```
[icon/UI description], [design style], game UI design, [color scheme], [background] --ar 1:1 --stylize 50
```

**원칙:**
- 미드저니는 UI에 한계가 있으므로 참고/영감용으로 활용
- 낮은 stylize 값 (프롬프트 충실도 우선)
- 명확한 색상 팔레트 지정

### 포토리얼리스틱

**공식:**
```
[subject], [camera/lens spec], [lighting setup], [composition], photorealistic, [quality] --ar 3:2 --style raw --stylize 100
```

**원칙:**
- `--style raw` 사용 (미드저니 기본 미화 최소화)
- 카메라/렌즈 스펙 명시 (85mm f/1.4, shot on Hasselblad)
- 낮은 stylize 값

### 일러스트레이션

**공식:**
```
[subject], [illustration style], [color palette], [composition], [mood], illustration --ar 3:4 --stylize 400
```

**원칙:**
- 스타일 구체적으로 (watercolor, ink wash, gouache)
- 색상 팔레트 지정 (warm earth tones, pastel colors)
- 높은 stylize 값으로 미적 감각 활용

### 3D 렌더

**공식:**
```
[subject], 3D render, [renderer], [material/shader], [lighting], [composition] --ar 1:1 --stylize 200
```

**원칙:**
- 렌더러 명시 (octane render, blender, unreal engine 5)
- 셰이더/머티리얼 지정 (subsurface scattering, PBR materials)
- 클레이 렌더: `clay render, matte white material, soft studio lighting`

### 애니메이션 (Niji 7)

**공식:**
```
[subject], [anime/manga style], [color palette], [composition], [mood] --niji 7 --ar 2:3 --stylize 200
```

**원칙:**
- `--niji 7` 파라미터로 Niji 7 모델 활성화 (2026년 1월 출시)
- 동양 일러스트/애니메이션 미학에 특화된 코히어런시
- **제한사항**: `--cref` (Character Reference)와 `--oref` (Omni Reference) 미지원
- `--sref` (Style Reference)는 사용 가능

---

## 한국어 → 영어 변환 핵심 규칙

### 원칙
1. **직역 금지**: 뉘앙스를 미드저니 키워드로 의역
2. **기술 용어 영어 통일**: 미드저니에서 검증된 키워드 사용
3. **감성 표현 매핑**: 한국어 형용사를 미드저니 키워드로 변환
4. **중복 회피**: 비슷한 의미의 키워드 반복 금지

### 변환 예시

| 한국어 | 잘못된 직역 | 올바른 미드저니 키워드 |
|--------|-----------|---------------------|
| 아기자기한 | baby-like | whimsical, cute, charming |
| 우아한 | beautiful | elegant, graceful, refined |
| 신비로운 | mysterious | mystical, ethereal, otherworldly |
| 웅장한 | big and grand | epic, majestic, awe-inspiring |
| 몽환적인 | dream-like | dreamy, ethereal, surreal |
| 포근한 | warm | cozy, warm, snug, comforting |
| 세련된 | refined | sleek, sophisticated, polished |
| 투박한 | rough | rugged, raw, rustic |
| 소름끼치는 | scary | eerie, haunting, ominous |

### 게임 용어 변환

| 한국어 | 미드저니 키워드 |
|--------|---------------|
| 보스몹 | menacing boss creature, imposing monster |
| 잡몹 | common enemy creature, minion |
| 탱커 | heavily armored warrior, bulky tank character |
| 힐러 | ethereal healer, light magic caster |
| 마법사 | arcane mage, spellcaster |
| 궁수 | ranger, archer, marksman |
| 던전 | dark dungeon interior, underground labyrinth |
| 필드/맵 | open world landscape, game level terrain |

(상세 매핑은 `references/korean-english-mapping.md` 참조)

---

## 파라미터 추천 로직

### 종횡비 (--ar)

| 용도 | 추천 비율 |
|------|----------|
| 캐릭터 전신 | 2:3 또는 9:16 |
| 초상화/상반신 | 3:4 또는 4:5 |
| 풍경/환경 | 16:9 |
| 아이콘/아이템 | 1:1 |
| 배너/헤더 | 21:9 |
| 모바일 배경 | 9:16 또는 6:11 |
| 인스타그램 | 4:5 (세로) 또는 5:4 (가로) |
| 스프라이트 시트 | 16:9 또는 2:1 |

### Stylize (--s)

| 값 | 성격 | 사용 시점 |
|----|------|----------|
| 0-50 | 프롬프트 충실도 최대 | UI, 아이콘, 기술 도면 |
| 50-150 | 균형 | 포토리얼, 제품 사진 |
| 150-300 | 미적 강화 | 컨셉아트, 캐릭터 |
| 300-500 | 강한 미화 | 일러스트, 환경 |
| 500-1000 | 미드저니 미학 지배 | 추상, 실험적 아트 |

### Style (--style)

| 옵션 | 사용 시점 |
|------|----------|
| (기본) | 대부분의 경우 |
| raw | 포토리얼, 프롬프트 정확 재현 |
| expressive | 예술적 표현력 극대화 |
| scenic | 풍경, 환경 디자인 특화 |

### Chaos (--chaos)

| 값 | 사용 시점 |
|----|----------|
| 0 (기본) | 안정적, 일관된 결과 |
| 10-30 | 영감 탐색 |
| 30-60 | 다양한 해석 탐색 |
| 60-100 | 실험적 아트 |

### Weird (--weird)

| 값 | 사용 시점 |
|----|----------|
| 0 (기본) | 일반 결과 |
| 100-500 | 약간의 독창성 |
| 500-1500 | 초현실적 분위기 |
| 1500-3000 | 극도로 실험적 |

### 카테고리별 기본 프리셋

| 카테고리 | 기본 파라미터 |
|----------|-------------|
| 캐릭터 디자인 | `--ar 2:3 --stylize 200` |
| 환경/배경 | `--ar 16:9 --stylize 300 --style scenic` |
| 게임 아이템 | `--ar 1:1 --stylize 150` |
| UI/아이콘 | `--ar 1:1 --stylize 50` |
| 포토리얼 | `--ar 3:2 --style raw --stylize 100` |
| 일러스트 | `--ar 3:4 --stylize 400` |
| 3D 렌더 | `--ar 1:1 --stylize 200` |
| 애니메이션 | `--niji 7 --ar 2:3 --stylize 200` |
| 캐릭터 시트 | `--ar 16:9 --stylize 150` |

---

## 출력 형식

모든 프롬프트 생성 결과는 다음 형식으로 출력합니다:

```
## 미드저니 프롬프트

**카테고리:** [결정된 카테고리]

### 메인 프롬프트
`/imagine prompt: [영어 프롬프트 전체] --파라미터들`

### 프롬프트 해설
| 요소 | 내용 | 설명 |
|------|------|------|
| 주제 | [영어] | [한국어 설명] |
| 스타일 | [영어] | [한국어 설명] |
| 조명 | [영어] | [한국어 설명] |
| 구도 | [영어] | [한국어 설명] |
| 분위기 | [영어] | [한국어 설명] |
| 파라미터 | [파라미터] | [선택 이유] |

### 변형 제안

**변형 1 - [변형 설명]:**
`/imagine prompt: [변형 프롬프트] --파라미터들`

**변형 2 - [변형 설명]:**
`/imagine prompt: [변형 프롬프트] --파라미터들`
```

### 출력 규칙
1. 프롬프트는 항상 코드 블록 안에 `/imagine prompt:` 접두사와 함께 표시
2. 프롬프트 해설로 각 요소의 역할을 한국어로 설명
3. 변형 제안은 최소 2개 (스타일 변형, 분위기 변형 등)
4. 사용자가 "간단하게"를 요청하면 해설 생략, 프롬프트만 출력
5. 레퍼런스 이미지 사용 시: **웹 UI 설정 안내**를 함께 출력 (아래 형식)
6. Editor 모드(인페인팅/리텍스처) 요청 시: **Editor 전용 출력 형식** 사용 (Editor 모드 프롬프트 가이드 섹션 참조)

### 이미지 레퍼런스 사용 시 추가 출력

레퍼런스 이미지가 포함된 요청에는 프롬프트와 함께 다음을 출력합니다:

```
### 웹 UI 설정 안내
1. **Create 페이지**에서 Imagine 바의 이미지 아이콘 클릭
2. 캐릭터 이미지 업로드
3. [구체적인 섹션 드롭 안내 - 상황에 따라 다름]
4. 프롬프트 입력 후 생성

> 주의: Editor(Edit 버튼) 모드에서는 포즈 변경이 불가합니다. 반드시 Create 페이지를 사용하세요.
```

---

## 이미지 레퍼런스 가이드

사용자가 기존 이미지를 참조하여 변형(포즈 변경, 장면 변경 등)을 요청할 때 이 섹션을 따릅니다.
상세 레퍼런스는 `references/image-reference-guide.md`를 참조합니다.

### 핵심 판단: 어떤 참조 방식을 사용할 것인가

| 사용자 요청 | 추천 방식 | 웹 UI 설정 |
|------------|----------|-----------|
| "이 캐릭터로 다른 포즈" | --cref + --sref (Shift+클릭) | Character Ref + Style Ref |
| "이 캐릭터를 정확히 이 포즈로" | 포즈 사진(Image Prompt) + --cref | Image Prompt + Character Ref |
| "이 캐릭터 의상만 변경" | --cref (--cw 0) + --sref | Character Ref(cw 0) + Style Ref |
| "이 그림체로 다른 캐릭터" | --sref만 사용 | Style Ref만 |
| "이 이미지 분위기 그대로 재현" | Image Prompt | Image Prompt |

### 포즈 변경 시 프롬프트 작성 원칙

1. **신체 동작을 구체적으로 기술**: `lunging forward`, `arm fully extended`, `back leg planted` 등 관절/무게중심 묘사
2. **불 이펙트 등 부가 요소는 최소화**: 토큰을 동작 묘사에 집중 투자
3. **캐릭터 핵심 외모를 텍스트로도 명시**: 이중 보험 (머리색, 눈색, 의상 등)
4. **--stylize 낮게**: 50~150으로 설정해야 --cref/--sref 효과가 강해짐

### 주의사항

- **Editor(Edit 버튼) 모드에서는 포즈 변경 불가** → 반드시 Create 페이지 사용
- **Image Prompt에 넣으면 포즈 고정됨** → Character Reference에 넣어야 포즈 변경 가능
- **--cref만 쓰면 그림체 달라짐** → --sref를 같은 이미지로 함께 사용 (Shift+클릭)
- **Editor에서 부분 수정(인페인팅/리텍스처)이 필요하면** → 아래 "Editor 모드 프롬프트 가이드" 섹션 참조

---

## Editor 모드 프롬프트 가이드

기존 이미지를 **부분 수정(Inpaint)** 하거나 **스타일 변환(Retexture)** 할 때 사용하는 Editor 전용 프롬프트 생성 가이드.
Editor는 `--ar`, `--stylize`, `--cref`, `--sref`, `--oref` 등 **파라미터를 사용할 수 없으며**, 텍스트 프롬프트만으로 결과를 제어한다.
상세 도구 설명과 실전 시나리오는 `references/editor-mode-guide.md`를 참조한다.

### Editor vs Create 판단 기준

| 하고 싶은 것 | 사용할 모드 |
|------------|-----------|
| 배경 교체, 소품 추가/제거, 색상 변경 | **Editor** (Erase/Inpaint) |
| 전체 스타일/질감/분위기 변환 | **Editor** (Retexture) |
| 여러 이미지 합성 | **Editor** (Layers) |
| 이미지 확장 (Outpainting) | **Editor** (Move/Resize) |
| 포즈 변경, 새 구도, 새 캐릭터 생성 | **Create 페이지** |
| 파라미터(--ar, --stylize 등) 사용 | **Create 페이지** |

### Editor 프롬프트 워크플로우

**Step 1: 작업 유형 분류**

| 사용자 요청 | 작업 유형 | Editor 도구 |
|------------|----------|------------|
| "배경을 바다로 바꿔줘" | Erase/Inpaint | Erase 또는 Smart Select |
| "고양이를 추가해줘" | Erase/Inpaint | Erase (빈 영역) |
| "무기를 제거해줘" | Erase/Inpaint | Erase (해당 부분) |
| "전체적으로 수채화 느낌으로" | Retexture | Retexture |
| "색감을 가을 느낌으로" | Retexture | Retexture |

**Step 2: Editor 전용 프롬프트 조립**

**Erase/Inpaint 공식:**
```
[마스킹 영역에 채울 구체적 묘사], [스타일/질감 힌트], [조명 일관성], [분위기]
```

원칙:
- **30단어 이내** 권장
- 마스킹 영역에 나타날 내용**만** 묘사 (전체 이미지 재묘사 불필요)
- 원본 이미지와의 스타일/조명 일관성 키워드 포함
- 포즈/구도 변경 시도 금지 (작동하지 않음)

**Retexture 공식:**
```
[새 스타일/매체], [색상 팔레트], [질감/텍스처], [분위기/톤]
```

원칙:
- **50단어 이내** 권장
- 구조/구도 묘사 불필요 (자동 유지됨)
- 스타일, 질감, 색감, 분위기에 집중
- 구체적인 미술 매체/화풍 명시가 효과적

**Step 3: Editor 전용 출력 형식으로 출력**

### Editor용 출력 형식

```
## 미드저니 Editor 프롬프트

**작업 유형:** [Erase/Inpaint | Retexture | Layers]
**Editor 도구:** [사용할 도구]

### 메인 프롬프트
`[영어 프롬프트 - 파라미터 없음]`

### 프롬프트 해설
| 요소 | 내용 | 설명 |
|------|------|------|
| 대상 | [영어] | [한국어 설명] |
| 스타일 | [영어] | [한국어 설명] |
| 분위기 | [영어] | [한국어 설명] |

### Editor 조작 가이드
1. [도구 선택 안내]
2. [마스킹/브러시 범위 안내]
3. 위 프롬프트 입력 후 Submit

### 변형 제안
**변형 1 - [변형 설명]:**
`[변형 프롬프트]`

**변형 2 - [변형 설명]:**
`[변형 프롬프트]`
```

### Editor 출력 규칙
1. `/imagine prompt:` 접두사 **생략** (Editor에서는 사용하지 않음)
2. 파라미터(`--ar`, `--stylize` 등) **포함하지 않음**
3. **Editor 조작 가이드** 섹션 필수 (어떤 도구를 어떻게 사용할지)
4. 변형 제안도 파라미터 없이 텍스트만
5. 포즈 변경이 필요한 요청에는 Create 페이지 + `--cref` 사용을 안내

### Editor 제한사항
- 포즈 변경 **불가** (마스킹 영역만 재생성)
- `--ar`, `--stylize`, `--cref`, `--sref`, `--oref` 등 파라미터 **미지원**
- 텍스트 프롬프트**만** 사용 가능
- 편집 결과는 **Upscale하지 않으면** 갤러리에 저장되지 않음

---

## 품질 체크리스트

프롬프트 생성 후 반드시 검증:

- [ ] **구체성**: 주제가 모호하지 않은가? ("a character" X → "a young elven archer with auburn hair" O)
- [ ] **구조 순서**: Subject → Style → Technical → Lighting → Composition → Mood → Quality
- [ ] **중복 제거**: 동의어 반복 없는가? ("beautiful, pretty, gorgeous" 전부 사용 X)
- [ ] **길이 적정**: 150토큰 이내인가? (약 40~80단어, V7은 짧은 프롬프트 권장)
- [ ] **파라미터 적합**: 용도에 맞는 ar, stylize, style이 설정되었는가?
- [ ] **직역 없음**: 한국어를 직역한 어색한 표현이 없는가?
- [ ] **키워드 효과성**: 미드저니가 잘 인식하는 검증된 키워드를 사용했는가?

---

## V7 신기능 활용 팁

### Draft Mode
- **10x 빠른 생성**, GPU 비용 50% 절감
- 아이디어 빠른 탐색에 최적: Draft → 마음에 드는 결과 → Fast/Turbo로 고품질 최종 생성
- 대화식 수정 가능 ("고양이를 부엉이로 바꿔", "밤으로 바꿔")

### 텍스트 렌더링 (V7 신기능)
- 이미지 내 텍스트 삽입 **95%+ 정확도**
- 사용법: 프롬프트에 큰따옴표로 텍스트 감싸기 → `"HELLO WORLD"`
- 추가 키워드: `legible text`, `clear typography`
- 텍스트는 **1~3단어** 이내가 최적

### Personalization (--p)
- V7에서 **기본 활성화** — 사용자의 미적 선호도를 학습하여 결과에 반영
- 5분 이미지 평가로 빠르게 프로필 생성 가능

### Style Version (--sv)
- `--sref`와 함께 사용하여 스타일 참조 해석 방식 제어
- `--sv 1`~`--sv 6` (기본: 6) — 낮을수록 추상적, 높을수록 충실한 스타일 재현

---

## 레퍼런스 파일 안내

상세 정보가 필요할 때 다음 파일을 참조합니다:

| 파일 | 참조 시점 |
|------|----------|
| `references/styles-photorealistic.md` | 실사 이미지 요청 시 |
| `references/styles-illustration.md` | 그림체 이미지 요청 시 |
| `references/styles-3d-render.md` | 3D 스타일 요청 시 |
| `references/styles-game-art.md` | 게임 에셋 요청 시 |
| `references/params-reference.md` | 파라미터 상세 조정 시 |
| `references/korean-english-mapping.md` | 한국어 변환 어려울 때 |
| `references/templates-gallery.md` | 참고 예시 필요 시 |
| `references/image-reference-guide.md` | 기존 이미지 참조/변형 요청 시 |
| `references/editor-mode-guide.md` | Editor 모드(인페인팅/리텍스처) 상세 가이드 |
