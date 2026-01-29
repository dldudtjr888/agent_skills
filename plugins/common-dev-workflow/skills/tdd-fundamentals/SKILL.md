---
name: tdd-fundamentals
description: |
  테스트 주도 개발(TDD) 핵심 개념. Red-Green-Refactor 사이클, 테스트 피라미드, AAA 패턴, 커버리지 가이드라인.
  언어 무관 원칙. Python/TypeScript 치트시트 포함.
version: 1.0.0
category: testing
user-invocable: true
triggers:
  keywords:
    - tdd
    - test driven
    - 테스트 주도
    - red green refactor
    - test pyramid
    - 테스트 피라미드
    - test coverage
    - 테스트 커버리지
    - aaa pattern
    - given when then
  intentPatterns:
    - "(TDD|테스트 주도).*(방법|원칙|가이드)"
    - "(테스트|test).*(작성법|패턴|원칙)"
---

# TDD Fundamentals

언어 무관 테스트 주도 개발 핵심 원칙.

## Red-Green-Refactor 사이클

```
┌─────────────────────────────────────────┐
│                                         │
│    RED ──────► GREEN ──────► REFACTOR   │
│     │                            │      │
│     └────────────────────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

### 1. RED: 실패하는 테스트 작성

```
- 구현 전에 테스트 작성
- 테스트가 실패하는지 확인 (FAILED)
- 테스트가 명확한 요구사항을 표현
```

### 2. GREEN: 최소 구현

```
- 테스트를 통과하는 최소한의 코드 작성
- 완벽한 코드가 아니어도 됨
- 테스트 통과가 목표 (PASSED)
```

### 3. REFACTOR: 코드 개선

```
- 중복 제거
- 가독성 향상
- 성능 최적화
- 테스트는 여전히 통과해야 함
```

## 테스트 피라미드

```
         /\
        /E2E\        ← 적게 (느림, 비쌈)
       /──────\
      /Integration\   ← 중간
     /──────────────\
    /    Unit Tests   \  ← 많이 (빠름, 저렴)
   ──────────────────────
```

| 레벨 | 비율 | 속도 | 범위 |
|------|------|------|------|
| Unit | 70% | 빠름 | 함수/클래스 |
| Integration | 20% | 중간 | 모듈 간 상호작용 |
| E2E | 10% | 느림 | 전체 시스템 |

## AAA / Given-When-Then 패턴

```
# Arrange (Given) - 준비
테스트 데이터와 환경 설정

# Act (When) - 실행
테스트 대상 동작 실행

# Assert (Then) - 검증
예상 결과 확인
```

**예시 (의사 코드)**:
```
test "user can change password":
    # Arrange
    user = create_user(password="old")

    # Act
    user.change_password("new")

    # Assert
    assert user.verify_password("new") == true
    assert user.verify_password("old") == false
```

## 커버리지 가이드라인

| 영역 | 최소 커버리지 | 우선순위 |
|------|-------------|---------|
| 비즈니스 로직 | 90% | 높음 |
| API 엔드포인트 | 80% | 높음 |
| 유틸리티 함수 | 80% | 중간 |
| 모델/스키마 | 70% | 중간 |
| UI 컴포넌트 | 70% | 낮음 |
| **전체** | **80%** | - |

### 커버리지 ≠ 품질

```
✅ 좋은 테스트: 동작을 검증, 엣지 케이스 포함
❌ 나쁜 테스트: 라인만 실행, 의미 없는 assertion
```

## 모킹 원칙

### 경계에서만 모킹

```
┌──────────────────────────────────────┐
│         Your Code (실제 실행)          │
│  ┌─────────────────────────────────┐ │
│  │    Business Logic               │ │
│  │    (모킹 X - 실제 테스트)          │ │
│  └─────────────────────────────────┘ │
│              ↓                        │
│  ┌─────────────────────────────────┐ │
│  │    External Boundaries          │ │
│  │    (모킹 O)                      │ │
│  │    - Database                   │ │
│  │    - External APIs              │ │
│  │    - File System                │ │
│  │    - Time/Random                │ │
│  └─────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### 모킹 체크리스트

