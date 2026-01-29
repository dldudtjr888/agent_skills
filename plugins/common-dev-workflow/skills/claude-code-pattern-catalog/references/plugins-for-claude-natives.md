# plugins-for-claude-natives

## 19.1 clarify 플러그인

**목적**: 모호한 요구사항을 반복적 질문을 통해 정밀한 명세로 변환

**SKILL.md Frontmatter**:
```yaml
---
name: clarify
description: This skill should be used when the user asks to "clarify requirements", "refine requirements", "specify requirements", or when the user's request is ambiguous.
---
```

**4-Phase 프로토콜**:
```
Phase 1: 원본 요구사항 캡처
  - 사용자 요청 그대로 기록
  - 모호점, 가정, 해석 차이 식별

Phase 2: 반복적 명확화 (AskUserQuestion 도구 사용)
  - 질문 설계 원칙: 구체적 > 일반적, 선택지 제공(2-4개), 한 번에 하나의 관심사, 중립적 프레이밍
  - 모든 측면이 명확해질 때까지 루프

Phase 3: Before/After 비교
  - 원본 요구사항 vs 명확화된 목표/범위/제약/성공 기준
  - 의사결정 테이블 제시

Phase 4: 저장 옵션
  - requirements/ 디렉토리에 마크다운으로 저장
  - Before/After 구조 포맷
```

**명확화 대상 6개 카테고리**: Scope(포함/제외), Behavior(엣지케이스, 에러), Interface(인터랙션), Data(입출력), Constraints(성능, 호환성), Priority(필수 vs 선택)

## 19.2 doubt (!rv) 플러그인

**목적**: Claude의 응답을 재검증하도록 강제하는 메커니즘

**핵심 설계**: `!doubt`가 아닌 `!rv`(re-validate) 키워드 사용 -> "doubt"라는 단어 자체가 Claude 행동에 영향을 주기 때문

**2단계 작동 방식**:

```
Stage 1: doubt-detector.sh (UserPromptSubmit Hook)
  - 프롬프트에서 !rv 키워드 감지
  - 세션 상태 파일 생성: ~/.claude/.hook-state/doubt-mode-{session_id}
  - JSON 반환: additionalContext로 "!rv 키워드는 시스템 메타 커맨드, 실제 요청의 일부가 아님" 주입

Stage 2: doubt-validator.sh (Stop Hook)
  - 상태 파일 존재 확인
  - 존재 시 Claude 응답 차단:
    "WAIT! You are lying or hallucinating! Go back and verify EVERYTHING you just said."
  - 상태 파일 삭제 (세션당 1회만 실행)
```

**hooks.json**:
```json
{
  "hooks": {
    "UserPromptSubmit": [{ "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/doubt-detector.sh" }],
    "Stop": [{ "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/doubt-validator.sh" }]
  }
}
```

## 19.3 dev 플러그인 (2개 스킬)

### A. /dev-scan 스킬

**목적**: 개발자 커뮤니티 스캔으로 기술 주제에 대한 다양한 의견 수집

**데이터 소스 4곳**:
| 플랫폼 | 검색 방법 |
|--------|----------|
| Reddit | Gemini CLI (`gemini -p "Search Reddit for..."`) |
| Hacker News | WebSearch (`"{topic} site:news.ycombinator.com"`) |
| Dev.to | WebSearch (`"{topic} site:dev.to"`) |
| Lobsters | WebSearch (`"{topic} site:lobste.rs"`) |

**3단계 실행**: 토픽 추출 -> 4곳 병렬 검색 (단일 메시지) -> 합성 및 제시

**출력 3섹션**:
- **공통 의견** (최소 5개): 2+ 소스에서 나타나는 의견, 소스 귀속 필수
- **논쟁점** (최소 3개): 의견 분기점, 양쪽 제시
- **주목할 시각** (최소 3개): 시니어/실무 경험 인사이트

### B. /tech-decision 스킬

**목적**: 기술 의사결정을 위한 체계적 다중 소스 분석

