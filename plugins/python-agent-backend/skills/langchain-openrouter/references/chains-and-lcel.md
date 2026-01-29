# Chains and LCEL

LangChain Expression Language (LCEL) for composing chains.

## Official Documentation

- https://python.langchain.com/docs/concepts/lcel/
- https://python.langchain.com/docs/how_to/sequence/

## What is LCEL?

LCEL (LangChain Expression Language) uses the pipe operator `|` to chain components:

```python
chain = prompt | llm | parser
```

This replaces the deprecated `LLMChain` class (removed in LangChain 1.0).

## Basic Chain

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])

# Chain: prompt -> llm -> parse string
chain = prompt | llm | StrOutputParser()

# Invoke
result = chain.invoke({"question": "What is Python?"})
print(result)  # String output
```

## Runnable Components

Everything in LCEL is a `Runnable` with these methods:

| Method | Purpose |
|--------|---------|
| `invoke(input)` | Sync single call |
| `ainvoke(input)` | Async single call |
| `stream(input)` | Sync streaming |
| `astream(input)` | Async streaming |
| `batch(inputs)` | Sync batch |
| `abatch(inputs)` | Async batch |

```python
# All chains support these methods
result = chain.invoke({"question": "Hello"})
result = await chain.ainvoke({"question": "Hello"})

for chunk in chain.stream({"question": "Hello"}):
    print(chunk, end="")

results = chain.batch([
    {"question": "What is 1+1?"},
    {"question": "What is 2+2?"},
])
```

## RunnableLambda

Wrap any function as a Runnable:

```python
from langchain_core.runnables import RunnableLambda

def format_output(text: str) -> str:
    return f"Answer: {text.upper()}"

chain = prompt | llm | StrOutputParser() | RunnableLambda(format_output)
```

## RunnablePassthrough

Pass input through unchanged, or add computed fields:

```python
from langchain_core.runnables import RunnablePassthrough

# Pass through
chain = RunnablePassthrough() | llm

# Add computed field
chain = RunnablePassthrough.assign(
    context=lambda x: fetch_context(x["question"])
) | prompt | llm
```

## RunnableParallel

Run multiple chains in parallel:

```python
from langchain_core.runnables import RunnableParallel

# Run two prompts in parallel
chain = RunnableParallel(
    summary=summary_prompt | llm | StrOutputParser(),
    keywords=keywords_prompt | llm | StrOutputParser(),
)

result = chain.invoke({"text": "Some long text..."})
print(result["summary"])
print(result["keywords"])
```

## Branching with RunnableBranch

```python
from langchain_core.runnables import RunnableBranch

def is_math_question(x):
    return "math" in x["question"].lower()

chain = RunnableBranch(
    (is_math_question, math_chain),
    default_chain,  # Fallback
)
```

## With Fallbacks

```python
# If primary fails, try fallback
primary_llm = ChatOpenAI(model="anthropic/claude-sonnet-4-20250514", ...)
fallback_llm = ChatOpenAI(model="openai/gpt-4o-mini", ...)

llm_with_fallback = primary_llm.with_fallbacks([fallback_llm])
chain = prompt | llm_with_fallback | StrOutputParser()
```

## Output Parsers

```python
from langchain_core.output_parsers import (
    StrOutputParser,      # Parse to string
    JsonOutputParser,     # Parse to JSON dict
    PydanticOutputParser, # Parse to Pydantic model
)

# String output
chain = prompt | llm | StrOutputParser()

# JSON output
chain = prompt | llm | JsonOutputParser()

# Pydantic output
from pydantic import BaseModel

class Answer(BaseModel):
    text: str
    confidence: float

parser = PydanticOutputParser(pydantic_object=Answer)
chain = prompt | llm | parser
```

## Streaming Through Chain

```python
# Stream the final output
for chunk in chain.stream({"question": "Tell me a story"}):
    print(chunk, end="", flush=True)

# Async streaming
async for chunk in chain.astream({"question": "Tell me a story"}):
    print(chunk, end="", flush=True)
```

## Equivalent Syntaxes

```python
from langchain_core.runnables import RunnableSequence

# These are all equivalent:
chain = prompt | llm | parser
chain = prompt.pipe(llm).pipe(parser)
chain = RunnableSequence(prompt, llm, parser)
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: Using deprecated LLMChain
from langchain.chains import LLMChain  # Deprecated!
chain = LLMChain(llm=llm, prompt=prompt)

# ✅ CORRECT: Use LCEL
chain = prompt | llm

# ❌ WRONG: Expecting dict output from StrOutputParser
result = (prompt | llm | StrOutputParser()).invoke(...)
print(result["text"])  # Error! result is a string

# ✅ CORRECT: StrOutputParser returns string
result = (prompt | llm | StrOutputParser()).invoke(...)
print(result)  # String

# ❌ WRONG: Pipe after with_structured_output
structured = llm.with_structured_output(MyModel)
chain = prompt | structured | parser  # structured is a RunnableSequence!

# ✅ CORRECT: with_structured_output already includes parsing
structured = llm.with_structured_output(MyModel)
chain = prompt | structured  # Returns MyModel directly
```
