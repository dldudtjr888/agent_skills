# Deep Agents Builder Skill

LangChain **Deep Agents**로 복잡한 멀티스텝 에이전트를 구축하는 종합 가이드 스킬입니다.

## 개요

Deep Agents는 Claude Code, Deep Research 같은 애플리케이션을 구축하기 위한 에이전트 하네스입니다.
LangGraph 기반으로 다음 4가지 핵심 기능을 제공합니다:

1. **Planning Tool**: 작업 분해 및 추적
2. **Filesystem**: 컨텍스트 관리 및 메모리
3. **Subagents**: 전문화된 하위 에이전트 위임
4. **Shell Access**: 셸 명령어 실행

## 트리거 조건

이 스킬은 다음 키워드에 자동 활성화됩니다:
- "deep agents", "deepagents"
- "langchain agent", "langchain 에이전트"
- "에이전트 빌더", "agent builder"
- "서브에이전트", "subagent"
- "에이전트 미들웨어", "middleware"

## 스킬 구조

```
deep-agents-builder/
├── SKILL.md              # 메인 스킬 (요약 가이드)
├── README.md             # 이 파일
└── references/
    ├── 01-quickstart.md  # 설치 및 첫 에이전트
    ├── 02-core-concepts.md # 4가지 핵심 구성요소
    ├── 03-api-reference.md # API 상세
    ├── 04-middleware.md    # 미들웨어 패턴
    ├── 05-subagents.md     # 서브에이전트 설계
    ├── 06-backends.md      # 백엔드 옵션
    └── 07-naviseoai-integration.md  # naviseoAI 프로젝트 통합
```

## 참고 자료

- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [Deep Agents Docs](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents Blog](https://blog.langchain.com/deep-agents/)
- [DeepAgents Quickstarts](https://github.com/langchain-ai/deepagents-quickstarts)

## 작성자

- **작성자**: Claude
- **작성일**: 2025-12-18
- **버전**: 1.0.0