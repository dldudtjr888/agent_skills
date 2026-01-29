# claude-hud

## 아키텍처

```
Claude Code → stdin JSON (context_window, model, cwd)
           ↘ transcript_path → JSONL (도구/에이전트/TODO 파싱)
           ↘ config counting (MCP/rules/hooks)
           ↘ git status (branch/dirty/ahead-behind)
           ↘ OAuth API → usage limits (5h/7d 사용량)
           ↘ ~/.claude/plugins/claude-hud/config.json
                 ↓
           render() → stdout (멀티라인 HUD 출력)
```

## HUD 디스플레이 출력

```
[Opus | Pro] █████░░░░░ 45% | usage: 50% | ⏱️ 5m
project-name git:(main) | 2 CLAUDE.md | 3 MCPs | 1 hook
◐ Edit: auth.ts | ✓ Read ×3 | ✓ Grep ×2
◐ explore [haiku]: Finding auth code (2m 15s)
▸ Fix authentication bug (2/5)
```

## 레이아웃 모드

**Compact** (단일 라인): 모델 + 컨텍스트 바 + 프로젝트 + Git + 설정 카운트 + 사용량 + 세션 시간

**Expanded** (멀티 라인):
```
Line 1: Model/Context/Duration (identity)
Line 2: Project Path/Git Status (project)
Line 3: Config Counts (environment)
Line 4: Usage Limits (optional, usageBarEnabled=false일 때)
--- separator (optional) ---
Activity Lines: Tools / Agents / Todos
```

## 컨텍스트 추적

```typescript
// 우선순위 체인
1. 네이티브 퍼센트 (v2.1.6+) - 가장 정확, /context 출력과 일치
2. 수동 계산: (totalTokens / contextSize) * 100

// Autocompact Buffer
Raw percent + 22.5% 버퍼 (경험적 관찰값)
설정: display.autocompactBuffer: 'enabled' | 'disabled'

// 색상 코딩
< 70% → 녹색 (정상)
70-85% → 노란색 (주의)
> 85% → 빨간색 (위험, 토큰 브레이크다운 표시: "in: 45k, cache: 12k")
```

## 도구/에이전트 추적

**도구 표시**:
- 실행 중 (최근 2개): `◐ Read: auth.ts | ◐ Edit: config.ts`
- 완료 (상위 4개): `✓ Read ×3 | ✓ Grep ×2`
- 타겟 추출: Read/Write/Edit → file_path, Glob/Grep → pattern, Bash → command 앞 30자

**에이전트 표시**:
- 실행 중: `◐ explore [haiku]: Finding auth code (2m 15s)`
- 완료: `✓ refactor: Cleaned up imports (1m 30s)`
- 최대 3개 (실행 중 전부 + 최근 완료 2개)

## Git Status

```typescript
interface GitStatus {
  branch: string;       // git rev-parse --abbrev-ref HEAD
  isDirty: boolean;     // * 표시
  ahead: number;        // ↑X
  behind: number;       // ↓X
  fileStats?: {
    modified: number;   // !X
    added: number;      // +X
    deleted: number;    // ✘X
    untracked: number;  // ?X
  };
}
// 포맷: git:(main*) ↑2 ↓1 !3 +2 ✘1 ?5
// 커맨드당 1초 타임아웃 (느린 레포 방지)
```

## 사용량 제한 표시

**데이터 소스**: Anthropic OAuth API (`api.anthropic.com/api/oauth/usage`)
- macOS Keychain에서 OAuth 토큰 추출
- 5시간/7일 롤링 윈도우 사용량
- 캐싱: 성공 60초, 실패 15초, Keychain 실패 60초 백오프

**표시 로직**:
| 조건 | 표시 |
|------|------|
| 100% (제한 도달) | `⚠ Limit reached (resets 2h 30m)` (빨강) |
| API 불가 | `⚠` (노랑) |
| 임계값 이상 | `█████░░░░░ 50% (2h 30m / 5h)` |
| 7일 ≥ 80% | 양쪽 표시: `5h: 50% | 7d: 85%` |

## TODO 진행도 표시

| 상태 | 표시 |
|------|------|
| 진행 중 있음 | `▸ Fix authentication bug (2/5)` |
| 전부 완료 | `✓ All todos complete (5/5)` |
| 대기만 | 표시 없음 |

## 설정 옵션 (config.json)

```typescript
interface HudConfig {
  lineLayout: 'compact' | 'expanded';   // 기본: expanded
  showSeparators: boolean;              // 기본: false
  pathLevels: 1 | 2 | 3;               // 경로 세그먼트 (기본: 1)
  gitStatus: {
    enabled: boolean;                    // 기본: true
    showDirty: boolean;                  // 기본: true
    showAheadBehind: boolean;            // 기본: false
    showFileStats: boolean;              // 기본: false
  };
  display: {
    showModel: boolean;                  // 기본: true
    showContextBar: boolean;             // 기본: true
    showConfigCounts: boolean;           // 기본: true
    showDuration: boolean;               // 기본: true
    showTokenBreakdown: boolean;         // 기본: true
    showUsage: boolean;                  // 기본: true
    usageBarEnabled: boolean;            // 기본: true
    showTools: boolean;                  // 기본: true
    showAgents: boolean;                 // 기본: true
    showTodos: boolean;                  // 기본: true
    autocompactBuffer: 'enabled' | 'disabled';  // 기본: enabled
    usageThreshold: number;              // 최소 사용량 % (기본: 0)
    environmentThreshold: number;        // 최소 설정 카운트 (기본: 0)
  };
}
```

## plugin.json

```json
{
  "name": "claude-hud",
  "description": "Real-time statusline HUD for Claude Code - context health, tool activity, agent tracking, and todo progress",
  "version": "0.0.6",
  "author": { "name": "Jarrod Watts", "url": "https://github.com/jarrodwatts" },
  "homepage": "https://github.com/jarrodwatts/claude-hud",
  "license": "MIT",
  "keywords": ["hud", "monitoring", "statusline", "context", "tools", "agents", "todos"]
}
```
