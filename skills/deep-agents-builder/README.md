# Deep Agents Builder Skill

LangChain **Deep Agents**로 복잡한 멀티스텝 에이전트를 구축하는 종합 가이드 스킬입니다.

> **버전**: 3.0.0 (deepagents 0.3.8 기준)
> **최종 업데이트**: 2026-01-23

## 개요

Deep Agents는 Claude Code, Deep Research 같은 애플리케이션을 구축하기 위한 에이전트 하네스입니다.
LangGraph 기반으로 다음 핵심 기능을 제공합니다:

1. **Planning Tool**: 작업 분해 및 추적 (`write_todos`, `read_todos`)
2. **Filesystem**: 컨텍스트 관리 및 메모리 (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute`)
3. **Subagents**: 전문화된 하위 에이전트 위임 (`task`)
4. **Human-in-the-Loop**: 민감한 도구 승인 워크플로우
5. **Long-term Memory**: 대화 간 영속 메모리

## 트리거 조건

이 스킬은 다음 키워드에 자동 활성화됩니다:
- "deep agents", "deepagents"
- "langchain agent", "langchain 에이전트"
- "에이전트 빌더", "agent builder"
- "서브에이전트", "subagent"
- "에이전트 미들웨어", "middleware"
- "deepagents CLI"
- "에이전트 영속 메모리"

## 스킬 구조

```
deep-agents-builder/
├── SKILL.md              # 메인 스킬 (요약 가이드)
├── README.md             # 이 파일
└── references/
    ├── 01-quickstart.md  # 설치, CLI, 첫 에이전트
    ├── 02-core-concepts.md # 4가지 핵심 구성요소
    ├── 03-api-reference.md # API 상세 (새 파라미터 포함)
    ├── 04-middleware.md    # 7개 미들웨어 스택
    ├── 05-subagents.md     # 서브에이전트 설계
    ├── 06-backends.md      # StateBackend, StoreBackend, CompositeBackend
    ├── 07-naviseoai-integration.md  # naviseoAI 프로젝트 통합
    ├── 08-hitl-memory.md   # Human-in-the-Loop, 장기 메모리
    ├── 09-mcp-integration.md    # MCP 도구 통합
    ├── 10-langsmith-production.md # LangSmith 배포/모니터링
    └── 11-debugging-testing.md   # 디버깅 및 테스트
```

## 주요 업데이트 (v3.0.0)

### deepagents 0.3.x 새 기능

| 버전 | 기능 |
|------|------|
| **0.3.8** | Tool truncation for execute, unique thread IDs for summarization |
| **0.3.7** | **Summarization offloading**, SystemMessage support, file truncation in history |
| **0.3.6** | Agent naming improvements, **subagent output validation** |
| **0.3.5** | Memory functionality ported to CLI |
| **0.3.4** | Memory prompt streamlined, **permissive AGENTS.md handling** |

### 주요 변경사항

- **Summarization Offloading** (0.3.7): 대용량 컨텍스트 요약을 비동기 처리하여 성능 향상
- **SystemMessage Support** (0.3.7): LangChain SystemMessage 직접 지원
- **Tool Output Truncation** (0.3.8): execute 도구 출력 자동 잘라내기
- **Subagent Validation** (0.3.6): 서브에이전트 출력 유효성 자동 검증
- **Permissive AGENTS.md** (0.3.4): AGENTS.md 파일 없어도 에러 없이 진행

---

## 이전 업데이트 (v2.0.0)

### 새로운 API 파라미터
- `checkpointer`: 상태 영속화 (HITL 필수)
- `store`: LangGraph Store (장기 메모리)
- `response_format`: 구조화된 출력
- `context_schema`: 커스텀 상태 스키마
- `debug`, `name`, `cache`: 추가 옵션

### 7개 미들웨어 스택
1. TodoListMiddleware
2. FilesystemMiddleware
3. SubAgentMiddleware
4. SummarizationMiddleware (170k 토큰 자동 압축)
5. AnthropicPromptCachingMiddleware
6. PatchToolCallsMiddleware
7. HumanInTheLoopMiddleware

### 새로운 백엔드
- StateBackend (기본, 임시)
- FilesystemBackend (로컬 디스크)
- StoreBackend (LangGraph Store, 영속)
- CompositeBackend (경로별 라우팅)

### DeepAgents CLI
- 영속 메모리 (`~/.deepagents/AGENT_NAME/memories/`)
- Human-in-the-Loop 기본 지원
- 다중 에이전트 관리

### MCP 도구 통합
- `langchain-mcp-adapters`를 통한 MCP 서버 연결
- `MultiServerMCPClient`로 다중 MCP 서버 동시 사용
- stdio, http, streamable_http 트랜스포트 지원

### LangSmith 배포/모니터링
- LangGraph Platform 배포
- LangSmith 추적 및 평가
- Polly AI 기반 디버깅
- LangSmith Fetch CLI

### 디버깅 및 테스트
- `debug=True` 모드
- 스트리밍 이벤트 디버깅
- pytest 기반 단위/통합 테스트
- Mock LLM/Tool 테스트

## 참고 자료

- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [Deep Agents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [API Reference](https://reference.langchain.com/python/deepagents/)
- [DeepAgents CLI Blog](https://blog.langchain.com/introducing-deepagents-cli/)
- [LangChain Changelog](https://changelog.langchain.com/)
- [DeepAgents Quickstarts](https://github.com/langchain-ai/deepagents-quickstarts)

## 작성자

- **작성자**: Claude
- **최초 작성일**: 2025-12-18
- **마지막 업데이트**: 2026-01-23
- **버전**: 3.0.0
