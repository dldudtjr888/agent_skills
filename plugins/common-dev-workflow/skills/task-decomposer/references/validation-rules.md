# Validation Rules

태스크 완료 조건 및 최종 검증 체크리스트 가이드.

## 태스크별 완료 조건

### 완료 조건 작성 원칙

**SMART 기준 적용:**
- **Specific**: 구체적으로 무엇을 확인하는가
- **Measurable**: 성공/실패를 객관적으로 판단 가능한가
- **Achievable**: 현실적으로 검증 가능한가
- **Relevant**: 태스크 목적과 연관되는가
- **Time-bound**: 검증에 얼마나 걸리는가 (즉시~5분 이내 권장)

### 완료 조건 유형

#### 1. 테스트 통과
```markdown
완료 조건: `npm test -- user.service.spec.ts` 통과
완료 조건: `pytest tests/test_auth.py -v` 전체 통과
완료 조건: 관련 테스트 스위트 100% 통과
```

#### 2. 빌드 성공
```markdown
완료 조건: `npm run build` 에러 없이 완료
완료 조건: TypeScript 컴파일 에러 0개
완료 조건: ESLint 경고/에러 0개
```

#### 3. 기능 동작 확인
```markdown
완료 조건: POST /api/users 호출 시 201 응답
완료 조건: 로그인 후 대시보드 페이지 접근 가능
완료 조건: 버튼 클릭 시 모달 표시
```

#### 4. 코드 품질
```markdown
완료 조건: 함수 복잡도 10 이하 (radon 기준)
완료 조건: 테스트 커버리지 80% 이상
완료 조건: 코드 리뷰 승인
```

#### 5. 데이터 확인
```markdown
완료 조건: DB에 users 테이블 생성 확인
완료 조건: 마이그레이션 후 기존 데이터 유지
완료 조건: 로그에 에러 메시지 없음
```

### 작업 유형별 완료 조건 예시

#### 모델/스키마 작성
```markdown
- [ ] **T-001**: User 모델 정의
  - 파일: `src/models/user.ts`
  - 작업: id, email, password, createdAt 필드 포함
  - 완료 조건: TypeScript 컴파일 성공, 필수 필드 타입 검증
```

#### API 엔드포인트 구현
```markdown
- [ ] **T-002**: 사용자 생성 API 구현
  - 파일: `src/routes/users.ts`
  - 작업: POST /users 엔드포인트 추가
  - 완료 조건: 
    - 유효한 요청 시 201 + user 객체 반환
    - 중복 이메일 시 409 반환
    - 잘못된 형식 시 400 반환
```

#### 프론트엔드 컴포넌트
```markdown
- [ ] **T-003**: LoginForm 컴포넌트 구현
  - 파일: `src/components/LoginForm.tsx`
  - 작업: 이메일/비밀번호 입력, 제출 버튼
  - 완료 조건:
    - 스토리북에서 렌더링 확인
    - 빈 필드 제출 시 validation 에러 표시
    - 제출 시 onSubmit 콜백 호출
```

#### 버그 수정
```markdown
- [ ] **T-004**: 로그인 실패 시 에러 메시지 미표시 버그 수정
  - 파일: `src/pages/Login.tsx`
  - 작업: catch 블록에서 setError 호출 추가
  - 완료 조건:
    - 실패 테스트 케이스 추가 및 통과
    - 잘못된 비밀번호 입력 시 에러 메시지 표시
```

## 검증 섹션 구성

### 레벨별 검증

```markdown
## Verification

### Unit Level
- [ ] 모든 새 함수에 단위 테스트 존재
- [ ] 테스트 커버리지 감소 없음
- [ ] 엣지 케이스 테스트 포함

### Integration Level
- [ ] API 엔드포인트 간 연동 테스트 통과
- [ ] 데이터베이스 트랜잭션 정상 동작
- [ ] 외부 서비스 연동 확인 (또는 목 사용)

### System Level
- [ ] 전체 빌드 성공
- [ ] 기존 기능 회귀 없음
- [ ] 성능 저하 없음 (해당 시)

### Acceptance Criteria
- [ ] 원래 요구사항 모두 충족
- [ ] 사용자 시나리오 테스트 통과
```

### 유형별 검증 체크리스트

#### 새 기능
```markdown
## Verification

### Functionality
- [ ] 핵심 기능 정상 동작
- [ ] 에러 케이스 적절히 처리
- [ ] 권한/인증 적용 (해당 시)

### Quality
- [ ] 코드 스타일 가이드 준수
- [ ] 중복 코드 없음
- [ ] 적절한 로깅 추가

### Documentation
- [ ] API 문서 업데이트 (해당 시)
- [ ] README 업데이트 (해당 시)
- [ ] 인라인 주석 (복잡한 로직)
```

