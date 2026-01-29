# Hook 공통 패턴

### 5.1 Hook 이벤트 유형 (전체)

| 이벤트 | 시점 | 주요 용도 | 출처 |
|--------|------|----------|------|
| **UserPromptSubmit** | 사용자 입력 전송 시 | 스킬 자동 추천, 키워드 감지, 매직 키워드 | 전체 |
| **SessionStart** | 세션 시작 시 | 컨텍스트 로드, 초기화, 프로젝트 정보 표시 | omc, everything, moai |
| **Setup** | 초기 설정 시 | 원타임 초기화, 유지보수 모드 | omc |
| **PreToolUse** | 도구 실행 전 | 보안 검증, main 브랜치 보호, 위임 규칙 | infra, moai, showcase |
| **PermissionRequest** | 권한 요청 시 | 스마트 Bash 권한 처리 | omc |
| **PostToolUse** | 도구 실행 후 | 코드 포매팅, 린팅, 타입체크, AST 스캔 | 전체 |
| **SubagentStart** | 서브에이전트 시작 시 | 활성 서브에이전트 추적 | omc |
| **SubagentStop** | 서브에이전트 종료 시 | 서브에이전트 추적 완료 | omc |
| **PreCompact** | 컨텍스트 압축 전 | 상태 저장, 압축 준비 | omc, everything |
| **Stop** | Claude 응답 완료 시 | TTS, 지속 모드, 빌드 체크, console.log 감사 | 전체 |
| **SessionEnd** | 세션 종료 시 | 상태 저장, 정리, 패턴 추출, 랭크 제출 | omc, everything, moai |

### 5.2 settings.json Hook 설정 패턴

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/skill-activation-prompt.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/security-guard.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/code-formatter.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/stop-handler.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### 5.3 필수 Hook 조합 (infrastructure-showcase 기반)

스킬 자동 활성화를 위한 최소 구성:

1. **skill-activation-prompt** (UserPromptSubmit)
   - skill-rules.json 읽기 → 키워드/의도 매칭 → 스킬 추천 주입

2. **post-tool-use-tracker** (PostToolUse)
   - 편집된 파일 추적 → 프로젝트 구조 감지 → 컨텍스트 캐시 유지

---

## Hook Script 언어 패턴

### 17.1 지원 언어

| 언어 | 확장자 | 용도 | 출처 |
|------|--------|------|------|
| **JavaScript/Node.js** | `.js`, `.mjs` | 크로스 플랫폼 훅, 세션 관리 | everything-claude-code |
| **Python 3** | `.py` | LSP 통합, 품질 게이트, 보안 검사 | moai-adk |
| **Shell (Bash)** | `.sh` | 스킬 활성화, 관찰 수집, 간단한 자동화 | infrastructure, everything |
| **TypeScript** | `.ts` | 복잡한 훅 로직 (컴파일 필요) | oh-my-claudecode |

### 17.2 Hook Script 공통 패턴

```python
#!/usr/bin/env python3
"""Hook 설명 및 목적.

Matcher: Write|Edit
Exit Codes:
  0: 성공
  1: 에러 (실행 차단)
  2: 주의 필요 (Claude에게 피드백)
"""

import sys
import json

# stdin으로 도구 호출 정보 수신
input_data = json.loads(sys.stdin.read())

# 로직 실행
# ...

# stderr로 Claude에게 메시지 전달
print("피드백 메시지", file=sys.stderr)
sys.exit(0)  # 0: 성공, 1: 차단, 2: 주의
```

### 17.3 주요 Hook Script 예시 (moai-adk)

| 스크립트 | 이벤트 | 목적 |
|---------|--------|------|
| `session_start__show_project_info.py` | SessionStart | Git 상태, SPEC 진행도, 버전 표시 |
| `post_tool__lsp_diagnostic.py` | PostToolUse (Write\|Edit) | LSP 진단 자동 실행 |
| `post_tool__code_formatter.py` | PostToolUse (Write\|Edit) | 코드 자동 포매팅 |
| `post_tool__ast_grep_scan.py` | PostToolUse (Write\|Edit) | AST 기반 보안 스캔 |
| `pre_tool__security_guard.py` | PreToolUse | 실행 전 보안 검사 |
| `quality_gate_with_lsp.py` | PreSync | Ralph 스타일 품질 게이트 |
| `stop__loop_controller.py` | Stop | 루프 방지 가드 |
| `session_end__rank_submit.py` | SessionEnd | 세션 메트릭 제출 |
