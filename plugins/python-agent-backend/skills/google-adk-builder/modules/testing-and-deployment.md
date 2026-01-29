# Testing & Deployment (테스트 & 배포)

> 메인 스킬: `../SKILL.md`

adk eval 평가, pytest 단위 테스트, 로컬 개발, Cloud Run/Vertex AI 배포를 다룬다.

---

## adk eval (에이전트 평가)

Golden Dataset을 사용하여 에이전트의 응답 품질을 자동으로 평가한다.

### Golden Dataset 형식

```json
[
  {
    "query": "서울 날씨 어때?",
    "expected_tool_use": [
      {
        "tool_name": "get_weather",
        "tool_input": {"city": "서울"}
      }
    ],
    "reference": "서울의 현재 날씨는"
  },
  {
    "query": "부산과 대전 날씨 비교해줘",
    "expected_tool_use": [
      {
        "tool_name": "get_weather",
        "tool_input": {"city": "부산"}
      },
      {
        "tool_name": "get_weather",
        "tool_input": {"city": "대전"}
      }
    ],
    "reference": "부산과 대전의 날씨를 비교"
  }
]
```

### 평가 실행

```bash
# 기본 실행
adk eval my_agent tests/test_eval.json

# 특정 모델로 평가
adk eval my_agent tests/test_eval.json --model gemini-2.0-flash
```

### 평가 기준

| 기준 | 설명 |
|------|------|
| `tool_trajectory_avg_score` | 도구 호출 시퀀스 일치도 |
| `response_match_score` | 최종 응답과 reference 유사도 |
| `response_evaluation_score` | LLM 기반 응답 품질 점수 |

### 평가 결과 예시

```
Test Case 1: "서울 날씨 어때?"
  tool_trajectory: PASS (1.0)
  response_match: 0.85
  response_quality: 0.90

Test Case 2: "부산과 대전 날씨 비교해줘"
  tool_trajectory: PASS (1.0)
  response_match: 0.78
  response_quality: 0.85

Overall Score: 0.88
```

---

## pytest 단위 테스트

InMemoryRunner를 사용하여 에이전트를 프로그래밍 방식으로 테스트한다.

### 기본 테스트 구조

```python
# tests/test_agent.py
import pytest
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from my_agent.agent import root_agent

@pytest.fixture
def runner():
    return InMemoryRunner(agent=root_agent, app_name="test")

@pytest.fixture
async def session(runner):
    return await runner.session_service.create_session(
        app_name="test", user_id="test_user"
    )

async def get_response(runner, session_id: str, message: str) -> str:
    """에이전트에 메시지를 보내고 텍스트 응답을 반환한다."""
    responses = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session_id,
        new_message=Content(parts=[Part(text=message)]),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    responses.append(part.text)
    return " ".join(responses)

@pytest.mark.asyncio
async def test_basic_response(runner, session):
    response = await get_response(runner, session.id, "안녕하세요")
    assert response  # 빈 응답이 아닌지 확인
    assert len(response) > 0

@pytest.mark.asyncio
async def test_tool_usage(runner, session):
    response = await get_response(runner, session.id, "서울 날씨 어때?")
    assert "서울" in response or "날씨" in response

@pytest.mark.asyncio
async def test_state_persistence(runner, session):
    # 첫 번째 메시지
    await get_response(runner, session.id, "내 이름은 홍길동이야")
    # 두 번째 메시지 (state 유지 확인)
    response = await get_response(runner, session.id, "내 이름이 뭐야?")
    assert "홍길동" in response
```

### 도구 모킹

```python
from unittest.mock import patch

@pytest.mark.asyncio
async def test_with_mocked_tool(runner, session):
    with patch("my_agent.tools.get_weather") as mock_weather:
        mock_weather.return_value = {
            "city": "서울",
            "temp": "25C",
            "condition": "맑음"
        }
        response = await get_response(runner, session.id, "서울 날씨")
        assert "25" in response or "맑음" in response
```

---

## 로컬 개발

### adk web (웹 UI)

대화형 웹 인터페이스로 에이전트를 테스트한다.

```bash
# 기본 실행 (localhost:8000)
adk web my_agent

# 포트 지정
adk web my_agent --port 3000

# 호스트 지정 (외부 접근 허용)
adk web my_agent --host 0.0.0.0 --port 8080
```

웹 UI 제공 기능:
- 대화형 채팅 인터페이스
- 세션 상태 실시간 확인
- 도구 호출 내역 시각화
- 에이전트 전환 추적
- 이벤트 스트림 확인

### adk run (CLI)

터미널에서 에이전트와 대화한다.

```bash
# 대화형 실행
adk run my_agent

# 입력:
# > 서울 날씨 어때?
# 서울의 현재 날씨는 맑고 기온은 20도입니다.
# > /exit
```

---

## 배포: Cloud Run

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["adk", "web", "my_agent", "--host", "0.0.0.0", "--port", "8080"]
```

### requirements.txt

```
google-adk>=1.23.0  # 최신 버전은 pip index versions google-adk 로 확인
```

### 배포 명령어

```bash
# gcloud CLI로 배포
gcloud run deploy my-agent-service \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_API_KEY=your-key"

# 또는 환경 변수 Secret Manager 사용
gcloud run deploy my-agent-service \
    --source . \
    --region us-central1 \
    --set-secrets "GOOGLE_API_KEY=my-api-key:latest"
```

---

## 배포: Vertex AI Agent Engine

완전 관리형 배포. 자동 스케일링, 모니터링, Google Cloud 통합.

### 설정

```python
import vertexai
from vertexai import agent_engines
from my_agent.agent import root_agent

# Vertex AI 초기화
vertexai.init(
    project="your-project-id",
    location="us-central1",
)

# Agent Engine에 배포
remote_agent = agent_engines.create(
    agent_engine=root_agent,
    display_name="My Production Agent",
    description="프로덕션 날씨 에이전트",
)

print(f"Agent deployed: {remote_agent.resource_name}")
```

### 배포된 에이전트 호출

```python
# 원격 에이전트 쿼리
response = remote_agent.query(input="서울 날씨 어때?")
print(response)
```

### 정리

```python
# 배포 삭제
remote_agent.delete()
```

---

## 배포: Custom Server (FastAPI)

기존 웹 서버에 에이전트를 통합한다.

```python
# server.py
from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai.types import Content, Part
from my_agent.agent import root_agent

app = FastAPI()

session_service = DatabaseSessionService(
    db_url="postgresql://user:pass@localhost:5432/mydb"
)
runner = Runner(
    agent=root_agent,
    app_name="my_app",
    session_service=session_service,
)

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    responses = []
    async for event in runner.run_async(
        user_id=req.user_id,
        session_id=req.session_id,
        new_message=Content(parts=[Part(text=req.message)]),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    responses.append(part.text)
    return ChatResponse(response=" ".join(responses))

@app.post("/sessions")
async def create_session(user_id: str):
    session = await session_service.create_session(
        app_name="my_app", user_id=user_id
    )
    return {"session_id": session.id}
```

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## 배포 옵션 비교

| 옵션 | 복잡도 | 확장성 | 관리 비용 | 적합한 경우 |
|------|--------|--------|----------|------------|
| `adk web` (로컬) | 낮음 | 없음 | 없음 | 개발/테스트 |
| Cloud Run | 중간 | 자동 | 낮음 | 일반 프로덕션 |
| Vertex AI | 낮음 | 자동 | 없음 | Google Cloud 환경 |
| Custom Server | 높음 | 수동 | 높음 | 기존 인프라 통합 |
