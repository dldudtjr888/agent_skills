# Decomposition Patterns

재귀적 태스크 분해를 위한 패턴과 예시.

## 분해 중단 조건 (리프 태스크 판별)

다음 **모두** 충족 시 분해 중단:

```
✓ 단일 파일 또는 단일 함수 수준
✓ 30분 이내 완료 예상
✓ 완료 조건이 명확하고 검증 가능
✓ 추가 분해 시 의미있는 단위로 나뉘지 않음
```

## 작업 유형별 분해 패턴 (예시)

작업 유형은 고정되지 않음. 계획의 성격에 맞게 유연하게 적용.

### 새 기능 개발 (예시)

```
기능 추가
├── 데이터 레이어
│   ├── 스키마/모델 정의
│   ├── 마이그레이션 작성
│   └── Repository/DAO 구현
├── 비즈니스 로직
│   ├── Service 클래스 생성
│   ├── 핵심 메서드 구현
│   └── 유효성 검증 로직
├── API 레이어
│   ├── DTO 정의
│   ├── Controller/Handler 작성
│   └── 라우팅 설정
├── 프론트엔드
│   ├── API 클라이언트 함수
│   ├── 상태 관리 (store/hook)
│   └── UI 컴포넌트
└── 테스트
    ├── Unit 테스트
    ├── Integration 테스트
    └── E2E 테스트 (필요시)
```

### 리팩토링 (예시)

```
리팩토링
├── 준비
│   ├── 기존 테스트 확인/보강
│   ├── 영향 범위 파악
│   └── 롤백 계획 수립
├── 구조 변경
│   ├── 새 구조 생성 (기존 유지)
│   ├── 로직 이전
│   ├── 참조 업데이트
│   └── 기존 구조 제거
└── 검증
    ├── 기존 테스트 통과 확인
    ├── 성능 비교
    └── 코드 리뷰
```

### 버그 수정 (예시)

```
버그 수정
├── 분석
│   ├── 재현 조건 확인
│   ├── 근본 원인 파악
│   └── 영향 범위 확인
├── 수정
│   ├── 실패 테스트 작성 (재현)
│   ├── 코드 수정
│   └── 테스트 통과 확인
└── 검증
    ├── 회귀 테스트
    ├── 관련 기능 테스트
    └── 엣지 케이스 확인
```

## 분해 신호별 처리

### 여러 파일 수정이 필요한 경우

**Before:**
```
- [ ] API와 프론트엔드 연결
```

**After:**
```
- [ ] T-001: API 엔드포인트 응답 스키마 확인
  - 완료 조건: 응답 JSON 구조 문서화 완료
- [ ] T-002: 프론트엔드 API 클라이언트 함수 작성
  - 완료 조건: 함수 호출 시 타입 에러 없음
- [ ] T-003: 응답 데이터 타입 정의
  - 완료 조건: TypeScript 컴파일 통과
- [ ] T-004: 컴포넌트에서 API 호출 연결
  - 완료 조건: 데이터 렌더링 확인
- [ ] T-005: 에러 핸들링 추가
  - 완료 조건: 네트워크 에러 시 에러 UI 표시
```

### 복합 동사가 포함된 경우

**Before:**
```
- [ ] 데이터 검증하고 저장
```

**After:**
```
- [ ] T-001: 입력 데이터 유효성 검증 로직 구현
  - 완료 조건: 유효성 검증 단위 테스트 통과
- [ ] T-002: 검증 실패 시 에러 응답 처리
  - 완료 조건: 잘못된 입력 시 400 에러 반환
- [ ] T-003: 검증 통과 시 DB 저장 로직 구현
  - 완료 조건: 저장 후 DB 조회로 데이터 확인
- [ ] T-004: 저장 성공/실패 응답 처리
  - 완료 조건: 성공 시 201, 실패 시 500 반환
```

### 암묵적 단계가 숨어있는 경우

**Before:**
```
- [ ] 테스트 작성
```

