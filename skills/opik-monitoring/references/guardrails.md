# Guardrails Reference Guide

Complete guide to real-time validation and safety checks for LLM applications.

**Quick Navigation:**
- [Overview](#overview) - What are guardrails?
- [Built-in Guardrails](#built-in-guardrails) - PII, Topic moderation
- [Custom Guardrails](#custom-guardrails) - Build your own
- [Integration Patterns](#integration-patterns) - With tracing, multiple guardrails
- [Third-Party Integration](#third-party-integration) - Guardrails AI
- [Advanced Patterns](#advanced-patterns)
- [Best Practices](#best-practices)

---

## Overview

Guardrails validate LLM inputs/outputs in real-time, blocking harmful content before it reaches users or your application.

**Key features**:
- Real-time validation (synchronous)
- Automatic logging to Opik traces
- Built-in and custom guardrails
- Third-party integration support

## Built-in Guardrails

### PII Detection

Detect and block personally identifiable information:

```python
from opik.guardrails import PIIGuardrail

# Create guardrail
pii_guard = PIIGuardrail(
    entities=[
        "PERSON",           # Names
        "EMAIL",            # Email addresses
        "PHONE_NUMBER",     # Phone numbers
        "CREDIT_CARD",      # Credit card numbers
        "SSN",              # Social security numbers
        "IP_ADDRESS",       # IP addresses
        "LOCATION",         # Physical locations
        "DATE_TIME",        # Dates and times
        "URL"               # URLs
    ]
)

# Validate input
try:
    result = pii_guard.validate(
        input="My email is john.doe@example.com and my phone is 555-123-4567"
    )
    # Validation passed (unexpected!)
except GuardrailException as e:
    print(f"PII detected: {e}")
    print(f"Detected entities: {e.detected_entities}")
    # Handle: log, redact, reject request
```

**Select specific entities**:
```python
# Only check for email and phone
pii_guard = PIIGuardrail(entities=["EMAIL", "PHONE_NUMBER"])
```

**Redaction instead of blocking**:
```python
from opik.guardrails import PIIGuardrail

class RedactingPIIGuardrail(PIIGuardrail):
    def validate(self, input=None, output=None):
        try:
            super().validate(input, output)
            return {"passed": True, "text": input or output}
        except GuardrailException as e:
            # Redact detected PII
            text = input or output
            for entity in e.detected_entities:
                text = text.replace(entity["text"], "[REDACTED]")
            return {"passed": True, "text": text}

guardrail = RedactingPIIGuardrail()
result = guardrail.validate(input="Email me at john@example.com")
print(result["text"])  # "Email me at [REDACTED]"
```

### Topic Moderation

Ensure content stays on-topic:

```python
from opik.guardrails import TopicGuardrail

# Allow only certain topics
topic_guard = TopicGuardrail(
    allowed_topics=["technology", "science", "education"],
    threshold=0.7  # Confidence threshold (0.0-1.0)
)

try:
    result = topic_guard.validate(
        input="Let's discuss quantum computing and AI"
    )
    # Passes - technology/science topic
except GuardrailException as e:
    print(f"Off-topic: {e}")
```

**Or disallow specific topics**:
```python
# Block certain topics
topic_guard = TopicGuardrail(
    disallowed_topics=["politics", "religion", "violence"]
)

try:
    topic_guard.validate(input="What's your opinion on the election?")
except GuardrailException as e:
    print("Blocked: politics topic")
```

**How it works**:
- Uses zero-shot classification model (BART-based)
- Fast inference (~50ms)
- Configurable threshold

## Custom Guardrails

Create domain-specific validation logic:

```python
from opik.guardrails import BaseGuardrail, GuardrailException

class ProfanityGuardrail(BaseGuardrail):
    def __init__(self):
        self.banned_words = ["badword1", "badword2", "badword3"]
    
    def validate(self, input: str = None, output: str = None) -> dict:
        text = (input or output or "").lower()
        
        for word in self.banned_words:
            if word in text:
                raise GuardrailException(
                    f"Profanity detected: {word}",
                    guardrail_type="profanity",
                    details={"detected_word": word}
                )
        
        return {"passed": True}

# Use it
profanity_guard = ProfanityGuardrail()
```

**LLM-based custom guardrail**:
```python
from opik.guardrails import BaseGuardrail, GuardrailException
from openai import OpenAI

class LLMSafetyGuardrail(BaseGuardrail):
    def __init__(self):
        self.client = OpenAI()
    
    def validate(self, input: str = None, output: str = None) -> dict:
        text = input or output or ""
        
        # Ask LLM to judge safety
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Is this text safe for all audiences?
                
Text: {text}

Respond with JSON: {{"safe": true/false, "reason": "explanation"}}"""
            }],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        if not result["safe"]:
            raise GuardrailException(
                f"Unsafe content: {result['reason']}",
                guardrail_type="llm_safety"
            )
        
        return {"passed": True}
```

**Async guardrails** (for better performance):
```python
import asyncio
from opik.guardrails import BaseGuardrail

class AsyncGuardrail(BaseGuardrail):
    async def avalidate(self, input=None, output=None):
        # Async validation logic
        await asyncio.sleep(0.1)  # Simulated API call
        
        if "bad" in (input or output or ""):
            raise GuardrailException("Bad content")
        
        return {"passed": True}

# Use with async
guardrail = AsyncGuardrail()
result = await guardrail.avalidate(input="test")
```

## Integration Patterns

### With Tracing

Guardrails automatically log to Opik traces:

```python
from opik import track
from opik.guardrails import PIIGuardrail, TopicGuardrail

pii_guard = PIIGuardrail()
topic_guard = TopicGuardrail(allowed_topics=["tech"])

@track
def my_agent(user_input: str) -> str:
    # Validate input
    try:
        pii_guard.validate(input=user_input)
        topic_guard.validate(input=user_input)
    except GuardrailException as e:
        # Guardrail failure logged to trace
        return f"Request blocked: {e}"
    
    # Process request
    response = llm(user_input)
    
    # Validate output
    try:
        pii_guard.validate(output=response)
    except GuardrailException as e:
        # Output failure logged to trace
        return "Response blocked due to safety concerns"
    
    return response
```

**In Opik UI:**
- Failed guardrails shown in trace
- Filter traces by guardrail failures
- View guardrail metrics (failure rate over time)

### Multiple Guardrails

Chain multiple guardrails:

```python
class GuardrailChain:
    def __init__(self, *guardrails):
        self.guardrails = guardrails
    
    def validate(self, input=None, output=None):
        for guardrail in self.guardrails:
            guardrail.validate(input=input, output=output)
        return {"passed": True}

# Create chain
guardrail_chain = GuardrailChain(
    PIIGuardrail(),
    TopicGuardrail(allowed_topics=["tech"]),
    ProfanityGuardrail(),
    LLMSafetyGuardrail()
)

# Validate
try:
    guardrail_chain.validate(input=user_message)
except GuardrailException as e:
    print(f"Failed at: {e.guardrail_type}")
```

### Parallel Guardrails (Async)

Run multiple guardrails in parallel for speed:

```python
import asyncio
from opik.guardrails import PIIGuardrail, TopicGuardrail

async def validate_parallel(text, input_or_output="input"):
    guards = [
        PIIGuardrail(),
        TopicGuardrail(allowed_topics=["tech"]),
        CustomGuardrail()
    ]
    
    # Run all validations in parallel
    kwargs = {input_or_output: text}
    results = await asyncio.gather(
        *[guard.avalidate(**kwargs) for guard in guards],
        return_exceptions=True
    )
    
    # Check for any failures
    for i, result in enumerate(results):
        if isinstance(result, GuardrailException):
            raise result
    
    return {"passed": True}

# Use
try:
    await validate_parallel(user_input, "input")
except GuardrailException as e:
    print(f"Validation failed: {e}")
```

## Third-Party Integration

### Guardrails AI

Integrate with Guardrails AI library:

```python
from guardrails import Guard, OnFailAction
from guardrails.hub import PolitenessCheck, ToxicLanguage
from opik.integrations.guardrails import track_guardrails

# Create Guardrails AI guard
guard = Guard().use_many(
    PolitenessCheck(on_fail=OnFailAction.EXCEPTION),
    ToxicLanguage(threshold=0.5, on_fail=OnFailAction.EXCEPTION)
)

# Wrap with Opik tracking
tracked_guard = track_guardrails(guard, project_name="my-project")

# Use (automatically logged to Opik)
try:
    result = tracked_guard.validate("Your message here")
except Exception as e:
    print(f"Guardrails AI check failed: {e}")
```

**All validations logged to Opik** with:
- Pass/fail status
- Validation details
- Performance metrics

### NeMo Guardrails

```python
# Coming soon
```

### Custom Library Integration

Wrap any validation library:

```python
from opik.guardrails import BaseGuardrail
from some_library import SafetyChecker  # Your library

class CustomLibraryGuardrail(BaseGuardrail):
    def __init__(self):
        self.checker = SafetyChecker()
    
    def validate(self, input=None, output=None):
        text = input or output
        
        # Use library
        is_safe = self.checker.check(text)
        
        if not is_safe:
            raise GuardrailException(
                "Content failed safety check",
                guardrail_type="custom_library"
            )
        
        return {"passed": True}
```

## Advanced Patterns

### Conditional Guardrails

Apply guardrails based on context:

```python
@track
def my_agent(user_input: str, user_role: str) -> str:
    # Stricter validation for public users
    if user_role == "public":
        ProfanityGuardrail().validate(input=user_input)
        TopicGuardrail(disallowed_topics=["politics"]).validate(input=user_input)
    
    # Relaxed for admins
    elif user_role == "admin":
        PIIGuardrail().validate(input=user_input)  # Only check PII
    
    return llm(user_input)
```

### Streaming with Guardrails

Validate streaming outputs chunk-by-chunk:

```python
from opik import track
from opik.guardrails import PIIGuardrail

@track
def streaming_agent(user_input: str):
    pii_guard = PIIGuardrail()
    
    # Validate input
    pii_guard.validate(input=user_input)
    
    # Stream response
    full_response = ""
    for chunk in llm_stream(user_input):
        full_response += chunk
        
        # Validate accumulated response
        try:
            pii_guard.validate(output=full_response)
            yield chunk
        except GuardrailException:
            # Stop streaming if guardrail fails
            yield "[Response terminated due to safety concerns]"
            break
```

### Fallback on Failure

Provide fallback when guardrail fails:

```python
@track
def safe_agent(user_input: str) -> str:
    try:
        # Try with full capabilities
        pii_guard.validate(input=user_input)
        topic_guard.validate(input=user_input)
        return advanced_llm(user_input)
    
    except GuardrailException as e:
        # Fallback to safe, canned response
        if e.guardrail_type == "pii":
            return "I can't process requests with personal information."
        elif e.guardrail_type == "topic":
            return "I can only help with technology-related questions."
        else:
            return "I couldn't process that request."
```

## Performance Considerations

### Latency

**Typical latencies**:
- PII Detection: ~50-100ms
- Topic Moderation: ~50-100ms
- Custom heuristics: <10ms
- LLM-based: 500-2000ms

**Optimization strategies**:
```python
# 1. Run guardrails in parallel (async)
async def fast_validation(text):
    await asyncio.gather(
        pii_guard.avalidate(input=text),
        topic_guard.avalidate(input=text)
    )

# 2. Cache results for repeated inputs
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_validation(text):
    pii_guard.validate(input=text)
    return True

# 3. Sample validation (don't check every request)
import random

if random.random() < 0.1:  # 10% sampling
    guardrail.validate(input=text)
```

### GPU Acceleration

Guardrails backend automatically uses GPU if available:

```bash
# Check GPU usage
nvidia-smi

# Configure GPU device
export CUDA_VISIBLE_DEVICES=0
```

## Monitoring & Analytics

### Metrics Dashboard

View guardrail performance in Opik UI:
- Failure rate over time
- Most common violations
- Latency per guardrail
- Filter by guardrail type

### Alerts

Set up alerts for:
- High failure rate (>5%)
- Specific violation types
- Unusual patterns

```python
# Via SDK (Enterprise)
from opik import Opik

client = Opik()
client.create_alert(
    name="High PII Detection Rate",
    condition="guardrail_failure_rate > 0.05",
    guardrail_type="pii",
    notification_channel="slack"
)
```

## Best Practices

### 1. Layer Defense

Use multiple complementary guardrails:
```python
# Layer 1: Fast heuristics
profanity_guard.validate(input=text)

# Layer 2: Model-based detection
pii_guard.validate(input=text)
topic_guard.validate(input=text)

# Layer 3: LLM-based safety (expensive but thorough)
if high_risk_request:
    llm_safety_guard.validate(input=text)
```

### 2. Log Everything

```python
@track
def my_agent(user_input):
    try:
        guardrail.validate(input=user_input)
        response = llm(user_input)
        guardrail.validate(output=response)
        return response
    except GuardrailException as e:
        # Log to Opik (automatic via @track)
        # Also log to your own system
        logger.warning(f"Guardrail failure: {e}", extra={
            "user_id": user_id,
            "guardrail_type": e.guardrail_type
        })
        raise
```

### 3. Fail Gracefully

```python
def safe_validation(text, guardrail):
    try:
        guardrail.validate(input=text)
        return True
    except GuardrailException:
        return False
    except Exception as e:
        # Guardrail itself failed (model down, etc.)
        logger.error(f"Guardrail error: {e}")
        return True  # Fail open (allow request) or closed (block request)?
```

### 4. Test Guardrails

```python
# Unit tests
def test_pii_detection():
    guard = PIIGuardrail()
    
    # Should fail
    with pytest.raises(GuardrailException):
        guard.validate(input="My email is test@example.com")
    
    # Should pass
    guard.validate(input="Hello, how are you?")

# Integration tests
def test_agent_with_guardrails():
    response = my_agent("Safe input")
    assert response is not None
    
    response = my_agent("email: pii@example.com")
    assert "blocked" in response.lower()
```

## Troubleshooting

**False positives:**
- Adjust thresholds
- Whitelist specific patterns
- Use more specific guardrails

**False negatives:**
- Lower thresholds
- Add more guardrails
- Use LLM-based validation

**Slow performance:**
- Use async validation
- Cache results
- Sample validation
- Use GPU
