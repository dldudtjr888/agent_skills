# Infrastructure Setup Guide

RAG 시스템을 위한 로컬 개발 환경 설정

## 빠른 시작

```bash
# 1. 인프라 시작
docker-compose up -d

# 2. 상태 확인
docker-compose ps

# 3. 로그 확인
docker-compose logs -f

# 4. 종료
docker-compose down
```

## 서비스 엔드포인트

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Qdrant REST** | http://localhost:6333 | Vector DB REST API |
| **Qdrant gRPC** | localhost:6334 | Vector DB gRPC API |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | 웹 UI |
| **FalkorDB** | localhost:6379 | Graph DB (Redis protocol) |
| **FalkorDB Browser** | http://localhost:3000 | 웹 UI |
| **Prometheus** | http://localhost:9090 | 메트릭 서버 |
| **Grafana** | http://localhost:3001 | 대시보드 (admin/admin) |

## 연결 테스트

### Qdrant

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
print(client.get_collections())
```

```bash
# REST API
curl http://localhost:6333/collections

# 메트릭
curl http://localhost:6333/metrics
```

### FalkorDB

```python
from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('test')
result = graph.query("RETURN 'Hello!' AS msg")
print(result.result_set)
```

```bash
# Redis CLI
redis-cli -p 6379 PING
```

## 파일 구조

```
infrastructure/
├── docker-compose.yml      # 개발용 Docker Compose
├── docker-compose.prod.yml # 프로덕션용 (선택)
├── prometheus.yml          # Prometheus 설정
├── qdrant-config.yaml      # Qdrant 설정 (선택)
└── grafana/
    └── provisioning/       # Grafana 자동 설정
        ├── datasources/
        └── dashboards/
```

## 볼륨 관리

```bash
# 데이터 확인
docker volume ls | grep rag

# 특정 볼륨 삭제
docker volume rm infrastructure_qdrant_data

# 모든 볼륨 삭제 (주의!)
docker-compose down -v
```

## Grafana 대시보드 설정

1. http://localhost:3001 접속
2. admin/admin 로그인
3. Data Sources → Add → Prometheus
   - URL: http://prometheus:9090
4. Dashboards → Import → ID: 24074 (Qdrant)

## 문제 해결

### Qdrant 연결 실패

```bash
# 컨테이너 상태 확인
docker-compose ps qdrant

# 로그 확인
docker-compose logs qdrant

# 재시작
docker-compose restart qdrant
```

### FalkorDB 연결 실패

```bash
# Redis CLI로 테스트
docker exec -it falkordb redis-cli PING

# 메모리 사용량 확인
docker stats falkordb
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
lsof -i :6333
lsof -i :6379

# docker-compose.yml에서 포트 변경
# "6333:6333" → "16333:6333"
```

## 프로덕션 고려사항

### 리소스 제한

```yaml
services:
  qdrant:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          memory: 2G
```

### 영구 스토리지

```yaml
volumes:
  qdrant_data:
    driver: local
    driver_opts:
      type: none
      device: /data/qdrant
      o: bind
```

### 네트워크 보안

```yaml
services:
  qdrant:
    environment:
      - QDRANT__SERVICE__API_KEY=your-secret-key
```

## 다음 단계

- [qdrant-mastery/references/monitoring-setup.md](../skills/qdrant-mastery/references/monitoring-setup.md) - 모니터링 상세
- [rag-patterns/modules/production-patterns.md](../skills/rag-patterns/modules/production-patterns.md) - 프로덕션 패턴
