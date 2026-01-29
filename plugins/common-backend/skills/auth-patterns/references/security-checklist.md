# Authentication Security Checklist

## Password Security

- [ ] 강력한 비밀번호 정책 (최소 8자, 대소문자, 숫자, 특수문자)
- [ ] bcrypt/argon2로 해싱 (MD5, SHA1 사용 금지)
- [ ] Salt는 자동 생성 (bcrypt 내장)
- [ ] 비밀번호 평문 로깅 금지
- [ ] 비밀번호 재설정 토큰 일회용 + 시간 제한

## Token Security

### Access Token
- [ ] 짧은 수명 (15분 ~ 1시간)
- [ ] 서명 알고리즘 명시 (alg != "none")
- [ ] 민감 정보 payload에 미포함
- [ ] 만료 시간(exp) 검증
- [ ] 발급자(iss) 검증
- [ ] 수신자(aud) 검증

### Refresh Token
- [ ] 긴 수명이지만 제한 (7일 ~ 30일)
- [ ] 서버 측 저장 (revocation 가능)
- [ ] Rotation 구현 (재사용 방지)
- [ ] 탈취 감지 시 전체 무효화

## Session Security

- [ ] HttpOnly 쿠키 사용
- [ ] Secure 플래그 (HTTPS)
- [ ] SameSite=Strict 또는 Lax
- [ ] 로그인 시 세션 ID 재생성
- [ ] 절대 만료 시간 설정
- [ ] 동시 세션 수 제한

## OAuth2 Security

- [ ] state 파라미터로 CSRF 방지
- [ ] PKCE 사용 (SPA, 모바일)
- [ ] redirect_uri 화이트리스트 검증
- [ ] client_secret 안전하게 저장
- [ ] 토큰 응답은 HTTPS만

## API Security

- [ ] Rate limiting 구현
- [ ] Brute-force 방지 (계정 잠금)
- [ ] 로그인 실패 로깅
- [ ] 민감 엔드포인트 재인증 요구
- [ ] CORS 제한적 설정

## CSRF Prevention

- [ ] SameSite 쿠키 사용
- [ ] CSRF 토큰 검증 (상태 변경 요청)
- [ ] Origin/Referer 헤더 검증

## XSS Prevention

- [ ] HttpOnly 쿠키 (토큰 보호)
- [ ] Content-Security-Policy 헤더
- [ ] 출력 인코딩

## Logging & Monitoring

- [ ] 로그인 성공/실패 로깅
- [ ] 비정상 활동 알림
- [ ] 민감 정보 로그에서 제외
- [ ] 세션 활동 감사 로그
