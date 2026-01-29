# API Documentation Patterns

OpenAPI/Swagger 기반 API 문서화.

## OpenAPI 3.0 Structure

```yaml
openapi: 3.0.3
info:
  title: My API
  version: 1.0.0
  description: API description

servers:
  - url: https://api.example.com/v1

paths:
  /users:
    get: ...
    post: ...

components:
  schemas: ...
  securitySchemes: ...
```

## Path Definition

```yaml
paths:
  /users/{id}:
    get:
      summary: Get user by ID
      operationId: getUser
      tags:
        - Users
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found
```

## Schema Definition

```yaml
components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: integer
          format: int64
          example: 123
        email:
          type: string
          format: email
          example: user@example.com
        name:
          type: string
          example: John Doe
        createdAt:
          type: string
          format: date-time

    CreateUserRequest:
      type: object
      required:
        - email
        - password
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
        name:
          type: string
```

## Authentication

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

    apiKey:
      type: apiKey
      in: header
      name: X-API-Key

security:
  - bearerAuth: []
```

## Request Examples

```yaml
paths:
  /users:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
            examples:
              basic:
                summary: Basic user
                value:
                  email: user@example.com
                  password: secretpass123
              withName:
                summary: User with name
                value:
                  email: user@example.com
                  password: secretpass123
                  name: John Doe
```

## Error Responses

```yaml
components:
  schemas:
    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              example: VALIDATION_ERROR
            message:
              type: string
              example: Invalid request
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

## Best Practices

### 1. Use Examples
```yaml
properties:
  email:
    type: string
    example: user@example.com  # 실제 예시 제공
```

### 2. Consistent Naming
```yaml
# operationId 일관성
getUsers, getUser, createUser, updateUser, deleteUser
```

### 3. Tags for Organization
```yaml
tags:
  - name: Users
    description: User management
  - name: Orders
    description: Order management
```

### 4. Descriptions
```yaml
summary: Create a new user          # 짧은 요약
description: |                       # 상세 설명
  Creates a new user account.
  - Email must be unique
  - Password must be at least 8 characters
```

## Code Generation

```bash
# OpenAPI Generator
openapi-generator generate -i api.yaml -g python-fastapi -o ./generated

# Swagger Codegen
swagger-codegen generate -i api.yaml -l python -o ./generated
```
