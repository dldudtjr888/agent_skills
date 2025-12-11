# Evaluation Reference Guide

Complete guide to evaluating LLM applications with Opik.

**Quick Navigation:**
- [Dataset Management](#dataset-management) - Create, manage, expand datasets
- [Evaluation Metrics](#evaluation-metrics) - Heuristic & LLM-as-a-judge
- [Running Evaluations](#running-evaluations) - Prompts, apps, agents
- [Experiment Management](#experiment-management) - Compare, re-run
- [Best Practices](#best-practices)

---

## Dataset Management

### Creating Datasets

**Method 1: Python SDK**
```python
from opik import Opik

client = Opik()

# Create or get existing
dataset = client.get_or_create_dataset(
    name="my-test-cases",
    description="Evaluation dataset for customer support bot"
)

# Add items
dataset.insert([
    {
        "input": "How do I reset my password?",
        "expected_output": "Click 'Forgot Password' on the login page..."
    },
    {
        "input": "What are your business hours?",
        "expected_output": "We're open Monday-Friday, 9am-5pm EST"
    }
])
```

**Method 2: From Pandas**
```python
import pandas as pd

df = pd.DataFrame({
    "input": ["Question 1", "Question 2"],
    "expected_output": ["Answer 1", "Answer 2"],
    "category": ["billing", "technical"]
})

dataset.insert_from_pandas(df)
```

**Method 3: From JSONL**
```python
# File format: one JSON object per line
dataset.read_jsonl_from_file(
    "test_cases.jsonl",
    keys_mapping={"question": "input", "answer": "expected_output"}
)
```

**Method 4: From CSV (UI)**
- Navigate to Evaluation → Datasets
- Click "Create new dataset"
- Upload CSV (max 1,000 rows via UI)
- For >1,000 rows, use SDK

**Method 5: From Traces (UI)**
- Select traces in Traces view
- Actions → Add to dataset
- Useful for creating evaluation sets from production data

### Dataset Operations

**Get dataset:**
```python
dataset = client.get_dataset(name="my-dataset")
```

**Update items:**
```python
# Get items first
items = dataset.get_items(limit=10)

# Modify
for item in items:
    item["expected_output"] = "Updated answer"

# Update
dataset.update(items)
```

**Delete items:**
```python
dataset.delete(item_ids=["item-id-1", "item-id-2"])
```

**Convert to DataFrame:**
```python
df = dataset.to_pandas()
```

**Export to JSON:**
```python
json_str = dataset.to_json()
```

### AI-Assisted Dataset Expansion

Generate variations of existing examples:

```python
# Expand dataset with variations
dataset.expand(
    n_samples=50,  # Generate 50 new samples
    preserve_fields=["category"],  # Keep category unchanged
    variation_instructions="""
    Create variations with:
    - Different phrasings
    - Different difficulty levels
    - Different user personas (beginner, advanced, frustrated)
    """
)
```

**Best practices:**
- Start with 5-10 high-quality examples
- Review generated samples before using
- Iterate on instructions for better results

## Evaluation Metrics

### Heuristic Metrics (Deterministic)

**Equals** - Exact match:
```python
from opik.evaluation.metrics import Equals

metric = Equals()
score = metric.score(
    output="Paris",
    reference="Paris"
)
# Returns: ScoreResult(value=1.0, name="Equals")
```

**Contains** - Substring check:
```python
from opik.evaluation.metrics import Contains

metric = Contains()
score = metric.score(
    output="The capital of France is Paris",
    reference="Paris"
)
# Returns: ScoreResult(value=1.0)
```

**RegexMatch** - Pattern matching:
```python
from opik.evaluation.metrics import RegexMatch

metric = RegexMatch(regex=r"\d{3}-\d{3}-\d{4}")  # Phone number
score = metric.score(output="Call us at 555-123-4567")
# Returns: ScoreResult(value=1.0)
```

**IsJson** - Valid JSON check:
```python
from opik.evaluation.metrics import IsJson

metric = IsJson()
score = metric.score(output='{"name": "John", "age": 30}')
# Returns: ScoreResult(value=1.0)
```

**LevenshteinRatio** - String similarity (0-1):
```python
from opik.evaluation.metrics import LevenshteinRatio

metric = LevenshteinRatio()
score = metric.score(
    output="The cat sat on the mat",
    reference="The cat sit on the mat"
)
# Returns: ScoreResult(value=0.95)  # High similarity
```

**BLEU** - Translation quality:
```python
from opik.evaluation.metrics import SentenceBLEU, CorpusBLEU

# Single sentence
metric = SentenceBLEU()
score = metric.score(
    output="the cat is on the mat",
    references=["the cat sits on the mat", "there is a cat on the mat"]
)

# Corpus (multiple sentences)
metric = CorpusBLEU()
score = metric.score(
    outputs=["sentence 1", "sentence 2"],
    references=[
        ["reference 1a", "reference 1b"],  # Multiple refs for sentence 1
        ["reference 2a"]  # One ref for sentence 2
    ]
)
```

**Sentiment** - Sentiment analysis (-1 to 1):
```python
from opik.evaluation.metrics import Sentiment

metric = Sentiment()
score = metric.score(output="I love this product! It's amazing!")
# Returns: ScoreResult(value=0.95)  # Very positive
```

### LLM-as-a-Judge Metrics

All LLM-as-a-judge metrics use GPT-4o by default. Customize with `model_name` parameter.

**Hallucination** - Detect factual inconsistencies:
```python
from opik.evaluation.metrics import Hallucination

metric = Hallucination(model_name="gpt-4o")  # Optional
score = metric.score(
    input="What is the capital of France?",
    output="The capital of France is London.",  # Hallucination!
    context=["France is a country in Europe.", "Paris is the capital of France."]
)
# Returns: ScoreResult(
#     value=0.1,  # Low score = likely hallucination
#     reason="The output contradicts the context. Paris is mentioned as the capital, not London."
# )
```

**AnswerRelevance** - Check if answer addresses question:
```python
from opik.evaluation.metrics import AnswerRelevance

metric = AnswerRelevance()
score = metric.score(
    input="What is the capital of France?",
    output="France is a beautiful country with great food."  # Not relevant
)
# Returns: ScoreResult(
#     value=0.2,  # Low relevance
#     reason="The output doesn't answer the question about the capital."
# )
```

**ContextPrecision** - Quality of retrieved context:
```python
from opik.evaluation.metrics import ContextPrecision

metric = ContextPrecision()
score = metric.score(
    input="What is the capital of France?",
    context=[
        "Paris is the capital of France.",  # Relevant
        "The Eiffel Tower is in Paris.",  # Somewhat relevant
        "The weather is nice today."  # Not relevant
    ],
    expected_output="Paris"
)
# Measures how much of the context is actually relevant
```

**ContextRecall** - Does context contain answer:
```python
from opik.evaluation.metrics import ContextRecall

metric = ContextRecall()
score = metric.score(
    input="What is the capital of France?",
    context=["France has many cities.", "Lyon is a major city."],  # Missing Paris!
    expected_output="Paris"
)
# Returns: ScoreResult(
#     value=0.0,  # Context doesn't contain the answer
#     reason="The expected output 'Paris' is not found in the context."
# )
```

**Moderation** - General content safety:
```python
from opik.evaluation.metrics import Moderation

metric = Moderation()
score = metric.score(
    input="Some potentially harmful content"
)
# Checks for: hate speech, violence, sexual content, self-harm
```

**AgentModeration** - Agent behavior safety:
```python
from opik.evaluation.metrics import AgentModeration

metric = AgentModeration()
score = metric.score(
    input="User message",
    output="Agent response"
)
# Checks if agent behaves appropriately
```

**UserModeration** - User input safety:
```python
from opik.evaluation.metrics import UserModeration

metric = UserModeration()
score = metric.score(
    input="User message to check"
)
# Checks user input for safety issues
```

### G-Eval (Custom LLM Judge)

Create custom LLM-as-a-judge metrics with Chain-of-Thought:

```python
from opik.evaluation.metrics import GEval

# Define custom criteria
metric = GEval(
    name="code_quality",
    task_introduction="You are evaluating code quality",
    evaluation_criteria="""
    The code should be:
    1. Correct and bug-free
    2. Well-structured and readable
    3. Properly documented
    4. Following best practices
    """,
    model_name="gpt-4o"
)

score = metric.score(
    input="Write a function to reverse a string",
    output="def reverse(s): return s[::-1]"
)
# Returns detailed reasoning from LLM
```

### Custom Metrics

**Simple custom metric:**
```python
from opik.evaluation.metrics import BaseMetric, ScoreResult

class WordCountMetric(BaseMetric):
    def __init__(self, min_words=10, max_words=100):
        super().__init__(name="word_count")
        self.min_words = min_words
        self.max_words = max_words
    
    def score(self, output: str, **kwargs) -> ScoreResult:
        word_count = len(output.split())
        
        # Score 1.0 if in range, 0.0 if not
        in_range = self.min_words <= word_count <= self.max_words
        
        return ScoreResult(
            name=self.name,
            value=1.0 if in_range else 0.0,
            reason=f"Word count: {word_count} (target: {self.min_words}-{self.max_words})"
        )
```

**LLM-based custom metric:**
```python
from opik.evaluation.metrics import BaseMetric, ScoreResult
from opik.llm_models import LitellmChatModel

class CustomLLMMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="custom_llm_metric")
        self.llm = LitellmChatModel(model_name="gpt-4o")
    
    def score(self, input: str, output: str, **kwargs) -> ScoreResult:
        prompt = f"""
        Evaluate if the output properly answers the input.
        
        Input: {input}
        Output: {output}
        
        Return JSON: {{"score": 0.0-1.0, "reason": "explanation"}}
        """
        
        response = self.llm.call(messages=[{"role": "user", "content": prompt}])
        result = json.loads(response)
        
        return ScoreResult(
            name=self.name,
            value=result["score"],
            reason=result["reason"]
        )
```

**Multiple scores from one metric:**
```python
class MultiScoreMetric(BaseMetric):
    def score(self, output: str, **kwargs) -> list[ScoreResult]:
        return [
            ScoreResult(name="length", value=len(output) / 100),
            ScoreResult(name="has_question_mark", value=1.0 if "?" in output else 0.0),
            ScoreResult(name="politeness", value=self.check_politeness(output))
        ]
```

### Task Span Metrics (Advanced)

Evaluate internal execution details:

```python
from opik.evaluation.metrics import BaseMetric, ScoreResult

class LatencyMetric(BaseMetric):
    def __init__(self, max_latency_ms=1000):
        super().__init__(name="latency")
        self.max_latency_ms = max_latency_ms
    
    def score(self, task_span, **kwargs) -> ScoreResult:
        # task_span.start_time and task_span.end_time
        duration_ms = (task_span.end_time - task_span.start_time) * 1000
        
        # Score higher if faster
        score = max(0, 1 - (duration_ms / self.max_latency_ms))
        
        return ScoreResult(
            name=self.name,
            value=score,
            reason=f"Completed in {duration_ms:.0f}ms"
        )

class ToolUsageMetric(BaseMetric):
    def score(self, task_span, **kwargs) -> ScoreResult:
        # Check which tools were called
        tool_calls = [s for s in task_span.spans if s.type == "tool"]
        
        return ScoreResult(
            name="tool_usage",
            value=1.0 if len(tool_calls) > 0 else 0.0,
            reason=f"Used {len(tool_calls)} tools"
        )
```

## Running Evaluations

### Evaluate Single Prompts

```python
from opik import Opik
from opik.evaluation import evaluate_prompt
from opik.evaluation.metrics import Hallucination, AnswerRelevance

client = Opik()
dataset = client.get_dataset("my-dataset")

# Define prompt template
prompt = {
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "{{input}}"}  # Variable from dataset
    ],
    "temperature": 0.7
}

# Run evaluation
result = evaluate_prompt(
    prompt=prompt,
    dataset=dataset,
    scoring_metrics=[
        Hallucination(),
        AnswerRelevance()
    ],
    experiment_name="gpt4o-baseline"
)

# Access results
print(f"Average scores: {result.mean_scores}")
```

### Evaluate Applications/Agents

**Basic evaluation:**
```python
from opik.evaluation import evaluate
from opik.evaluation.metrics import Hallucination, AnswerRelevance

def evaluation_task(dataset_item: dict) -> dict:
    # Run your application
    user_question = dataset_item["input"]
    
    # Your app logic
    context = retrieve_context(user_question)
    answer = my_llm(user_question, context)
    
    # Return dict with fields needed by metrics
    return {
        "input": user_question,
        "output": answer,
        "context": context,
        "expected_output": dataset_item.get("expected_output")
    }

result = evaluate(
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=[
        Hallucination(),
        AnswerRelevance()
    ],
    experiment_config={
        "model": "gpt-4o",
        "temperature": 0.7,
        "retrieval_k": 5
    }
)
```

**Parallel evaluation** (faster):
```python
result = evaluate(
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=[Hallucination(), AnswerRelevance()],
    task_threads=4,      # Run 4 tasks in parallel
    scoring_threads=10   # Run 10 scoring operations in parallel
)
```

**Use subset for speed:**
```python
result = evaluate(
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=[Hallucination()],
    n_samples=50  # Only use first 50 items
)
```

**With additional context:**
```python
from functools import partial

def task_with_config(dataset_item, retriever, model_name):
    context = retriever.search(dataset_item["input"])
    output = call_llm(dataset_item["input"], context, model=model_name)
    return {"input": dataset_item["input"], "output": output, "context": context}

# Create partial function with fixed args
task = partial(task_with_config, retriever=my_retriever, model_name="gpt-4o")

result = evaluate(dataset=dataset, task=task, scoring_metrics=[...])
```

### Multi-Metric Evaluation

```python
# Combine metrics
metrics = [
    # LLM-as-judge
    Hallucination(model_name="gpt-4o"),
    AnswerRelevance(model_name="gpt-4o"),
    ContextRecall(),
    
    # Heuristic
    LevenshteinRatio(),
    Contains(),
    
    # Custom
    MyCustomMetric()
]

result = evaluate(
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=metrics
)

# Access scores
for metric_name, avg_score in result.mean_scores.items():
    print(f"{metric_name}: {avg_score:.2f}")
```

## Experiment Management

### Compare Experiments

**In UI:**
1. Navigate to Experiments
2. Select 2+ experiments
3. Click "Compare"
4. View side-by-side metrics

**Via SDK:**
```python
from opik import Opik

client = Opik()

# Get experiments
exp1 = client.get_experiment(name="experiment-1")
exp2 = client.get_experiment(name="experiment-2")

# Compare programmatically
print(f"Exp1 avg score: {exp1.mean_scores}")
print(f"Exp2 avg score: {exp2.mean_scores}")
```

### Re-run Experiments

```python
# Re-run with different config
result = evaluate(
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=[Hallucination()],
    experiment_name="rerun-with-gpt4o",
    experiment_config={
        "model": "gpt-4o",  # Changed from gpt-3.5-turbo
        "temperature": 0.5
    }
)
```

### Group and Filter Experiments

**In UI:**
- Group by: model, temperature, or any config field
- Filter by: date range, score range, tags
- Export to CSV

## Best Practices

### Dataset Quality

1. **Size**: 50-200 examples for most tasks
2. **Diversity**: Cover edge cases, different phrasings
3. **Quality**: Manually review expected outputs
4. **Balance**: Represent real distribution of queries

### Train/Test Split

```python
# Get full dataset
all_items = dataset.get_items()

# Split 80/20
from sklearn.model_selection import train_test_split
train_items, test_items = train_test_split(all_items, test_size=0.2)

# Create separate datasets
train_dataset = client.get_or_create_dataset("my-dataset-train")
test_dataset = client.get_or_create_dataset("my-dataset-test")

train_dataset.insert(train_items)
test_dataset.insert(test_items)

# Use train for optimization, test for final eval
```

### Metric Selection

- **Hallucination**: When factual accuracy is critical
- **AnswerRelevance**: When answers must address the question
- **ContextRecall**: For RAG systems, check retrieval quality
- **ContextPrecision**: Minimize irrelevant context
- **Moderation**: For user-facing applications
- **Custom metrics**: For domain-specific requirements

### Evaluation Troubleshooting

**ScoreMethodMissingArguments error:**
```python
# Problem: Metric expects fields not in task output
def task(item):
    return {"output": "..."}  # Missing "input" and "context"

# Solution: Return all required fields
def task(item):
    return {
        "input": item["input"],
        "output": "...",
        "context": [...],  # Add if metric needs it
        "expected_output": item.get("expected_output")
    }
```

**Slow evaluation:**
- Use `n_samples` to test on subset first
- Increase `task_threads` and `scoring_threads`
- Use cheaper LLM for scoring (gpt-4o-mini)

**Inconsistent scores:**
- Set temperature=0 for LLM-as-judge metrics
- Use multiple judges and average
- Validate with human annotation on subset
