# LLM 프로바이더 통합

PydanticAI가 지원하는 LLM 프로바이더 설정과 FallbackModel 패턴.

---

## 프로바이더 목록

| 프로바이더 | 모델 문자열 | 설치 | 환경 변수 |
|-----------|------------|------|----------|
| **OpenAI** | `'openai:gpt-4o'` | 기본 포함 | `OPENAI_API_KEY` |
| **Anthropic** | `'anthropic:claude-sonnet-4-20250514'` | 기본 포함 | `ANTHROPIC_API_KEY` |
| **Google Gemini (AI Studio)** | `'google-gla:gemini-2.0-flash'` | 기본 포함 | `GEMINI_API_KEY` |
| **Google Gemini (Vertex)** | `'google-vertex:gemini-2.0-flash'` | 기본 포함 | GCP 인증 |
| **Groq** | `'groq:llama-3.3-70b-versatile'` | 기본 포함 | `GROQ_API_KEY` |
| **Mistral** | `'mistral:mistral-large-latest'` | 기본 포함 | `MISTRAL_API_KEY` |
| **Cohere** | `'cohere:command-r-plus'` | 기본 포함 | `CO_API_KEY` |
| **AWS Bedrock** | `'bedrock:...'` | 기본 포함 | AWS 인증 |
| **xAI (Grok)** | OpenAI 호환 | 기본 포함 | `XAI_API_KEY` |

---

## 프로바이더별 설정

### OpenAI

```python
from pydantic_ai import Agent

# 문자열 방식 (가장 간단)
agent = Agent('openai:gpt-4o')

# Provider 클래스 사용 (커스텀 설정)
from pydantic_ai.providers.openai import OpenAIProvider

agent = Agent(
    'openai:gpt-4o',
    provider=OpenAIProvider(api_key='sk-...'),  # 명시적 키
)
```

### Anthropic

```python
agent = Agent('anthropic:claude-sonnet-4-20250514')

# 또는 Claude 3.5 Haiku (빠르고 저렴)
agent = Agent('anthropic:claude-3-5-haiku-20241022')
```

### Google Gemini

```python
# AI Studio API
agent = Agent('google-gla:gemini-2.0-flash')

# Vertex AI
agent = Agent('google-vertex:gemini-2.0-flash')
```

### Groq (빠른 추론)

```python
agent = Agent('groq:llama-3.3-70b-versatile')
# 또는
agent = Agent('groq:mixtral-8x7b-32768')
```

### OpenAI 호환 API (DeepSeek, Ollama 등)

```python
from pydantic_ai.providers.openai import OpenAIProvider

# DeepSeek
agent = Agent(
    'openai:deepseek-chat',
    provider=OpenAIProvider(
        base_url='https://api.deepseek.com',
        api_key='...',
    ),
)

# Ollama (로컬)
agent = Agent(
    'openai:llama3.2',
    provider=OpenAIProvider(
        base_url='http://localhost:11434/v1',
        api_key='ollama',  # 아무 값
    ),
)

# OpenRouter
agent = Agent(
    'openai:anthropic/claude-sonnet-4-20250514',
    provider=OpenAIProvider(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-...',
    ),
)
```

---

## FallbackModel (장애 대비)

여러 모델을 순서대로 시도. 4xx/5xx 에러 시 자동으로 다음 모델로 전환.

```python
from pydantic_ai import Agent
from pydantic_ai.models import FallbackModel

agent = Agent(
    FallbackModel(
        'openai:gpt-4o',              # 1차: OpenAI
        'anthropic:claude-sonnet-4-20250514',  # 2차: Anthropic
        'groq:llama-3.3-70b-versatile',        # 3차: Groq
    ),
    output_type=MyOutput,
)

# ValidationError는 retry (같은 모델에서 재시도)
# HTTP 4xx/5xx는 fallback (다음 모델로 전환)
```

---

## ModelSettings (모델 튜닝)

```python
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

# Agent 생성 시 기본값 설정
agent = Agent(
    'openai:gpt-4o',
    model_settings=ModelSettings(
        temperature=0.0,        # 결정적 출력 (분석/분류에 적합)
        max_tokens=4096,        # 최대 응답 길이
        top_p=0.9,              # 핵 샘플링
        timeout=30,             # 요청 타임아웃 (초)
    ),
)

# 실행 시 오버라이드
result = agent.run_sync(
    'creative writing task',
    model_settings={'temperature': 0.9},  # 이번만 창의적
)
```

### 작업별 권장 설정

| 작업 유형 | temperature | max_tokens | 비고 |
|----------|-------------|------------|------|
| 분류/분석 | 0.0 | 1000 | 결정적, 짧은 응답 |
| 코드 생성 | 0.1 | 4096 | 약간의 변동, 긴 출력 |
| 창작/글쓰기 | 0.7~0.9 | 4096 | 다양성 확보 |
| 데이터 추출 | 0.0 | 2000 | 정확한 구조화 |

---

## 환경 변수 관리

```python
# .env 파일
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
GROQ_API_KEY=gsk_...

# Python에서 로드
from dotenv import load_dotenv
load_dotenv()

# PydanticAI는 자동으로 환경 변수에서 API 키를 읽음
agent = Agent('openai:gpt-4o')  # OPENAI_API_KEY 자동 사용
```

---

## 모델 선택 가이드

```
정확성 + 복잡한 추론 필요
  → OpenAI gpt-4o / Anthropic claude-sonnet-4

빠른 응답 + 비용 절감
  → OpenAI gpt-4o-mini / Groq llama-3.3

긴 컨텍스트 (100K+ 토큰)
  → Google gemini-2.0-flash / Anthropic claude-sonnet

로컬 실행 (프라이버시)
  → Ollama + llama3.2 (OpenAI 호환)

장애 대비
  → FallbackModel로 3개 프로바이더 체이닝
```
