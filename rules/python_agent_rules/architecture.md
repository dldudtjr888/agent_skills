# 아키텍처 규칙

> 공통 인프라: `core-infrastructure.md` | 프로바이더: `ai-provider-patterns.md` | 에이전트: `ai-agent-patterns.md`

## 계층형 아키텍처 (엄격한 Import 방향)

```
router/    → HTTP 엔드포인트 전용 (요청/응답 처리)
  ↓
services/  → 비즈니스 로직, 오케스트레이션, 워크플로우 구성
  ↓
domain/    → 프로젝트별 에이전트, 핸들러, 메모리, 확장
  ↓
core/      → 범용 재사용 모듈 (domain 의존성 없음)
```

**Import 방향**: `core → domain → services → router`
- 각 레이어는 하위 레이어에서만 import
- `core/`는 어디서든 import 가능 (최하위 레이어)
- `router/`는 다른 레이어에서 절대 import하지 않음 (최상위 레이어)

## 레이어 책임

- **router/**: API 엔드포인트, SSE 스트리밍, 요청 검증만. 비즈니스 로직 금지.
- **services/**: 에이전트 호출, 세션 관리, 워크플로우 구성.
- **domain/**: 에이전트 정의, 핸들러, 메모리 어댑터, 프로젝트별 확장.
- **core/**: 프로바이더 추상화, DI 컨테이너, 로깅, 인프라 유틸리티. 범용 유지 필수.

## 위반 사례

- Router에 비즈니스 로직 포함 → `services/`로 이동
- `core/`에서 `domain/` import → core는 프로젝트 비의존 유지 필수
- Router에서 `domain/`을 직접 호출 → 사이에 `services/` 레이어 추가

## 확장 패턴

`domain/`은 프로젝트별 동작을 위해 `core/`의 Protocol과 기본 클래스를 확장.
전체 매핑 표는 `core-infrastructure.md`의 "core/ 확장 패턴" 참조.

## 요청 처리 파이프라인

```
입력 → 가드레일 → 라우팅 → 메시지 조립 → 프로바이더 호출 → 가드레일 → 출력
       (검증)     (분배)   (요청 포맷팅)   (LLM 호출)      (검증)
```

## 단일 작성자 패턴

- 세션 영속화를 위한 유일한 작성자로 하나의 레이어/모듈을 지정
- 오케스트레이터와 핸들러는 세션 데이터를 직접 저장하면 안 됨
- 추적성을 위해 저장 시 항상 provider 파라미터 명시

## 절대 하지 말 것

- `router/`에 비즈니스 로직 배치 (엔드포인트 전용)
- `core/`에서 `domain/` import (범용성 파괴)
- 세션 데이터에 대한 다중 작성자 (경쟁 상태 유발)
- `router/`와 `domain/` 사이에 `services/` 레이어 생략
