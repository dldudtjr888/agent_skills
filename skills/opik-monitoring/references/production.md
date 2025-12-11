# Production Monitoring Reference Guide

Complete guide to monitoring LLM applications in production with Opik.

**Quick Navigation:**
- [Online Evaluation Rules](#online-evaluation-rules) - Auto-score production traces
- [Dashboard Analytics](#dashboard-analytics) - Metrics, filtering, export
- [Alerts](#alerts-enterprise) - Configure notifications
- [Advanced Monitoring](#advanced-monitoring) - Custom dashboards, A/B testing
- [Gateway](#gateway-enterprise) - LLM proxy features
- [Production Best Practices](#production-best-practices)
- [Cost Optimization](#cost-optimization)

---

## Online Evaluation Rules

Automatically evaluate production traces with LLM-as-a-judge metrics.

### Setup via UI

1. Navigate to your project
2. Go to "Rules" tab
3. Click "Create new rule"
4. Configure:
   - **Rule name**: e.g., "Production Hallucination Check"
   - **Metric**: Select from dropdown (Hallucination, AnswerRelevance, etc.)
   - **Sampling rate**: 0.0-1.0 (e.g., 0.1 = 10% of traces)
   - **Field mappings**: Map trace fields → metric parameters
5. Save

**Field mapping example**:
```
Metric parameter "input" ← Trace field "input.question"
Metric parameter "output" ← Trace field "output.answer"
Metric parameter "context" ← Trace field "metadata.retrieved_docs"
```

### Setup via SDK

```python
from opik import Opik
from opik.evaluation.metrics import Hallucination

client = Opik()

# Create rule
rule = client.create_scoring_rule(
    name="hallucination-check-prod",
    metric=Hallucination(model_name="gpt-4o"),
    sampling_rate=0.1,  # 10% of traces
    field_mappings={
        "input": "input.question",
        "output": "output.answer",
        "context": "metadata.context"
    },
    filters={
        "tags": ["production"],  # Only traces with this tag
        "project_name": "my-prod-project"
    }
)
```

### Multiple Rules

Set up rules for different metrics:

```python
# Rule 1: Check hallucinations
client.create_scoring_rule(
    name="hallucination-check",
    metric=Hallucination(),
    sampling_rate=0.2
)

# Rule 2: Check answer relevance
client.create_scoring_rule(
    name="relevance-check",
    metric=AnswerRelevance(),
    sampling_rate=0.15
)

# Rule 3: Check moderation
client.create_scoring_rule(
    name="safety-check",
    metric=Moderation(),
    sampling_rate=1.0  # Check all traces
)
```

### Thread-Level Evaluation

Evaluate entire conversations:

```python
from opik.evaluation.metrics import ConversationCoherence

# This runs on complete threads (after they go inactive)
client.create_scoring_rule(
    name="conversation-quality",
    metric=ConversationCoherence(),
    sampling_rate=0.05,
    target="thread"  # Evaluate threads, not individual traces
)
```

## Dashboard Analytics

### Accessing the Dashboard

Navigate to your Opik project → Dashboard

### Key Metrics

**Trace Metrics**:
- Total trace count (hourly/daily)
- Traces with errors
- Average response time
- p50, p95, p99 latency

**Quality Metrics**:
- Average feedback scores by metric
- Score trends over time
- Score distribution histograms

**Cost Metrics**:
- Total tokens used (prompt + completion)
- Estimated cost in USD
- Cost by model
- Cost trends

**Guardrail Metrics**:
- Guardrail failure rate
- Failures by type (PII, topic, etc.)
- Blocked requests

### Filtering & Grouping

**Filter by**:
- Date range
- Project
- Tags
- Model
- User ID
- Error status

**Group by**:
- Model
- Temperature
- Tags
- Custom metadata fields

**Example**: "Show me GPT-4 traces from last week with score < 0.5"

### Exporting Data

**Via UI**:
1. Filter traces as desired
2. Select traces
3. Actions → Export CSV

**Via SDK**:
```python
from opik import Opik
import pandas as pd

client = Opik()

# Search traces
traces = client.search_traces(
    project_name="production",
    filters={
        "tags": ["prod"],
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-31T23:59:59Z"
    },
    limit=10000
)

# Convert to DataFrame
df = pd.DataFrame([{
    "id": t.id,
    "input": t.input,
    "output": t.output,
    "start_time": t.start_time,
    "end_time": t.end_time,
    "tags": t.tags,
    "metadata": t.metadata
} for t in traces])

# Analyze or export
df.to_csv("production_traces.csv")
```

**Export spans**:
```python
spans = client.search_spans(
    project_name="production",
    filters={"type": "llm"},
    limit=10000
)

df_spans = pd.DataFrame([{
    "trace_id": s.trace_id,
    "name": s.name,
    "type": s.type,
    "input": s.input,
    "output": s.output,
    "usage": s.usage
} for s in spans])
```

## Alerts (Enterprise)

Configure alerts for production issues.

### Alert Types

**Score-based alerts**:
```python
client.create_alert(
    name="Low Answer Relevance",
    condition="average_score < 0.7",
    metric="AnswerRelevance",
    window="1h",  # Check every hour
    notification_channels=["email", "slack"]
)
```

**Cost alerts**:
```python
client.create_alert(
    name="High Cost",
    condition="daily_cost > 100",  # $100/day
    notification_channels=["email"]
)
```

**Error rate alerts**:
```python
client.create_alert(
    name="High Error Rate",
    condition="error_rate > 0.05",  # >5% errors
    window="15m",
    notification_channels=["slack", "pagerduty"]
)
```

**Latency alerts**:
```python
client.create_alert(
    name="Slow Responses",
    condition="p95_latency > 5000",  # >5 seconds
    window="5m",
    notification_channels=["slack"]
)
```

### Notification Channels

**Email**:
```python
client.add_notification_channel(
    type="email",
    config={"recipients": ["team@example.com"]}
)
```

**Slack**:
```python
client.add_notification_channel(
    type="slack",
    config={
        "webhook_url": "https://hooks.slack.com/...",
        "channel": "#alerts"
    }
)
```

**PagerDuty** (Enterprise):
```python
client.add_notification_channel(
    type="pagerduty",
    config={"integration_key": "..."}
)
```

## Advanced Monitoring

### Custom Dashboards

Create custom visualizations:

```python
from opik import Opik
import plotly.express as px

client = Opik()

# Get data
traces = client.search_traces(project_name="prod", limit=1000)

# Extract metrics
timestamps = [t.start_time for t in traces]
latencies = [(t.end_time - t.start_time) * 1000 for t in traces]

# Plot
fig = px.line(x=timestamps, y=latencies, title="Response Latency Over Time")
fig.show()
```

### Segment Analysis

Analyze performance by user segment:

```python
# Get traces with user metadata
traces = client.search_traces(
    project_name="prod",
    filters={"metadata.user_tier": "premium"}
)

premium_scores = [t.feedback_scores.get("quality", 0) for t in traces]

# Compare with free tier
free_traces = client.search_traces(
    filters={"metadata.user_tier": "free"}
)

free_scores = [t.feedback_scores.get("quality", 0) for t in free_traces]

print(f"Premium avg: {sum(premium_scores)/len(premium_scores):.2f}")
print(f"Free avg: {sum(free_scores)/len(free_scores):.2f}")
```

### A/B Testing

Track different model versions:

```python
# Deploy two versions
@track(tags=["model-a"], metadata={"model": "gpt-4o"})
def agent_v1(input):
    return gpt4o(input)

@track(tags=["model-b"], metadata={"model": "gpt-4o-mini"})
def agent_v2(input):
    return gpt4o_mini(input)

# Random assignment
import random

def serve_request(input):
    if random.random() < 0.5:
        return agent_v1(input)
    else:
        return agent_v2(input)
```

**Analyze in dashboard**:
- Filter by tags: `model-a` vs `model-b`
- Compare average scores
- Compare costs
- Compare latencies

### Anomaly Detection

Set up anomaly detection:

```python
from opik import Opik
import numpy as np

client = Opik()

def detect_anomalies():
    # Get recent traces
    traces = client.search_traces(
        project_name="prod",
        filters={"start_time": "last_24h"}
    )
    
    # Calculate hourly error rates
    hourly_errors = {}  # hour -> error_count
    hourly_totals = {}  # hour -> total_count
    
    for trace in traces:
        hour = trace.start_time.strftime("%Y-%m-%d %H:00")
        hourly_totals[hour] = hourly_totals.get(hour, 0) + 1
        if trace.error:
            hourly_errors[hour] = hourly_errors.get(hour, 0) + 1
    
    # Calculate error rates
    error_rates = {
        hour: hourly_errors.get(hour, 0) / total
        for hour, total in hourly_totals.items()
    }
    
    # Detect anomalies (simple threshold)
    baseline = np.mean(list(error_rates.values()))
    threshold = baseline * 2  # 2x baseline
    
    anomalies = {
        hour: rate
        for hour, rate in error_rates.items()
        if rate > threshold
    }
    
    if anomalies:
        print(f"⚠️  Anomalies detected: {anomalies}")
        # Send alert
```

## Gateway (Enterprise)

LLM proxy for centralized logging and control.

### Setup

```python
from opik.gateway import Gateway

gateway = Gateway(
    project_name="production",
    default_model="gpt-4o"
)

# Use as OpenAI client
response = gateway.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
# Automatically logged to Opik
```

### Features

**Rate Limiting**:
```python
gateway = Gateway(
    rate_limits={
        "gpt-4o": {"requests_per_minute": 100},
        "gpt-4o-mini": {"requests_per_minute": 500}
    }
)
```

**Cost Control**:
```python
gateway = Gateway(
    cost_limits={
        "daily_budget": 100,  # $100/day
        "per_request_max": 0.50  # Max $0.50 per request
    }
)
```

**Model Routing**:
```python
gateway = Gateway(
    routing_rules={
        "cheap_tasks": "gpt-4o-mini",
        "complex_tasks": "gpt-4o",
        "fallback": "claude-3-sonnet"
    }
)

# Automatic routing based on task complexity
response = gateway.chat.completions.create(
    model="auto",  # Gateway chooses
    messages=[...]
)
```

**Caching**:
```python
gateway = Gateway(
    cache_enabled=True,
    cache_ttl=3600  # 1 hour
)

# Duplicate requests served from cache
```

## Production Best Practices

### 1. Sampling Strategy

Don't evaluate every trace:

```python
# High-traffic apps: sample 5-10%
client.create_scoring_rule(
    metric=Hallucination(),
    sampling_rate=0.05  # 5%
)

# Critical paths: sample 100%
client.create_scoring_rule(
    metric=Moderation(),
    sampling_rate=1.0,
    filters={"tags": ["critical"]}
)

# Experimental features: sample heavily
client.create_scoring_rule(
    metric=AnswerRelevance(),
    sampling_rate=0.5,  # 50%
    filters={"tags": ["beta"]}
)
```

### 2. Progressive Rollout

Roll out changes gradually:

```python
# Week 1: 5% traffic
@track(tags=["new-model"], metadata={"rollout": "5pct"})
def new_agent(input):
    return new_model(input)

if random.random() < 0.05:
    return new_agent(input)
else:
    return old_agent(input)

# Monitor dashboard for issues
# Week 2: Increase to 25% if metrics good
# Week 3: 50%
# Week 4: 100%
```

### 3. Alerting Hierarchy

Set up tiered alerts:

```python
# P1: Immediate action required
client.create_alert(
    name="Production Down",
    condition="error_rate > 0.5",  # >50% errors
    severity="critical",
    channels=["pagerduty", "sms"]
)

# P2: Investigate soon
client.create_alert(
    name="High Error Rate",
    condition="error_rate > 0.1",  # >10% errors
    severity="high",
    channels=["slack"]
)

# P3: Monitor
client.create_alert(
    name="Elevated Errors",
    condition="error_rate > 0.05",  # >5% errors
    severity="medium",
    channels=["email"]
)
```

### 4. Regular Reporting

Generate weekly reports:

```python
def weekly_report():
    client = Opik()
    
    # Get week's data
    traces = client.search_traces(
        filters={"start_time": "last_7d"}
    )
    
    # Calculate metrics
    total_traces = len(traces)
    avg_latency = np.mean([
        (t.end_time - t.start_time) * 1000 
        for t in traces
    ])
    error_rate = len([t for t in traces if t.error]) / total_traces
    total_cost = sum([
        t.metadata.get("cost", 0) 
        for t in traces
    ])
    
    # Send report
    report = f"""
    Weekly Report (Week of {datetime.now().strftime('%Y-%m-%d')})
    
    Total Requests: {total_traces:,}
    Avg Latency: {avg_latency:.0f}ms
    Error Rate: {error_rate:.2%}
    Total Cost: ${total_cost:.2f}
    
    Top Errors:
    {get_top_errors(traces)}
    """
    
    send_email(to="team@example.com", subject="Weekly LLM Report", body=report)
```

### 5. Incident Response

Set up runbooks:

```markdown
# Incident: High Error Rate

## Detection
- Alert triggered: error_rate > 10%

## Investigation
1. Check Opik dashboard for error patterns
2. Filter traces by error type
3. Review recent deployments
4. Check external dependencies (OpenAI status, etc.)

## Mitigation
- If model issue: Switch to fallback model
- If deployment issue: Rollback
- If rate limit: Reduce traffic or switch models

## Communication
- Update status page
- Notify team on Slack
- Email affected customers if needed

## Post-Incident
- Root cause analysis
- Update monitoring/alerts
- Document in incident log
```

## Cost Optimization

### Track Costs

```python
# View cost breakdown
traces = client.search_traces(project_name="prod")

costs_by_model = {}
for trace in traces:
    model = trace.metadata.get("model")
    cost = trace.metadata.get("cost", 0)
    costs_by_model[model] = costs_by_model.get(model, 0) + cost

for model, total_cost in sorted(costs_by_model.items(), key=lambda x: x[1], reverse=True):
    print(f"{model}: ${total_cost:.2f}")
```

### Optimization Strategies

**1. Model selection**:
```python
# Use cheaper models for simple tasks
def route_to_model(task_complexity):
    if task_complexity == "simple":
        return "gpt-4o-mini"  # Cheaper
    elif task_complexity == "medium":
        return "gpt-4o"
    else:
        return "o1"  # Most expensive, for hardest tasks
```

**2. Prompt optimization**:
- Use Agent Optimizer to reduce tokens
- Remove unnecessary context
- Use shorter system prompts

**3. Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_llm_call(prompt):
    return llm(prompt)
```

**4. Batch processing**:
```python
# Process multiple items in one call
def batch_process(items):
    prompt = "Process these items:\n" + "\n".join(items)
    return llm(prompt)  # More efficient than individual calls
```

## Troubleshooting Production Issues

### High Latency

**Diagnosis**:
- Check p95/p99 latency in dashboard
- Filter slow traces
- Identify common patterns

**Solutions**:
- Use faster models (gpt-4o-mini)
- Reduce max_tokens
- Implement caching
- Use parallel processing

### High Costs

**Diagnosis**:
- Check cost trends in dashboard
- Identify expensive models/prompts
- Find high-token-usage traces

**Solutions**:
- Switch to cheaper models
- Optimize prompts (fewer tokens)
- Implement caching
- Add rate limits

### Low Quality Scores

**Diagnosis**:
- Check score trends
- Filter low-scoring traces
- Review evaluation metrics

**Solutions**:
- Run prompt optimization
- Add more context to prompts
- Switch to more capable model
- Update training data
