# 설정 & 프롬프트 관리 규칙

> 구현 코드/pytest 설정/conftest: Skills `config-management.md` 참조.

## 핵심 철학

1. **코드로서의 설정**: YAML 기반, 버전 관리
2. **시크릿 분리**: 민감한 값은 `.env`에만, YAML에서 `${VAR}`로 참조
3. **안전 우선 설계**: 설정 누락 시 안전한 기본값
4. **시작 시 검증**: 런타임 에러 방지를 위해 시작 시 설정 검증
5. **핫 리로드**: 재시작 없이 프롬프트 버전 전환 가능

## 에이전트 설정 상속

- 모든 에이전트는 `_defaults.yaml`을 상속, 개별 파일에서 오버라이드
- `config/agents/*.yaml`이 모델/LLM 설정의 단일 소스

## 프롬프트 버전 관리

- 유일한 버전 소스: `prompts/*.yaml`의 `current` 값
- 롤백을 위해 이전 버전 모두 보존 (v1, v2, v3...)
- 재시작 불필요 — 에이전트 생성 시마다 YAML 재읽기

## 규칙

- 새 에이전트는 필수: `config/agents/{agent}.yaml` + `prompts/{agent}/system.yaml`
- 설정 변경은 재시작 필요 (프롬프트 `current` 변경 제외)
- `CONFIG_STRICT_MODE=true`: 설정 누락 시 폴백 대신 raise
- 환경변수 워크플로우: `.env.example`에 먼저 추가 → YAML에 `${VAR}` 추가
- 프로젝트 싱글턴 ConfigLoader만 사용

## 절대 하지 말 것

- YAML 파일에 시크릿 직접 입력 (`.env` + `${VAR}` 사용)
- `config/agents/` 외부에 에이전트 설정 생성
- 에이전트 설정에 `prompt_version` 설정 (`prompts/*.yaml`의 `current`만 사용)
- 새 config loader 생성 (기존 ConfigLoader 사용)
- 새 환경변수 추가 시 `.env.example` 업데이트 생략
- 이전 프롬프트 버전 삭제 (롤백용 보관)