**After:**
```
- [ ] T-001: 테스트 파일 생성 및 기본 구조 설정
  - 완료 조건: 빈 테스트 스위트 실행 성공
- [ ] T-002: 테스트 픽스처/목 데이터 준비
  - 완료 조건: 픽스처 파일 생성 완료
- [ ] T-003: 정상 케이스 테스트 작성
  - 완료 조건: happy path 테스트 통과
- [ ] T-004: 엣지 케이스 테스트 작성
  - 완료 조건: 경계값 테스트 통과
- [ ] T-005: 에러 케이스 테스트 작성
  - 완료 조건: 예외 처리 테스트 통과
- [ ] T-006: 테스트 실행 및 커버리지 확인
  - 완료 조건: 커버리지 80% 이상
```

### 시간 추정이 30분 초과인 경우

**Before:**
```
- [ ] 사용자 인증 시스템 구현
```

**After:**
```
Wave 1:
- [ ] T-001: User 모델에 password 필드 추가
  - 완료 조건: 마이그레이션 성공, 스키마 반영
- [ ] T-002: 비밀번호 해싱 유틸 함수 작성
  - 완료 조건: bcrypt 해싱/검증 테스트 통과

Wave 2:
- [ ] T-003: 회원가입 API 엔드포인트 구현
  - 완료 조건: POST /signup 201 응답
- [ ] T-004: 로그인 API 엔드포인트 구현
  - 완료 조건: POST /login 토큰 반환

Wave 3:
- [ ] T-005: JWT 토큰 생성 로직 구현
  - 완료 조건: 유효한 JWT 생성 확인
- [ ] T-006: 토큰 검증 미들웨어 구현
  - 완료 조건: 유효/무효 토큰 분기 처리

Wave 4:
- [ ] T-007: 인증 필요 라우트에 미들웨어 적용
  - 완료 조건: 미인증 요청 401 반환
- [ ] T-008: 로그아웃/토큰 무효화 구현
  - 완료 조건: 로그아웃 후 토큰 거부

Wave 5:
- [ ] T-009: 인증 흐름 통합 테스트
  - 완료 조건: 회원가입→로그인→인증API→로그아웃 시나리오 통과
```

## 컨텍스트별 분해 깊이 조정

### 익숙한 코드베이스
- 파일/함수 수준까지 구체적으로
- 라인 번호 참조 가능

### 새로운 코드베이스
- 모듈/컴포넌트 수준으로
- 탐색 태스크 선행 추가

### 프로토타입/MVP
- 기능 단위로 느슨하게
- 리팩토링 태스크는 별도 배치

### 프로덕션 코드
- 테스트/검증 태스크 필수 포함
- 롤백 계획 태스크 추가

## 분해 품질 체크리스트

각 리프 태스크가 다음을 만족하는지 확인:

```
□ 무엇을 해야 하는지 명확한가?
□ 어디서 해야 하는지 (파일/위치) 알 수 있는가?
□ 완료 여부를 어떻게 확인하는가?
□ 다른 태스크와 의존성이 명시되어 있는가?
□ 혼자서 30분 내에 완료 가능한가?
□ 작업이 체크박스로 세분화되어 있는가? (5분 단위)
□ 검증 명령어가 실행 가능한가?
□ 참조할 기존 코드/문서가 명시되어 있는가?
```

---

## 작업(작업) 세분화 패턴

### 원칙: 5분 룰
각 서브스텝은 **5분 이내**에 완료 가능해야 함.

### 세분화 신호

| 신호 | 분해 방법 |
|------|----------|
| "등" 또는 괄호 안에 여러 항목 | 각 항목을 별도 체크박스로 |
| 복합 동사 (생성하고, 추가하고) | 동사별로 분리 |
| "전체", "모든" | 구체적 대상 나열 |
| 시간 추정 10분 초과 | 단계별로 쪼개기 |

### 세분화 예시

#### YAML/Config 파일 작성

**Before (나쁨):**
```markdown
- 작업: OpenRouter Provider 기본값 설정 파일 생성 (api, defaults, provider, routing, model_types, tiers, fallback, reasoning, advanced 섹션)
```

