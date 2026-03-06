---
title: 3D 렌더 스타일 가이드
category: style
tags: 3d, render, octane, unreal, blender
---

# 3D 렌더 프롬프트 가이드

## 렌더러별 키워드

| 렌더러 | 키워드 | 특징/용도 |
|--------|--------|----------|
| Octane | octane render | 포토리얼 GPU 렌더, 깨끗한 결과 |
| Unreal | unreal engine 5, UE5 | 게임 엔진 리얼타임 렌더 |
| Blender | blender 3d, cycles render | 오픈소스, 범용 |
| Cinema 4D | cinema 4d render, C4D | 모션그래픽, 제품 |
| V-Ray | v-ray render | 건축 시각화 |
| KeyShot | keyshot render | 제품 디자인 |
| Arnold | arnold render | 영화/VFX |
| Redshift | redshift render | GPU 렌더, VFX |

## 머티리얼/셰이더

### 기본 머티리얼
- PBR materials, physically based rendering
- matte finish, matte surface
- glossy, high gloss finish
- metallic, brushed metal, chrome
- glass, transparent, refractive
- ceramic, porcelain
- rubber, soft touch

### 고급 셰이더
- subsurface scattering (피부/밀랍/젤리 투과광)
- iridescent, holographic (무지개빛)
- anisotropic (방향성 반사)
- frosted glass (반투명 유리)
- velvet shader (벨벳 질감)
- translucent (반투명)
- emission, self-illuminating (발광체)

### 텍스처
- procedural textures (절차적 텍스처)
- displacement mapping (변위 매핑)
- normal mapping (노멀 매핑)
- weathered, aged surface (풍화된 표면)
- pristine, factory new (깨끗한 신제품)

## 특수 3D 스타일

### 클레이/미니어처
- clay render, matte white material (클레이 렌더)
- miniature, tilt-shift effect (미니어처 효과)
- diorama, scale model (디오라마)
- stop motion style (스톱모션 느낌)

### 로우폴리/스타일라이즈드
- low poly, geometric, faceted (로우폴리)
- voxel art, minecraft style (복셀 아트)
- isometric 3D (아이소메트릭)
- stylized 3D, Pixar style (스타일라이즈드)
- cel-shaded 3D, toon shading (셀셰이딩)

### 기술적 스타일
- wireframe overlay (와이어프레임)
- cross-section, cutaway view (단면도)
- exploded view (분해도)
- x-ray view (투시도)
- blueprint style 3D (블루프린트)

### 볼류메트릭/대기
- volumetric fog, atmospheric haze (볼류메트릭 안개)
- god rays, light shafts (빛줄기)
- dust particles in light (빛 속 먼지 입자)
- underwater caustics (수중 코스틱)

## 조명 세팅

### 스튜디오
- studio lighting (스튜디오 조명)
- HDRI environment (HDRI 환경광)
- softbox lighting (소프트박스)
- spotlight, focused light (스포트라이트)
- area light, large diffused (면조명)

### 배경
- gradient background (그라디언트 배경)
- infinite floor, cyclorama (인피니트 플로어)
- dark background, black background
- environment backdrop, outdoor HDRI
- abstract background

### 특수 조명
- neon lighting, cyberpunk glow
- candlelight, warm point light
- bioluminescent, organic glow
- rim light, edge light (가장자리 조명)
- colored lighting, gel lights (컬러 조명)

## 카메라/구도

- depth of field, shallow DOF (피사계 심도)
- bokeh (보케)
- product shot, hero shot (제품 메인 샷)
- turntable view (턴테이블 뷰)
- eye level, worm's eye, bird's eye
- Dutch angle (더치 앵글)
- over the shoulder (오버숄더)

## 예시 프롬프트

### 스타일라이즈드 캐릭터
```
a cute robot companion character, Pixar-style 3D render, soft rounded forms, metallic and matte materials, subsurface scattering on translucent elements, studio lighting with warm rim light, clean white background, octane render, highly detailed --ar 1:1 --stylize 200
```

### 클레이 렌더
```
a medieval fantasy castle, clay render style, matte white material, soft shadows, clean studio lighting from above, miniature diorama feel, no textures only form, architectural model, subtle ambient occlusion --ar 16:9 --stylize 150
```

### 제품 시각화
```
futuristic gaming headset floating in mid-air, matte black with RGB lighting accents, sleek aerodynamic design, studio three-point lighting, dark gradient background, octane render, sharp reflections, product visualization --ar 4:3 --stylize 150
```

### 아이소메트릭 디오라마
```
isometric fantasy tavern interior, cozy wooden interior with fireplace, small tables and barrels, warm candlelight glow, stylized 3D render, low poly with smooth shading, game art style, charming miniature world --ar 1:1 --stylize 250
```

### 사이버펑크 환경
```
cyberpunk city street corner at night, neon holographic signs, wet reflective ground, volumetric fog and light rays, unreal engine 5 render, PBR materials, detailed weathered surfaces, cinematic composition --ar 21:9 --stylize 300
```
