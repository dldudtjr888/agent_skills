# Optimization Reference Guide

Complete guide to automated prompt and agent optimization with Opik.

**Quick Navigation:**
- [Installation & Quick Start](#installation)
- [Available Optimizers](#available-optimizers) - 7 algorithms compared
- [Advanced Features](#advanced-features) - Tool optimization, chaining, multi-metric
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Benchmarks](#benchmarks)

---

## Installation

```bash
pip install opik-optimizer
```

## Quick Start

```python
from opik import Opik
from opik_optimizer import MetaPromptOptimizer
from opik.evaluation.metrics import LevenshteinRatio

# 1. Load dataset
client = Opik()
dataset = client.get_dataset("my-dataset")

# 2. Define starting prompt
prompt = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "{{input}}"}
    ]
}

# 3. Create and run optimizer
optimizer = MetaPromptOptimizer(model="gpt-4o", max_trials=10)
result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=LevenshteinRatio(),
    n_samples=50
)

# 4. Use best prompt
print(f"Best score: {result.best_score}")
print(f"Best prompt: {result.best_prompt}")
```

## Available Optimizers

### 1. MetaPromptOptimizer

**Best for**: General prompt refinement, MCP tool optimization

**How it works**: LLM acts as prompt engineer, iteratively critiquing and improving

```python
from opik_optimizer import MetaPromptOptimizer

optimizer = MetaPromptOptimizer(
    model="gpt-4o",  # Model for optimization (use reasoning models for best results)
    max_trials=20,
    llm_params={"temperature": 0.7}  # Optional LLM parameters
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric,
    n_samples=100,
    auto_continue=False,  # True to continue past max_trials if improving
    experiment_config={"optimizer": "MetaPrompt", "version": "1.0"}
)
```

**Pros**:
- Works well for complex prompts
- Supports MCP tool optimization
- Good balance of speed and quality

**Cons**:
- Requires powerful model (expensive)
- Can be slower than heuristic methods

### 2. GepaOptimizer

**Best for**: High-quality optimization with reflection

**How it works**: Combines evolutionary algorithm with LLM reflection

```python
from opik_optimizer import GepaOptimizer

optimizer = GepaOptimizer(
    task_model="gpt-4o-mini",  # Model to evaluate prompts
    reflection_model="gpt-4o",  # Model for reflection
    max_trials=20,
    population_size=10,
    reflection_minibatch_size=5,
    seed=42  # For reproducibility
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric
)
```

**Pros**:
- Very high quality results
- Systematic exploration via evolution
- Reflection improves over time

**Cons**:
- Slower than other methods
- More expensive (uses two models)

**Note**: GEPA has two scores:
- **GEPA Score**: Internal score used for evolution
- **Opik Score**: Fresh evaluation on full dataset (use this for comparison)

### 3. FewShotBayesianOptimizer

**Best for**: Optimizing few-shot examples

**How it works**: Uses Bayesian optimization (Optuna) to select best examples from dataset

```python
from opik_optimizer import FewShotBayesianOptimizer

optimizer = FewShotBayesianOptimizer(
    model="gpt-4o",  # Model for few-shot template generation
    max_trials=30,
    n_trials_optuna=50,  # Bayesian optimization trials
    max_examples=5  # Max few-shot examples to include
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric
)
```

**Pros**:
- Very effective for few-shot learning
- Fast compared to LLM-based methods
- Systematic example selection

**Cons**:
- Only optimizes examples, not instructions
- Requires dataset with good example coverage

### 4. EvolutionaryOptimizer

**Best for**: Broad exploration of prompt space

**How it works**: Genetic algorithm with mutation and crossover

```python
from opik_optimizer import EvolutionaryOptimizer

optimizer = EvolutionaryOptimizer(
    model="gpt-4o",
    max_trials=30,
    population_size=10,
    mutation_rate=0.3,
    crossover_rate=0.5
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric
)
```

**Pros**:
- Explores diverse prompt variations
- Good for escaping local optima
- Works without domain knowledge

**Cons**:
- Can be slow
- May produce unusual prompts

### 5. MiproOptimizer

**Best for**: DSPy-based workflows, multi-input optimization

**How it works**: MIPRO algorithm from DSPy

```python
from opik_optimizer import MiproOptimizer

optimizer = MiproOptimizer(
    model="gpt-4o-mini",
    max_trials=20
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric
)
```

**Pros**:
- Battle-tested algorithm
- Good for complex pipelines
- Optimizes demonstrations

**Cons**:
- Requires DSPy understanding
- Less flexible than others

### 6. HierarchicalReflectiveOptimizer

**Best for**: Systematic analysis and improvement

**How it works**: Hierarchical reflection on prompt performance

```python
from opik_optimizer import HierarchicalReflectiveOptimizer

optimizer = HierarchicalReflectiveOptimizer(
    model="gpt-4o",
    max_trials=15,
    reflection_depth=3  # Levels of reflection
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric
)
```

**Pros**:
- Deep analysis of errors
- Structured improvement process

**Cons**:
- Can be slow
- May overthink simple problems

### 7. ParameterOptimizer

**Best for**: Hyperparameter tuning (temperature, top_p, etc.)

**How it works**: Bayesian optimization for LLM parameters

```python
from opik_optimizer import ParameterOptimizer

optimizer = ParameterOptimizer(
    max_trials=30,
    parameters_to_optimize=["temperature", "top_p", "max_tokens"]
)

result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=metric
)

# Access best parameters
print(result.best_prompt["temperature"])
print(result.best_prompt["top_p"])
```

**Pros**:
- Fast and efficient
- Often overlooked but impactful
- Works with any prompt

**Cons**:
- Only optimizes parameters, not content
- Limited impact if prompt is poor

## Optimizer Comparison Table

| Optimizer | Speed | Quality | Cost | Best For |
|-----------|-------|---------|------|----------|
| MetaPrompt | Medium | High | High | General use, tools |
| GEPA | Slow | Very High | Very High | Best quality needed |
| FewShot Bayesian | Fast | High | Medium | Few-shot tasks |
| Evolutionary | Slow | Medium | High | Broad exploration |
| MIPRO | Medium | High | Medium | DSPy workflows |
| Hierarchical | Slow | High | High | Deep analysis |
| Parameter | Fast | Medium | Low | Quick wins |

## Advanced Features

### Tool Optimization (MCP & Function Calling)

**Optimize prompts that use tools** (Beta, MetaPromptOptimizer only):

```python
from opik_optimizer import MetaPromptOptimizer
from opik_optimizer.types import MCPExecutionConfig

# Define MCP tools
mcp_config = MCPExecutionConfig(
    tools=[
        {
            "name": "search_web",
            "description": "Search the internet for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"]
            }
        }
    ]
)

optimizer = MetaPromptOptimizer(model="gpt-4o")

# Optimize both prompt AND tool usage
result = optimizer.optimize_mcp(
    prompt=prompt,
    dataset=dataset,
    metric=metric,
    mcp_config=mcp_config
)
```

**Note**: This optimizes:
- System prompt for tool usage
- Tool descriptions
- When to use which tool

### Chaining Optimizers

Combine multiple optimizers for best results:

```python
# Stage 1: Broad exploration with Evolutionary
evo_optimizer = EvolutionaryOptimizer(model="gpt-4o", max_trials=20)
result1 = evo_optimizer.optimize_prompt(prompt, dataset, metric)

# Stage 2: Refine with MetaPrompt
meta_optimizer = MetaPromptOptimizer(model="gpt-4o", max_trials=10)
result2 = meta_optimizer.optimize_prompt(
    result1.best_prompt,  # Start from best evolutionary result
    dataset,
    metric
)

# Stage 3: Tune parameters
param_optimizer = ParameterOptimizer(max_trials=20)
final_result = param_optimizer.optimize_prompt(
    result2.best_prompt,
    dataset,
    metric
)

print(f"Final score: {final_result.best_score}")
```

### Multi-Metric Optimization

Optimize for multiple metrics simultaneously:

**Method 1: Composite metric**
```python
from opik.evaluation.metrics import Hallucination, AnswerRelevance, BaseMetric, ScoreResult

class CompositeMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="composite")
        self.hallucination = Hallucination()
        self.relevance = AnswerRelevance()
    
    def score(self, input, output, context, **kwargs):
        h_score = self.hallucination.score(input, output, context)
        r_score = self.relevance.score(input, output)
        
        # Weighted average
        combined = 0.7 * h_score.value + 0.3 * r_score.value
        
        return ScoreResult(
            name=self.name,
            value=combined,
            reason=f"Hallucination: {h_score.value:.2f}, Relevance: {r_score.value:.2f}"
        )

optimizer = MetaPromptOptimizer(model="gpt-4o")
result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=CompositeMetric()
)
```

**Method 2: Pareto optimization** (future feature)

### Custom Optimization Strategies

Extend optimizers with custom logic:

```python
from opik_optimizer import MetaPromptOptimizer

class MyCustomOptimizer(MetaPromptOptimizer):
    def generate_candidate(self, current_prompt, feedback):
        # Custom logic to generate next prompt
        # Use LLM, rules, or hybrid approach
        return new_prompt
    
    def should_stop(self, iteration, best_score):
        # Custom stopping criteria
        if best_score > 0.95:  # Stop if good enough
            return True
        return iteration >= self.max_trials

optimizer = MyCustomOptimizer(model="gpt-4o")
result = optimizer.optimize_prompt(prompt, dataset, metric)
```

## Best Practices

### Dataset Requirements

**Size**: 50-200 examples
- Too few: Optimizer overfits
- Too many: Slow, expensive
- Sweet spot: 100-150

**Quality over quantity**:
```python
# Bad: Generic examples
{"input": "Hello", "output": "Hi"}

# Good: Diverse, realistic examples
{"input": "I need to return a defective product", "output": "I'd be happy to help..."}
```

**Coverage**: Include edge cases
- Different phrasings
- Various difficulty levels
- Common failure modes

### Train/Test Split

**Critical**: Always test on holdout set

```python
# Split dataset
train_dataset = client.get_dataset("train")
test_dataset = client.get_dataset("test")

# Optimize on train
result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=train_dataset,
    metric=metric
)

# Evaluate on test
from opik.evaluation import evaluate

test_result = evaluate(
    dataset=test_dataset,
    task=lambda item: my_agent(item["input"], prompt=result.best_prompt),
    scoring_metrics=[metric]
)

print(f"Train score: {result.best_score}")
print(f"Test score: {test_result.mean_scores[metric.name]}")
```

### Baseline Comparison

Always compare against original prompt:

```python
# Baseline
baseline_result = evaluate(dataset, task_with_original_prompt, [metric])

# Optimized
optimized_result = evaluate(dataset, task_with_optimized_prompt, [metric])

improvement = optimized_result.mean_score - baseline_result.mean_score
print(f"Improvement: {improvement:.2%}")
```

### Cost Management

**Use cheaper models for optimization:**
```python
# Expensive: gpt-4o for both optimization and evaluation
optimizer = MetaPromptOptimizer(model="gpt-4o")
prompt.model = "gpt-4o"

# Better: gpt-4o for optimization, gpt-4o-mini for evaluation
optimizer = MetaPromptOptimizer(model="gpt-4o")
prompt.model = "gpt-4o-mini"  # Cheaper model being optimized
```

**Start with fewer trials:**
```python
# Quick test with 5 trials
result_quick = optimizer.optimize_prompt(
    prompt, dataset, metric,
    max_trials=5,
    n_samples=20  # Use subset
)

# If promising, run full optimization
result_full = optimizer.optimize_prompt(
    result_quick.best_prompt,  # Start from quick result
    dataset, metric,
    max_trials=20,
    n_samples=None  # Use full dataset
)
```

### Reproducibility

```python
# Set seeds for reproducibility
optimizer = GepaOptimizer(
    task_model="gpt-4o-mini",
    reflection_model="gpt-4o",
    seed=42  # Reproducible results
)

# Also set in prompt
prompt = {
    "model": "gpt-4o-mini",
    "seed": 42,
    "messages": [...]
}
```

### Monitoring Progress

All optimization runs are logged to Opik:

1. Go to Opik UI → Agent Optimization
2. View all trials with scores
3. Inspect prompt evolution
4. Compare different optimizers

## Troubleshooting

### Not Improving

**Problem**: Score not increasing across trials

**Solutions**:
1. Check dataset quality
   - Too small? Add more examples
   - Too homogeneous? Add diversity
   - Wrong expected outputs? Review manually

2. Try different optimizer
   - GEPA for quality
   - Evolutionary for exploration
   - FewShot if examples matter

3. Increase trials
   ```python
   optimizer = MetaPromptOptimizer(max_trials=30)  # More exploration
   ```

4. Check metric alignment
   - Does metric measure what you care about?
   - Try different metrics

### Overfitting

**Problem**: Good train score, poor test score

**Solutions**:
1. Increase dataset size
2. Add regularization (fewer trials)
3. Use simpler optimizer (Parameter instead of MetaPrompt)
4. Validate on larger test set

### Slow Optimization

**Solutions**:
1. Use subset: `n_samples=50`
2. Reduce trials: `max_trials=10`
3. Use faster optimizer: `ParameterOptimizer`
4. Use cheaper model: `gpt-4o-mini`
5. Reduce `scoring_threads`

### High Cost

**Solutions**:
1. Use `gpt-4o-mini` for optimization
2. Reduce dataset size
3. Cache LLM responses
4. Use heuristic metrics instead of LLM-as-judge

## Benchmarks

Approximate performance on common tasks (GSM8K, HotpotQA):

| Optimizer | Avg Improvement | Time | Cost |
|-----------|----------------|------|------|
| MetaPrompt | +15% | 30 min | $$$ |
| GEPA | +22% | 60 min | $$$$ |
| FewShot | +18% | 20 min | $$ |
| Parameter | +8% | 10 min | $ |
| Evolutionary | +12% | 45 min | $$$ |

**Note**: Results vary by task, dataset, and starting prompt quality.

Run benchmarks yourself:
```bash
cd opik-optimizer
python benchmarks/run_benchmarks.py
```