```
✅ 모킹해야 할 것:
- 외부 API 호출
- 데이터베이스 연결
- 파일 시스템
- 네트워크 요청
- 현재 시간/난수

❌ 모킹하지 말 것:
- 내부 비즈니스 로직
- 순수 함수
- 데이터 변환
```

## 테스트 격리 원칙

### 1. 독립적 테스트

```
❌ 나쁨: 테스트 간 의존성
test_1: user = create_user()
test_2: update(user)  ← test_1에 의존

✅ 좋음: 각 테스트 독립적
test_1: user = create_user(); ...
test_2: user = create_user(); update(user); ...
```

### 2. 상태 공유 금지

```
❌ 나쁨: 공유 상태
global_counter = 0  # 테스트 간 공유

✅ 좋음: 격리된 상태
def test_counter():
    counter = Counter()  # 테스트 내 생성
```

### 3. 정리 (Cleanup)

```
setup:    테스트 전 환경 준비
teardown: 테스트 후 환경 정리

매 테스트마다 깨끗한 상태로 시작
```

## 테스트 명명 규칙

```
# 패턴 1: should_behavior_when_condition
test_should_return_error_when_invalid_input

# 패턴 2: method_condition_expected
test_login_with_wrong_password_fails

# 패턴 3: 설명적 문장
test "user can reset password via email"
```

**좋은 테스트 이름**:
- 테스트가 무엇을 검증하는지 명확
- 실패 시 원인 파악 가능
- 문서 역할 수행

## 필수 테스트 시나리오

### 1. Happy Path (정상 경로)
```
- 유효한 입력 → 예상 출력
- 가장 일반적인 사용 케이스
```

### 2. Edge Cases (경계 케이스)
```
- 빈 입력 (null, [], "")
- 경계값 (0, -1, MAX_INT)
- 특수 문자 (유니코드, 이모지)
```

### 3. Error Cases (에러 케이스)
```
- 잘못된 입력 타입
- 권한 없음
- 리소스 없음
- 네트워크 실패
```

### 4. 보안 케이스
```
- 인젝션 시도
- 인증/인가 우회
- 입력 길이 초과
```

## 테스트 안티패턴

| 안티패턴 | 문제점 | 해결책 |
|---------|-------|--------|
| 구현 세부사항 테스트 | 리팩토링에 취약 | 동작/결과 테스트 |
| 과도한 모킹 | 실제 동작 미검증 | 경계에서만 모킹 |
| 테스트 간 의존성 | 순서 의존, 불안정 | 독립적 테스트 |
| 고정 대기 시간 | 느림, 불안정 | 조건 대기 |
| 테스트 중복 | 유지보수 어려움 | 헬퍼 함수 |

## 언어별 상세 가이드

프로젝트 언어에 따라 해당 모듈 참조:

| 언어 | 상세 가이드 | 빠른 참조 |
|------|------------|----------|
| **Python** | `modules/python-testing.md` | `references/python-cheatsheet.md` |
| **TypeScript** | `modules/typescript-testing.md` | `references/typescript-cheatsheet.md` |
| **Rust** | `modules/rust-testing.md` | `references/rust-cheatsheet.md` |

### 모듈 내용

- **python-testing.md**: pytest 설정, conftest.py 패턴, Fixtures, Parametrize, Mock/Patch, FastAPI 테스트, Async 테스트, 커버리지
- **typescript-testing.md**: Vitest/Jest 설정, Testing Library, Hook 테스트, MSW 모킹, Playwright E2E
- **rust-testing.md**: cargo test, Unit/Integration 테스트, Mockall, Async 테스트, Proptest, Criterion 벤치마크