#### 리팩토링
```markdown
## Verification

### Behavior Preservation
- [ ] 기존 테스트 100% 통과
- [ ] 공개 API 시그니처 유지 (또는 의도적 변경 문서화)
- [ ] 기존 기능 동일하게 동작

### Improvement Metrics
- [ ] 코드 복잡도 감소 확인
- [ ] 중복 제거 확인
- [ ] 가독성 향상 (주관적이나 리뷰어 동의)

### Safety
- [ ] 롤백 가능 상태 유지
- [ ] 점진적 변경 (big bang 아님)
```

#### 버그 수정
```markdown
## Verification

### Bug Resolution
- [ ] 버그 재현 테스트 통과 (수정 전 실패, 후 성공)
- [ ] 근본 원인 해결 (증상만 가리지 않음)
- [ ] 관련 코드 경로 검토

### Regression
- [ ] 기존 테스트 통과
- [ ] 관련 기능 수동 테스트
- [ ] 유사 버그 패턴 검색 및 확인

### Prevention
- [ ] 버그 방지 테스트 추가
- [ ] 필요시 타입/검증 강화
```

## 검증 자동화 힌트

### CI/CD 연동 체크
```markdown
- 검증:
  - [ ] GitHub Actions 워크플로우 통과
  - [ ] PR 체크 모두 녹색
```

### 스크립트 기반 검증
```markdown
- 검증:
  - [ ] `./scripts/verify.sh`
  - [ ] `make test && make lint`
```

### 수동 검증 최소화
- 가능한 자동화된 검증 조건 사용
- 수동 검증 필요 시 구체적 단계 명시
- 스크린샷/로그 증거 요청 (필요시)

---

## 언어/프레임워크별 검증 명령어

### Python (uv 기반)
```markdown
- 검증:
  - [ ] `uv run python -m py_compile path/to/file.py`  # 문법 검사
  - [ ] `uv run ruff check path/to/file.py`  # 린트
  - [ ] `uv run ruff format --check path/to/file.py`  # 포맷
  - [ ] `uv run mypy path/to/file.py`  # 타입 체크
  - [ ] `uv run pytest tests/unit/test_xxx.py -v`  # 단위 테스트
  - [ ] `uv run pytest tests/integration/ -v`  # 통합 테스트
```

### Python (YAML 검증)
```markdown
- 검증:
  - [ ] `python -c "import yaml; yaml.safe_load(open('config/xxx.yaml'))"`
```

### TypeScript/JavaScript
```markdown
- 검증:
  - [ ] `tsc --noEmit`  # 타입 체크
  - [ ] `npm run lint` 또는 `eslint path/to/file.ts`
  - [ ] `npm test -- file.spec.ts`  # 단위 테스트
  - [ ] `npm run build`  # 빌드
```

### API 검증
```markdown
- 검증:
  - [ ] `curl -s http://localhost:8000/health | jq .`  # 헬스체크
  - [ ] `curl -X POST http://localhost:8000/api/xxx -d '{}' -H 'Content-Type: application/json'`
  - [ ] 응답 코드 확인: 200/201/4xx/5xx
```

### 데이터베이스 검증
```markdown
- 검증:
  - [ ] `mysql -e "DESCRIBE table_name;"`  # 스키마 확인
  - [ ] `mysql -e "SELECT COUNT(*) FROM table_name;"`  # 데이터 확인
```

### Git/파일 검증
```markdown
- 검증:
  - [ ] `test -f path/to/file.py`  # 파일 존재
  - [ ] `git diff --name-only`  # 변경 파일 확인
  - [ ] `wc -l path/to/file.py`  # 라인 수 확인
```

### 복합 검증 (체이닝)
```markdown
- 검증:
  - [ ] `uv run ruff check . && uv run pytest tests/unit/ -v`  # 린트 + 테스트
  - [ ] `npm run lint && npm test && npm run build`  # 전체 검증
```

---

## 검증 섹션 작성 가이드

### 필수 규칙
1. **실행 가능한 명령어 우선** - 복사-붙여넣기로 바로 실행 가능
2. **체크박스 형식** - 진행률 추적 가능
3. **수동 검증 최소화** - 불가피한 경우만 "수동:" 접두사 사용

### 좋은 예시
```markdown
- 검증:
  - [ ] `uv run pytest tests/unit/test_param_policy.py -v`
  - [ ] `uv run ruff check core/ai/providers/langchain/param_policy.py`
```

### 나쁜 예시
```markdown
- 완료 조건: 테스트 통과, 린트 성공  ← 명령어 없음
- 완료 조건: 정상 동작 확인  ← 모호함
```

## 검증 실패 시 대응

```markdown
### Rollback Plan
- [ ] 변경 전 상태로 복구 가능
- [ ] 데이터 백업 존재 (DB 변경 시)
- [ ] 피처 플래그로 비활성화 가능 (해당 시)

### Escalation
- 검증 실패 시 담당자 알림
- 블로커 이슈 생성
- 의존 태스크 일시 중단
```
