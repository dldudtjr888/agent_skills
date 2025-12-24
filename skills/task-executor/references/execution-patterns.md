# Execution Patterns

Wave별 병렬 실행 패턴 상세 가이드.

## 기본 실행 패턴

### Wave 순차, 태스크 병렬

```
Wave 1: ─────────────────────────────────────►
        ├─ T-001 (agent 1) ──────►
        ├─ T-002 (agent 2) ────►
        └─ T-003 (agent 3) ──────────►
                                     │
                              모두 완료 대기
                                     │
Wave 2: ─────────────────────────────────────►
        ├─ T-004 (agent 1) ────►
        └─ T-005 (agent 2) ──────►
```

## Task 도구 호출 패턴

### 병렬 실행 (같은 Wave)
```python
# 단일 메시지에서 여러 Task 호출
Task(
    subagent_type="backend-architect",
    prompt="T-001: UserService 구현",
    run_in_background=True
) → agent_id_1

Task(
    subagent_type="frontend-architect",
    prompt="T-002: UserForm 컴포넌트",
    run_in_background=True
) → agent_id_2

# 결과 수집
TaskOutput(task_id=agent_id_1, block=True) → result_1
TaskOutput(task_id=agent_id_2, block=True) → result_2
```

### 순차 실행 (Wave 간)
```python
# Wave 1 완료 후
if all_tasks_complete(wave_1):
    # Wave 2 시작
    execute_wave(wave_2)
```

## 병렬 제한

- **동시 에이전트**: 최대 5개
- **큰 Wave 처리**: 5개씩 배치로 분할

```python
if len(wave_tasks) > 5:
    batches = chunk(wave_tasks, 5)
    for batch in batches:
        execute_parallel(batch)
        wait_all(batch)
```

## 의존성 처리

### 단순 의존성
```
T-004 blocked by: T-001
→ T-001 완료 확인 후 T-004 실행
```

### 복합 의존성
```
T-006 blocked by: T-003, T-004
→ T-003 AND T-004 모두 완료 후 실행
```

### 의존성 실패
```
T-003 실패 → T-006 자동 스킵
```

## 프롬프트 생성 템플릿

```markdown
## 태스크: {task.title}

**파일**: {task.file}
**작업**:
{task.work (체크박스 목록)}

**검증**:
{task.verification (명령어 목록)}

**지침**:
1. 파일 읽기 → 현재 상태 파악
2. 작업 항목 순차 수행
3. 각 항목 완료 후 체크
4. 검증 명령 실행
5. 성공/실패 보고
```

## 결과 판정

### 성공 조건
- 모든 작업 항목 완료
- 검증 명령 통과
- 에러 없음

### 실패 조건
- 작업 중 에러 발생
- 검증 실패
- 타임아웃 (10분)

## 상태 업데이트 타이밍

| 이벤트 | 마크다운 업데이트 |
|--------|-----------------|
| 태스크 시작 | `- [ ]` → `- [~]` |
| 태스크 성공 | `- [~]` → `- [x]` |
| 태스크 실패 | `- [~]` → `- [!]` |
| 의존성 스킵 | `- [ ]` → `- [-]` |
| Wave 완료 | ⏳ → ✅ |
