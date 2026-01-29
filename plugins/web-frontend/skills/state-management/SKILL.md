---
name: state-management
description: Zustand, Jotai, TanStack Query, React Context를 활용한 React 상태 관리 패턴. 각 솔루션의 사용 시점과 모범 사례를 다룹니다.
version: 1.0.0
category: patterns
user-invocable: true
triggers:
  keywords: [state, zustand, jotai, tanstack, query, context, store, global state, server state]
  intentPatterns:
    - "(상태|스토어|전역).*(관리|패턴|설계)"
    - "(state|store|global).*(management|pattern|design)"
    - "(zustand|jotai|tanstack|react-query)"
---

# 상태 관리 패턴

React 애플리케이션의 현대적인 상태 관리 접근법. Vercel의 react-best-practices를 보완하며 상태 관리 아키텍처에 집중합니다.

## 솔루션 선택 가이드

### 결정 매트릭스

| 필요 상황 | 솔루션 | 이유 |
|----------|--------|------|
| 서버 상태 (API 데이터) | **TanStack Query** | 내장 캐싱, 재요청, 낙관적 업데이트 |
| 간단한 전역 상태 | **Zustand** | 최소 보일러플레이트, Provider 불필요 |
| 원자적/세분화된 상태 | **Jotai** | 미세한 반응성, 파생 atom |
| 컴포넌트 트리 상태 | **React Context** | 내장, 테마/인증에 적합 |
| 복잡한 폼 | **React Hook Form** | 성능 최적화, 검증 |
| URL 상태 | **nuqs / useSearchParams** | 공유 가능, 북마크 가능 |

## TanStack Query (서버 상태)

### 기본 설정

```typescript
// lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5분
      gcTime: 1000 * 60 * 30,   // 30분 (이전 cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
```

### 쿼리 패턴

```typescript
// hooks/useItems.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// 쿼리 키 팩토리 (권장)
export const itemKeys = {
  all: ['items'] as const,
  lists: () => [...itemKeys.all, 'list'] as const,
  list: (filters: string) => [...itemKeys.lists(), { filters }] as const,
  details: () => [...itemKeys.all, 'detail'] as const,
  detail: (id: string) => [...itemKeys.details(), id] as const,
}

// 쿼리 훅
export function useItems(filters?: string) {
  return useQuery({
    queryKey: itemKeys.list(filters ?? ''),
    queryFn: () => fetchItems(filters),
    select: (data) => data.items, // 데이터 변환
  })
}

// 낙관적 업데이트가 있는 뮤테이션
export function useCreateItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createItem,
    onMutate: async (newItem) => {
      // 진행 중인 재요청 취소
      await queryClient.cancelQueries({ queryKey: itemKeys.lists() })

      // 이전 값 스냅샷
      const previousItems = queryClient.getQueryData(itemKeys.lists())

      // 낙관적 업데이트
      queryClient.setQueryData(itemKeys.lists(), (old: Item[]) => [
        ...old,
        { ...newItem, id: 'temp-id' },
      ])

      return { previousItems }
    },
    onError: (err, newItem, context) => {
      // 에러 시 롤백
      queryClient.setQueryData(itemKeys.lists(), context?.previousItems)
    },
    onSettled: () => {
      // 뮤테이션 후 재요청
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
  })
}
```

### 프리페칭

```typescript
// 호버 시 프리페치
function ItemLink({ id }: { id: string }) {
  const queryClient = useQueryClient()

  const prefetchItem = () => {
    queryClient.prefetchQuery({
      queryKey: itemKeys.detail(id),
      queryFn: () => fetchItem(id),
      staleTime: 1000 * 60, // 데이터가 1분 이상 오래된 경우만 프리페치
    })
  }

  return (
    <Link href={`/items/${id}`} onMouseEnter={prefetchItem}>
      상세 보기
    </Link>
  )
}
```

## Zustand (클라이언트 전역 상태)

### 스토어 패턴

```typescript
// stores/ui-store.ts
import { create } from 'zustand'
import { persist, devtools } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  notifications: Notification[]

  // 액션
  toggleSidebar: () => void
  setTheme: (theme: UIState['theme']) => void
  addNotification: (notification: Notification) => void
  removeNotification: (id: string) => void
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set) => ({
        sidebarOpen: true,
        theme: 'system',
        notifications: [],

        toggleSidebar: () => set((state) => ({
          sidebarOpen: !state.sidebarOpen
        })),

        setTheme: (theme) => set({ theme }),

        addNotification: (notification) => set((state) => ({
          notifications: [...state.notifications, notification],
        })),

        removeNotification: (id) => set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
      }),
      { name: 'ui-storage' } // localStorage 키
    ),
    { name: 'UIStore' } // devtools 이름
  )
)
```

### 셀렉터 (성능)

```typescript
// 셀렉터로 불필요한 리렌더 방지
function Sidebar() {
  // sidebarOpen이 변경될 때만 리렌더
  const sidebarOpen = useUIStore((state) => state.sidebarOpen)
  const toggleSidebar = useUIStore((state) => state.toggleSidebar)

  return (
    <aside className={sidebarOpen ? 'open' : 'closed'}>
      <button onClick={toggleSidebar}>토글</button>
    </aside>
  )
}

// shallow compare로 여러 값 선택
import { shallow } from 'zustand/shallow'

function Header() {
  const { theme, notifications } = useUIStore(
    (state) => ({ theme: state.theme, notifications: state.notifications }),
    shallow
  )
}
```

### 비동기 액션

