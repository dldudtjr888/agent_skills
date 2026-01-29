# Tools and Functions

Tool calling with LangChain + OpenRouter.

## Official Documentation

- https://docs.langchain.com/oss/python/integrations/chat/openai
- https://openrouter.ai/docs/api/reference/overview

## Define Tools

### Using @tool Decorator

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for.
    """
    # Your implementation
    return f"Weather in {city}: Sunny, 22°C"

@tool
def calculate(expression: str) -> float:
    """Calculate a mathematical expression.

    Args:
        expression: A math expression like '2 + 2' or '10 * 5'.
    """
    return eval(expression)
```

### Using Pydantic

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class WeatherInput(BaseModel):
    """Input for weather tool."""
    city: str = Field(description="The city name")
    unit: str = Field(default="celsius", description="Temperature unit")

@tool(args_schema=WeatherInput)
def get_weather_v2(city: str, unit: str = "celsius") -> str:
    """Get weather with unit preference."""
    return f"Weather in {city}: 22°{unit[0].upper()}"
```

## Bind Tools to LLM

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Bind single tool
llm_with_tool = llm.bind_tools([get_weather])

# Bind multiple tools
llm_with_tools = llm.bind_tools([get_weather, calculate])
```

## Invoke and Handle Tool Calls

```python
response = llm_with_tools.invoke("What's the weather in Seoul?")

# Check if model wants to call tools
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call['name']}")
        print(f"Args: {tool_call['args']}")
        print(f"ID: {tool_call['id']}")
else:
    # No tool call, just a text response
    print(response.content)
```

## Execute Tools and Continue Conversation

```python
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Initial request
messages = [HumanMessage(content="What's the weather in Seoul?")]
response = llm_with_tools.invoke(messages)

if response.tool_calls:
    # Add AI response to messages
    messages.append(response)

    # Execute each tool and add results
    for tool_call in response.tool_calls:
        if tool_call["name"] == "get_weather":
            result = get_weather.invoke(tool_call["args"])
            messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_call["id"],
                )
            )

    # Get final response
    final_response = llm_with_tools.invoke(messages)
    print(final_response.content)
```

## Force Tool Use

```python
# Force specific tool
llm_forced = llm.bind_tools(
    [get_weather, calculate],
    tool_choice={"type": "function", "function": {"name": "get_weather"}},
)

# Force any tool (model must use at least one)
llm_any_tool = llm.bind_tools(
    [get_weather, calculate],
    tool_choice="any",
)

# Allow no tool (default)
llm_auto = llm.bind_tools(
    [get_weather, calculate],
    tool_choice="auto",
)
```

## Parallel Tool Calls

Some models support calling multiple tools in one response:

```python
response = llm_with_tools.invoke(
    "What's the weather in Seoul and Tokyo? Also calculate 15 * 23."
)

# May return multiple tool calls
for tool_call in response.tool_calls:
    print(f"{tool_call['name']}: {tool_call['args']}")
```

## OpenRouter :exacto Variant

For better tool-calling accuracy, use the `:exacto` variant:

```python
llm = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514:exacto",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

llm_with_tools = llm.bind_tools([get_weather])
```

## Common Mistakes (DO NOT)

```python
# ❌ WRONG: Tools without docstring
@tool
def bad_tool(x: str) -> str:
    return x  # No docstring - model won't know what it does!

# ✅ CORRECT: Always include docstring
@tool
def good_tool(x: str) -> str:
    """Process the input string and return result."""
    return x

# ❌ WRONG: Forgetting to handle tool_calls
response = llm_with_tools.invoke("What's the weather?")
print(response.content)  # May be empty if tool was called!

# ✅ CORRECT: Check for tool_calls
if response.tool_calls:
    # Handle tool calls
    pass
else:
    print(response.content)
```
