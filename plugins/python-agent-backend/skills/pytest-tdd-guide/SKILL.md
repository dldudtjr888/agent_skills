---
name: pytest-tdd-guide
description: Python TDD 방법론 및 pytest 테스트 가이드. Red-Green-Refactor 사이클, pytest 명령어, 테스트 패턴, FastAPI/Multi-Agent 테스트 템플릿 제공. 테스트 작성법, TDD 방법론, pytest 사용법, 커버리지 목표 설정 시 사용.
---

# Python TDD Guide

pytest 기반 Test-Driven Development 방법론 가이드.

## TDD 원칙

1. **테스트 먼저** - 구현 전에 실패하는 테스트 작성
2. **최소 구현** - 테스트 통과하는 최소한의 코드
3. **리팩토링** - 테스트 통과 후 코드 정리
4. **80%+ 커버리지** - 핵심 로직 커버리지 유지

## Red-Green-Refactor 사이클

```bash
# RED: 실패하는 테스트 작성
pytest tests/test_feature.py -v  # FAILED

# GREEN: 최소 구현으로 통과
pytest tests/test_feature.py -v  # PASSED

# REFACTOR: 코드 정리 후 여전히 통과 확인
pytest tests/test_feature.py -v  # PASSED
```

## Pytest 핵심 명령어

```bash
# 기본 실행
pytest                           # 전체 테스트
pytest -v                        # 상세 출력
pytest tests/test_user.py        # 특정 파일
pytest -k "user and create"      # 키워드 필터

# 커버리지
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-fail-under=80

# 디버깅
pytest --lf                      # 실패한 테스트만 재실행
pytest -x                        # 첫 실패에서 중단
pytest --pdb                     # 디버거 실행

# 병렬 실행
pytest -n auto                   # pytest-xdist
```

## 커버리지 목표

| 영역 | 최소 커버리지 |
|------|-------------|
| 비즈니스 로직 (services/) | 90% |
| API 엔드포인트 (routes/) | 80% |
| 모델/스키마 (models/) | 70% |
| 전체 | 80% |

## 상세 레퍼런스

- **테스트 패턴** (AAA, Fixtures, Parametrize, Mock): `references/test-patterns.md`
- **FastAPI/Multi-Agent 테스트**: `references/fastapi-testing.md`
