# Dependency Analysis Tools

의존성 분석을 위한 도구와 명령어 가이드.

---

## 의존성 유형

### Upstream (내가 의존하는 것)
- 내 코드가 import하는 모듈/함수
- 사용하는 외부 라이브러리
- 호출하는 API/서비스

### Downstream (나에게 의존하는 것)
- 내 코드를 import하는 모듈
- 변경 시 영향받는 코드
- **반드시 검증 필요**

### Shared Resources (공유 자원)
- 데이터베이스 테이블
- 외부 API
- 전역 상태/캐시
- 환경 변수

---

## Claude Code 도구

### 1. Serena MCP (권장)

**심볼 개요 파악:**
```
mcp__serena__get_symbols_overview
  relative_path: "src/services/user.ts"
  depth: 1
```
→ 파일 내 클래스, 함수, 변수 목록

**특정 심볼 찾기:**
```
mcp__serena__find_symbol
  name_path_pattern: "UserService"
  include_body: true
```
→ 심볼 정의와 본문

**참조 찾기 (Downstream):**
```
mcp__serena__find_referencing_symbols
  name_path: "UserService/createUser"
  relative_path: "src/services/user.ts"
```
→ 이 함수를 호출하는 모든 곳

**패턴 검색:**
```
mcp__serena__search_for_pattern
  substring_pattern: "UserService"
  restrict_search_to_code_files: true
```
→ 코드 전체에서 패턴 검색

### 2. Grep (텍스트 검색)

**Import 검색 (Downstream):**
```
# TypeScript/JavaScript
Grep: "from ['\"].*user['\"]"
Grep: "import.*User"

# Python
Grep: "from.*user.*import\|import.*user"
```

**함수 호출 검색:**
```
Grep: "createUser\("
Grep: "UserService\."
```

**특정 파일 타입만:**
```
Grep: "pattern" --glob "**/*.ts"
Grep: "pattern" --type py
```

### 3. Glob (파일 검색)

**관련 파일 찾기:**
```
Glob: **/user*.ts
Glob: **/*Service*
```

---

## 언어별 Import 패턴

### TypeScript/JavaScript

```typescript
// Named import
import { UserService } from './services/user'

// Default import
import UserService from './services/user'

// Namespace import
import * as UserModule from './services/user'

// Dynamic import
const UserService = await import('./services/user')
```

**검색 패턴:**
```
Grep: "from ['\"]\..*user"
Grep: "import.*from.*user"
```

### Python

```python
# Direct import
from services.user import UserService

# Module import
import services.user as user_module

# Relative import
from .user import UserService
from ..services import UserService
```

**검색 패턴:**
```
Grep: "from.*user.*import\|import.*user"
```

### Go

```go
import (
    "myapp/services/user"
    userSvc "myapp/services/user"
)
```

**검색 패턴:**
```
Grep: "import.*user\|\".*user\""
```

---

## 의존성 그래프 시각화

### 분석 결과 정리 형식

```markdown
## Dependency Map: UserService

### Upstream (의존)
| 모듈 | 용도 |
|------|------|
| `db/connection` | DB 연결 |
| `utils/validator` | 입력 검증 |
| `types/user` | 타입 정의 |

### Downstream (의존받음)
| 모듈 | 사용 함수 |
|------|----------|
| `api/users` | createUser, getUser |
| `api/auth` | validateUser |
| `jobs/cleanup` | deleteInactiveUsers |

### Shared Resources
| 자원 | 유형 |
|------|------|
| `users` 테이블 | Database |
| `REDIS_CACHE` | Cache |
| `AUTH_SECRET` | Env var |
```

---

## 분석 워크플로우

### Step 1: 타겟 파일 분석
```
Read: [target_file]
mcp__serena__get_symbols_overview: [target_file]
```

### Step 2: Upstream 파악
```
# 파일 상단 import 문 확인
Read: [target_file] (상단 20줄)
```

### Step 3: Downstream 파악
```
mcp__serena__find_referencing_symbols: [main_symbol]
# 또는
Grep: "import.*[module_name]\|from.*[module_name]"
```

### Step 4: Shared Resources 확인
```
# DB 접근
Grep: "SELECT\|INSERT\|UPDATE\|DELETE" --path [target_file]
Grep: "\.find\|\.create\|\.update\|\.delete" --path [target_file]

# 외부 API
Grep: "fetch\|axios\|requests\." --path [target_file]

# 환경 변수
Grep: "process\.env\|os\.environ\|getenv" --path [target_file]
```

---

## 위험 신호 탐지

### 순환 의존성
```
A → B → C → A (문제!)
```

**탐지 방법:**
1. A의 import 목록 확인
2. 각 import된 모듈이 A를 다시 import하는지 확인
```
mcp__serena__find_referencing_symbols로 역추적
```

### 높은 결합도
```
# 5개 이상의 모듈이 의존하면 변경 위험
Downstream 개수 > 5 → 🔴 High Risk
```

### God Object
```
# 너무 많은 책임을 가진 모듈
Upstream 개수 > 10 → 리팩토링 검토
```

---

## 체크리스트

의존성 분석 완료 확인:

- [ ] Upstream 모듈 목록 작성됨
- [ ] Downstream 모듈 목록 작성됨 (변경 영향 범위)
- [ ] Shared resources 식별됨
- [ ] 순환 의존성 확인됨
- [ ] 높은 결합도 영역 표시됨
