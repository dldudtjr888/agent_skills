---
name: tailwind-patterns
description: Tailwind CSS 패턴, 구성 전략, 커스텀 설정, 확장 가능한 스타일링 모범 사례.
version: 1.0.0
category: styling
user-invocable: true
triggers:
  keywords: [tailwind, css, styling, className, cn, cva, variants, responsive, dark mode]
  intentPatterns:
    - "(tailwind|스타일|CSS).*(패턴|구성|설정)"
    - "(style|class|variant).*(pattern|organize|config)"
---

# Tailwind CSS 패턴

React 애플리케이션에서 Tailwind CSS 사용 모범 사례. 구성, 변형, 반응형 디자인, 고급 패턴을 다룹니다.

## 필수 설정

### cn()으로 클래스 병합

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### 사용법

```tsx
import { cn } from '@/lib/utils'

function Button({ className, disabled, ...props }) {
  return (
    <button
      className={cn(
        'px-4 py-2 rounded-lg font-medium',
        'bg-blue-500 text-white',
        'hover:bg-blue-600 active:bg-blue-700',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className // 오버라이드 허용
      )}
      disabled={disabled}
      {...props}
    />
  )
}
```

## CVA로 컴포넌트 변형

### 기본 변형

```typescript
// components/button.tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  // 기본 스타일
  'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}
```

### 복합 변형

```typescript
const alertVariants = cva(
  'relative w-full rounded-lg border p-4',
  {
    variants: {
      variant: {
        default: 'bg-background text-foreground',
        destructive: 'border-destructive/50 text-destructive dark:border-destructive',
        warning: 'border-yellow-500/50 text-yellow-700 dark:text-yellow-500',
        success: 'border-green-500/50 text-green-700 dark:text-green-500',
      },
      withIcon: {
        true: 'pl-12',
        false: '',
      },
    },
    compoundVariants: [
      {
        variant: 'destructive',
        withIcon: true,
        className: '[&>svg]:text-destructive',
      },
      {
        variant: 'warning',
        withIcon: true,
        className: '[&>svg]:text-yellow-500',
      },
      {
        variant: 'success',
        withIcon: true,
        className: '[&>svg]:text-green-500',
      },
    ],
    defaultVariants: {
      variant: 'default',
      withIcon: false,
    },
  }
)
```

## Tailwind 설정 모범 사례

### 디자인 토큰

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // CSS 변수를 사용한 시맨틱 색상
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    require('@tailwindcss/typography'),
  ],
}

export default config
```

### CSS 변수

```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

## 반응형 디자인 패턴

### 모바일 우선 접근

```tsx
// 항상 모바일부터 시작, 큰 화면용 브레이크포인트 추가
<div className="
  p-4
  md:p-6
  lg:p-8
">
  <h1 className="
    text-xl
    md:text-2xl
    lg:text-3xl
  ">
    반응형 제목
  </h1>

  <div className="
    grid
    grid-cols-1
    md:grid-cols-2
    lg:grid-cols-3
    gap-4
  ">
    {/* 카드들 */}
  </div>
</div>
```

### 컨테이너 쿼리

```tsx
// Tailwind 3.4+ 컨테이너 쿼리 지원
<div className="@container">
  <div className="
    @sm:flex
    @sm:flex-row
    @lg:grid
    @lg:grid-cols-3
  ">
    {/* 뷰포트가 아닌 컨테이너에 반응 */}
  </div>
</div>
```

## 다크 모드

### 클래스 기반 다크 모드

```tsx
// next-themes 설정
import { ThemeProvider } from 'next-themes'

export function Providers({ children }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      {children}
    </ThemeProvider>
  )
}

// 다크 모드가 있는 컴포넌트
<div className="
  bg-white dark:bg-gray-900
  text-gray-900 dark:text-gray-100
  border-gray-200 dark:border-gray-700
">
  콘텐츠
</div>
```

### 테마 토글

```tsx
import { useTheme } from 'next-themes'
import { Moon, Sun } from 'lucide-react'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-lg hover:bg-accent"
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">테마 전환</span>
    </button>
  )
}
```

## 일반 패턴

### 카드 컴포넌트

```tsx
const Card = ({ className, ...props }) => (
  <div
    className={cn(
      'rounded-lg border bg-card text-card-foreground shadow-sm',
      className
    )}
    {...props}
  />
)

const CardHeader = ({ className, ...props }) => (
  <div
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
)

const CardTitle = ({ className, ...props }) => (
  <h3
    className={cn('text-2xl font-semibold leading-none tracking-tight', className)}
    {...props}
  />
)

const CardContent = ({ className, ...props }) => (
  <div className={cn('p-6 pt-0', className)} {...props} />
)
```

### 라벨이 있는 입력

```tsx
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
          'ring-offset-background',
          'file:border-0 file:bg-transparent file:text-sm file:font-medium',
          'placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
```

### 스켈레톤 로딩

```tsx
function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
      {...props}
    />
  )
}

// 사용
function CardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-24 w-full" />
      </CardContent>
    </Card>
  )
}
```

## 안티패턴

### 1. 인라인 스타일 객체

```tsx
// 나쁨
<div style={{ padding: '16px', margin: '8px' }}>

// 좋음
<div className="p-4 m-2">
```

### 2. 임의 값 남용

```tsx
// 나쁨 - 너무 많은 임의 값
<div className="w-[347px] h-[89px] p-[13px] m-[7px]">

// 좋음 - 디자인 토큰 사용
<div className="w-80 h-24 p-3 m-2">
```

### 3. 중복 클래스 그룹

```tsx
// 나쁨
<div className="p-4 p-6 text-sm text-lg">

// 좋음 - cn()이 처리
<div className={cn('p-4', isLarge && 'p-6', 'text-sm', isLarge && 'text-lg')}>
```

### 4. 길고 읽기 어려운 클래스 문자열

```tsx
// 나쁨
<div className="flex items-center justify-between p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-200 dark:border-gray-700">

// 좋음 - 논리적 그룹으로 분리
<div className={cn(
  // 레이아웃
  'flex items-center justify-between p-4',
  // 색상
  'bg-white dark:bg-gray-900',
  // 형태
  'rounded-lg',
  // 그림자 & 트랜지션
  'shadow-md hover:shadow-lg transition-shadow duration-200',
  // 테두리
  'border border-gray-200 dark:border-gray-700'
)}>
```

## 성능 팁

1. **PurgeCSS 사용** (Tailwind 내장) - `content` 경로가 올바른지 확인
2. **동적 클래스 생성 피하기** - Tailwind가 `bg-${color}-500` 퍼지 불가
3. **`@apply` 절제** - 진짜 반복 패턴에만
4. **CSS 변수 활용** - 런타임 테마 전환용
