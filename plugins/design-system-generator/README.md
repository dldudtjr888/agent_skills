# Design System Generator

Tailwind CSS 토큰 변환 및 디자인 시스템 접근성 검증 플러그인.

## 함께 사용할 플러그인

이 플러그인은 아래 플러그인들과 함께 사용하세요:

- [frontend-design](https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design) - Anthropic 공식 디자인 원칙
- [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) - 컬러/타이포그래피 데이터 (16.9k ⭐)

## Features

- **Tailwind CSS 토큰** - v4 @theme 디렉티브, CSS 변수, Style Dictionary 형식
- **접근성 검증** - WCAG 2.1 컬러 대비율 자동 체크
- **다크 모드 검증** - 라이트/다크 모드 토큰 매핑 검증

## Installation

```bash
/plugin install design-system-generator@hibye-plugins
```

## Skills

### /tailwind-tokens

디자인 토큰을 Tailwind CSS 형식으로 변환합니다.

```
/tailwind-tokens 현재 디자인 토큰을 Tailwind v4 @theme 형식으로 변환
```

## Agent

### design-system-reviewer

디자인 시스템의 일관성과 접근성을 검증합니다.

- WCAG 컬러 대비율 체크
- 토큰 네이밍 일관성
- 누락된 토큰 감지
- 다크 모드 매핑 검증

## Output Formats

- **Tailwind v4** - `@theme` 디렉티브
- **Tailwind v3** - `tailwind.config.ts`
- **CSS Variables** - `globals.css`
- **Style Dictionary** - JSON 토큰

## Example Output

```css
@theme {
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-900: #1e3a8a;

  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;

  --radius-md: 0.375rem;
}
```

## License

MIT
