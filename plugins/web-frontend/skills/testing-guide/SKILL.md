---
name: testing-guide
description: React/Next.js 프론트엔드 테스트 패턴. Provider 테스트, 접근성 쿼리, React Query 테스트 등 React 특화 패턴.
version: 1.0.0
category: testing
user-invocable: true
triggers:
  keywords: [react test, component test, testing library, provider test, react query test]
  intentPatterns:
    - "(React|컴포넌트).*(테스트|검증)"
    - "(component|react).*(test|testing)"
---

# React/Next.js 테스트 가이드

React/Next.js 애플리케이션의 프론트엔드 특화 테스트 패턴.

> **기본 설정 및 일반 패턴**: Vitest 설정, Testing Library 기본, MSW, Playwright E2E는
> `@common-dev-workflow/tdd-fundamentals` (modules/typescript-testing.md) 참조

## React 특화 패턴

### Provider Wrapper 설정

```typescript
// test/render.tsx
import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from 'next-themes'
import { SessionProvider } from 'next-auth/react'

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

interface WrapperProps {
  children: React.ReactNode
}

function AllProviders({ children }: WrapperProps) {
  const queryClient = createTestQueryClient()

  return (
    <SessionProvider session={null}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    </SessionProvider>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options })
}

export * from '@testing-library/react'
export { renderWithProviders as render }
```

### React Query 테스트

```typescript
import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useUserQuery, useUpdateUserMutation } from './useUser'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useUserQuery', () => {
  it('fetches user data', async () => {
    const { result } = renderHook(() => useUserQuery(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual({
      id: 1,
      name: 'Test User',
    })
  })

  it('handles error state', async () => {
    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.json({ error: 'Not found' }, { status: 404 })
      })
    )

    const { result } = renderHook(() => useUserQuery(999), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useUpdateUserMutation', () => {
  it('updates user and invalidates query', async () => {
    const queryClient = new QueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useUpdateUserMutation(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    })

    await result.current.mutateAsync({ id: 1, name: 'Updated' })

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['users'] })
  })
})
```

### Next.js Router 모킹

```typescript
// test/setup.ts
import { vi } from 'vitest'

// Next.js App Router 모킹
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  })),
  usePathname: vi.fn(() => '/'),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  useParams: vi.fn(() => ({})),
  redirect: vi.fn(),
  notFound: vi.fn(),
}))

// 테스트에서 사용
import { useRouter } from 'next/navigation'

it('navigates on submit', async () => {
  const mockPush = vi.fn()
  vi.mocked(useRouter).mockReturnValue({
    push: mockPush,
    // ... other methods
  })

  const user = userEvent.setup()
  render(<LoginForm />)

  await user.type(screen.getByLabelText(/email/i), 'test@example.com')
  await user.click(screen.getByRole('button', { name: /login/i }))

  await waitFor(() => {
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })
})
```

### Server Component 테스트

```typescript
// Server Component는 async 함수이므로 직접 호출
import { UserProfile } from './UserProfile'

describe('UserProfile (Server Component)', () => {
  it('renders user data', async () => {
    // Server Component를 직접 호출
    const component = await UserProfile({ userId: '1' })

    // 결과를 render
    render(component)

    expect(screen.getByText('Test User')).toBeInTheDocument()
  })
})
```

### Zustand Store 테스트

```typescript
import { renderHook, act } from '@testing-library/react'
import { useCounterStore } from './counterStore'

// 각 테스트 전에 store 리셋
beforeEach(() => {
  useCounterStore.setState({ count: 0 })
})

describe('useCounterStore', () => {
  it('increments count', () => {
    const { result } = renderHook(() => useCounterStore())

    act(() => {
      result.current.increment()
    })

    expect(result.current.count).toBe(1)
  })

  it('resets count', () => {
    const { result } = renderHook(() => useCounterStore())

    act(() => {
      result.current.increment()
      result.current.increment()
      result.current.reset()
    })

    expect(result.current.count).toBe(0)
  })
})
```

### Form Library 테스트 (React Hook Form + Zod)

```typescript
import { render, screen, waitFor } from '@/test/render'
import userEvent from '@testing-library/user-event'
import { ContactForm } from './ContactForm'

describe('ContactForm', () => {
  it('shows validation errors', async () => {
    const user = userEvent.setup()
    render(<ContactForm onSubmit={vi.fn()} />)

    // 빈 폼 제출
    await user.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/message must be at least 10 characters/i)).toBeInTheDocument()
    })
  })

  it('submits valid form', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(<ContactForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/message/i), 'This is a valid message')
    await user.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        message: 'This is a valid message',
      })
    })
  })
})
```

### 접근성 테스트

```typescript
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('Button accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(
      <Button onClick={() => {}}>Click me</Button>
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

### 쿼리 우선순위

```typescript
// 1순위: Role (스크린리더 접근)
screen.getByRole('button', { name: /submit/i })
screen.getByRole('textbox', { name: /email/i })
screen.getByRole('heading', { level: 1 })

// 2순위: Label (폼 접근성)
screen.getByLabelText(/password/i)

// 3순위: Placeholder (폼 입력)
screen.getByPlaceholderText('Search...')

// 4순위: Text (정적 콘텐츠)
screen.getByText(/welcome/i)

// 최후 수단 (피하기)
screen.getByTestId('custom-element')
```

## 테스트 실행

```bash
# 단위/통합 테스트
npm test
npm test -- --coverage
npm test -- --watch

# E2E (Playwright)
npx playwright test
npx playwright test --ui
npx playwright test --debug
```

## 관련 문서

- **일반 TypeScript 테스트**: `@common-dev-workflow/tdd-fundamentals`
- **TDD 원칙**: `@common-dev-workflow/tdd-fundamentals` (SKILL.md)
