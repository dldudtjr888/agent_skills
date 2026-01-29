# Data Types Guide

## PostgreSQL Data Types

| Use Case | Recommended | Avoid |
|----------|-------------|-------|
| Primary Key | `bigint` | `int` (2.1B 한계) |
| UUID PK | `uuid` (UUIDv7) | Random UUID |
| String | `text` | `varchar(255)` (불필요한 제한) |
| Timestamp | `timestamptz` | `timestamp` (타임존 없음) |
| Money | `numeric(p,s)` | `float` (정밀도 손실) |
| Boolean | `boolean` | `varchar`, `int` |
| JSON | `jsonb` | `json` (인덱스 불가) |

## Numeric Types

| Type | Range | Storage |
|------|-------|---------|
| `smallint` | -32,768 ~ 32,767 | 2 bytes |
| `int` | -2.1B ~ 2.1B | 4 bytes |
| `bigint` | -9.2E18 ~ 9.2E18 | 8 bytes |
| `numeric(p,s)` | 정밀 소수점 | 가변 |
| `real` | 6자리 정밀도 | 4 bytes |
| `double` | 15자리 정밀도 | 8 bytes |

## String Types

| Type | Description |
|------|-------------|
| `text` | 무제한 가변 길이 (권장) |
| `varchar(n)` | n자 제한 가변 길이 |
| `char(n)` | n자 고정 길이 |

## Date/Time Types

| Type | Description |
|------|-------------|
| `timestamptz` | 타임존 포함 (권장) |
| `timestamp` | 타임존 없음 |
| `date` | 날짜만 |
| `time` | 시간만 |
| `interval` | 기간 |

## MySQL Equivalents

| PostgreSQL | MySQL |
|------------|-------|
| `bigint` | `BIGINT` |
| `text` | `TEXT` / `LONGTEXT` |
| `timestamptz` | `TIMESTAMP` |
| `jsonb` | `JSON` |
| `boolean` | `TINYINT(1)` |

## Quick Reference

```sql
-- Good schema example
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email text NOT NULL UNIQUE,
  name text,
  balance numeric(12,2) DEFAULT 0,
  is_active boolean DEFAULT true,
  metadata jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```
