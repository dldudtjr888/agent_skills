# Structured Output

Get structured responses with Pydantic models.

## Official Documentation

- https://docs.langchain.com/oss/python/integrations/chat/openai
- https://python.langchain.com/docs/concepts/structured_outputs/

## Basic Structured Output

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class Person(BaseModel):
    """Information about a person."""
    name: str = Field(description="The person's full name")
    age: int = Field(description="The person's age in years")

llm = ChatOpenAI(
    model="openai/gpt-4o",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

structured_llm = llm.with_structured_output(Person)
result = structured_llm.invoke("John Smith is 30 years old.")

print(result.name)  # "John Smith"
print(result.age)   # 30
print(type(result)) # <class 'Person'>
```

## Complex Schemas

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(BaseModel):
    """A task to be completed."""
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed description")
    priority: Priority = Field(description="Task priority level")
    due_date: Optional[str] = Field(default=None, description="Due date if any")

class TaskList(BaseModel):
    """A list of tasks extracted from text."""
    tasks: List[Task] = Field(description="List of tasks")
    summary: str = Field(description="Brief summary of all tasks")

structured_llm = llm.with_structured_output(TaskList)
result = structured_llm.invoke("""
Extract tasks from this email:
Hi team, we need to finish the report by Friday (high priority),
update the website copy sometime next week, and review the Q3 budget.
""")

for task in result.tasks:
    print(f"- [{task.priority.value}] {task.title}")
```

## Strict Mode (OpenAI)

For OpenAI models, use strict mode for guaranteed schema compliance:

```python
structured_llm = llm.with_structured_output(Person, strict=True)
```

## Method Options

```python
# Default: Uses tool calling under the hood
structured_llm = llm.with_structured_output(Person)

# Explicit method selection
structured_llm = llm.with_structured_output(
    Person,
    method="function_calling",  # or "json_mode" or "json_schema"
)

# Include raw response
structured_llm = llm.with_structured_output(
    Person,
    include_raw=True,
)
result = structured_llm.invoke("John is 30")
print(result["parsed"])  # Person object
print(result["raw"])     # Original AIMessage
```

## Combined with Tools (langchain-openai >= 0.3.29)

```python
from langchain_core.tools import tool

@tool
def get_user_info(user_id: str) -> str:
    """Get information about a user."""
    return f"User {user_id}: John Smith, age 30"

class OutputSchema(BaseModel):
    answer: str = Field(description="The answer to the user's question")
    sources: List[str] = Field(description="Sources used")

# Bind tools with structured response format
structured_llm = llm.bind_tools(
    [get_user_info],
    response_format=OutputSchema,
    strict=True,
)
```

## Error Handling

```python
from langchain_core.exceptions import OutputParserException

try:
    result = structured_llm.invoke("Some ambiguous text")
except OutputParserException as e:
    print(f"Failed to parse: {e}")
    # Fallback logic
```

## Streaming Structured Output

```python
async for chunk in structured_llm.astream("John is 30 years old"):
    # Chunks are partial Person objects being built
    print(chunk)
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: Using with_structured_output then bind_tools
structured = llm.with_structured_output(Person)
with_tools = structured.bind_tools([my_tool])  # Error! Returns RunnableSequence

# ✅ CORRECT: Use bind_tools with response_format (langchain-openai >= 0.3.29)
llm_combined = llm.bind_tools(
    [my_tool],
    response_format=Person,
    strict=True,
)

# ❌ WRONG: No Field descriptions
class BadSchema(BaseModel):
    name: str
    age: int  # Model doesn't know what these fields mean!

# ✅ CORRECT: Always add descriptions
class GoodSchema(BaseModel):
    name: str = Field(description="Full name of the person")
    age: int = Field(description="Age in years")
```

## Model Compatibility

Not all models support structured output equally:

| Model | Method | Notes |
|-------|--------|-------|
| `openai/gpt-4o` | `function_calling`, `json_schema` | Best support, use `strict=True` |
| `anthropic/claude-*` | `function_calling` | Good support |
| `google/gemini-*` | `function_calling` | Good support |
| Open source models | Varies | Check model docs |