```typescript
// stores/auth-store.ts
interface AuthState {
  user: User | null
  isLoading: boolean
  error: string | null

  login: (credentials: Credentials) => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  user: null,
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null })
    try {
      const user = await authApi.login(credentials)
      set({ user, isLoading: false })
    } catch (error) {
      set({ error: error.message, isLoading: false })
    }
  },

  logout: async () => {
    await authApi.logout()
    set({ user: null })
  },
}))
```

## Jotai (원자적 상태)

### 기본 Atom

```typescript
// atoms/filters.ts
import { atom } from 'jotai'
import { atomWithStorage } from 'jotai/utils'

// 단순 atom
export const searchQueryAtom = atom('')

// 영속 atom
export const sortOrderAtom = atomWithStorage<'asc' | 'desc'>('sortOrder', 'desc')

// 파생 atom (읽기 전용)
export const filteredItemsAtom = atom((get) => {
  const query = get(searchQueryAtom)
  const items = get(itemsAtom)

  if (!query) return items
  return items.filter((m) =>
    m.name.toLowerCase().includes(query.toLowerCase())
  )
})

// 쓰기 가능한 파생 atom
export const sortedItemsAtom = atom(
  (get) => {
    const items = get(filteredItemsAtom)
    const order = get(sortOrderAtom)

    return [...items].sort((a, b) =>
      order === 'asc' ? a.volume - b.volume : b.volume - a.volume
    )
  },
  (get, set, newItems: Item[]) => {
    set(itemsAtom, newItems)
  }
)
```

### 비동기 Atom

```typescript
// atoms/user.ts
import { atom } from 'jotai'
import { atomWithQuery } from 'jotai-tanstack-query'

// TanStack Query 통합 비동기 atom
export const userAtom = atomWithQuery(() => ({
  queryKey: ['user'],
  queryFn: fetchCurrentUser,
}))

// 사용
function UserProfile() {
  const [{ data: user, isLoading }] = useAtom(userAtom)

  if (isLoading) return <Spinner />
  return <div>{user.name}</div>
}
```

## React Context (컴포넌트 트리 상태)

### Context 사용 시점

- 테마/외관 설정
- 인증 상태
- 피처 플래그
- 로컬라이제이션
- 모달/다이얼로그 관리

### 패턴: Context + Reducer

```typescript
// contexts/cart-context.tsx
import { createContext, useContext, useReducer, ReactNode } from 'react'

interface CartState {
  items: CartItem[]
  total: number
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: CartItem }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'CLEAR_CART' }

const CartContext = createContext<{
  state: CartState
  dispatch: React.Dispatch<CartAction>
} | null>(null)

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM':
      return {
        ...state,
        items: [...state.items, action.payload],
        total: state.total + action.payload.price,
      }
    case 'REMOVE_ITEM':
      const item = state.items.find((i) => i.id === action.payload)
      return {
        ...state,
        items: state.items.filter((i) => i.id !== action.payload),
        total: state.total - (item?.price ?? 0),
      }
    case 'CLEAR_CART':
      return { items: [], total: 0 }
    default:
      return state
  }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [], total: 0 })

  return (
    <CartContext.Provider value={{ state, dispatch }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const context = useContext(CartContext)
  if (!context) {
    throw new Error('useCart must be used within CartProvider')
  }
  return context
}
```

## URL 상태 (nuqs)

```typescript
// 공유 가능/북마크 가능한 상태용
import { useQueryState, parseAsString, parseAsInteger } from 'nuqs'

function ItemFilters() {
  const [search, setSearch] = useQueryState('q', parseAsString.withDefault(''))
  const [page, setPage] = useQueryState('page', parseAsInteger.withDefault(1))
  const [sort, setSort] = useQueryState('sort', parseAsString.withDefault('volume'))

  // URL: /items?q=keyword&page=2&sort=volume

  return (
    <div>
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <button onClick={() => setPage(page + 1)}>다음 페이지</button>
    </div>
  )
}
```

## 피해야 할 안티패턴

### 1. Zustand/Context에 서버 상태 넣기

```typescript
// 나쁨: 서버 상태 수동 관리
const useStore = create((set) => ({
  items: [],
  fetchItems: async () => {
    const data = await fetch('/api/items')
    set({ items: data })
  },
}))

// 좋음: 서버 상태는 TanStack Query 사용
const { data: items } = useQuery({
  queryKey: ['items'],
  queryFn: fetchItems,
})
```

### 2. Context 남용

```typescript
// 나쁨: 자주 변경되는 값에 Context 사용
const MousePositionContext = createContext({ x: 0, y: 0 })

// 좋음: 빈번한 업데이트에는 Zustand 또는 Jotai 사용
const useMousePosition = create((set) => ({
  x: 0,
  y: 0,
  update: (x, y) => set({ x, y }),
}))
```

### 3. 셀렉터 미사용

```typescript
// 나쁨: 전체 스토어 구독
const store = useUIStore()

// 좋음: 필요한 것만 구독
const theme = useUIStore((state) => state.theme)
```

## 권장 스택

대부분의 React 애플리케이션:

```
서버 상태      -> TanStack Query
클라이언트 UI  -> Zustand
원자적 상태    -> Jotai (필요 시)
URL 상태      -> nuqs
폼 상태       -> React Hook Form + Zod
```

이 조합의 장점:
- 자동 캐싱 및 백그라운드 업데이트 (TanStack Query)
- 간단하고 성능 좋은 전역 상태 (Zustand)
- 필요 시 미세한 반응성 (Jotai)
- 공유 가능한 URL (nuqs)
- 타입 안전한 폼 (React Hook Form)
