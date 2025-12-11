# Production Guide

Deploy agents to production with confidence.

## Error Handling

### Comprehensive Error Handling

```python
from agents.exceptions import (
    MaxTurnsExceeded,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    ModelBehaviorError,
)

async def robust_agent_call(agent, input, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await Runner.run(
                agent,
                input,
                max_turns=20,
            )
            return result
        
        except MaxTurnsExceeded:
            logger.error("Agent exceeded max turns")
            if attempt == max_retries - 1:
                return fallback_response()
        
        except InputGuardrailTripwireTriggered as e:
            logger.warning(f"Input blocked: {e}")
            return {"error": "Input not allowed"}
        
        except OutputGuardrailTripwireTriggered as e:
            logger.warning(f"Output blocked: {e}")
            if attempt == max_retries - 1:
                return {"error": "Could not generate safe output"}
        
        except ModelBehaviorError as e:
            logger.error(f"Model error: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt == max_retries - 1:
                raise
```

### Rate Limiting

```python
from asyncio import Semaphore
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_calls: int, period: timedelta):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.semaphore = Semaphore(max_calls)
    
    async def __aenter__(self):
        async with self.semaphore:
            now = datetime.now()
            
            # Remove old calls
            cutoff = now - self.period
            self.calls = [c for c in self.calls if c > cutoff]
            
            # Wait if at limit
            if len(self.calls) >= self.max_calls:
                wait_time = (self.calls[0] - cutoff).total_seconds()
                await asyncio.sleep(wait_time)
            
            self.calls.append(now)
    
    async def __aexit__(self, *args):
        pass

# Usage
limiter = RateLimiter(max_calls=100, period=timedelta(minutes=1))

async with limiter:
    result = await Runner.run(agent, input)
```

## Security

### Input Validation

```python
def validate_input(user_input: str) -> bool:
    # Check length
    if len(user_input) > 10000:
        return False
    
    # Check for malicious patterns
    dangerous_patterns = ["eval(", "exec(", "import os"]
    if any(pattern in user_input.lower() for pattern in dangerous_patterns):
        return False
    
    return True

async def safe_agent_call(user_input: str):
    if not validate_input(user_input):
        return {"error": "Invalid input"}
    
    result = await Runner.run(agent, user_input)
    return result.final_output
```

### API Key Management

```python
import os
from pathlib import Path

# Use environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Or use secrets management
from google.cloud import secretmanager

def get_api_key():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/PROJECT_ID/secrets/openai-api-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

## Monitoring

### Metrics Collection

```python
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class AgentMetrics:
    duration: float
    input_length: int
    output_length: int
    tool_calls: int
    handoffs: int
    success: bool
    error: Optional[str] = None

async def monitored_run(agent, input):
    start = time.time()
    
    try:
        result = await Runner.run(agent, input)
        
        metrics = AgentMetrics(
            duration=time.time() - start,
            input_length=len(input),
            output_length=len(result.final_output),
            tool_calls=sum(1 for item in result.new_items if item.type == "tool_call_item"),
            handoffs=sum(1 for item in result.new_items if item.type == "handoff_item"),
            success=True,
        )
        
        log_metrics(metrics)
        return result
    
    except Exception as e:
        metrics = AgentMetrics(
            duration=time.time() - start,
            input_length=len(input),
            output_length=0,
            tool_calls=0,
            handoffs=0,
            success=False,
            error=str(e),
        )
        
        log_metrics(metrics)
        raise
```

### Alerting

```python
async def monitored_agent_with_alerts(agent, input):
    result = await monitored_run(agent, input)
    
    # Alert on slow responses
    if result.duration > 10.0:
        send_alert(f"Slow response: {result.duration}s")
    
    # Alert on errors
    if not result.success:
        send_alert(f"Agent error: {result.error}")
    
    return result
```

## Cost Optimization

### Model Selection

```python
# Use cheaper models for simple tasks
simple_agent = Agent(
    name="Simple",
    instructions="...",
    model_settings=ModelSettings(model="gpt-4o-mini"),
)

# Use expensive models only when needed
complex_agent = Agent(
    name="Complex",
    instructions="...",
    model_settings=ModelSettings(model="gpt-4o"),
)
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def cached_agent_call(input: str) -> str:
    result = await Runner.run(agent, input)
    return result.final_output

# Or use Redis
import redis.asyncio as redis

redis_client = redis.Redis(...)

async def redis_cached_call(input: str) -> str:
    # Check cache
    cached = await redis_client.get(f"agent:{input}")
    if cached:
        return cached.decode()
    
    # Call agent
    result = await Runner.run(agent, input)
    
    # Cache result
    await redis_client.setex(
        f"agent:{input}",
        3600,  # 1 hour
        result.final_output
    )
    
    return result.final_output
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-service
  template:
    metadata:
      labels:
        app: agent-service
    spec:
      containers:
      - name: agent-service
        image: agent-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Best Practices

1. **Always Use Tracing**: Enable for all production runs
2. **Implement Retries**: Handle transient failures
3. **Set Timeouts**: Prevent hanging operations
4. **Monitor Costs**: Track token usage
5. **Use Guardrails**: Validate all inputs/outputs
6. **Implement Circuit Breakers**: Fail fast when downstream is down
7. **Log Everything**: Comprehensive logging for debugging
8. **Version Control**: Track prompt/instruction changes
9. **A/B Testing**: Test changes with subset of traffic
10. **Gradual Rollouts**: Deploy incrementally

## Resources

- [Production Checklist](https://platform.openai.com/docs/guides/production-best-practices)
- [Security Guide](https://platform.openai.com/docs/guides/safety-best-practices)
