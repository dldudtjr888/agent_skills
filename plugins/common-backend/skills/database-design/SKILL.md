---
name: database-design
description: |
  데이터베이스 설계 가이드. 스키마 설계, 정규화, 인덱싱 전략, 마이그레이션 패턴.
  언어/ORM 무관한 개념 중심 + Python/Rust 치트시트 포함.
version: 1.0.0
category: database
user-invocable: true
triggers:
  keywords:
    - database design
    - schema design
    - 스키마 설계
    - 데이터베이스 설계
    - normalization
    - 정규화
    - indexing
    - 인덱스
    - migration
    - 마이그레이션
    - ERD
    - foreign key
    - primary key
  intentPatterns:
    - "(설계|디자인).*(데이터베이스|스키마|테이블)"
    - "(추가|생성).*(인덱스|마이그레이션)"
    - "(최적화).*(쿼리|인덱스)"
---

# Database Design Guide

데이터베이스 설계의 핵심 개념과 패턴을 다루는 스킬.

## 목차

| Module | 설명 |
|--------|------|
| [schema-design](modules/schema-design.md) | 테이블 설계, 관계, 제약조건 |
| [normalization](modules/normalization.md) | 정규화 단계, 역정규화 전략 |
| [indexing-strategies](modules/indexing-strategies.md) | 인덱스 타입, 복합 인덱스, 부분 인덱스 |
| [migration-patterns](modules/migration-patterns.md) | 무중단 마이그레이션, 롤백 전략 |

## Quick References

| Reference | 설명 |
|-----------|------|
| [data-types-guide](references/data-types-guide.md) | 데이터 타입 선택 가이드 |
| [anti-patterns](references/anti-patterns.md) | 피해야 할 안티패턴 |
| [python-cheatsheet](references/python-cheatsheet.md) | SQLAlchemy, Alembic 치트시트 |
| [rust-cheatsheet](references/rust-cheatsheet.md) | Diesel, SQLx, SeaORM 치트시트 |

## 핵심 원칙

### 1. 적절한 데이터 타입 선택
- `bigint` for IDs (not `int`)
- `text` for strings (not `varchar(255)`)
- `timestamptz` for timestamps (not `timestamp`)
- `numeric` for money (not `float`)

### 2. 인덱스는 필수
- WHERE 절 컬럼
- JOIN 조건 컬럼
- Foreign Key 컬럼
- ORDER BY 컬럼

### 3. 정규화 vs 성능
- 기본적으로 3NF까지 정규화
- 읽기 성능이 중요하면 선택적 역정규화
- 역정규화 시 데이터 일관성 전략 필수

## Workflow

```
1. 요구사항 분석
   ↓
2. 개념적 설계 (ERD)
   ↓
3. 논리적 설계 (정규화)
   ↓
4. 물리적 설계 (인덱스, 파티션)
   ↓
5. 마이그레이션 계획
```

## 관련 에이전트

- `@database-reviewer` - 스키마/쿼리 리뷰
- `@performance-analyst` - 쿼리 성능 분석
