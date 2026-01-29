# Token Comparison

## JWT vs Session vs API Key

| Feature | JWT | Session | API Key |
|---------|-----|---------|---------|
| **저장** | 클라이언트 | 서버 | 클라이언트 |
| **Stateless** | Yes | No | Yes |
| **확장성** | 높음 | 분산 저장소 필요 | 높음 |
| **무효화** | 어려움 | 즉시 가능 | DB 조회 필요 |
| **크기** | 큼 (payload) | 작음 (ID만) | 작음 |
| **수명** | 짧음 (분~시간) | 중간 (시간~일) | 김 (영구) |
| **Use Case** | API 인증 | 웹 세션 | 서버 간 통신 |

## When to Use

### JWT
```
✅ SPA, 모바일 앱
✅ 마이크로서비스 간 통신
✅ Stateless 필요
❌ 즉시 무효화 필요
❌ 민감 데이터 포함 필요
```

### Session
```
✅ 전통적 웹 애플리케이션
✅ 즉시 무효화 필요
✅ 세션 데이터 많음
❌ 수평 확장 어려움 (분산 저장소 없이)
```

### API Key
```
✅ 서버 간 통신
✅ 외부 개발자 API 접근
✅ 장기 인증
❌ 사용자 인증
❌ 짧은 수명 필요
```

## Hybrid Approaches

### JWT + Session (BFF)
```
Web App → BFF (Session) → API (JWT)

- 웹앱은 세션 쿠키 사용
- BFF가 JWT로 API 호출
- 두 장점 결합
```

### JWT + Blacklist
```
- JWT의 Stateless 특성 유지
- Redis에 revoked 토큰 저장
- 무효화 가능
```

### Short JWT + Refresh Token
```
- Access Token: 15분 (무효화 불필요)
- Refresh Token: 7일 (서버 저장, 무효화 가능)
```

## Security Comparison

| Threat | JWT | Session | API Key |
|--------|-----|---------|---------|
| XSS | HttpOnly Cookie | HttpOnly Cookie | 헤더만 |
| CSRF | Bearer 헤더 | SameSite Cookie | 헤더만 |
| 탈취 시 | 만료까지 유효 | 즉시 무효화 | 무효화 가능 |
| Replay | exp 검증 | 세션 검증 | Rate limit |

## Performance

| Aspect | JWT | Session | API Key |
|--------|-----|---------|---------|
| 검증 속도 | 빠름 (로컬) | DB/Redis 조회 | DB 조회 |
| 네트워크 | 없음 | Redis 왕복 | DB 왕복 |
| 부하 | CPU (서명) | I/O (조회) | I/O (조회) |
