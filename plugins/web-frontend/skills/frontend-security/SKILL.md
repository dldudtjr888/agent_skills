---
name: frontend-security
description: React/Next.js 애플리케이션의 프론트엔드 보안 패턴 및 모범 사례. XSS 방지, CSRF 보호, 안전한 인증, CSP, 일반 취약점을 다룹니다.
version: 1.0.0
category: security
user-invocable: true
triggers:
  keywords: [security, xss, csrf, authentication, csp, sanitize, escape, vulnerability]
  intentPatterns:
    - "(보안|취약점|인증).*(패턴|검토|가이드)"
    - "(security|xss|csrf|auth).*(pattern|review|guide)"
---

# 프론트엔드 보안 가이드

React/Next.js 애플리케이션의 보안 모범 사례. 일반 취약점, 방지 전략, 안전한 코딩 패턴을 다룹니다.

## XSS (크로스 사이트 스크립팅) 방지

### React의 내장 보호

```tsx
// React는 JSX의 값을 자동으로 이스케이프
const userInput = '<script>alert("xss")</script>'

// 안전: React가 자동으로 이스케이프
<div>{userInput}</div>
// 텍스트로 렌더: <script>alert("xss")</script>
```

### 피해야 할 위험 패턴

```tsx
// 위험: dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// 반드시 사용해야 한다면, 먼저 살균
import DOMPurify from 'dompurify'

<div dangerouslySetInnerHTML={{
  __html: DOMPurify.sanitize(userInput)
}} />
```

### URL 인젝션

```tsx
// 위험: 사용자 제어 URL
const userUrl = 'javascript:alert("xss")'
<a href={userUrl}>클릭</a>

// 안전: URL 프로토콜 검증
function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

<a href={isValidUrl(userUrl) ? userUrl : '#'}>클릭</a>
```

### 동적 속성 이름

```tsx
// 위험: 사용자 제어 속성 이름
const attrName = userInput // 'onload' 또는 'onerror'일 수 있음
<div {...{ [attrName]: 'alert(1)' }} />

// 안전: 허용 속성 화이트리스트
const ALLOWED_ATTRS = ['id', 'className', 'data-testid']
const safeAttrs = Object.fromEntries(
  Object.entries(attrs).filter(([key]) => ALLOWED_ATTRS.includes(key))
)
```

## CSRF 보호

### Same-Site 쿠키

```typescript
// next.config.js 또는 API route
export async function POST(req: Request) {
  const response = NextResponse.json({ success: true })

  response.cookies.set('session', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict', // CSRF 방지
    maxAge: 60 * 60 * 24 * 7, // 1주
  })

  return response
}
```

### CSRF 토큰

```typescript
// CSRF 토큰 생성
import { randomBytes } from 'crypto'

function generateCsrfToken(): string {
  return randomBytes(32).toString('hex')
}

// API route - 토큰 설정
export async function GET() {
  const token = generateCsrfToken()

  const response = NextResponse.json({ csrfToken: token })
  response.cookies.set('csrf', token, {
    httpOnly: true,
    sameSite: 'strict',
  })

  return response
}

// API route - 토큰 검증
export async function POST(req: Request) {
  const cookieToken = req.cookies.get('csrf')?.value
  const headerToken = req.headers.get('x-csrf-token')

  if (!cookieToken || !headerToken || cookieToken !== headerToken) {
    return NextResponse.json({ error: 'Invalid CSRF token' }, { status: 403 })
  }

  // 요청 처리...
}
```

### 클라이언트 CSRF 토큰 사용

```typescript
// hooks/useCsrf.ts
export function useCsrf() {
  const [csrfToken, setCsrfToken] = useState<string>('')

  useEffect(() => {
    fetch('/api/csrf')
      .then((res) => res.json())
      .then((data) => setCsrfToken(data.csrfToken))
  }, [])

  return csrfToken
}

// 폼에서 사용
function MyForm() {
  const csrfToken = useCsrf()

  const handleSubmit = async (data: FormData) => {
    await fetch('/api/submit', {
      method: 'POST',
      headers: {
        'x-csrf-token': csrfToken,
      },
      body: JSON.stringify(data),
    })
  }
}
```

## 안전한 인증

### JWT 모범 사례

```typescript
// JWT를 localStorage에 저장하지 말 것 (XSS에 취약)
// httpOnly 쿠키 사용

// API route - 로그인
export async function POST(req: Request) {
  const { email, password } = await req.json()

  const user = await verifyCredentials(email, password)
  if (!user) {
    return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 })
  }

  const token = await createJWT(user)

  const response = NextResponse.json({ user })
  response.cookies.set('auth', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24, // 24시간
    path: '/',
  })

  return response
}

// JWT 생성
import { SignJWT, jwtVerify } from 'jose'

const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET)

async function createJWT(user: User) {
  return new SignJWT({ userId: user.id, email: user.email })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(JWT_SECRET)
}

async function verifyJWT(token: string) {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET)
    return payload
  } catch {
    return null
  }
}
```