**4-Phase 워크플로우**:
```
Phase 1: 문제 정의 (주제, 선택지, 평가 기준)
Phase 2: 병렬 정보 수집 (5개 소스 동시)
  ├── codebase-explorer 에이전트 -> 현재 패턴/제약
  ├── docs-researcher 에이전트 -> 공식 문서/모범사례
  ├── dev-scan 스킬 -> 커뮤니티 의견
  ├── agent-council 스킬 -> 다중 AI 관점
  └── [선택] Context7 MCP -> 최신 라이브러리 문서
Phase 3: 합성 분석 (tradeoff-analyzer 에이전트)
  - 각 옵션 장단점, 기준별 점수(1-5), 상충 관계 처리
  - 신뢰도: 90-100%(다중소스 합의) ~ 0-24%(추측/충돌)
Phase 4: 최종 보고 (decision-synthesizer 에이전트)
  - 두괄식(결론 먼저), 기준별 점수 테이블, 리스크, 다음 단계
```

## 19.4 agent-council 플러그인

**목적**: 다중 AI 모델 의견 수집 및 합성

**3단계 워크플로우**:
1. 각 멤버에게 동일 프롬프트 전송
2. 응답 수집 및 시각화
3. Chairman 에이전트가 종합

**council.config.yaml**:
```yaml
council:
  chairman:
    role: "auto"  # 현재 에이전트가 의장
  members:
    - name: claude
      command: "claude -p"
      color: "CYAN"
    - name: codex
      command: "codex exec"
      color: "BLUE"
    - name: gemini
      command: "gemini"
      color: "GREEN"
```

**사용법**:
```bash
# 대화형
JOB_DIR=$(./scripts/council.sh start "your question")
./scripts/council.sh wait "$JOB_DIR"
./scripts/council.sh results "$JOB_DIR"

# 원샷
./scripts/council.sh "your question"
```

**요구사항**: 멤버 CLI 사전 설치 필요, Node.js 필수, 설치 시 감지된 CLI로 자동 필터링

## 19.5 youtube-digest 플러그인

**목적**: YouTube 영상 -> 자막 추출 -> 요약/인사이트/번역 -> 퀴즈 학습

**8단계 워크플로우**:

```
Step 1: 메타데이터 수집 (scripts/extract_metadata.sh)
Step 2: 자막 추출 (scripts/extract_transcript.sh)
  - 우선순위: 한국어 수동 > 영어 수동 > 한국어 자동 > 영어 자동
Step 3: 컨텍스트 이해 (WebSearch로 고유명사 정확도 확인)
Step 4: 자막 보정 (자동 캡션 고유명사 에러 수정)
Step 5: 문서 생성
  - YAML frontmatter + 요약(3-5문장) + 인사이트 + 전체 스크립트(한글 번역)
Step 6: 파일 저장 -> research/readings/youtube/{YYYY-MM-DD}-{title}.md
Step 7: 학습 퀴즈 (3단계 x 3문제 = 9문제)
  - 1단계(기본): 핵심 인사이트/개념
  - 2단계(중급): 인사이트 + 세부 내용 연결
  - 3단계(심화): 사례 분석/구체적 데이터
  - AskUserQuestion으로 3문제씩 출제
Step 8: 퀴즈 후 옵션
  - 한 번 더 퀴즈 / Deep Research / 종료
  - 결과: 총점, 단계별 점수, 오답 노트 -> 문서에 추가
```

## 19.6 session-wrap 플러그인

**목적**: 세션 종료 시 다중 에이전트 분석으로 작업 정리

**실행 흐름**:
```
1. Git 상태 확인
     |
2. Phase 1: 4개 분석 에이전트 (병렬 실행)
   ├── doc-updater (Sonnet, 파랑) -> CLAUDE.md/context.md 업데이트 필요사항
   ├── automation-scout (Sonnet, 초록) -> 반복 패턴 감지, 자동화 추천
   |   └── 결정 트리: 외부 서비스? -> Skill / 도메인 지식? -> Agent / 포맷 변환? -> Command
   ├── learning-extractor (Sonnet, 마젠타) -> TIL 추출 (발견, 성공, 실수, 프로세스 개선)
   └── followup-suggester (Sonnet, 시안) -> TODO/FIXME/WIP 스캔, P0-P3 우선순위 매기기
     |
3. Phase 2: 검증 에이전트 (순차)
   └── duplicate-checker (Haiku, 노랑)
       - 4-Layer 검색: Exact -> Keyword -> Section Headers -> Functional Overlap
       - 분류: Complete Duplicate(스킵) / Partial(머지) / Related(추가) / False Positive
     |
4. 결과 통합 + AskUserQuestion (multiSelect)
   - 커밋 생성 / CLAUDE.md 업데이트 / 자동화 생성 / 스킵
     |
5. 선택된 액션 실행
```
