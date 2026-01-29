---
name: tailwind-tokens
description: 디자인 토큰을 Tailwind CSS v4 @theme 형식으로 변환. CSS 변수, Style Dictionary 호환.
version: 1.0.0
category: design
user-invocable: true
triggers:
  keywords: [tailwind, tokens, 토큰, @theme, css variables, 변수, config]
  intentPatterns:
    - "(tailwind|테일윈드).*(토큰|token|설정|config)"
    - "(디자인|design).*(토큰|token).*(변환|convert|export)"
    - "@theme.*(생성|만들|설정)"
---

# Tailwind Tokens Generator

디자인 토큰을 Tailwind CSS v4 @theme 형식으로 변환합니다.

---

## 워크플로우

### Step 1: 입력 수집

사용자에게 다음 정보를 확인하세요:

```
필수:
- Primary 컬러 (예: #3B82F6)
- Tailwind 버전 (v3 또는 v4)
- 출력 경로 (기본: ./src/styles/)

선택:
- Secondary 컬러
- Accent 컬러
- 폰트 패밀리 (sans, mono)
- 다크 모드 여부
```

### Step 2: 프로젝트 분석

```
1. 기존 tailwind.config.ts 또는 tailwind.config.js 확인
2. 기존 globals.css 또는 app.css 확인
3. 사용 중인 Tailwind 버전 확인 (package.json)
4. 기존 CSS 변수 정의 확인
```

### Step 3: 토큰 생성

Primary 컬러에서 50-950 스케일 자동 생성:

```
입력: #3B82F6 (blue-500)

출력:
- 50:  밝기 +45%
- 100: 밝기 +40%
- 200: 밝기 +30%
- 300: 밝기 +20%
- 400: 밝기 +10%
- 500: 원본
- 600: 밝기 -10%
- 700: 밝기 -20%
- 800: 밝기 -30%
- 900: 밝기 -40%
- 950: 밝기 -45%
```

### Step 4: 파일 생성

출력 형식에 따라 파일 생성:

| Tailwind 버전 | 생성 파일 |
|--------------|----------|
| v4 | `app.css` (@theme 디렉티브) |
| v3 | `tailwind.config.ts` + `globals.css` |

---

## 출력 형식

### Tailwind v4 (@theme)

```css
/* app.css */
@import "tailwindcss";

@theme {
  /* Primary Color Scale */
  --color-primary-50: oklch(0.97 0.02 250);
  --color-primary-100: oklch(0.93 0.04 250);
  --color-primary-200: oklch(0.86 0.08 250);
  --color-primary-300: oklch(0.76 0.12 250);
  --color-primary-400: oklch(0.66 0.16 250);
  --color-primary-500: oklch(0.55 0.20 250);
  --color-primary-600: oklch(0.48 0.18 250);
  --color-primary-700: oklch(0.40 0.16 250);
  --color-primary-800: oklch(0.33 0.14 250);
  --color-primary-900: oklch(0.27 0.12 250);
  --color-primary-950: oklch(0.20 0.10 250);

  /* Typography */
  --font-family-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-family-mono: "JetBrains Mono", ui-monospace, monospace;

  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --radius-full: 9999px;
}

/* Semantic Tokens */
:root {
  --background: var(--color-primary-50);
  --foreground: var(--color-primary-950);
  --primary: var(--color-primary-500);
  --primary-foreground: white;
}

.dark {
  --background: var(--color-primary-950);
  --foreground: var(--color-primary-50);
  --primary: var(--color-primary-400);
}
```

### Tailwind v3 (config + CSS)

**tailwind.config.ts:**
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
}

export default config
```

**globals.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 210 40% 98%;
    --foreground: 222 84% 5%;
    --primary: 221 83% 53%;
    --primary-foreground: 210 40% 98%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222 84% 5%;
    --foreground: 210 40% 98%;
    --primary: 217 91% 60%;
    --primary-foreground: 222 47% 11%;
  }
}
```

---

## 실행 예시

**사용자 입력:**
```
/tailwind-tokens primary: #10B981, v4, 다크모드 포함
```

**실행 단계:**
1. 프로젝트에서 기존 Tailwind 설정 확인
2. #10B981에서 50-950 스케일 생성
3. @theme 디렉티브로 app.css 생성
4. 다크모드 시맨틱 토큰 추가
5. 파일 저장 후 경로 출력

**출력:**
```
✅ 생성 완료:
- src/styles/app.css (Tailwind v4 @theme)

사용법:
import './styles/app.css'
```

---

## 함께 사용할 플러그인

- [frontend-design](https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design) - 디자인 원칙
- [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) - 컬러/타이포그래피 추천

---

## 출처

- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs) - @theme 디렉티브
- [shadcn/ui](https://ui.shadcn.com/) - CSS 변수 구조
