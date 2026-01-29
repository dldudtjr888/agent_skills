# Deep Agents 핵심 개념

Deep Agents는 **4가지 핵심 구성요소**를 통해 복잡한 작업을 처리합니다.

---

## 1. Planning Tool

### 개요
Todo 리스트 도구는 기술적으로는 간단하지만, **문맥 관리를 통해 에이전트의 초점을 유지**하는 전략적 역할을 합니다.

### 도구

| 도구 | 용도 |
|-----|------|
| `write_todos` | 작업 목록 생성 및 업데이트 |
| `read_todos` | 현재 TODO 목록 확인 |

### 에이전트 자동 행동

```python
# 에이전트는 복잡한 작업에서 자동으로:
# 1. write_todos로 연구 단계 계획
# 2. task()로 서브에이전트에 위임
# 3. write_file로 /final_report.md 저장
# 4. read_file로 보고서 검증
```

### 연구 워크플로우 예시

```
1. Plan: write_todos로 연구 작업 분해
2. Save: write_file()로 연구 질문 저장 → /research_request.md
3. Research: task()로 서브에이전트에 위임 (직접 연구 금지)
4. Synthesize: 모든 서브에이전트 결과 통합
5. Write Report: /final_report.md 작성
6. Verify: /research_request.md 읽고 모든 측면 확인
```

---

## 2. Filesystem

### 개요
장시간 실행되는 에이전트가 생성된 메모리와 중간 결과를 **저장하고 공유**할 수 있는 공동 작업 공간입니다.

### 도구

| 도구 | 용도 | 비고 |
|-----|------|------|
| `ls` | 디렉토리 목록 | 절대 경로 사용 |
| `read_file` | 파일 읽기 | 페이지네이션 지원 |
| `write_file` | 파일 생성/덮어쓰기 | |
| `edit_file` | 정확한 문자열 교체 | |
| `glob` | 패턴 매칭 파일 검색 | 예: `**/*.py` |
| `grep` | 텍스트 패턴 검색 | |

### 컨텍스트 관리 패턴

```python
# 웹 검색, RAG 등 가변 길이 결과를 파일에 저장
# → 컨텍스트 윈도우 오버플로우 방지

# 예: 연구 결과 저장
# 에이전트가 자동으로:
# 1. 검색 결과 → /research_findings.md
# 2. 분석 결과 → /analysis.md
# 3. 최종 보고서 → /final_report.md
```

---

## 3. Subagents

### 개요
복잡한 작업을 **개별 작업에 집중된 하위 에이전트로 분산**하여 처리합니다.
문맥 격리와 프롬프트 효율성을 향상시킵니다.

### 도구

| 도구 | 용도 |
|-----|------|
| `task` | 서브에이전트에 작업 위임 |

### 서브에이전트 장점

1. **컨텍스트 격리**: 메인 에이전트 컨텍스트 윈도우 보호
2. **전문화**: 각 서브에이전트가 특정 도메인에 집중
3. **모델 유연성**: 서브에이전트별 다른 모델 사용 가능
4. **병렬 실행**: 여러 서브에이전트 동시 실행

### 연구 계획 가이드라인

```
- 단순 사실 확인: 1개 서브에이전트
- 비교/다면적 주제: 병렬 서브에이전트
- 각 서브에이전트는 한 가지 측면만 연구
```

---

## 4. Shell Access

### 개요
에이전트가 **셸 명령어를 실행**할 수 있습니다.
샌드박스 백엔드 사용 시 안전하게 격리됩니다.

### 도구

| 도구 | 용도 |
|-----|------|
| `execute` | 셸 명령어 실행 |

### 보안 고려사항

```python
# 프로덕션에서는 샌드박스 백엔드 사용 권장
# - Runloop
# - Daytona
# - Modal

# 샌드박스는 격리된 환경에서 코드 실행
```

---

## Think Tool (전략적 반성)

### 개요
에이전트가 검색 후 **전략적으로 반성**할 수 있는 도구입니다.

```python
from research_agent.tools import think_tool

# 초기 검색 후 반성
reflection = think_tool.invoke({
    "reflection": """
    양자 컴퓨팅 응용 검색 후:
    - 양자 암호화와 신약 개발 정보 발견
    - 누락: 상용화 사례
    - 품질: 기초 이해는 좋으나 구체적 사례 필요
    - 결정: 실제 양자 컴퓨팅 배포 사례 추가 검색 필요
    """
})
# 반환: "Reflection recorded: [reflection text]"
```

---

## 핵심 원리 요약

> **"planning (사전 계획), computer access (셸/파일시스템 접근), sub-agent delegation (격리된 작업 실행)"**

이 세 가지 원리를 통해 Deep Agents는 단순한 도구 호출 루프를 넘어 **복잡한 작업을 장시간에 걸쳐 계획하고 실행**할 수 있습니다.

---

## 다음 단계

- [03-api-reference.md](03-api-reference.md): API 파라미터 상세
- [04-middleware.md](04-middleware.md): 미들웨어 패턴
- [05-subagents.md](05-subagents.md): 서브에이전트 설계
