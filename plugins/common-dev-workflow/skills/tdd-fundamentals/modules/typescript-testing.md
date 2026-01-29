# TypeScript Testing Guide

Vitest/Jest 기반 TypeScript 테스트 상세 가이드.

## Vitest 설정

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'e2e'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
      thresholds: {
        lines: 80,
        branches: 80,
        functions: 80,
        statements: 80,
      },
    },
    testTimeout: 10000,
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### setup.ts

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// 각 테스트 후 정리
afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

// 전역 모킹
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  })),
  usePathname: vi.fn(() => '/'),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}))

// ResizeObserver 모킹
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// matchMedia 모킹
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
```

## Jest 설정

### jest.config.js

```javascript
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.test.json',
    }],
  },
  testMatch: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/test/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}
```

## Testing Library 패턴

### 기본 컴포넌트 테스트

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)

    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(<Button onClick={handleClick}>Click</Button>)

    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)

    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

### 폼 테스트

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(<LoginForm onSubmit={onSubmit} />)

    // 입력
    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')

    // 제출
    await user.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })
  })

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup()

    render(<LoginForm onSubmit={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('shows error for invalid email format', async () => {
    const user = userEvent.setup()

    render(<LoginForm onSubmit={vi.fn()} />)

    await user.type(screen.getByLabelText(/email/i), 'invalid-email')
    await user.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })
  })
})
```

### 쿼리 우선순위

```typescript
// 1순위: Accessible roles (접근성)
screen.getByRole('button', { name: /submit/i })
screen.getByRole('textbox', { name: /email/i })
screen.getByRole('heading', { level: 1 })
screen.getByRole('link', { name: /home/i })
screen.getByRole('checkbox', { name: /agree/i })

// 2순위: Form labels
screen.getByLabelText(/password/i)
screen.getByPlaceholderText('Search...')

// 3순위: Text content
screen.getByText(/welcome back/i)
screen.getByAltText('Company Logo')
screen.getByTitle('Close')

// 최후의 수단 (접근성 개선 필요 시 사용)
screen.getByTestId('custom-element')
```

### Async 패턴

```typescript
import { render, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react'

// waitFor: 조건 충족 대기
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// waitForElementToBeRemoved: 요소 제거 대기
await waitForElementToBeRemoved(() => screen.queryByText('Loading...'))

// findBy: getBy + waitFor
const element = await screen.findByText('Async Content')

// 타임아웃 설정
await waitFor(
  () => expect(screen.getByText('Done')).toBeInTheDocument(),
  { timeout: 5000 }
)
```

## Hook 테스트

```typescript
import { renderHook, act } from '@testing-library/react'
import { useCounter } from './useCounter'

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useCounter())

    expect(result.current.count).toBe(0)
  })

  it('initializes with custom value', () => {
    const { result } = renderHook(() => useCounter(10))

    expect(result.current.count).toBe(10)
  })

  it('increments count', () => {
    const { result } = renderHook(() => useCounter())

    act(() => {
      result.current.increment()
    })

    expect(result.current.count).toBe(1)
  })

  it('decrements count', () => {
    const { result } = renderHook(() => useCounter(5))

    act(() => {
      result.current.decrement()
    })

    expect(result.current.count).toBe(4)
  })

  it('resets to initial value', () => {
    const { result } = renderHook(() => useCounter(10))

    act(() => {
      result.current.increment()
      result.current.increment()
      result.current.reset()
    })

    expect(result.current.count).toBe(10)
  })
})
```

### Wrapper로 Context 제공

```typescript
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useUser } from './useUser'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useUser', () => {
  it('fetches user data', async () => {
    const { result } = renderHook(() => useUser(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual({ id: 1, name: 'Test User' })
  })
})
```

## MSW (Mock Service Worker) 패턴

### 기본 설정

```typescript
// src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  // GET 요청
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'John' },
      { id: 2, name: 'Jane' },
    ])
  }),

  // GET with params
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: Number(params.id),
      name: 'User ' + params.id,
    })
  }),

  // POST 요청
  http.post('/api/users', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json(
      { id: 3, ...body },
      { status: 201 }
    )
  }),

  // 에러 응답
  http.get('/api/error', () => {
    return HttpResponse.json(
      { message: 'Internal Server Error' },
      { status: 500 }
    )
  }),
]
```

```typescript
// src/test/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

```typescript
// src/test/setup.ts
import { server } from './mocks/server'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### 테스트별 핸들러 오버라이드

```typescript
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'

describe('UserList', () => {
  it('shows users from API', async () => {
    render(<UserList />)

    expect(await screen.findByText('John')).toBeInTheDocument()
    expect(await screen.findByText('Jane')).toBeInTheDocument()
  })

  it('shows error message on API failure', async () => {
    // 이 테스트에서만 핸들러 오버라이드
    server.use(
      http.get('/api/users', () => {
        return HttpResponse.json(
          { message: 'Failed to fetch' },
          { status: 500 }
        )
      })
    )

    render(<UserList />)

    expect(await screen.findByText(/failed to fetch/i)).toBeInTheDocument()
  })

  it('shows empty state when no users', async () => {
    server.use(
      http.get('/api/users', () => {
        return HttpResponse.json([])
      })
    )

    render(<UserList />)

    expect(await screen.findByText(/no users found/i)).toBeInTheDocument()
  })
})
```

### 지연 및 네트워크 상태 시뮬레이션

