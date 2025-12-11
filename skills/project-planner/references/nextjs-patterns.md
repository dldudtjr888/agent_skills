# Next.js & React Refactoring Patterns

Comprehensive guide to Next.js and React-specific refactoring patterns, optimized for Next.js 14+ and React 18+.

## Table of Contents

1. [Component Refactoring](#component-refactoring)
2. [Hooks Patterns](#hooks-patterns)
3. [Next.js App Router Patterns](#nextjs-app-router-patterns)
4. [Performance Optimization](#performance-optimization)
5. [State Management](#state-management)
6. [Server vs Client Components](#server-vs-client-components)

---

## Component Refactoring

### Extract Component

**When to Use**: Component > 200 lines, multiple responsibilities

```tsx
// Before - Large monolithic component
function UserDashboard({ user }) {
  const [orders, setOrders] = useState([])
  const [profile, setProfile] = useState(user)
  const [settings, setSettings] = useState({})
  
  // 150+ lines of mixed logic
  return (
    <div>
      <div className="profile">
        {/* Profile UI - 50 lines */}
      </div>
      <div className="orders">
        {/* Orders UI - 50 lines */}
      </div>
      <div className="settings">
        {/* Settings UI - 50 lines */}
      </div>
    </div>
  )
}

// After - Extracted components
function UserDashboard({ user }) {
  return (
    <div>
      <UserProfile user={user} />
      <UserOrders userId={user.id} />
      <UserSettings userId={user.id} />
    </div>
  )
}

function UserProfile({ user }) {
  const [profile, setProfile] = useState(user)
  
  return (
    <div className="profile">
      {/* Profile-specific UI */}
    </div>
  )
}

function UserOrders({ userId }) {
  const [orders, setOrders] = useState([])
  
  useEffect(() => {
    loadOrders(userId).then(setOrders)
  }, [userId])
  
  return (
    <div className="orders">
      {/* Orders-specific UI */}
    </div>
  )
}

function UserSettings({ userId }) {
  const [settings, setSettings] = useState({})
  
  return (
    <div className="settings">
      {/* Settings-specific UI */}
    </div>
  )
}
```

### Component Composition over Props Drilling

**When to Use**: Passing props through 3+ levels

```tsx
// Before - Props drilling
function App() {
  const [theme, setTheme] = useState('light')
  return <Layout theme={theme} setTheme={setTheme} />
}

function Layout({ theme, setTheme }) {
  return <Sidebar theme={theme} setTheme={setTheme} />
}

function Sidebar({ theme, setTheme }) {
  return <ThemeToggle theme={theme} setTheme={setTheme} />
}

// After - Context
import { createContext, useContext, useState } from 'react'

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light')
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}

// Usage
function App() {
  return (
    <ThemeProvider>
      <Layout />
    </ThemeProvider>
  )
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  return <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} />
}
```

### Split by Responsibility (Container/Presentational)

```tsx
// Before - Mixed concerns
function ProductList() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => {
        setProducts(data)
        setLoading(false)
      })
  }, [])
  
  if (loading) return <div>Loading...</div>
  
  return (
    <div className="grid">
      {products.map(product => (
        <div key={product.id} className="card">
          <img src={product.image} alt={product.name} />
          <h3>{product.name}</h3>
          <p>${product.price}</p>
        </div>
      ))}
    </div>
  )
}

// After - Separated concerns
// Container (logic)
function ProductListContainer() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => {
        setProducts(data)
        setLoading(false)
      })
  }, [])
  
  if (loading) return <LoadingSpinner />
  
  return <ProductListView products={products} />
}

// Presentational (UI)
function ProductListView({ products }) {
  return (
    <div className="grid">
      {products.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}

function ProductCard({ product }) {
  return (
    <div className="card">
      <img src={product.image} alt={product.name} />
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  )
}
```

---

## Hooks Patterns

### Extract Custom Hook

**When to Use**: Duplicated hook logic, complex state management

```tsx
// Before - Repeated logic
function UserProfile() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    fetch('/api/user')
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])
  
  // Use data, loading, error
}

function UserOrders() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    fetch('/api/orders')
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])
  
  // Use data, loading, error
}

// After - Custom hook
function useFetch(url) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    setLoading(true)
    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok')
        return res.json()
      })
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [url])
  
  return { data, loading, error }
}

// Usage
function UserProfile() {
  const { data, loading, error } = useFetch('/api/user')
  // ...
}

function UserOrders() {
  const { data, loading, error } = useFetch('/api/orders')
  // ...
}
```

### Optimize with useCallback

**When to Use**: Passing callbacks to memoized child components

```tsx
// Before - Creates new function on every render
function TodoList({ todos }) {
  const handleToggle = (id) => {
    // Toggle logic
  }
  
  return todos.map(todo => (
    <TodoItem 
      key={todo.id} 
      todo={todo} 
      onToggle={handleToggle}  // New function every render
    />
  ))
}

// After - Memoized callback
import { useCallback } from 'react'

function TodoList({ todos }) {
  const handleToggle = useCallback((id) => {
    // Toggle logic
  }, []) // Dependencies
  
  return todos.map(todo => (
    <TodoItem 
      key={todo.id} 
      todo={todo} 
      onToggle={handleToggle}  // Same function reference
    />
  ))
}

const TodoItem = React.memo(({ todo, onToggle }) => {
  return (
    <div onClick={() => onToggle(todo.id)}>
      {todo.title}
    </div>
  )
})
```

### Optimize with useMemo

**When to Use**: Expensive calculations

```tsx
// Before - Recalculates on every render
function ProductList({ products, filter }) {
  const filteredProducts = products
    .filter(p => p.category === filter)
    .sort((a, b) => a.price - b.price)
    .map(p => ({
      ...p,
      displayPrice: formatCurrency(p.price)
    }))
  
  return <div>{/* Render filtered products */}</div>
}

// After - Memoized calculation
import { useMemo } from 'react'

function ProductList({ products, filter }) {
  const filteredProducts = useMemo(() => {
    return products
      .filter(p => p.category === filter)
      .sort((a, b) => a.price - b.price)
      .map(p => ({
        ...p,
        displayPrice: formatCurrency(p.price)
      }))
  }, [products, filter])
  
  return <div>{/* Render filtered products */}</div>
}
```

---

## Next.js App Router Patterns

### Server vs Client Component Optimization

**When to Use**: Minimize client-side JavaScript

```tsx
// Before - Everything client-side
'use client'

export default function ProductPage({ productId }) {
  const [product, setProduct] = useState(null)
  const [reviews, setReviews] = useState([])
  
  useEffect(() => {
    fetchProduct(productId).then(setProduct)
    fetchReviews(productId).then(setReviews)
  }, [productId])
  
  return (
    <div>
      {product && <ProductDetails product={product} />}
      {reviews && <ReviewList reviews={reviews} />}
    </div>
  )
}

// After - Server component with selective client components
// app/product/[id]/page.tsx - Server Component
import { ProductDetails } from './ProductDetails'
import { ReviewList } from './ReviewList'
import { AddToCartButton } from './AddToCartButton'

export default async function ProductPage({ params }) {
  const product = await fetchProduct(params.id)
  const reviews = await fetchReviews(params.id)
  
  return (
    <div>
      <ProductDetails product={product} />
      <AddToCartButton productId={product.id} />
      <ReviewList reviews={reviews} />
    </div>
  )
}

// AddToCartButton.tsx - Client Component (needs interactivity)
'use client'

export function AddToCartButton({ productId }) {
  const [loading, setLoading] = useState(false)
  
  const handleClick = async () => {
    setLoading(true)
    await addToCart(productId)
    setLoading(false)
  }
  
  return (
    <button onClick={handleClick} disabled={loading}>
      {loading ? 'Adding...' : 'Add to Cart'}
    </button>
  )
}
```

### Parallel Data Fetching

```tsx
// Before - Sequential fetching
export default async function Dashboard() {
  const user = await fetchUser()
  const stats = await fetchStats(user.id)
  const activity = await fetchActivity(user.id)
  
  return <div>{/* Render */}</div>
}

// After - Parallel fetching
export default async function Dashboard() {
  const [user, stats, activity] = await Promise.all([
    fetchUser(),
    fetchStats(),
    fetchActivity()
  ])
  
  return <div>{/* Render */}</div>
}

// Even better - Streaming with Suspense
import { Suspense } from 'react'

export default function Dashboard() {
  return (
    <div>
      <Suspense fallback={<UserSkeleton />}>
        <UserInfo />
      </Suspense>
      <Suspense fallback={<StatsSkeleton />}>
        <Stats />
      </Suspense>
      <Suspense fallback={<ActivitySkeleton />}>
        <Activity />
      </Suspense>
    </div>
  )
}

async function UserInfo() {
  const user = await fetchUser()
  return <div>{/* User UI */}</div>
}

async function Stats() {
  const stats = await fetchStats()
  return <div>{/* Stats UI */}</div>
}

async function Activity() {
  const activity = await fetchActivity()
  return <div>{/* Activity UI */}</div>
}
```

### Route Organization

```typescript
// Before - Flat structure
app/
  dashboard/page.tsx
  dashboard-settings/page.tsx
  dashboard-analytics/page.tsx
  dashboard-reports/page.tsx

// After - Route groups
app/
  (dashboard)/
    layout.tsx              // Shared layout for dashboard
    dashboard/page.tsx
    settings/page.tsx
    analytics/page.tsx
    reports/page.tsx
```

### Next.js 15 Cache Directive Optimization

```tsx
// Before - Everything cached
export default async function ProductPage({ params }) {
  const product = await fetch(`/api/products/${params.id}`)
  return <div>{/* Render */}</div>
}

// After - Selective caching with Next.js 15
import { unstable_cache as cache } from 'next/cache'

// Cache static product details
const getCachedProduct = cache(
  async (id: string) => {
    const res = await fetch(`/api/products/${id}`)
    return res.json()
  },
  ['product-details'],
  { revalidate: 3600 } // 1 hour
)

// Don't cache dynamic inventory
async function getInventory(id: string) {
  'use cache'
  const res = await fetch(`/api/inventory/${id}`, {
    next: { revalidate: 0 }  // Always fresh
  })
  return res.json()
}

export default async function ProductPage({ params }) {
  const [product, inventory] = await Promise.all([
    getCachedProduct(params.id),
    getInventory(params.id)
  ])
  
  return <div>{/* Render with fresh inventory */}</div>
}
```

---

## Performance Optimization

### Code Splitting with Dynamic Imports

```tsx
// Before - Everything bundled
import HeavyChart from './HeavyChart'
import HeavyEditor from './HeavyEditor'

export default function Dashboard() {
  return (
    <div>
      <HeavyChart data={data} />
      <HeavyEditor content={content} />
    </div>
  )
}

// After - Dynamic imports
import dynamic from 'next/dynamic'

const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false  // Only load on client if needed
})

const HeavyEditor = dynamic(() => import('./HeavyEditor'), {
  loading: () => <EditorSkeleton />
})

export default function Dashboard() {
  const [showChart, setShowChart] = useState(false)
  
  return (
    <div>
      {showChart && <HeavyChart data={data} />}
      <HeavyEditor content={content} />
    </div>
  )
}
```

### Image Optimization

```tsx
// Before - Regular img tag
<img 
  src="/product.jpg" 
  alt="Product" 
  style={{ width: '100%' }}
/>

// After - Next.js Image component
import Image from 'next/image'

<Image
  src="/product.jpg"
  alt="Product"
  width={800}
  height={600}
  priority={true}  // For LCP images
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
/>
```

### React.memo for Pure Components

```tsx
// Before - Re-renders on every parent render
function ExpensiveComponent({ data, config }) {
  const processed = processData(data)  // Expensive operation
  
  return <div>{/* Render */}</div>
}

// After - Memoized component
import { memo } from 'react'

const ExpensiveComponent = memo(function ExpensiveComponent({ data, config }) {
  const processed = processData(data)
  
  return <div>{/* Render */}</div>
}, (prevProps, nextProps) => {
  // Custom comparison function
  return prevProps.data === nextProps.data && 
         prevProps.config === nextProps.config
})
```

---

## State Management

### Lift State Down (Avoid Global State)

```tsx
// Before - Unnecessary global state
const [formData, setFormData] = useState({})  // In App component

function App() {
  return (
    <div>
      <Header />
      <Sidebar />
      <Form formData={formData} setFormData={setFormData} />
    </div>
  )
}

// After - Local state
function App() {
  return (
    <div>
      <Header />
      <Sidebar />
      <Form />  // Manages its own state
    </div>
  )
}

function Form() {
  const [formData, setFormData] = useState({})
  // Form logic
}
```

### Use Reducers for Complex State

```tsx
// Before - Multiple related useState
function ShoppingCart() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [discount, setDiscount] = useState(0)
  const [shipping, setShipping] = useState(0)
  
  const addItem = (item) => {
    setItems([...items, item])
    setTotal(total + item.price)
    // Lots of related state updates
  }
  
  // More handlers...
}

// After - useReducer
import { useReducer } from 'react'

const initialState = {
  items: [],
  total: 0,
  discount: 0,
  shipping: 0
}

function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD_ITEM':
      const newTotal = state.total + action.item.price
      return {
        ...state,
        items: [...state.items, action.item],
        total: newTotal,
        shipping: newTotal > 100 ? 0 : 10
      }
    
    case 'APPLY_DISCOUNT':
      return {
        ...state,
        discount: action.discount,
        total: state.total - action.discount
      }
    
    default:
      return state
  }
}

function ShoppingCart() {
  const [state, dispatch] = useReducer(cartReducer, initialState)
  
  const addItem = (item) => {
    dispatch({ type: 'ADD_ITEM', item })
  }
  
  const applyDiscount = (discount) => {
    dispatch({ type: 'APPLY_DISCOUNT', discount })
  }
  
  return <div>{/* Render */}</div>
}
```

---

## TypeScript Best Practices

### Proper Type Definitions

```tsx
// Before - Loose typing
function ProductCard({ product }) {
  return <div>{product.name}</div>
}

// After - Strict typing
interface Product {
  id: string
  name: string
  price: number
  image: string
  category: string
}

interface ProductCardProps {
  product: Product
  onAddToCart?: (productId: string) => void
}

function ProductCard({ product, onAddToCart }: ProductCardProps) {
  return <div>{product.name}</div>
}

// Even better - Generic types for reusable components
interface ListProps<T> {
  items: T[]
  renderItem: (item: T) => React.ReactNode
  keyExtractor: (item: T) => string
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <div>
      {items.map(item => (
        <div key={keyExtractor(item)}>
          {renderItem(item)}
        </div>
      ))}
    </div>
  )
}
```

### Discriminated Unions for State

```tsx
// Before - Optional fields
interface LoadingState {
  loading: boolean
  data?: User
  error?: Error
}

// After - Discriminated union
type LoadingState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: User }
  | { status: 'error'; error: Error }

function UserProfile() {
  const [state, setState] = useState<LoadingState>({ status: 'idle' })
  
  // TypeScript ensures we handle all cases
  if (state.status === 'loading') {
    return <Spinner />
  }
  
  if (state.status === 'error') {
    return <Error message={state.error.message} />
  }
  
  if (state.status === 'success') {
    return <UserDetails user={state.data} />
  }
  
  return null
}
```
