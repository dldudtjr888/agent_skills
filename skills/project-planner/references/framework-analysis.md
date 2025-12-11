# Framework Analysis Guide

프레임워크별 프로젝트 분석 가이드. 각 프레임워크의 핵심 구조와 분석 포인트를 정리.

---

## Next.js (App Router)

### 핵심 파일/폴더

| 파일/폴더 | 용도 | 분석 포인트 |
|-----------|------|------------|
| `app/` | App Router 라우팅 | 폴더 구조 = URL 구조 |
| `app/layout.tsx` | 루트 레이아웃 | 전역 상태, Provider 래핑 |
| `app/page.tsx` | 루트 페이지 | 메인 엔트리 |
| `app/api/` | API Routes | 서버 엔드포인트 |
| `next.config.js` | Next.js 설정 | 환경변수, 리다이렉트, 미들웨어 |
| `middleware.ts` | 미들웨어 | 인증, 리다이렉트 로직 |

### 분석 명령어

```
# 라우트 구조 파악
Glob: app/**/page.tsx

# API 엔드포인트 목록
Glob: app/api/**/route.ts

# Server vs Client 컴포넌트 분포
Grep: "use client"

# 서버 액션 찾기
Grep: "use server"

# 데이터 페칭 패턴
Grep: "fetch\|getServerSideProps\|getStaticProps"
```

### 주의 사항
- **Server Component**: 기본값, DB 직접 접근 가능
- **Client Component**: `"use client"` 선언 필요, 훅 사용 가능
- **경계 확인**: Server → Client 데이터 전달 시 직렬화 가능 여부

---

## Next.js (Pages Router - Legacy)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `pages/` | 페이지 라우팅 |
| `pages/api/` | API Routes |
| `pages/_app.tsx` | 앱 래퍼 |
| `pages/_document.tsx` | HTML 문서 구조 |

### 분석 명령어

```
# 페이지 목록
Glob: pages/**/*.tsx

# 데이터 페칭
Grep: "getServerSideProps\|getStaticProps\|getInitialProps"
```

---

## React (Vite/CRA)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `src/App.tsx` | 루트 컴포넌트 |
| `src/main.tsx` | 엔트리 포인트 |
| `src/index.tsx` | CRA 엔트리 |
| `vite.config.ts` | Vite 설정 |

### 분석 명령어

```
# 컴포넌트 목록
Glob: src/**/*.tsx

# 훅 사용 현황
Grep: "use[A-Z][a-zA-Z]*\("

# 상태 관리
Grep: "useContext\|Redux\|Zustand\|Recoil\|Jotai"

# 라우팅
Grep: "react-router\|Routes\|BrowserRouter"
```

### 구조 패턴

```
Feature-based:
src/
  features/
    auth/
      components/
      hooks/
      api/
    dashboard/
      ...

Layered:
src/
  components/
  hooks/
  services/
  utils/
```

---

## Python (FastAPI)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `main.py` | 앱 엔트리 |
| `app/` | 애플리케이션 패키지 |
| `routers/` | API 라우터 |
| `models/` | Pydantic/ORM 모델 |
| `schemas/` | 요청/응답 스키마 |
| `services/` | 비즈니스 로직 |
| `alembic/` | DB 마이그레이션 |

### 분석 명령어

```
# 엔드포인트 목록
Grep: "@app\.\|@router\."

# Pydantic 모델
Grep: "class.*BaseModel\|class.*Base\)"

# 의존성 주입
Grep: "Depends\("

# DB 모델
Grep: "class.*Base\):\|Column\|relationship"
```

### 구조 패턴

```
app/
  api/
    v1/
      endpoints/
  core/
    config.py
    security.py
  models/
  schemas/
  services/
  db/
```

---

## Python (Django)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `manage.py` | CLI 엔트리 |
| `settings.py` | 프로젝트 설정 |
| `urls.py` | URL 라우팅 |
| `models.py` | ORM 모델 |
| `views.py` | 뷰 로직 |
| `serializers.py` | DRF 직렬화 |

### 분석 명령어

```
# URL 패턴
Grep: "path\(\|url\("

# 모델 정의
Grep: "class.*models\.Model"

# 뷰 클래스/함수
Grep: "class.*View\|def.*request"

# Admin 등록
Grep: "admin\.site\.register"
```

---

## Python (Flask)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `app.py` / `__init__.py` | 앱 팩토리 |
| `routes/` | 블루프린트 |
| `models.py` | SQLAlchemy 모델 |
| `config.py` | 설정 |

### 분석 명령어

```
# 라우트 정의
Grep: "@app\.route\|@.*\.route"

# 블루프린트
Grep: "Blueprint\("
```

---

## Node.js (Express)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `app.js` / `server.js` | 엔트리 |
| `routes/` | 라우터 |
| `controllers/` | 컨트롤러 |
| `models/` | DB 모델 |
| `middleware/` | 미들웨어 |

### 분석 명령어

```
# 라우트 정의
Grep: "router\.\|app\.(get\|post\|put\|delete)"

# 미들웨어
Grep: "app\.use\("

# 모델 (Mongoose)
Grep: "mongoose\.Schema\|new Schema"
```

---

## Go (Standard/Gin/Echo)

### 핵심 파일/폴더

| 파일/폴더 | 용도 |
|-----------|------|
| `main.go` | 엔트리 |
| `cmd/` | CLI 명령어 |
| `internal/` | 내부 패키지 |
| `pkg/` | 외부 노출 패키지 |
| `handlers/` | HTTP 핸들러 |

### 분석 명령어

```
# 핸들러 정의
Grep: "func.*Handler\|\.GET\|\.POST"

# 라우터 설정
Grep: "\.Group\|\.Handle"

# 구조체 정의
Grep: "type.*struct"
```

---

## 공통 분석 체크리스트

### 1. 엔트리 포인트
```
Glob: **/main.*, **/index.*, **/app.*
```

### 2. 설정 파일
```
Glob: **/*config*, **/.env*, **/settings.*
```

### 3. 테스트 위치
```
Glob: **/*test*, **/*spec*, **/tests/**
```

### 4. 타입/스키마
```
Glob: **/types/*, **/schemas/*, **/models/*
```

### 5. 유틸리티
```
Glob: **/utils/*, **/helpers/*, **/lib/*
```
