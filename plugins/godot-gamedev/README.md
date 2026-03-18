# godot-gamedev

Godot 4.x 게임 개발을 위한 Claude Code 플러그인.

## godot-dev 스킬

Godot 파일(`.gd`, `.tscn`, `.tres`, `.gdshader`, `project.godot`)을 다룰 때 자동 활성화.

### 제공 기능

1. **변경 API 선별 조회** — Godot 4.3~4.6에서 변경된 API만 WebFetch로 공식 문서 확인. 안정적인 API는 내장 지식 사용. HTML 잘리면 GitHub raw RST fallback.
2. **.tscn/.tres 형식 가이드** — 씬/리소스 파일의 정확한 텍스트 형식 스펙. 실제 프로젝트 파일에서 검증.
3. **아키텍처 패턴** — 공식/커뮤니티 출처 구분. 의존성 주입, Autoload, 씬 합성, Resource, 상태 머신 등.
4. **.gdshader 기본 가이드** — GLSL ES 3.0 유사 문법, 셰이더 타입, uniform 힌트.

### 레퍼런스

| 파일 | 내용 |
|------|------|
| `breaking-changes.md` | 4.3~4.6 변경 API 목록 (공식 RST에서 추출, WebFetch 트리거 기준) |
| `tscn-format.md` | .tscn/.tres/project.godot 텍스트 형식 스펙 |
| `godot-patterns.md` | 아키텍처 패턴 & GDScript 컨벤션 (공식/커뮤니티 출처 표기) |
