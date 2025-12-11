# Dependency Mapping

태스크 간 의존성 분석과 병렬화 웨이브 구성 가이드.

## 의존성 유형

### Hard Dependency (필수)
반드시 선행 태스크 완료 후 시작 가능.

```
표기: blocked by: T-XXX
```

**예시:**
- DB 스키마 → 마이그레이션 실행
- 인터페이스 정의 → 구현체 작성
- API 엔드포인트 → 프론트엔드 연동
- 모듈 생성 → 해당 모듈 import하는 코드

### Soft Dependency (권장)
순서 권장하지만 역순도 기술적으로 가능.

```
표기: recommended after: T-XXX
```

**예시:**
- 구현 → 테스트 (TDD는 역순)
- 코어 로직 → 에러 핸들링
- 기본 기능 → 최적화

## 의존성 식별 패턴

### 데이터 흐름 기반
```
생성 → 사용 → 변환 → 출력

T-001: User 모델 정의
T-002: UserRepository 구현 (blocked by: T-001)
T-003: UserService 구현 (blocked by: T-002)
T-004: UserController 구현 (blocked by: T-003)
```

### Import/Export 기반
```
T-001: utils/validator.ts 생성
T-002: services/user.ts에서 validator 사용 (blocked by: T-001)
```

### 인프라 기반
```
T-001: 환경변수 설정
T-002: DB 연결 설정 (blocked by: T-001)
T-003: 서버 초기화 (blocked by: T-002)
```

### 테스트 기반
```
T-001: 테스트 픽스처 준비
T-002: Unit 테스트 작성 (blocked by: T-001)
T-003: Integration 테스트 (blocked by: T-002, 구현 완료)
```

## 웨이브 구성 알고리즘

### Step 1: 의존성 그래프 구축
```
T-001 → T-003
T-002 → T-003
T-003 → T-005
T-004 → T-005
```

### Step 2: 진입 차수(in-degree) 계산
```
T-001: 0 (의존성 없음)
T-002: 0 (의존성 없음)
T-003: 2 (T-001, T-002 대기)
T-004: 0 (의존성 없음)
T-005: 2 (T-003, T-004 대기)
```

### Step 3: 웨이브 할당
```
Wave 1: in-degree = 0인 태스크
  → T-001, T-002, T-004

Wave 2: Wave 1 완료 후 in-degree = 0이 되는 태스크
  → T-003

Wave 3: Wave 2 완료 후 in-degree = 0이 되는 태스크
  → T-005
```

## 웨이브 구성 예시

### 새 API 엔드포인트 추가

```
### Wave 1 ⏳ (병렬 실행 가능)
- [ ] T-001: Request DTO 정의
- [ ] T-002: Response DTO 정의
- [ ] T-003: 테스트 픽스처 준비

### Wave 2 🔄
- [ ] T-004: Service 메서드 구현
  - blocked by: T-001
- [ ] T-005: Repository 메서드 구현
  - blocked by: T-001

### Wave 3 ⏳
- [ ] T-006: Controller 핸들러 구현
  - blocked by: T-002, T-004, T-005
- [ ] T-007: Unit 테스트 작성
  - blocked by: T-003, T-004

### Wave 4 ⏳
- [ ] T-008: Integration 테스트
  - blocked by: T-006, T-007
```

### 리팩토링 (Extract Method)

```
### Wave 1 ⏳
- [ ] T-001: 기존 코드 테스트 커버리지 확인
- [ ] T-002: 추출할 로직 범위 확정

### Wave 2 🔄
- [ ] T-003: 새 메서드 시그니처 정의
  - blocked by: T-002
- [ ] T-004: 테스트에 새 메서드 케이스 추가
  - blocked by: T-001, T-003

### Wave 3 ⏳
- [ ] T-005: 로직을 새 메서드로 이동
  - blocked by: T-003
- [ ] T-006: 기존 위치에서 새 메서드 호출로 교체
  - blocked by: T-005

### Wave 4 ⏳
- [ ] T-007: 전체 테스트 실행 및 통과 확인
  - blocked by: T-004, T-006
```

## 크리티컬 패스 식별

가장 긴 의존성 체인 = 최소 완료 시간 결정.

### 표기법
```
🔴 Critical Path Task - 지연 시 전체 일정 영향
```

### 예시
```
Wave 1:
- [ ] T-001: DB 스키마 설계 🔴
- [ ] T-002: UI 목업 작성

Wave 2:
- [ ] T-003: 마이그레이션 실행 🔴
  - blocked by: T-001

Wave 3:
- [ ] T-004: Repository 구현 🔴
  - blocked by: T-003
- [ ] T-005: 컴포넌트 스타일링
  - blocked by: T-002

Wave 4:
- [ ] T-006: API 통합 🔴
  - blocked by: T-004, T-005
```

크리티컬 패스: T-001 → T-003 → T-004 → T-006

## 순환 의존성 감지

순환 발견 시:
1. 공통 의존성 추출
2. 인터페이스로 분리
3. 단계 재구성

**Before (순환):**
```
T-001: UserService 구현 (needs AuthService)
T-002: AuthService 구현 (needs UserService)
```

**After (해결):**
```
T-001: IUserProvider 인터페이스 정의
T-002: UserService 구현 (implements IUserProvider)
T-003: AuthService 구현 (depends on IUserProvider)
```

## 병렬화 최적화 팁

### 독립적인 작업 식별
- 서로 다른 파일/모듈
- 서로 다른 레이어 (프론트/백엔드)
- 서로 다른 기능 영역

### 의존성 최소화 전략
- 인터페이스 먼저 정의 → 구현 병렬화
- 목(Mock) 사용 → 테스트 선행 가능
- 환경 설정 선행 → 이후 작업 병렬화

### 웨이브 크기 균형
- 너무 작은 웨이브: 오버헤드 증가
- 너무 큰 웨이브: 병렬화 이점 감소
- 권장: 웨이브당 2-5개 태스크
