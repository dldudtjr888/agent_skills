# HTTP Status Code Guide

## Success (2xx)

| Code | Name | Use Case |
|------|------|----------|
| 200 | OK | GET, PUT, PATCH 성공 |
| 201 | Created | POST로 리소스 생성 |
| 202 | Accepted | 비동기 작업 수락 |
| 204 | No Content | DELETE 성공 (본문 없음) |

## Redirect (3xx)

| Code | Name | Use Case |
|------|------|----------|
| 301 | Moved Permanently | 영구 이동 |
| 302 | Found | 임시 이동 |
| 304 | Not Modified | 캐시 유효 |

## Client Error (4xx)

| Code | Name | Use Case |
|------|------|----------|
| 400 | Bad Request | 잘못된 요청 형식 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 405 | Method Not Allowed | 허용되지 않은 메서드 |
| 409 | Conflict | 충돌 (중복 생성 등) |
| 422 | Unprocessable Entity | 검증 실패 |
| 429 | Too Many Requests | Rate limit 초과 |

## Server Error (5xx)

| Code | Name | Use Case |
|------|------|----------|
| 500 | Internal Server Error | 서버 오류 |
| 502 | Bad Gateway | 업스트림 오류 |
| 503 | Service Unavailable | 서비스 불가 |
| 504 | Gateway Timeout | 업스트림 타임아웃 |

## Decision Guide

```
요청 성공?
├── Yes → 리소스 생성? → 201
│         본문 있음? → 200
│         본문 없음? → 204
│
└── No → 클라이언트 문제?
         ├── 인증 필요? → 401
         ├── 권한 없음? → 403
         ├── 리소스 없음? → 404
         ├── 검증 실패? → 422
         └── 형식 오류? → 400

         서버 문제? → 500
```
