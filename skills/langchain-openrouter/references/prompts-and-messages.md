# Prompts and Messages

Message types and prompt templates with LangChain + OpenRouter.

## Official Documentation

- https://docs.langchain.com/oss/python/langchain/messages
- https://python.langchain.com/docs/concepts/messages/

## Message Types

LangChain provides several message classes in `langchain_core.messages`:

| Type | Purpose | When to Use |
|------|---------|-------------|
| `SystemMessage` | Set model behavior/rules | First message, instructions |
| `HumanMessage` | User input | User queries |
| `AIMessage` | Model response | Previous assistant responses |
| `ToolMessage` | Tool execution result | After tool calls |

```python
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is 2+2?"),
    AIMessage(content="2+2 equals 4."),
    HumanMessage(content="And 3+3?"),
]
```

## Basic Message Usage

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# With message objects
messages = [
    SystemMessage(content="You are a pirate. Respond in pirate speak."),
    HumanMessage(content="Hello, how are you?"),
]
response = llm.invoke(messages)
print(response.content)

# Tuple shorthand (equivalent)
messages = [
    ("system", "You are a pirate. Respond in pirate speak."),
    ("human", "Hello, how are you?"),
]
response = llm.invoke(messages)
```

## Multimodal Messages (Images)

```python
from langchain_core.messages import HumanMessage
import base64

# From URL
message = HumanMessage(
    content=[
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
    ]
)

# From base64
with open("image.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

message = HumanMessage(
    content=[
        {"type": "text", "text": "Describe this image."},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_data}"},
        },
    ]
)

response = llm.invoke([message])
```

## Prompt Templates

```python
from langchain_core.prompts import ChatPromptTemplate

# Basic template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}. Be helpful and concise."),
    ("human", "{question}"),
])

# Format and invoke
messages = prompt.format_messages(role="scientist", question="What is DNA?")
response = llm.invoke(messages)

# Or chain with pipe operator (LCEL)
chain = prompt | llm
response = chain.invoke({"role": "scientist", "question": "What is DNA?"})
```

## Message Placeholder (for Chat History)

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# With conversation history
history = [
    HumanMessage(content="My name is Alice."),
    AIMessage(content="Hello Alice! How can I help you today?"),
]

chain = prompt | llm
response = chain.invoke({"history": history, "input": "What's my name?"})
```

## Chat History Requirements

Most models expect messages in this order:

1. `SystemMessage` (optional, but if present must be first)
2. `HumanMessage`
3. `AIMessage` / `ToolMessage` (alternating with human)
4. `HumanMessage` (last, for the current query)

```python
# Valid order
messages = [
    SystemMessage(content="You are helpful."),  # Optional first
    HumanMessage(content="Hi"),
    AIMessage(content="Hello!"),
    HumanMessage(content="How are you?"),  # Current query last
]

# ToolMessage must follow AIMessage with tool_calls
messages = [
    HumanMessage(content="What's the weather?"),
    AIMessage(content="", tool_calls=[{"id": "call_1", "name": "get_weather", ...}]),
    ToolMessage(content="Sunny, 22C", tool_call_id="call_1"),
    # Model will respond based on tool result
]
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: ToolMessage without preceding AIMessage with tool_calls
messages = [
    HumanMessage(content="Hi"),
    ToolMessage(content="result", tool_call_id="123"),  # Error!
]

# ❌ WRONG: Starting with AIMessage
messages = [
    AIMessage(content="Hello!"),  # Can't start with AI
    HumanMessage(content="Hi"),
]

# ❌ WRONG: Old deprecated import
from langchain.schema import HumanMessage  # Deprecated!

# ✅ CORRECT: Current import
from langchain_core.messages import HumanMessage
```
