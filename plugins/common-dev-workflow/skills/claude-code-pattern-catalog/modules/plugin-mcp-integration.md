# Plugin, MCP, Contexts 통합 패턴

## 11. Plugin Manifest System

### 11.1 디렉토리 구조

```
.claude-plugin/
├── plugin.json         # 플러그인 메타데이터
└── marketplace.json    # 마켓플레이스 등록 정보
```

### 11.2 plugin.json

```json
{
  "name": "plugin-name",
  "version": "3.7.5",
  "description": "플러그인 설명",
  "skills": "./skills/"
}
```

### 11.3 marketplace.json

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "short-name",
  "description": "마켓플레이스 표시 설명",
  "owner": {
    "name": "Author Name",
    "email": "email@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "상세 설명",
      "version": "3.7.5",
      "author": { "name": "Author", "email": "email" },
      "source": "./",
      "category": "productivity",
      "homepage": "https://github.com/...",
      "tags": ["multi-agent", "orchestration"]
    }
  ]
}
```

---

## 12. MCP Configuration Patterns

### 12.1 .mcp.json 구조 (claude-code-showcase)

```json
{
  "mcpServers": {
    "jira": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-jira"],
      "env": {
        "JIRA_HOST": "${JIRA_HOST}",
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
      }
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-github"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

### 12.2 MCP 서버 유형

| 유형 | 설정 방식 | 예시 |
|------|----------|------|
| **stdio** | `command` + `args` | github, jira, linear, sentry, postgres, slack, notion |
| **http** | `url` | vercel, cloudflare-docs, clickhouse |

### 12.3 주요 MCP 서버 카탈로그

| 서버 | 목적 | 출처 |
|------|------|------|
| `github` | PR, 이슈, 레포 관리 | showcase, everything |
| `jira` / `linear` | 이슈 트래킹 | showcase |
| `sentry` | 에러 모니터링 | showcase |
| `postgres` | DB 쿼리 | showcase |
| `slack` / `notion` | 커뮤니케이션/문서 | showcase |
| `memory` | 세션 간 메모리 | showcase, everything |
| `sequential-thinking` | 추론 체인 | everything |
| `firecrawl` | 웹 스크래핑 | everything |
| `supabase` | DB 서비스 | everything |
| `vercel` / `railway` | 배포 | everything |
| `cloudflare-*` | Edge 서비스 (docs, builds, bindings, observability) | everything |
| `context7` | 라이브 문서 | everything, moai |
| `magic` | UI 컴포넌트 | everything |

**컨텍스트 관리**: 프로젝트당 10개 미만 MCP 활성화, 총 80개 미만 도구 유지.

---

## 13. Contexts System

### 13.1 구조

```
.claude/contexts/
├── dev.md          # 개발 모드
├── review.md       # 코드 리뷰 모드
└── research.md     # 리서치 모드
```

### 13.2 dev.md (개발 모드)

```yaml
mode: "development"
focus: [코드 구현, 기능 개발, 버그 수정, 테스트]

behavior:
  - "코드 먼저 작성, 설명은 후"
  - "완벽보다 동작 우선"
  - "변경 후 테스트 실행"
  - "원자적 커밋"

priorities: [동작하게 → 올바르게 → 깔끔하게]

tools_preferred: [Read, Write, Edit, Bash, Grep, Glob]
tools_minimized: [WebSearch, WebFetch]

gates:
  - "코드 빌드 통과"
  - "테스트 통과"
  - "커버리지 감소 없음"
  - "새 취약점 없음"
```

### 13.3 review.md (리뷰 모드)

```yaml
mode: "review"
focus: [코드 품질, 보안 취약점, 성능 최적화, 유지보수성]

review_criteria:
  functionality: [의도 동작, 엣지 케이스, 에러 핸들링, 입력 검증]
  quality: [가독성, 네이밍, 복잡도, 중복]
  security: [입력 살균, 시크릿 관리, 인증/인가, OWASP]
  testing: [포괄성, 커버리지, 유지보수성, 엣지 케이스]
  performance: [명백한 성능 문제, DB 최적화, 캐싱, 알고리즘]

feedback_levels:
  "[CRITICAL]": "머지 전 반드시 수정"
  "[IMPORTANT]": "머지 전 수정 권장"
  "[SUGGESTION]": "개선 제안"
```

### 13.4 research.md (리서치 모드)

```yaml
mode: "research"
focus: [정보 수집, 개념 탐색, 아키텍처 연구, 기술 평가]

approach:
  breadth_first: "개요 → 핵심 개념 → 권위 있는 소스 → 전체 파악"
  depth_second: "상세 문서 → 코드 예제 → 구현 세부사항 → 대안 비교"
  synthesis: "핵심 패턴 → 모범 사례 → 접근법 비교 → 권고안"

tools_preferred: [WebSearch, WebFetch, Read, Grep, context7 MCP]
tools_minimized: [Write, Edit, Bash]

output: "발견사항 먼저, 권고사항 두 번째"
```

### 13.5 사용 방법

```bash
# 셸 별칭으로 모드 전환
alias claude-dev='claude --system-prompt "$(cat ~/.claude/contexts/dev.md)"'
alias claude-review='claude --system-prompt "$(cat ~/.claude/contexts/review.md)"'
alias claude-research='claude --system-prompt "$(cat ~/.claude/contexts/research.md)"'
```
