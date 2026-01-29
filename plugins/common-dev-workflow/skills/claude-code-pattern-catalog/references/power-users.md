# claude-code-for-power-users

## Hidden 환경 변수

**성능 최적화**:
| 변수 | 값 | 효과 |
|------|---|------|
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `1` | 불필요한 네트워크 트래픽 비활성화 |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS` | `1` | 비필수 모델 호출 비활성화 |
| `ENABLE_BACKGROUND_TASKS` | `1` | 백그라운드 작업 활성화 |
| `FORCE_AUTO_BACKGROUND_TASKS` | `1` | 자동 백그라운드 작업 강제 |
| `CLAUDE_CODE_ENABLE_UNIFIED_READ_TOOL` | `1` | 통합 Read 도구 활성화 |

**Extended Thinking**:
| 변수 | 값 | 효과 |
|------|---|------|
| `MAX_THINKING_TOKENS` | `50000` | 최대 사고 토큰 설정 |

**프라이버시**:
| 변수 | 값 | 효과 |
|------|---|------|
| `DISABLE_TELEMETRY` | `1` | 텔레메트리 비활성화 |
| `DISABLE_ERROR_REPORTING` | `1` | 에러 리포팅 비활성화 |

**디버깅**:
| 변수 | 값 | 효과 |
|------|---|------|
| `CLAUDE_CODE_DEBUG` | `1` | 디버그 모드 |
| `CLAUDE_CODE_VERBOSE_LOGGING` | `1` | 상세 로깅 |

**컨테이너 모드**:
| 변수 | 값 | 효과 |
|------|---|------|
| `CLAUDE_CODE_CONTAINER_MODE` | `1` | 컨테이너 모드 활성화 |
| `BYPASS_ALL_CONFIRMATIONS` | `1` | 모든 확인 우회 |

## CLI 플래그

**컨텍스트 관리**:
```bash
--scope="src/components,src/hooks"   # 특정 디렉토리로 컨텍스트 제한
--exclude="node_modules,dist,build"  # 불필요한 디렉토리 제외
--include="*.ts,*.tsx"               # 특정 파일 타입만 포함
--add-dir="../lib,../shared"         # 관련 프로젝트 디렉토리 추가
--clear-context                       # 대화 히스토리 초기화
--rescan-project                      # 프로젝트 재스캔
--max-context=50000                   # 컨텍스트 윈도우 크기 제한
```

**출력 제어**:
```bash
--output-format=json           # 구조화된 JSON 출력
--output-format=stream-json    # 스트리밍 JSON (장시간 작업용)
--output-format=text           # 텍스트 출력 (기본값)
-p                             # 프린트 모드 (비대화형, 단발 쿼리)
```

**세션 관리**:
```bash
--session="frontend"    # 명명된 세션 생성/작업
--resume="backend"      # 이전 세션 재개
-c                      # 마지막 세션 계속
```

**보안 & 권한**:
```bash
--allowedTools "Edit,View,mcp__git__*"       # 허용 도구 지정
--dangerously-skip-permissions                # 모든 권한 프롬프트 우회 (컨테이너용)
--confirmation-required "git push origin main" # 특정 명령 확인 필요
```

**MCP & 디버깅**:
```bash
--mcp-debug    # MCP 서버 디버깅
--headless     # 비대화형 모드
--verbose      # 상세 실행 로깅
--model opus   # 모델 직접 지정
```

## TDD 4단계 워크플로우 패턴

```
Phase 1: PLAN (계획)
  - 요구사항 분석
  - API 인터페이스 설계
  - 엣지 케이스/에러 시나리오 식별
  - 코드 작성 금지

Phase 2: TEST (테스트)
  - 단위 테스트 작성 (성공, 실패, 엣지 케이스)
  - 통합 테스트 작성
  - 모든 테스트가 적절히 실패하는지 확인

Phase 3: IMPLEMENTATION (구현)
  - 모든 테스트 통과하도록 코드 구현
  - SOLID 원칙 및 DI 패턴 적용
  - 적절한 에러 핸들링 추가

Phase 4: REFACTOR (리팩터링)
  - 코드 개선점 리뷰
  - 공통 패턴 추출
  - 문서화 추가
  - 최종 테스트 실행
```

## Extended Thinking 사용 패턴

| 수준 | 키워드 | 용도 |
|------|--------|------|
| 기본 | `think` | 복잡한 아키텍처 결정, 코드 설계 패턴 |
| 강화 | `think hard` | 보안 분석, 성능 최적화, 복잡한 디버깅 |
| 최대 | `ultrathink` | 시스템 전체 리팩터링, 핵심 비즈니스 로직, 고위험 결정 |

## 구조화된 문제 해결 프롬프트 패턴

```
CONTEXT: 프로젝트 범위 정의
CONSTRAINTS: 제한사항/요구사항 목록
GOAL: 원하는 결과 명시
FORMAT: 출력 기대치 정의
EXAMPLES: 유사 사례 제공
VALIDATION: 성공 기준 설명
```

## Git Worktree 병렬 개발

```bash
git worktree add ../feature-auth feature/authentication
git worktree add ../feature-ui feature/ui-redesign
# 각 worktree에서 독립적으로 Claude Code 실행 가능
```

## 슬래시 명령어 (power-users)

| 명령어 | 목적 |
|--------|------|
| `/security-audit` | 종합 보안 감사 |
| `/performance-audit` | 성능 분석 |
| `/architecture-review` | 시스템 아키텍처 평가 |
| `/gemini-analyze` | Gemini로 대규모 컨텍스트 분석 |
| `/ast-analyze` | AST-Grep 구조적 분석 |
| `/tech-debt` | 기술 부채 평가 |

## 오디오 알림 (Mac)

```bash
say "Task completed successfully"
say "I need your confirmation"
say "Ready for review" --voice=Samantha
say "Error encountered - check output" --rate=150
osascript -e 'display notification "Claude task finished" with title "Development Update"'
```