### 안전한 비밀번호 처리

```typescript
// 평문 비밀번호 절대 저장 금지
// bcrypt 또는 Argon2 사용

import bcrypt from 'bcryptjs'

// 저장 전 비밀번호 해시
async function hashPassword(password: string): Promise<string> {
  const salt = await bcrypt.genSalt(12)
  return bcrypt.hash(password, salt)
}

// 비밀번호 검증
async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}

// 비밀번호 강도 검증
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/

function isStrongPassword(password: string): boolean {
  return PASSWORD_REGEX.test(password)
}
```

## Content Security Policy (CSP)

### Next.js CSP 설정

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic';
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data: https:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
  `.replace(/\s{2,}/g, ' ').trim()

  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  })

  response.headers.set('Content-Security-Policy', cspHeader)

  return response
}
```

### 스크립트에 Nonce 사용

```tsx
// app/layout.tsx
import { headers } from 'next/headers'

export default function RootLayout({ children }) {
  const nonce = headers().get('x-nonce') || ''

  return (
    <html>
      <head>
        <script nonce={nonce} src="/analytics.js" />
      </head>
      <body>{children}</body>
    </html>
  )
}
```

## 보안 헤더

```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on',
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'Referrer-Policy',
    value: 'origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
]

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ]
  },
}
```

## 입력 검증

### Zod 스키마 검증

```typescript
import { z } from 'zod'

// 엄격한 스키마 정의
const UserInputSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[a-zA-Z\s]+$/),
  age: z.number().int().positive().max(150),
  url: z.string().url().optional(),
})

// 클라이언트와 서버 모두에서 검증
export async function POST(req: Request) {
  const body = await req.json()

  const result = UserInputSchema.safeParse(body)
  if (!result.success) {
    return NextResponse.json({
      error: 'Validation failed',
      details: result.error.flatten(),
    }, { status: 400 })
  }

  // result.data 사용 (검증되고 타입 지정됨)
  const { email, name, age } = result.data
}
```

### 살균

```typescript
import DOMPurify from 'dompurify'
import { JSDOM } from 'jsdom'

// 서버 사이드 DOMPurify
const window = new JSDOM('').window
const purify = DOMPurify(window)

function sanitizeHtml(dirty: string): string {
  return purify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target'],
  })
}

// SQL 유사 인젝션 방지 (검색 쿼리용)
function sanitizeSearchQuery(query: string): string {
  return query
    .replace(/['"`;]/g, '') // 따옴표와 세미콜론 제거
    .trim()
    .slice(0, 100) // 길이 제한
}
```

## 일반 취약점 체크리스트

### 클라이언트 사이드

- [ ] 살균 없는 `dangerouslySetInnerHTML` 없음
- [ ] 사용자 입력으로 `eval()` 또는 `new Function()` 없음
- [ ] 클라이언트 코드에 시크릿 없음
- [ ] 사용자 제공 링크 URL 검증
- [ ] 적절한 CORS 설정
- [ ] CSP 헤더 설정
- [ ] localStorage에 민감 데이터 없음

### 인증

- [ ] bcrypt/Argon2로 비밀번호 해시
- [ ] httpOnly 쿠키에 JWT 저장
- [ ] CSRF 보호 활성화
- [ ] 세션 타임아웃 구현
- [ ] 인증 엔드포인트 레이트 리미팅
- [ ] 안전한 비밀번호 요구사항

### API 보안

- [ ] 모든 엔드포인트 입력 검증
- [ ] 출력 인코딩/이스케이프
- [ ] 레이트 리미팅
- [ ] 인증/인가 확인
- [ ] 민감 작업 감사 로깅
- [ ] 에러 메시지가 민감 정보 누출 안 함

### 인프라

- [ ] HTTPS 강제
- [ ] 보안 헤더 설정
- [ ] 정기적 의존성 업데이트
- [ ] npm audit 깨끗
- [ ] 프로덕션에서 디버그 모드 없음
- [ ] 환경 변수에 시크릿

## 보안 테스트

```bash
# 취약한 의존성 확인
npm audit

# 자동 취약점 수정
npm audit fix

# 코드에서 시크릿 확인
npx trufflehog filesystem . --json

# OWASP 의존성 확인
npx owasp-dependency-check --project MyApp --scan .
```

## 참고 자료

- [OWASP 치트 시트 시리즈](https://cheatsheetseries.owasp.org/)
- [Next.js 보안 문서](https://nextjs.org/docs/app/building-your-application/configuring/security)
- [React 보안 모범 사례](https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html)
