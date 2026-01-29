---
name: typescript-advanced
description: 제네릭, 유틸리티 타입, 타입 가드, 브랜드 타입, React 전용 패턴 등 프론트엔드 개발을 위한 고급 TypeScript 패턴.
version: 1.0.0
category: language
user-invocable: true
triggers:
  keywords: [typescript, types, generics, infer, conditional types, type guards, branded types]
  intentPatterns:
    - "(타입|제네릭|TypeScript).*(패턴|고급|심화)"
    - "(type|generic|typescript).*(pattern|advanced|complex)"
---

# 고급 TypeScript 패턴

프론트엔드 React/Next.js 개발을 위한 고급 TypeScript 패턴. 타입 안전성, 제네릭, 실용적 패턴을 다룹니다.

## 유틸리티 타입

### 내장 유틸리티

```typescript
// Pick - 특정 속성 선택
type UserPreview = Pick<User, 'id' | 'name' | 'avatar'>

// Omit - 속성 제외
type UserWithoutPassword = Omit<User, 'password'>

// Partial - 모두 선택적으로
type UserUpdate = Partial<User>

// Required - 모두 필수로
type CompleteUser = Required<User>

// Readonly - 불변으로
type ImmutableUser = Readonly<User>

// Record - 키-값 매핑
type StatusMap = Record<'pending' | 'active' | 'closed', Item[]>

// NonNullable - null/undefined 제거
type DefinitelyString = NonNullable<string | null | undefined> // string

// ReturnType - 함수 반환 타입 추출
type ApiResponse = ReturnType<typeof fetchUser>

// Parameters - 함수 매개변수 추출
type FetchParams = Parameters<typeof fetchUser> // [id: string]

// Awaited - Promise 언래핑
type User = Awaited<ReturnType<typeof fetchUser>>
```

### 커스텀 유틸리티 타입

```typescript
// DeepPartial - 재귀적 partial
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

// DeepReadonly - 재귀적 readonly
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P]
}

// Nullable - 타입에 null 추가
type Nullable<T> = T | null

// ValueOf - 객체 값의 유니온 얻기
type ValueOf<T> = T[keyof T]
type ItemStatus = ValueOf<typeof ITEM_STATUS> // 'active' | 'resolved' | 'closed'

// RequireAtLeastOne - 최소 하나의 속성 필수
type RequireAtLeastOne<T, Keys extends keyof T = keyof T> =
  Pick<T, Exclude<keyof T, Keys>> &
  { [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>> }[Keys]

// 사용
type SearchParams = RequireAtLeastOne<{
  query?: string
  category?: string
  userId?: string
}, 'query' | 'category'> // query 또는 category 필수
```

## 제네릭

### 함수 제네릭

```typescript
// 기본 제네릭 함수
function identity<T>(value: T): T {
  return value
}

// 제약이 있는 제네릭
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

// 기본값이 있는 제네릭
function createArray<T = string>(length: number, value: T): T[] {
  return Array(length).fill(value)
}

// 다중 제네릭
function map<T, U>(arr: T[], fn: (item: T) => U): U[] {
  return arr.map(fn)
}
```

### 컴포넌트 제네릭

```typescript
// 제네릭 컴포넌트
interface ListProps<T> {
  items: T[]
  renderItem: (item: T) => React.ReactNode
  keyExtractor: (item: T) => string
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map((item) => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  )
}

// 타입 추론과 함께 사용
<List
  items={items}
  renderItem={(item) => <ItemCard item={item} />}
  keyExtractor={(item) => item.id}
/>
```

### 훅 제네릭

```typescript
// 제네릭 훅
function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue
    const stored = localStorage.getItem(key)
    return stored ? JSON.parse(stored) : initialValue
  })

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value))
  }, [key, value])

  return [value, setValue] as const
}

// 사용
const [user, setUser] = useLocalStorage<User | null>('user', null)
```

## 타입 가드

### 타입 서술어

```typescript
// 타입 서술어 함수
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value
  )
}

// 사용
function processData(data: unknown) {
  if (isUser(data)) {
    // TypeScript가 data가 User임을 앎
    console.log(data.email)
  }
}

// 타입 가드로 배열 필터
const users = items.filter(isUser) // User[]
```

### 판별 유니온

```typescript
// 판별 유니온
type ApiResult<T> =
  | { status: 'success'; data: T }
  | { status: 'error'; error: string }
  | { status: 'loading' }

function handleResult<T>(result: ApiResult<T>) {
  switch (result.status) {
    case 'success':
      return result.data // TypeScript가 data 존재를 앎
    case 'error':
      throw new Error(result.error)
    case 'loading':
      return null
  }
}

// 완전성 검사
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`)
}

function handleStatus(status: 'active' | 'pending' | 'closed') {
  switch (status) {
    case 'active': return '활성'
    case 'pending': return '대기'
    case 'closed': return '종료'
    default: return assertNever(status) // 케이스 누락 시 컴파일 에러
  }
}
```

### 단언 함수

```typescript
// 단언 함수
function assertIsDefined<T>(value: T): asserts value is NonNullable<T> {
  if (value === undefined || value === null) {
    throw new Error('Value is not defined')
  }
}

// 사용
function processUser(user: User | null) {
  assertIsDefined(user)
  // TypeScript가 user가 User임을 앎
  console.log(user.name)
}
```

## 브랜드 타입

```typescript
// 브랜드 타입으로 타입 혼동 방지
type UserId = string & { readonly brand: unique symbol }
type ItemId = string & { readonly brand: unique symbol }

// 팩토리 함수
function createUserId(id: string): UserId {
  return id as UserId
}

