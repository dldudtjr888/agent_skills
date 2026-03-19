---
name: sql-production-analyzer
description: "PostgreSQL/MySQL/SQLite 프로덕션 SQL 분석 — Prisma, TypeORM, SQLAlchemy, Django ORM, Sequelize, Drizzle, Knex 지원. SQL Injection 탐지, N+1 쿼리 패턴 감지, SELECT * 경고, OFFSET 페이지네이션 안티패턴, FK 인덱스 누락, 코드-DB 스키마 불일치 검사. Use when auditing SQL queries, checking for N+1 problems, finding SQL injection risks, analyzing ORM schema, reviewing database performance, or validating production readiness. 'SQL 분석', 'N+1 쿼리 찾아줘', 'SQL Injection 검사', '스키마 검토', 'DB 성능', '쿼리 최적화', 'ORM 분석', '프로덕션 DB 점검' 요청 시 반드시 트리거."
---

# SQL Production Analyzer

SQL 데이터베이스의 프로덕션 준비 상태를 분석합니다.

## Usage (Single Command)

```bash
# 정적 분석 (DB 연결 불필요)
python scripts/analyze.py /path/to/project

# 전체 분석 (Live DB 포함)
python scripts/analyze.py /path/to/project --connection "postgresql://user:pass@host/db"

# 파일 출력
python scripts/analyze.py /path/to/project -o report.json --pretty
```

## Output Format

```json
{
  "summary": {
    "total_issues": 5,
    "by_severity": {"critical": 1, "high": 2, "medium": 2, "low": 0},
    "by_category": {"security": 1, "performance": 2, "schema": 1, "consistency": 1}
  },
  "issues": [
    {"category": "security", "severity": "critical", "type": "sql_injection_risk", "file": "src/api.py", "line": 45, "message": "..."}
  ],
  "project_type": {"orm_type": "prisma", "has_raw_sql": false},
  "analysis_notes": [...]
}
```

## Supported

- **DB**: PostgreSQL, MySQL, SQLite
- **ORM**: Prisma, TypeORM, SQLAlchemy, Django, Sequelize, Peewee, Tortoise, Knex, Drizzle
- **Raw SQL**: aiomysql, asyncpg, pymysql (정적 분석 한계 있음 - 아래 참조)

## Analysis Categories

| Category | 검사 항목 |
|----------|----------|
| **security** | SQL Injection, 하드코딩된 credentials |
| **performance** | N+1 쿼리, SELECT *, OFFSET 페이지네이션, 느린 쿼리 |
| **schema** | FK 인덱스 누락, 제약조건, 정규화 |
| **consistency** | 코드-DB 스키마 불일치 (Live 분석 필요) |

## Severity

| Level | 대응 | 예시 |
|-------|------|------|
| CRITICAL | 즉시 | SQL Injection |
| HIGH | 24h | FK 인덱스 누락, N+1 쿼리 |
| MEDIUM | 1주 | SELECT *, 느린 쿼리 |
| LOW | 다음 스프린트 | 코드 스타일 |

## 🔒 Production Safety

Live 분석 시 **읽기 전용 모드**로 동작:
- PostgreSQL: `SET SESSION readonly=True`
- MySQL: `SET SESSION TRANSACTION READ ONLY`
- SQLite: `file:path?mode=ro` URI

## ⚠️ 정적 분석 한계 (중요)

### 탐지 가능

| 항목 | 예시 |
|------|------|
| ORM 스키마 파일 | Prisma schema, TypeORM Entity, Django models |
| 하드코딩된 SQL | `"SELECT * FROM users WHERE id = %s"` |
| 명시적 테이블 참조 | `cursor.execute("SELECT * FROM users")` |

### 탐지 불가

| 항목 | 이유 | 예시 |
|------|------|------|
| 동적 쿼리 | 런타임 결정 | `f"SELECT * FROM {table}"` |
| 변수 테이블명 | 정적 추론 불가 | `table = "users"; query(table)` |
| 외부 설정 기반 | 환경변수/설정파일 | `query(config.table_name)` |

### Raw SQL 프로젝트 권장 패턴

ORM 없이 raw SQL을 사용하는 프로젝트는 정적 분석 한계가 큼. **쿼리 중앙화 권장:**

```python
# ✅ 탐지 가능 - queries/users.py
GET_USER = "SELECT id, name, email FROM users WHERE id = %s"
GET_USER_BY_EMAIL = "SELECT id, name FROM users WHERE email = %s"

# 사용
await cur.execute(GET_USER, (user_id,))
```

## Connection Strings

```
PostgreSQL: postgresql://user:pass@host:5432/dbname
MySQL:      mysql://user:pass@host:3306/dbname
SQLite:     /path/to/database.db
```

## Advanced Scripts (개별 실행)

| Script | 용도 | DB 연결 |
|--------|------|---------|
| `find_queries.py` | SQL/ORM 쿼리 추출만 | 불필요 |
| `analyze_schema.py` | ORM 스키마 분석만 | 불필요 |
| `detect_n_plus_one.py` | N+1 쿼리 패턴 탐지만 | 불필요 |
| `inspect_live_schema.py` | 실제 DB 스키마 조회 | **필요** |
| `test_query_performance.py` | EXPLAIN ANALYZE 실행 | **필요** |
| `compare_schema_code.py` | 코드↔DB 스키마 비교 | **필요** |
