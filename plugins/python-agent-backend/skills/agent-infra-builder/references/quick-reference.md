# Quick Reference

에이전트 인프라 핵심 API 및 체크리스트 빠른 참조.

## 핵심 클래스 요약

### Guardrails

| 클래스 | 역할 |
|--------|------|
| `InputGuardrail` | 입력 검증 추상 클래스 |
| `OutputGuardrail` | 출력 검증 추상 클래스 |
| `GuardrailChain` | 가드레일 체인 실행기 |
| `GuardrailResult` | 개별 결과 |
| `AggregatedGuardrailResult` | 체인 전체 결과 |

### Handler

| 클래스 | 역할 |
|--------|------|
| `BaseHandler` | 핸들러 추상 클래스 (템플릿 메서드) |
| `SSEEvent` | SSE 이벤트 |
| `SSEEventType` | 이벤트 타입 enum |

### MCP

| 클래스 | 역할 |
|--------|------|
| `MCPServerPool` | MCP 서버 풀 (싱글톤) |
| `MCPServerStdio` | Stdio 기반 서버 |
| `MCPServerSse` | SSE 기반 서버 |

### Memory

| 클래스 | 역할 |
|--------|------|
| `MemoryManager` | 3-tier 메모리 관리자 |
| `MemoryStore` | 저장소 추상 클래스 |
| `SessionStore` | MySQL 세션 저장소 |
| `VectorStore` | 벡터 DB 저장소 |
| `AgentMemoryAdapter` | 에이전트 통합 어댑터 |
| `ContextAssembler` | 컨텍스트 조합기 |

### Prompt

| 클래스 | 역할 |
|--------|------|
| `ConfigLoader` | 프롬프트 로더 |
| `PromptVersionManager` | 버전 관리자 |
| `ABTestManager` | A/B 테스트 관리자 |
| `MessageBuilder` | 메시지 빌더 |

### LangGraph

| 클래스 | 역할 |
|--------|------|
| `StateGraph` | 그래프 빌더 |
| `CompiledStateGraph` | 컴파일된 그래프 |
| `Send` | 병렬 분기 생성 |

---

## 핵심 패턴

### Guardrail 체크

```python
chain = GuardrailChain(input_guardrails=[...], output_guardrails=[...])
result = await chain.check_input(content, context)
if result.blocked:
    # 차단 처리
message = result.final_content  # 수정된 메시지
```

### Handler 구현

```python
class MyHandler(BaseHandler):
    context_type = "my_context"

    async def _do_handle(self, message, context, session_id, trace_id, history):
        # 처리 로직
        yield SSEEvent.chunk_minimal("response")
```

### MCP 사용

```python
await MCPServerPool.register_config("mysql", config)
await MCPServerPool.warmup(["mysql"])
server = await MCPServerPool.get("mysql")
# 사용 후 직접 close 하지 않음
```

### Memory 사용

```python
manager = MemoryManager(cache, session, longterm)
await manager.save_conversation(user_input, agent_output, user_id, session_id)
context = await manager.get_context(query, user_id)
```

### Prompt 로드

```python
loader = get_config_loader()
prompt = loader.load_prompt("agents/mysql", variables={"db_host": "localhost"})
```

### LangGraph 빌드

```python
builder = StateGraph(WorkflowState)
builder.add_node("analyzer", analyzer_fn)
builder.add_edge(START, "analyzer")
builder.add_edge("analyzer", END)
graph = builder.compile()
```

---

## 통합 체크리스트

### 전체 흐름

- [ ] FastAPI lifespan에서 MCP 풀 초기화/종료
- [ ] Handler가 가드레일 체인 사용
- [ ] 메모리 매니저가 컨텍스트 제공
- [ ] 프롬프트 로더가 버전별 프롬프트 제공
- [ ] LangGraph 워크플로우가 스트리밍 지원

### Guardrails

- [ ] Blocking vs Non-blocking 구분
- [ ] Short-circuit 동작 확인
- [ ] Timeout 설정
- [ ] Fail-open 정책 (외부 API)

### Handler

- [ ] `handle()` 봉인, `_do_handle()` 오버라이드
- [ ] SSE 형식 준수
- [ ] 에러를 SSEEvent.error로 변환
- [ ] usage 이벤트 발송

### MCP

- [ ] 네임스페이스 격리
- [ ] 워밍으로 cold start 제거
- [ ] 헬스체크 및 복구
- [ ] 그레이스풀 셧다운

### Memory

- [ ] 3-tier 역할 구분
- [ ] 토큰 제한 관리
- [ ] 중복 제거
- [ ] 자동 승격

### Prompt

- [ ] current 버전 지정
- [ ] 변수 치환 동작
- [ ] 캐싱
- [ ] user_id 기반 A/B 테스트 일관성

### LangGraph

- [ ] State 불변성 (dict 반환)
- [ ] 병렬 결과 병합 (`Annotated[list, add]`)
- [ ] 모든 분기 케이스 처리
- [ ] 체크포인트 설정

---

## 에러 코드

| 코드 | 설명 |
|------|------|
| `guardrail_blocked` | 가드레일 차단 |
| `context_limit_exceeded` | 토큰 제한 초과 |
| `handler_error` | 핸들러 처리 에러 |
| `llm_error` | LLM 호출 에러 |
| `tool_error` | 도구 실행 에러 |
| `timeout` | 타임아웃 |

---

## Quick Commands

```bash
# 타입 체크
ty check core/

# 테스트
pytest tests/ -v

# 가드레일 테스트
pytest tests/guardrails/ -v

# MCP 상태 확인
curl http://localhost:8000/mcp/stats

# 프롬프트 버전 확인
cat prompts/orchestrator/supervisor.yaml | grep current
```