**After (좋음):**
```markdown
- 작업:
  - [ ] 빈 YAML 파일 생성
  - [ ] api 섹션 (base_url, timeout)
  - [ ] defaults 섹션 (temperature, max_tokens)
  - [ ] provider 섹션 (order, sort)
  - [ ] routing 섹션 (route, suffix)
  - [ ] model_types 섹션 (reasoning_models 목록)
  - [ ] tiers 섹션 (FAST/BALANCED/POWERFUL/CODING)
  - [ ] fallback 섹션 (models 배열)
  - [ ] reasoning 섹션 (effort levels)
  - [ ] advanced 섹션 (transforms, debug)
```

#### 클래스/함수 구현

**Before (나쁨):**
```markdown
- 작업: UserService 클래스 구현 (CRUD 메서드 포함)
```

**After (좋음):**
```markdown
- 작업:
  - [ ] 클래스 정의 및 생성자
  - [ ] create() 메서드 시그니처
  - [ ] create() 로직 구현
  - [ ] read() 메서드 시그니처
  - [ ] read() 로직 구현
  - [ ] update() 메서드
  - [ ] delete() 메서드
  - [ ] 에러 핸들링 추가
```

#### 데이터클래스/타입 정의

**Before (나쁨):**
```markdown
- 작업: OpenRouterConfig 데이터클래스 정의 (Routing, Provider Control, Reasoning, Headers, Advanced 필드)
```

**After (좋음):**
```markdown
- 작업:
  - [ ] @dataclass 데코레이터 추가
  - [ ] Routing 관련 필드 (route, suffix, models)
  - [ ] Provider Control 필드 (order, sort, require_parameters)
  - [ ] Reasoning 필드 (effort, max_tokens)
  - [ ] Headers 필드 (app_name, site_url)
  - [ ] Advanced 필드 (transforms, user, debug)
  - [ ] Optional 필드에 기본값 설정
```

#### 테스트 작성

**Before (나쁨):**
```markdown
- 작업: param_policy.py 단위 테스트 작성
```

**After (좋음):**
```markdown
- 작업:
  - [ ] 테스트 파일 생성 및 import
  - [ ] 픽스처 정의 (mock config, mock request)
  - [ ] test_reasoning_model_temperature_excluded()
  - [ ] test_fallback_models_applied()
  - [ ] test_normal_model_all_params_passed()
  - [ ] 엣지 케이스: 빈 config
  - [ ] 엣지 케이스: None 값 처리
```

#### 마이그레이션/리팩토링

**Before (나쁨):**
```markdown
- 작업: OpenRouterProvider 사용처를 LangChainProvider로 마이그레이션
```

**After (좋음):**
```markdown
- 작업:
  - [ ] grep으로 사용처 검색
  - [ ] 파일 1: xxx.py import 변경
  - [ ] 파일 1: 클래스명 변경
  - [ ] 파일 2: yyy.py import 변경
  - [ ] 파일 2: 클래스명 변경
  - [ ] 각 파일 린트 통과 확인
```

### 참조(참조) 섹션 패턴

참조 섹션은 **기존 패턴 따르기** 원칙을 위해 필수:

```markdown
- 참조:
  - 유사 파일: `existing/similar.py` (구조 참고)
  - 계획서: `docs/plan/xxx.md#section-name`
  - 기존 구현: `class ExistingClass` in `path/to/file.py`
```

### 검증(검증) 섹션 패턴

실행 가능한 명령어 우선:

```markdown
- 검증:
  - [ ] `python -c "import yaml; yaml.safe_load(open('config/xxx.yaml'))"`  # YAML 문법
  - [ ] `uv run pytest tests/unit/xxx.py -v`  # 테스트
  - [ ] `uv run ruff check path/to/file.py`  # 린트
  - [ ] `uv run python -m py_compile path/to/file.py`  # 문법
  - [ ] 수동: curl로 API 응답 확인 (자동화 불가 시)
```
