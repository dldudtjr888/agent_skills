# RBAC & ABAC

역할 기반(RBAC)과 속성 기반(ABAC) 접근 제어.

## RBAC (Role-Based Access Control)

### Concept
```
User → Role → Permissions

User: alice
  └── Role: editor
        ├── Permission: posts.read
        ├── Permission: posts.create
        └── Permission: posts.update
```

### Schema
```sql
CREATE TABLE roles (
  id bigint PRIMARY KEY,
  name text UNIQUE NOT NULL  -- admin, editor, viewer
);

CREATE TABLE permissions (
  id bigint PRIMARY KEY,
  name text UNIQUE NOT NULL  -- posts.read, posts.create
);

CREATE TABLE role_permissions (
  role_id bigint REFERENCES roles(id),
  permission_id bigint REFERENCES permissions(id),
  PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
  user_id bigint REFERENCES users(id),
  role_id bigint REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);
```

### Implementation
```python
def has_permission(user_id, permission):
    return db.execute("""
        SELECT 1 FROM user_roles ur
        JOIN role_permissions rp ON rp.role_id = ur.role_id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE ur.user_id = :user_id AND p.name = :permission
    """, {"user_id": user_id, "permission": permission}).first() is not None

# Usage
if has_permission(user_id, "posts.delete"):
    delete_post(post_id)
else:
    raise PermissionDenied()
```

### Hierarchical RBAC
```
admin
  └── editor
        └── viewer

admin은 editor, viewer 권한 포함
```

```python
ROLE_HIERARCHY = {
    "admin": ["editor", "viewer"],
    "editor": ["viewer"],
    "viewer": []
}

def get_effective_roles(role):
    roles = {role}
    for child in ROLE_HIERARCHY.get(role, []):
        roles |= get_effective_roles(child)
    return roles
```

## ABAC (Attribute-Based Access Control)

### Concept
```
Policy = Subject + Resource + Action + Environment

"user가 자신의 post를 업무 시간에 수정할 수 있다"

Subject: user.id, user.department
Resource: post.owner_id, post.status
Action: update
Environment: current_time
```

### Policy Example
```python
# Policy: 작성자만 자신의 게시물 수정 가능
def can_update_post(user, post):
    return (
        user.id == post.owner_id and
        post.status != 'archived'
    )

# Policy: 관리자는 모든 게시물 수정 가능
def can_update_post_admin(user, post):
    return 'admin' in user.roles

# Combined
def can_update_post(user, post):
    return (
        can_update_post_admin(user, post) or
        (user.id == post.owner_id and post.status != 'archived')
    )
```

### ABAC with Policy Engine
```python
# Policy definition
policies = [
    {
        "effect": "allow",
        "subjects": ["role:editor"],
        "resources": ["posts:*"],
        "actions": ["read", "update"],
        "conditions": {
            "owner_match": "subject.id == resource.owner_id"
        }
    }
]

# Evaluation
def evaluate(subject, resource, action):
    for policy in policies:
        if matches(policy, subject, resource, action):
            if policy["effect"] == "allow":
                return True
    return False
```

## RBAC vs ABAC

| Aspect | RBAC | ABAC |
|--------|------|------|
| 복잡도 | 낮음 | 높음 |
| 유연성 | 낮음 | 높음 |
| 구현 난이도 | 쉬움 | 어려움 |
| Use Case | 단순한 권한 | 복잡한 조건 |
| 예시 | "편집자는 게시물 수정 가능" | "작성자가 자신의 미공개 게시물만 수정 가능" |

### When to Use

**RBAC**
- 권한이 역할에 명확히 매핑됨
- 조건이 단순함
- 빠른 구현 필요

**ABAC**
- 소유자 기반 접근 제어
- 시간/위치 기반 제한
- 동적 조건이 많음

## Hybrid Approach

```python
# RBAC + ABAC 조합
def can_access(user, resource, action):
    # RBAC: 역할 기반 체크
    if has_role(user, 'admin'):
        return True

    # ABAC: 속성 기반 체크
    if action == 'update':
        return resource.owner_id == user.id

    # RBAC: 권한 체크
    return has_permission(user, f'{resource.type}.{action}')
```

## Best Practices

### 1. Deny by Default
```python
def check_permission(user, resource, action):
    # 명시적으로 허용된 경우만 True
    for policy in get_policies(user):
        if policy.allows(resource, action):
            return True
    return False  # 기본은 거부
```

### 2. Least Privilege
```python
# BAD: 과도한 권한
roles = ["admin"]

# GOOD: 최소 권한
roles = ["posts.editor"]  # 게시물 편집만
```

### 3. Audit Logging
```python
def check_and_log(user, resource, action):
    allowed = check_permission(user, resource, action)
    log_access_attempt(
        user=user,
        resource=resource,
        action=action,
        allowed=allowed
    )
    return allowed
```
