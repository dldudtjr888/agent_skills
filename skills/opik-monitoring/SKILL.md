---
name: opik-monitoring
description: Comprehensive guide for building, debugging, evaluating, and monitoring LLM applications and AI agents using Opik. Use when working with LLM observability, agent monitoring, prompt optimization, evaluation metrics, guardrails, or production monitoring. Includes tracing, datasets, experiments, LLM-as-a-judge metrics, agent optimization algorithms, and real-time guardrails for AI safety.
---

# Opik Agent Monitoring & Optimization

End-to-end platform for LLM observability, evaluation, and optimization.

## Quick Start

```bash
# Install
pip install opik

# Configure (choose one)
opik configure              # Cloud (comet.com/opik)
opik configure --use-local  # Self-hosted
```

## Decision Tree: Which Opik Feature Do I Need?

**"I want to see what my LLM/agent is doing"**
→ **Tracing** (references/tracing.md)  
Quick: `@opik.track` decorator or `track_openai(client)`

**"I want to measure how well my app performs"**
→ **Evaluation** (references/evaluation.md)  
Quick: Create dataset → Run `evaluate()` with metrics

**"I want to improve my prompts automatically"**
→ **Optimization** (references/optimization.md)  
Quick: `MetaPromptOptimizer` with dataset + metric

**"I want to prevent harmful outputs/inputs"**
→ **Guardrails** (references/guardrails.md)  
Quick: `PIIGuardrail()` or `TopicGuardrail()`

**"I want to monitor production continuously"**
→ **Production Monitoring** (references/production.md)  
Quick: Set up online evaluation rules in UI

**"I want to integrate with my framework"**
→ **Integrations** (references/integrations.md)  
Quick: Use framework wrapper (40+ supported)

## Core Workflow 1: Instrument & Debug Your Agent

**Goal**: Add observability to understand what your LLM app is doing.

**Steps**:

1. **Add tracking** (choose easiest method):
   ```python
   import opik
   
   # Method A: Function decorator (recommended)
   @opik.track
   def my_agent(input: str) -> str:
       return result
   
   # Method B: Framework integration
   from opik.integrations.openai import track_openai
   client = track_openai(openai.OpenAI())
   ```

2. **View traces in UI**:
   - Go to your Opik dashboard
   - See traces with timing, I/O, costs, errors
   - Click "Inspect trace" for AI-powered analysis

3. **Add metadata** (optional):
   ```python
   @opik.track(
       tags=["production", "v2"],
       metadata={"user_id": "123", "model": "gpt-4o"}
   )
   def my_function(input):
       return output
   ```

**For advanced tracing** (threads, multimodal, distributed): See references/tracing.md

## Core Workflow 2: Evaluate Performance

**Goal**: Measure your app's quality systematically.

**Steps**:

1. **Create a dataset**:
   ```python
   from opik import Opik
   
   client = Opik()
   dataset = client.get_or_create_dataset(name="my-test-cases")
   
   # Add test cases
   dataset.insert([
       {"input": "What is AI?", "expected_output": "Artificial Intelligence..."},
       {"input": "Explain ML", "expected_output": "Machine Learning..."}
   ])
   ```

2. **Define evaluation task**:
   ```python
   def evaluation_task(dataset_item: dict) -> dict:
       # Run your app
       output = my_agent(dataset_item["input"])
       
       # Return required fields for metrics
       return {
           "input": dataset_item["input"],
           "output": output
       }
   ```

3. **Run evaluation with metrics**:
   ```python
   from opik.evaluation import evaluate
   from opik.evaluation.metrics import Hallucination, AnswerRelevance
   
   result = evaluate(
       dataset=dataset,
       task=evaluation_task,
       scoring_metrics=[
           Hallucination(),
           AnswerRelevance()
       ]
   )
   ```

4. **Analyze results** in UI:
   - Compare experiments
   - Filter low-scoring items
   - Export to CSV

**For all metrics, custom metrics, dataset management**: See references/evaluation.md

## Core Workflow 3: Optimize Prompts Automatically

**Goal**: Improve prompts without manual trial-and-error.

**Steps**:

1. **Install optimizer**:
   ```bash
   pip install opik-optimizer
   ```

2. **Prepare dataset & metric** (reuse from Workflow 2)