```typescript
import { http, HttpResponse, delay } from 'msw'

// 지연된 응답
http.get('/api/slow', async () => {
  await delay(2000)
  return HttpResponse.json({ data: 'slow response' })
})

// 네트워크 에러
http.get('/api/network-error', () => {
  return HttpResponse.networkError('Failed to connect')
})

// 진행 중인 요청 테스트
it('shows loading state', async () => {
  server.use(
    http.get('/api/users', async () => {
      await delay('infinite')
      return HttpResponse.json([])
    })
  )

  render(<UserList />)

  expect(screen.getByText(/loading/i)).toBeInTheDocument()
})
```

## Mocking 패턴

### 모듈 모킹

```typescript
// 전체 모듈 모킹
vi.mock('./api', () => ({
  fetchUsers: vi.fn(() => Promise.resolve([{ id: 1, name: 'Test' }])),
  createUser: vi.fn(),
}))

// 부분 모킹 (나머지는 실제 구현 사용)
vi.mock('./utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./utils')>()
  return {
    ...actual,
    formatDate: vi.fn(() => '2024-01-01'),
  }
})

// 테스트에서 모킹된 함수 사용
import { fetchUsers } from './api'

it('uses mocked fetch', async () => {
  vi.mocked(fetchUsers).mockResolvedValueOnce([{ id: 2, name: 'Custom' }])

  // ...
})
```

### 타이머 모킹

```typescript
import { vi, beforeEach, afterEach } from 'vitest'

describe('Debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('debounces rapid calls', () => {
    const fn = vi.fn()
    const debounced = debounce(fn, 300)

    debounced()
    debounced()
    debounced()

    // 아직 호출되지 않음
    expect(fn).not.toHaveBeenCalled()

    // 시간 진행
    vi.advanceTimersByTime(300)

    // 1번만 호출됨
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('handles setTimeout', () => {
    const callback = vi.fn()

    setTimeout(callback, 1000)

    vi.advanceTimersByTime(500)
    expect(callback).not.toHaveBeenCalled()

    vi.advanceTimersByTime(500)
    expect(callback).toHaveBeenCalledTimes(1)
  })
})
```

### Date 모킹

```typescript
beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2024-01-15T10:00:00'))
})

afterEach(() => {
  vi.useRealTimers()
})

it('uses mocked date', () => {
  expect(new Date().toISOString()).toBe('2024-01-15T10:00:00.000Z')
})
```

## Playwright E2E 테스트

### 기본 설정

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### Page Object Model

```typescript
// e2e/pages/LoginPage.ts
import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly submitButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.emailInput = page.getByLabel('Email')
    this.passwordInput = page.getByLabel('Password')
    this.submitButton = page.getByRole('button', { name: 'Login' })
    this.errorMessage = page.getByRole('alert')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.submitButton.click()
  }

  async expectErrorMessage(message: string) {
    await expect(this.errorMessage).toContainText(message)
  }
}
```

```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/LoginPage'

test.describe('Login', () => {
  let loginPage: LoginPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
    await loginPage.goto()
  })

  test('successful login redirects to dashboard', async ({ page }) => {
    await loginPage.login('user@example.com', 'validpassword')

    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Welcome')).toBeVisible()
  })

  test('shows error for invalid credentials', async () => {
    await loginPage.login('user@example.com', 'wrongpassword')

    await loginPage.expectErrorMessage('Invalid credentials')
  })
})
```

### 인증 상태 저장

```typescript
// e2e/auth.setup.ts
import { test as setup, expect } from '@playwright/test'

const authFile = 'e2e/.auth/user.json'

setup('authenticate', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill('test@example.com')
  await page.getByLabel('Password').fill('password123')
  await page.getByRole('button', { name: 'Login' }).click()

  await expect(page.getByText('Dashboard')).toBeVisible()

  // 인증 상태 저장
  await page.context().storageState({ path: authFile })
})
```

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    // 인증 설정 프로젝트
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
})
```

### Visual Regression 테스트

```typescript
import { test, expect } from '@playwright/test'

test('homepage visual regression', async ({ page }) => {
  await page.goto('/')

  // 전체 페이지 스크린샷
  await expect(page).toHaveScreenshot('homepage.png')

  // 특정 요소 스크린샷
  const header = page.getByRole('banner')
  await expect(header).toHaveScreenshot('header.png')

  // 임계값 설정
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixelRatio: 0.1,
  })
})
```

## 테스트 구조 권장

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx     # 유닛 테스트
│   │   └── index.ts
│   └── Form/
│       ├── Form.tsx
│       └── Form.test.tsx
├── hooks/
│   ├── useCounter.ts
│   └── useCounter.test.ts
├── services/
│   ├── api.ts
│   └── api.test.ts
└── test/
    ├── setup.ts
    ├── utils.tsx               # 테스트 유틸리티
    └── mocks/
        ├── handlers.ts
        └── server.ts

e2e/
├── pages/                      # Page Objects
│   ├── LoginPage.ts
│   └── DashboardPage.ts
├── fixtures/                   # 테스트 데이터
│   └── users.json
├── auth.setup.ts
├── login.spec.ts
└── dashboard.spec.ts
```

## 디버깅 팁

```bash
# Vitest
npx vitest --ui                  # UI 모드
npx vitest --watch               # 워치 모드
npx vitest run --reporter=verbose # 상세 출력
DEBUG=vitest:* npx vitest        # 디버그 로그

# Playwright
npx playwright test --ui         # UI 모드
npx playwright test --debug      # 디버거
npx playwright test --headed     # 브라우저 표시
npx playwright codegen           # 코드 생성
npx playwright show-report       # 리포트 보기
```
