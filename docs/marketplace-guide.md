# Claude Code 마켓플레이스 & 플러그인 가이드

> Claude Code 플러그인 시스템의 구조, 컴포넌트, 설정 방법에 대한 종합 가이드

## 목차

- [마켓플레이스가 관리하는 컴포넌트](#마켓플레이스가-관리하는-컴포넌트)
- [카테고리별 분리 관리](#카테고리별-분리-관리)
- [plugin.json 스펙](#pluginjson-스펙)
- [marketplace.json 스펙](#marketplacejson-스펙)
- [레포지토리 구조](#레포지토리-구조)
- [공식 문서](#공식-문서)

---

## 마켓플레이스가 관리하는 컴포넌트

마켓플레이스는 **6가지 컴포넌트**를 포함하는 플러그인을 관리할 수 있습니다.

| 컴포넌트 | 기본 디렉토리 | 설명 |
|---------|-------------|------|
| **Skills** | `skills/` | Agent Skills (SKILL.md 구조, 모델이 자동 호출) |
| **Agents** | `agents/` | 전문화된 서브에이전트 정의 |
| **Hooks** | `hooks/hooks.json` | 이벤트 핸들러 (PreToolUse, PostToolUse, SessionStart 등) |
| **Commands** | `commands/` | 슬래시 커맨드 (`.md` 파일) |
| **MCP Servers** | `.mcp.json` | Model Context Protocol 서버 (외부 도구/API 연결) |
| **LSP Servers** | `.lsp.json` | Language Server Protocol (코드 인텔리전스) |

### 컴포넌트 설명

#### Skills
- `SKILL.md` 파일로 정의
- 모델이 상황에 맞게 자동으로 호출
- `references/`, `assets/` 폴더로 추가 리소스 제공 가능

#### Agents
- 전문화된 서브에이전트 정의
- 특정 도메인/작업에 최적화된 에이전트 생성

#### Hooks
- 이벤트 기반 자동화
- PreToolUse, PostToolUse, SessionStart, Stop 등 지원

#### Commands
- `/command-name` 형태로 사용자가 직접 호출
- `.md` 파일로 프롬프트 정의

#### MCP Servers
- 외부 API, 데이터베이스, 서비스 연결
- 도구(tools) 형태로 Claude에게 제공

#### LSP Servers
- 코드 자동완성, 정의 이동, 참조 찾기 등
- IDE 수준의 코드 인텔리전스 제공

---

## 카테고리별 분리 관리

하나의 마켓플레이스에서 여러 플러그인을 카테고리별로 분리 관리할 수 있습니다.

### 디렉토리 구조 예시

```
marketplace/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── frontend-tools/           # 프론트엔드 플러그인
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   ├── agents/
│   │   ├── hooks/
│   │   ├── commands/
│   │   └── .mcp.json
│   │
│   ├── python-backend/           # Python 백엔드 플러그인
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   ├── agents/
│   │   ├── hooks/
│   │   ├── commands/
│   │   └── .mcp.json
│   │
│   └── devops-tools/             # DevOps 플러그인
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/
│       └── hooks/
├── docs/                         # 문서 (플러그인에 영향 없음)
├── README.md
└── LICENSE
```

### marketplace.json 설정

```json
{
  "name": "company-tools",
  "owner": {
    "name": "DevTools Team",
    "email": "devtools@example.com"
  },
  "plugins": [
    {
      "name": "frontend-tools",
      "source": "./plugins/frontend-tools",
      "description": "React, Next.js, CSS 관련 도구",
      "category": "frontend",
      "tags": ["react", "nextjs", "css", "ui"]
    },
    {
      "name": "python-backend",
      "source": "./plugins/python-backend",
      "description": "FastAPI, Django, SQLAlchemy 도구",
      "category": "backend",
      "tags": ["python", "fastapi", "django", "api"]
    },
    {
      "name": "devops-tools",
      "source": "./plugins/devops-tools",
      "description": "CI/CD, Docker, Kubernetes 도구",
      "category": "devops",
      "tags": ["docker", "kubernetes", "ci-cd"]
    }
  ]
}
```

---

## plugin.json 스펙

각 플러그인의 `.claude-plugin/plugin.json` 파일 구조입니다.

### 필수 필드

```json
{
  "name": "my-plugin"
}
```

### 전체 스펙

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "플러그인 설명",
  "author": {
    "name": "Developer Name",
    "email": "dev@example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/user/plugin",
  "license": "MIT",
  "keywords": ["tag1", "tag2"],

  "commands": ["./custom/commands/", "./special.md"],
  "agents": "./custom/agents/",
  "skills": "./custom/skills/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/"
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|-----|------|-----|------|
| `name` | string | O | 플러그인 식별자 |
| `version` | string | X | 시맨틱 버전 |
| `description` | string | X | 플러그인 설명 |
| `author` | object | X | 작성자 정보 |
| `homepage` | string | X | 문서/홈페이지 URL |
| `repository` | string | X | Git 저장소 URL |
| `license` | string | X | 라이선스 |
| `keywords` | array | X | 검색 키워드 |
| `commands` | string/array | X | 커맨드 경로 |
| `agents` | string | X | 에이전트 경로 |
| `skills` | string | X | 스킬 경로 |
| `hooks` | string | X | 훅 설정 경로 |
| `mcpServers` | string | X | MCP 서버 설정 경로 |
| `lspServers` | string | X | LSP 서버 설정 경로 |

---

## marketplace.json 스펙

마켓플레이스의 `.claude-plugin/marketplace.json` 파일 구조입니다.

### 필수 필드

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "Organization Name",
    "email": "contact@example.com"
  },
  "plugins": []
}
```

### 전체 스펙

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "Organization Name",
    "email": "contact@example.com"
  },
  "metadata": {
    "description": "마켓플레이스 설명",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "플러그인 설명",
      "category": "category-name",
      "tags": ["tag1", "tag2"],
      "keywords": ["keyword1"],
      "strict": false,

      "skills": "./skills/",
      "agents": "./agents/",
      "hooks": "./hooks/hooks.json",
      "commands": "./commands/",
      "mcpServers": "./.mcp.json",
      "lspServers": "./.lsp.json"
    }
  ]
}
```

### 플러그인 소스 옵션

```json
{
  "plugins": [
    {
      "name": "local-plugin",
      "source": "./plugins/local"
    },
    {
      "name": "github-plugin",
      "source": {
        "source": "github",
        "repo": "owner/plugin-repo",
        "ref": "v2.0.0",
        "sha": "a1b2c3d4e5f6..."
      }
    },
    {
      "name": "gitlab-plugin",
      "source": {
        "source": "url",
        "url": "https://gitlab.com/team/plugin.git",
        "ref": "main"
      }
    }
  ]
}
```

---

## 레포지토리 구조

### 요구사항

플러그인 레포지토리의 **유일한 필수 요건**:
- `.claude-plugin/plugin.json` 또는 `.claude-plugin/marketplace.json` 파일 존재

### 플러그인과 무관한 파일

다음 파일/폴더는 **플러그인 기능에 영향을 주지 않으며** 자유롭게 추가 가능합니다:

- `README.md` - 사용법 설명
- `LICENSE` - 라이선스 정보
- `CHANGELOG.md` - 버전 히스토리
- `docs/` - 상세 문서
- `examples/` - 예제 코드
- 기타 문서화 파일

### 올바른 구조

```
plugin-repo/
├── .claude-plugin/
│   └── plugin.json          ← 필수 (내부에 위치)
├── skills/                   ← 플러그인 루트에 위치
├── agents/                   ← 플러그인 루트에 위치
├── hooks/                    ← 플러그인 루트에 위치
├── commands/                 ← 플러그인 루트에 위치
├── .mcp.json                 ← 플러그인 루트에 위치
├── docs/                     ← 문서 (선택)
├── README.md                 ← 선택
└── LICENSE                   ← 선택
```

### 주의사항

**하지 말아야 할 것:**
- 컴포넌트 폴더(`skills/`, `agents/` 등)를 `.claude-plugin/` **내부**에 넣기

**올바른 예:**
```
plugin/
├── .claude-plugin/
│   └── plugin.json           # 설정만 여기에
├── skills/                    # 컴포넌트는 루트에
└── hooks/
```

**잘못된 예:**
```
plugin/
├── .claude-plugin/
│   ├── plugin.json
│   ├── skills/               # ❌ 잘못된 위치
│   └── hooks/                # ❌ 잘못된 위치
```

---

## 공식 문서

- [마켓플레이스 생성](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [플러그인 레퍼런스](https://code.claude.com/docs/en/plugins-reference.md)
- [플러그인 생성](https://code.claude.com/docs/en/plugins.md)

---

*최종 업데이트: 2026-01-29*