function createItemId(id: string): ItemId {
  return id as ItemId
}

// 이제 타입 안전
function getUser(id: UserId): User { /* ... */ }
function getItem(id: ItemId): Item { /* ... */ }

const userId = createUserId('user-123')
const itemId = createItemId('item-456')

getUser(userId)   // OK
getUser(itemId)   // 에러: 'ItemId' 타입은 'UserId'에 할당 불가
```

## 조건부 타입

```typescript
// 기본 조건부
type IsString<T> = T extends string ? true : false

// infer 키워드
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T
type ArrayElement<T> = T extends (infer E)[] ? E : T

// Extract/Exclude
type NumberProps<T> = {
  [K in keyof T as T[K] extends number ? K : never]: T[K]
}

interface Stats {
  name: string
  count: number
  score: number
  active: boolean
}

type NumericStats = NumberProps<Stats> // { count: number; score: number }
```

## React 전용 패턴

### 컴포넌트 Props

```typescript
// HTML 요소 props 확장
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  isLoading?: boolean
}

// 다형성 컴포넌트 (as prop)
type PolymorphicProps<E extends React.ElementType> = {
  as?: E
} & Omit<React.ComponentPropsWithoutRef<E>, 'as'>

function Box<E extends React.ElementType = 'div'>({
  as,
  ...props
}: PolymorphicProps<E>) {
  const Component = as || 'div'
  return <Component {...props} />
}

// 사용
<Box as="section" id="main">콘텐츠</Box>
<Box as="a" href="/about">링크</Box>
```

### Children 타입

```typescript
// 문자열 children만
interface TitleProps {
  children: string
}

// 단일 React 요소
interface WrapperProps {
  children: React.ReactElement
}

// 모든 렌더 가능한 콘텐츠
interface ContainerProps {
  children: React.ReactNode
}

// 함수 children (render props)
interface DataProviderProps<T> {
  children: (data: T) => React.ReactNode
}
```

### 이벤트 핸들러

```typescript
// 타입 지정된 이벤트 핸들러
const handleClick: React.MouseEventHandler<HTMLButtonElement> = (e) => {
  console.log(e.currentTarget.name)
}

const handleChange: React.ChangeEventHandler<HTMLInputElement> = (e) => {
  console.log(e.target.value)
}

const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
  e.preventDefault()
  const formData = new FormData(e.currentTarget)
}

// 키보드 이벤트
const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
  if (e.key === 'Enter') {
    // 제출
  }
}
```

### Ref 타입

```typescript
// 제네릭으로 forward ref
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, ...props }, ref) => (
    <div>
      <label>{label}</label>
      <input ref={ref} {...props} />
    </div>
  )
)

// useRef 타입
const inputRef = useRef<HTMLInputElement>(null)
const valueRef = useRef<number>(0) // 변경 가능한 ref
const callbackRef = useRef<(() => void) | null>(null)
```

## API 응답 타입

```typescript
// 제네릭 API 응답
interface ApiResponse<T> {
  data: T
  meta: {
    total: number
    page: number
    limit: number
  }
}

// 타입 안전한 fetch 래퍼
async function apiFetch<T>(
  url: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const response = await fetch(url, options)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  return response.json()
}

// 사용
const { data: items } = await apiFetch<Item[]>('/api/items')
```

## Zod 통합

```typescript
import { z } from 'zod'

// 스키마 정의
const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'user', 'guest']),
  createdAt: z.string().datetime(),
})

// 스키마에서 타입 추론
type User = z.infer<typeof UserSchema>

// 런타임 검증
function parseUser(data: unknown): User {
  return UserSchema.parse(data)
}

// 안전한 파싱 (throw 안 함)
function safeParseUser(data: unknown) {
  const result = UserSchema.safeParse(data)
  if (result.success) {
    return { user: result.data, error: null }
  }
  return { user: null, error: result.error }
}
```

## 템플릿 리터럴 타입

```typescript
// API 라우트 타입
type ApiRoute = `/api/${string}`
type ItemRoute = `/items/${string}`

// 이벤트 이름
type EventName = `on${Capitalize<string>}`

// CSS 단위
type CSSUnit = `${number}${'px' | 'rem' | 'em' | '%'}`

// Getter/Setter 패턴
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
}

type Setters<T> = {
  [K in keyof T as `set${Capitalize<string & K>}`]: (value: T[K]) => void
}
```

## 모범 사례

### 1. 유니온에는 Type 선호

```typescript
// 유니온에는 type 사용
type Status = 'pending' | 'active' | 'closed'

// 확장 가능한 객체에는 interface 사용
interface User {
  id: string
  name: string
}

interface AdminUser extends User {
  permissions: string[]
}
```

### 2. 타입 검사에 `satisfies` 사용

```typescript
// satisfies는 리터럴 타입 보존
const config = {
  theme: 'dark',
  fontSize: 14,
} satisfies Record<string, string | number>

// config.theme은 여전히 'dark', string 아님
```

### 3. `any` 피하고 `unknown` 사용

```typescript
// 나쁨
function processData(data: any) {
  return data.value // 타입 안전성 없음
}

// 좋음
function processData(data: unknown) {
  if (isValidData(data)) {
    return data.value // 타입 안전
  }
  throw new Error('Invalid data')
}
```

### 4. `const` 단언 사용

```typescript
// const 단언 없이
const STATUSES = ['pending', 'active', 'closed']
// 타입: string[]

// const 단언과 함께
const STATUSES = ['pending', 'active', 'closed'] as const
// 타입: readonly ['pending', 'active', 'closed']

type Status = typeof STATUSES[number] // 'pending' | 'active' | 'closed'
```
