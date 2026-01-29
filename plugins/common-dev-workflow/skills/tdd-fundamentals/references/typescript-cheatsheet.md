# TypeScript (Vitest/Jest) Cheatsheet

## Vitest 기본 명령어

```bash
# 전체 테스트
npx vitest run

# 워치 모드
npx vitest

# 특정 파일
npx vitest run Button.test.tsx

# 키워드 필터
npx vitest run -t "user"

# 커버리지
npx vitest run --coverage

# UI 모드
npx vitest --ui
```

## Jest 기본 명령어

```bash
# 전체 테스트
npm test

# 워치 모드
npm test -- --watch

# 특정 파일
npm test -- Button.test.tsx

# 키워드 필터
npm test -- -t "user"

# 커버리지
npm test -- --coverage
```

## 기본 테스트 구조

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('Calculator', () => {
  let calc: Calculator

  beforeEach(() => {
    calc = new Calculator()
  })

  it('adds two numbers', () => {
    expect(calc.add(2, 3)).toBe(5)
  })

  it('throws on division by zero', () => {
    expect(() => calc.divide(10, 0)).toThrow()
  })
})
```

## Assertions

```typescript
// 동등성
expect(value).toBe(5)           // 정확히 같음 (===)
expect(obj).toEqual({ a: 1 })   // 깊은 비교

// Truthiness
expect(value).toBeTruthy()
expect(value).toBeFalsy()
expect(value).toBeNull()
expect(value).toBeUndefined()
expect(value).toBeDefined()

// 숫자
expect(value).toBeGreaterThan(3)
expect(value).toBeLessThan(10)
expect(value).toBeCloseTo(0.3, 5)

// 문자열
expect(str).toMatch(/pattern/)
expect(str).toContain('substring')

// 배열
expect(arr).toContain(item)
expect(arr).toHaveLength(3)

// 예외
expect(() => fn()).toThrow()
expect(() => fn()).toThrow('error message')
```

## Mock

```typescript
import { vi } from 'vitest'

// 함수 모킹
const mockFn = vi.fn()
mockFn.mockReturnValue(42)
mockFn.mockResolvedValue({ data: 'test' })

// 모듈 모킹
vi.mock('./api', () => ({
  fetchData: vi.fn(() => Promise.resolve({ data: 'mocked' }))
}))

// 검증
expect(mockFn).toHaveBeenCalled()
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2')
expect(mockFn).toHaveBeenCalledTimes(2)
```

## Async 테스트

```typescript
it('fetches data', async () => {
  const result = await fetchData()
  expect(result).toBeDefined()
})

it('handles async error', async () => {
  await expect(asyncFn()).rejects.toThrow('error')
})
```

## Timer Mock

```typescript
import { vi, beforeEach, afterEach } from 'vitest'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

it('debounces calls', () => {
  const fn = vi.fn()
  const debounced = debounce(fn, 100)

  debounced()
  debounced()
  debounced()

  vi.advanceTimersByTime(100)

  expect(fn).toHaveBeenCalledTimes(1)
})
```

## React Testing Library

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

it('submits form', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn()

  render(<Form onSubmit={onSubmit} />)

  await user.type(screen.getByLabelText(/email/i), 'test@example.com')
  await user.click(screen.getByRole('button', { name: /submit/i }))

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith({ email: 'test@example.com' })
  })
})
```

## 쿼리 우선순위

```typescript
// 1순위: Role (접근성)
screen.getByRole('button', { name: /submit/i })

// 2순위: Label (폼)
screen.getByLabelText(/email/i)

// 3순위: Placeholder
screen.getByPlaceholderText('Search...')

// 4순위: Text
screen.getByText(/welcome/i)

// 최후의 수단
screen.getByTestId('custom-element')
```

## Hook 테스트

```typescript
import { renderHook, act } from '@testing-library/react'

it('increments counter', () => {
  const { result } = renderHook(() => useCounter())

  act(() => {
    result.current.increment()
  })

  expect(result.current.count).toBe(1)
})
```

## 설정 파일 (vitest.config.ts)

```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      thresholds: {
        lines: 80,
        branches: 80,
        functions: 80,
        statements: 80,
      },
    },
  },
})
```
