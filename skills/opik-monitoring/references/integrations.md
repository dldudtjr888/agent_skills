# Integrations Reference Guide

Complete guide to integrating Opik with LLM frameworks and tools.

**Quick Navigation:**
- [Integration Patterns](#integration-patterns) - Wrappers, callbacks, decorators
- [Popular Integrations](#popular-integrations) - OpenAI, LangChain, LlamaIndex, etc.
- [Framework-Specific Guides](#framework-specific-guides) - Advanced usage
- [Custom Integration](#custom-integration) - For unsupported frameworks
- [Troubleshooting](#troubleshooting)
- [Integration Matrix](#integration-matrix) - 40+ frameworks at a glance

---

## Integration Patterns

Opik supports three integration patterns:

1. **Wrapper functions**: `track_openai()`, `track_crewai()`, etc.
2. **Callback handlers**: `OpikTracer` for LangChain/LangGraph
3. **Decorators**: `@track` for custom code

## Popular Integrations

### OpenAI

**Direct API:**
```python
from opik.integrations.openai import track_openai
import openai

# Wrap client
client = track_openai(openai.OpenAI())

# All calls automatically tracked
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Streaming:**
```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content)
# Entire stream logged as one trace
```

**Function calling:**
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather info",
            "parameters": {...}
        }
    }]
)
# Tool calls automatically logged
```

**Custom project:**
```python
client = track_openai(
    openai.OpenAI(),
    project_name="my-project",
    tags=["production"]
)
```

### OpenAI Agents

```python
from opik.integrations.openai_agents import track_agents
from openai import OpenAI

client = OpenAI()
track_agents(client)  # One-time setup

# Create agent
agent = client.beta.agents.create(
    name="My Agent",
    instructions="You are helpful",
    model="gpt-4o"
)

# All runs automatically tracked
run = agent.run(input="Hello")
```

**Multi-turn conversations:**
```python
# Thread ID automatically used for grouping
thread = client.beta.threads.create()

# All messages in thread grouped together
run1 = agent.run(thread_id=thread.id, input="Hello")
run2 = agent.run(thread_id=thread.id, input="How are you?")
# View as conversation in Opik UI
```

### Anthropic

```python
from opik.integrations.anthropic import track_anthropic
import anthropic

client = track_anthropic(anthropic.Anthropic())

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### LangChain

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from opik.integrations.langchain import OpikTracer

# Create chain
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful"),
    ("user", "{input}")
])
llm = ChatOpenAI(model="gpt-4o")
chain = prompt | llm

# Add Opik tracing
callbacks = [OpikTracer(tags=["langchain"], project_name="my-project")]

# Invoke with callbacks
response = chain.invoke(
    {"input": "Hello"},
    config={"callbacks": callbacks}
)
```

**RAG chain:**
```python
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Create RAG chain
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o"),
    retriever=vectorstore.as_retriever()
)

# Track
callbacks = [OpikTracer()]
result = qa_chain.invoke(
    {"query": "What is AI?"},
    config={"callbacks": callbacks}
)
```

**Agents:**
```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools import DuckDuckGoSearchRun

tools = [DuckDuckGoSearchRun()]
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Track agent execution
callbacks = [OpikTracer()]
result = agent_executor.invoke(
    {"input": "Search for AI news"},
    config={"callbacks": callbacks}
)
```

### LangGraph

```python
from langgraph.graph import StateGraph, END
from opik.integrations.langchain import OpikTracer

# Define graph
class State(TypedDict):
    messages: list[str]

def chatbot(state: State):
    return {"messages": state["messages"] + ["Hello"]}

graph = StateGraph(State)
graph.add_node("chatbot", chatbot)
graph.add_edge("chatbot", END)
graph.set_entry_point("chatbot")

app = graph.compile()

# Track with Opik
callbacks = [OpikTracer()]
result = app.invoke(
    {"messages": ["Hi"]},
    config={"callbacks": callbacks}
)
```

**Complex workflow:**
```python
from langgraph.graph import StateGraph, END

def retrieve(state):
    # Retrieval logic
    return {"context": [...]}

def generate(state):
    # Generation logic
    return {"answer": "..."}

graph = StateGraph(State)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)
graph.set_entry_point("retrieve")

app = graph.compile()

# All nodes tracked as spans
callbacks = [OpikTracer()]
result = app.invoke({"query": "..."}, config={"callbacks": callbacks})
```

### LlamaIndex

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.callbacks import CallbackManager
from opik.integrations.llama_index import OpikCallbackHandler

# Create index
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)

# Add Opik callback
opik_callback = OpikCallbackHandler()
callback_manager = CallbackManager([opik_callback])

# Query with tracking
query_engine = index.as_query_engine(callback_manager=callback_manager)
response = query_engine.query("What is AI?")
```

**Agents:**
```python
from llama_index.core.agent import ReActAgent
from llama_index.tools.wikipedia import WikipediaToolSpec

tools = WikipediaToolSpec().to_tool_list()
agent = ReActAgent.from_tools(
    tools,
    callback_manager=callback_manager
)

response = agent.chat("Tell me about Python")
```

### Haystack

```python
from haystack import Pipeline
from haystack.components.generators import OpenAIGenerator
from opik.integrations.haystack import OpikConnector

# Create pipeline
pipeline = Pipeline()
pipeline.add_component("llm", OpenAIGenerator(model="gpt-4o"))

# Add Opik tracking
opik_connector = OpikConnector(project_name="my-project")
pipeline.add_component("opik", opik_connector)

# Run
result = pipeline.run({"llm": {"prompt": "Hello"}})
```

### CrewAI

```python
from crewai import Crew, Agent, Task
from opik.integrations.crewai import track_crewai

# Define agents and tasks
agent1 = Agent(role="Researcher", goal="Research AI", backstory="...")
agent2 = Agent(role="Writer", goal="Write article", backstory="...")

task1 = Task(description="Research AI trends", agent=agent1)
task2 = Task(description="Write article", agent=agent2)

crew = Crew(agents=[agent1, agent2], tasks=[task1, task2])

# Track with Opik
tracked_crew = track_crewai(crew, project_name="my-project")

# Run (automatically tracked)
result = tracked_crew.kickoff()
```

### Autogen

```python
from autogen import AssistantAgent, UserProxyAgent
from opik.integrations.autogen import track_autogen

# Create agents
assistant = AssistantAgent(name="assistant")
user_proxy = UserProxyAgent(name="user")

# Track
track_autogen([assistant, user_proxy], project_name="my-project")

# Initiate chat (automatically tracked)
user_proxy.initiate_chat(
    assistant,
    message="Solve this problem: ..."
)
```

### Google ADK

```python
from google.genai import types
from opik.integrations.adk import OpikTracer

# Create runner
runner = types.Runner()
tracer = OpikTracer()

# Run with tracking
async for event in runner.run_async(
    agent=my_agent,
    user_prompt="Hello",
    tracer=tracer
):
    if event.is_final_response():
        print(event.response)
```

### Microsoft Agent Framework

```python
from microsoft.agent import Agent
import os

# Set environment variables for Opik
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://api.comet.com/opik/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = "Comet-Api-Key=YOUR_API_KEY"

# Create agent (automatically tracked via OpenTelemetry)
agent = Agent(name="my-agent")
response = agent.run("Hello")
```

### DSPy

```python
import dspy
from opik.integrations.dspy import OpikCallback

# Configure DSPy
dspy.configure(lm=dspy.OpenAI(model="gpt-4o"))

# Add Opik callback
opik_callback = OpikCallback(project_name="my-project")
dspy.settings.configure(callbacks=[opik_callback])

# Use DSPy (automatically tracked)
qa = dspy.ChainOfThought("question -> answer")
response = qa(question="What is AI?")
```

### Cohere

```python
from opik.integrations.cohere import track_cohere
import cohere

client = track_cohere(cohere.Client())

response = client.chat(
    message="Hello",
    model="command-r-plus"
)
```

### Groq

```python
from opik.integrations.groq import track_groq
from groq import Groq

client = track_groq(Groq())

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Ollama

```python
from opik.integrations.ollama import track_ollama
from ollama import Client

client = track_ollama(Client())

response = client.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Google Gemini

```python
from opik.integrations.google import track_google
import google.generativeai as genai

genai.configure(api_key="...")
model = track_google(genai.GenerativeModel("gemini-pro"))

response = model.generate_content("Hello")
```

### Bedrock

```python
from opik.integrations.bedrock import track_bedrock
import boto3

client = track_bedrock(boto3.client("bedrock-runtime"))

response = client.invoke_model(
    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    body=json.dumps({"prompt": "Hello", "max_tokens": 100})
)
```

### Vertex AI

```python
from opik.integrations.vertexai import track_vertexai
from google.cloud import aiplatform

model = track_vertexai(
    aiplatform.gapic.PredictionServiceClient()
)

response = model.predict(...)
```

## Framework-Specific Guides

### LangChain Advanced

**LCEL (LangChain Expression Language):**
```python
from langchain_core.runnables import RunnablePassthrough
from opik.integrations.langchain import OpikTracer

# Complex chain
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)

callbacks = [OpikTracer()]
result = chain.invoke("What is AI?", config={"callbacks": callbacks})
```

**Async:**
```python
result = await chain.ainvoke(
    "What is AI?",
    config={"callbacks": [OpikTracer()]}
)
```

**Batch:**
```python
results = chain.batch(
    ["Question 1", "Question 2"],
    config={"callbacks": [OpikTracer()]}
)
```

### LlamaIndex Advanced

**Multiple indices:**
```python
from llama_index.core import VectorStoreIndex
from llama_index.core.tools import QueryEngineTool

# Create multiple indices
index1 = VectorStoreIndex.from_documents(docs1)
index2 = VectorStoreIndex.from_documents(docs2)

# Create query engines
engine1 = index1.as_query_engine()
engine2 = index2.as_query_engine()

# Combine as tools
tools = [
    QueryEngineTool.from_defaults(engine1, name="docs1"),
    QueryEngineTool.from_defaults(engine2, name="docs2")
]

# Use with agent (tracked)
agent = ReActAgent.from_tools(
    tools,
    callback_manager=CallbackManager([OpikCallbackHandler()])
)
```

### CrewAI Advanced

**Custom agents:**
```python
from crewai import Agent, Task, Crew
from opik.integrations.crewai import track_crewai

researcher = Agent(
    role="Researcher",
    goal="Research thoroughly",
    backstory="Expert researcher",
    verbose=True,
    allow_delegation=False
)

writer = Agent(
    role="Writer",
    goal="Write engaging content",
    backstory="Professional writer",
    verbose=True
)

research_task = Task(
    description="Research AI trends in 2025",
    agent=researcher,
    expected_output="Detailed report"
)

write_task = Task(
    description="Write article based on research",
    agent=writer,
    expected_output="Article"
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    verbose=True
)

tracked_crew = track_crewai(crew)
result = tracked_crew.kickoff()
```

## Custom Integration

For frameworks not listed above:

```python
from opik import track

# Wrap your framework's main function
@track
def my_framework_call(input: str) -> str:
    # Your framework code
    result = framework.process(input)
    return result

# Or use context managers
from opik import opik_context

with opik_context.track_trace(name="my_framework") as trace:
    trace.update_current_trace(input={"query": "..."})
    
    with opik_context.track_span(name="step1"):
        opik_context.update_current_span(output={"result": "..."})
    
    trace.update_current_trace(output={"answer": "..."})
```

## Troubleshooting

### Traces Not Appearing

**LangChain:**
- Ensure `callbacks` in config: `config={"callbacks": [OpikTracer()]}`
- Check callback is passed to invoke/ainvoke/batch

**OpenAI:**
- Verify client is wrapped: `client = track_openai(openai.OpenAI())`
- Check API calls are actually made

**LlamaIndex:**
- Add callback manager to query engine: `index.as_query_engine(callback_manager=...)`

### Partial Traces

**LangChain/LangGraph:**
- Complex chains may need explicit callback passing
- Use `RunnableConfig` for consistent callbacks

**Agents:**
- Ensure all tools/components support callbacks
- Some tools may not propagate callbacks

### Performance Issues

**High overhead:**
- Reduce trace detail with sampling
- Use async tracing where supported
- Disable tracing in low-value code paths

**Memory leaks:**
- Call `opik.flush()` periodically in long-running apps
- Set reasonable trace retention

## Best Practices

1. **Use framework integrations when available** (easier than decorators)
2. **Tag traces** for filtering: `tags=["production", "v2"]`
3. **Set project names** for organization
4. **Test locally** before production deployment
5. **Monitor dashboard** regularly
6. **Update integrations** as frameworks evolve

## Integration Matrix

| Framework | Status | Method | Notes |
|-----------|--------|--------|-------|
| OpenAI | ✅ Stable | Wrapper | Full support |
| OpenAI Agents | ✅ Stable | Wrapper | Thread support |
| Anthropic | ✅ Stable | Wrapper | Claude 3.x |
| LangChain | ✅ Stable | Callback | Full LCEL support |
| LangGraph | ✅ Stable | Callback | State graph support |
| LlamaIndex | ✅ Stable | Callback | Agent support |
| Haystack | ✅ Stable | Connector | Pipeline support |
| CrewAI | ✅ Stable | Wrapper | Multi-agent support |
| Autogen | ✅ Stable | Wrapper | Multi-agent support |
| Google ADK | ✅ Stable | Tracer | Async support |
| Microsoft Agent | ✅ Stable | OpenTelemetry | Native OTEL |
| DSPy | ✅ Stable | Callback | Module support |
| Cohere | ✅ Stable | Wrapper | Command-R support |
| Groq | ✅ Stable | Wrapper | Llama 3.x support |
| Ollama | ✅ Stable | Wrapper | Local models |
| Gemini | ✅ Stable | Wrapper | Pro/Ultra support |
| Bedrock | ✅ Stable | Wrapper | Claude/Titan support |
| Vertex AI | ✅ Stable | Wrapper | GCP support |
| Flowise AI | ✅ Stable | Webhook | Visual flow builder |
| AG2 | ✅ Stable | Wrapper | Autogen fork |
| LangchainJS | ✅ Stable | Callback | TypeScript support |
| AIsuite | ✅ Stable | Wrapper | Multi-provider |

For the latest integration status, see: https://www.comet.com/docs/opik/tracing/integrations/overview
