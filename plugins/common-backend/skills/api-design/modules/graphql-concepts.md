# GraphQL Concepts

GraphQL 스키마, 쿼리, 리졸버 설계.

## Schema Design

### Types
```graphql
type User {
  id: ID!
  email: String!
  name: String
  createdAt: DateTime!
  orders: [Order!]!
}

type Order {
  id: ID!
  total: Float!
  status: OrderStatus!
  user: User!
  items: [OrderItem!]!
}

enum OrderStatus {
  PENDING
  PROCESSING
  COMPLETED
  CANCELLED
}
```

### Input Types
```graphql
input CreateUserInput {
  email: String!
  name: String
  password: String!
}

input UpdateUserInput {
  name: String
  email: String
}
```

### Query & Mutation
```graphql
type Query {
  user(id: ID!): User
  users(first: Int, after: String): UserConnection!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!
}
```

## Pagination (Relay-style)

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Query
query {
  users(first: 10, after: "cursor123") {
    edges {
      node {
        id
        name
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## N+1 Prevention

### Problem
```graphql
# 1 query for users + N queries for orders
query {
  users {
    id
    orders {  # N additional queries
      id
    }
  }
}
```

### DataLoader Solution
```python
# Python with Strawberry
from strawberry.dataloader import DataLoader

async def load_orders_by_user(user_ids: list[int]) -> list[list[Order]]:
    orders = await db.fetch_orders_for_users(user_ids)
    # Group by user_id
    return [
        [o for o in orders if o.user_id == uid]
        for uid in user_ids
    ]

order_loader = DataLoader(load_fn=load_orders_by_user)

@strawberry.type
class User:
    @strawberry.field
    async def orders(self, info) -> list[Order]:
        return await order_loader.load(self.id)
```

## Error Handling

### Partial Errors
```json
{
  "data": {
    "user": {
      "id": "123",
      "orders": null
    }
  },
  "errors": [
    {
      "message": "Failed to fetch orders",
      "path": ["user", "orders"],
      "extensions": {
        "code": "INTERNAL_ERROR"
      }
    }
  ]
}
```

### Union Error Types
```graphql
type CreateUserSuccess {
  user: User!
}

type ValidationError {
  field: String!
  message: String!
}

union CreateUserResult = CreateUserSuccess | ValidationError

type Mutation {
  createUser(input: CreateUserInput!): CreateUserResult!
}
```

## Query Complexity

### Limit Depth
```graphql
# Max depth: 3
query {
  users {           # 1
    orders {        # 2
      items {       # 3
        product {   # 4 - Blocked!
          ...
        }
      }
    }
  }
}
```

### Limit Complexity
```
Assign cost to each field
- Scalar: 1
- Object: 2
- List: 5 * first

Maximum complexity: 100
```

## Best Practices

### Nullable vs Non-Null
```graphql
# Non-null: 항상 값 존재
email: String!

# Nullable: 없을 수 있음
bio: String

# List: 빈 리스트 가능
orders: [Order!]!  # Non-null list, non-null items
```

### Naming
```graphql
# PascalCase for types
type User { }
type OrderItem { }

# camelCase for fields
firstName: String
createdAt: DateTime
```