3. **Run optimization**:
   ```python
   from opik_optimizer import MetaPromptOptimizer
   from opik.evaluation.metrics import LevenshteinRatio
   
   # Starting prompt
   prompt = {
       "model": "gpt-4o-mini",
       "messages": [
           {"role": "system", "content": "You are helpful"},
           {"role": "user", "content": "{{input}}"}
       ]
   }
   
   # Optimize
   optimizer = MetaPromptOptimizer(model="gpt-4o", max_trials=10)
   result = optimizer.optimize_prompt(
       prompt=prompt,
       dataset=dataset,
       metric=LevenshteinRatio(),
       n_samples=50  # Use subset for speed
   )
   
   # Get best prompt
   print(f"Best score: {result.best_score}")
   print(f"Best prompt: {result.best_prompt}")
   ```

4. **Test on holdout set** before deploying

**For all optimizers, tool optimization, chaining**: See references/optimization.md

## Core Workflow 4: Add Production Guardrails

**Goal**: Prevent harmful content in real-time.

**Steps**:

1. **Choose guardrail type**:
   ```python
   from opik.guardrails import PIIGuardrail, TopicGuardrail
   
   # Detect PII
   pii_guard = PIIGuardrail(
       entities=["PERSON", "EMAIL", "PHONE_NUMBER"]
   )
   
   # Enforce topics
   topic_guard = TopicGuardrail(
       allowed_topics=["technology", "science"]
   )
   ```

2. **Integrate with your app**:
   ```python
   @opik.track
   def my_agent(user_input: str) -> str:
       # Validate input
       try:
           pii_guard.validate(input=user_input)
           topic_guard.validate(input=user_input)
       except Exception as e:
           return "Request blocked: " + str(e)
       
       # Process
       response = llm(user_input)
       
       # Validate output
       try:
           pii_guard.validate(output=response)
       except Exception as e:
           return "Response blocked: " + str(e)
       
       return response
   ```

3. **Monitor failures** in Opik UI:
   - Filter traces by guardrail failures
   - View metrics on failure rates

**For custom guardrails, third-party integration**: See references/guardrails.md

## Core Workflow 5: Monitor Production

**Goal**: Continuously evaluate production traces.

**Steps**:

1. **Set up online evaluation rules** (in UI):
   - Navigate to Project → Rules
   - Create rule with:
     - Metric (e.g., Hallucination)
     - Sampling rate (e.g., 10%)
     - Field mappings (trace fields → metric inputs)

2. **View dashboard metrics**:
   - Average scores over time
   - Token usage & costs
   - Error rates
   - Latency distributions

3. **Set up alerts** (Enterprise):
   - Score thresholds
   - Cost anomalies
   - Error spikes

4. **Export data for analysis**:
   ```python
   from opik import Opik
   
   client = Opik()
   traces = client.search_traces(
       project_name="production",
       filters={"tags": ["prod"]},
       limit=1000
   )
   ```

**For alerts, data export, advanced monitoring**: See references/production.md

## Reference Guide Index

Use these guides when you need detailed information beyond the core workflows above:

| Guide | Use When You Need |
|-------|-------------------|
| **tracing.md** | Multi-turn conversations, multimodal traces, distributed tracing, cost tracking |
| **evaluation.md** | All metrics (heuristic + LLM-as-judge), custom metrics, dataset expansion |
| **optimization.md** | Optimizer comparison, tool/MCP optimization, chaining, benchmarks |
| **guardrails.md** | Custom guardrails, third-party integration, advanced validation |
| **production.md** | Advanced monitoring, alerts, data export, Gateway/proxy |
| **integrations.md** | Framework-specific setup (40+ frameworks), troubleshooting |

## Development Best Practices

1. **Start simple**: Begin with @opik.track decorator
2. **Iterate**: Add evaluation once you have traces
3. **Optimize**: Use Agent Optimizer when ready to improve
4. **Protect**: Add guardrails before production
5. **Monitor**: Set up online evaluation for continuous quality checks

## Troubleshooting Quick Fixes

**Traces not appearing?**
```python
# Force flush (for short-lived scripts)
import opik
opik.flush()

# Check config
opik.configure()  # Re-run configuration
```

**Evaluation failing?**
- Check task output has all required metric fields
- Ensure dataset items have expected structure

**Optimization not improving?**
- Verify dataset quality (50-200 diverse examples)
- Try different optimizer
- Increase max_trials

## Resources

- **Full Documentation**: https://www.comet.com/docs/opik/
- **GitHub**: https://github.com/comet-ml/opik
- **Video Tutorials**: Opik University
- **API Reference**: https://www.comet.com/docs/opik/python-sdk-reference/
