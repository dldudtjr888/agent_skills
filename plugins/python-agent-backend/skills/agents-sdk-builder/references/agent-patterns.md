# Agent Patterns

Production-tested multi-agent architectures and patterns.

## Core Patterns

### 1. Triage Pattern

Central agent routes to specialists:

```python
specialist1 = Agent(
    name="Booking Agent",
    handoff_description="Handles all booking and reservation requests",
    instructions="Help users book appointments and reservations",
)

specialist2 = Agent(
    name="Support Agent",
    handoff_description="Handles customer support and troubleshooting",
    instructions="Help users with technical issues and questions",
)

triage = Agent(
    name="Triage Agent",
    instructions="Route users to the appropriate specialist based on their needs",
    handoffs=[specialist1, specialist2],
)
```

### 2. Sequential Pattern

Agents hand off in sequence:

```python
researcher = Agent(
    name="Researcher",
    instructions="Research the topic thoroughly, then hand off to writer",
    handoffs=[writer],
)

writer = Agent(
    name="Writer",
    instructions="Write based on research, then hand off to editor",
    handoffs=[editor],
)

editor = Agent(
    name="Editor",
    instructions="Edit and polish the content",
)
```

### 3. Hierarchical Pattern (Agents as Tools)

Orchestrator uses specialists as tools:

```python
specialist1 = Agent(name="SQL Expert", instructions="Write SQL queries")
specialist2 = Agent(name="Python Expert", instructions="Write Python code")

orchestrator = Agent(
    name="Orchestrator",
    instructions="Coordinate specialists to solve complex tasks",
    tools=[
        specialist1.as_tool(
            tool_name="sql_expert",
            tool_description="Use for database queries",
        ),
        specialist2.as_tool(
            tool_name="python_expert",
            tool_description="Use for Python coding tasks",
        ),
    ],
)
```

### 4. Supervisor Pattern

Supervisor agent manages worker agents:

```python
worker1 = Agent(name="Worker 1", instructions="Process data")
worker2 = Agent(name="Worker 2", instructions="Analyze results")

supervisor = Agent(
    name="Supervisor",
    instructions="""
    You manage worker agents. 
    - Assign tasks to workers
    - Monitor progress
    - Aggregate results
    """,
    tools=[worker1.as_tool(...), worker2.as_tool(...)],
)
```

### 5. Reflection Pattern

Agent reviews and improves its own output:

```python
generator = Agent(
    name="Generator",
    instructions="Generate content",
)

critic = Agent(
    name="Critic",
    instructions="Review content and provide feedback",
)

async def reflection_loop(prompt: str, iterations: int = 3):
    content = prompt
    
    for i in range(iterations):
        # Generate
        result = await Runner.run(generator, content)
        output = result.final_output
        
        # Reflect
        feedback = await Runner.run(
            critic,
            f"Review this: {output}. Provide specific improvements."
        )
        
        # Improve
        content = f"Previous: {output}\nFeedback: {feedback.final_output}\nImprove it."
    
    return output
```

### 6. Parallel Execution

Multiple agents work simultaneously:

```python
import asyncio

agents = [
    Agent(name="Researcher 1", instructions="Research topic A"),
    Agent(name="Researcher 2", instructions="Research topic B"),
    Agent(name="Researcher 3", instructions="Research topic C"),
]

async def parallel_research(query: str):
    tasks = [
        Runner.run(agent, query)
        for agent in agents
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Aggregate results
    combined = "\n\n".join([r.final_output for r in results])
    
    # Synthesize
    synthesizer = Agent(name="Synthesizer", instructions="Combine research")
    final = await Runner.run(synthesizer, f"Synthesize: {combined}")
    
    return final.final_output
```

## Advanced Patterns

### Dynamic Agent Creation

```python
def create_specialist(domain: str) -> Agent:
    return Agent(
        name=f"{domain} Specialist",
        instructions=f"You are an expert in {domain}",
    )

async def dynamic_routing(query: str):
    # Analyze query to determine needed specialists
    analyzer = Agent(name="Analyzer", instructions="Determine required expertise")
    analysis = await Runner.run(analyzer, f"What expertise is needed: {query}")
    
    # Create specialists dynamically
    domains = extract_domains(analysis.final_output)
    specialists = [create_specialist(d) for d in domains]
    
    # Use specialists
    triage = Agent(
        name="Dynamic Triage",
        instructions="Route to appropriate specialist",
        handoffs=specialists,
    )
    
    result = await Runner.run(triage, query)
    return result.final_output
```

### Memory-Enhanced Pattern

```python
session = SQLiteSession("expert_system")

expert = Agent(
    name="Expert",
    instructions="You are an expert that learns from past conversations",
)

async def learning_interaction(query: str):
    # Previous context is automatically loaded
    result = await Runner.run(expert, query, session=session)
    
    # Memory persists for future interactions
    return result.final_output
```

### Human-in-the-Loop Pattern

```python
async def human_approval_flow(task: str):
    # Agent generates plan
    planner = Agent(name="Planner", instructions="Create detailed plan")
    plan = await Runner.run(planner, task)
    
    # Get human approval
    approved = await ask_human(plan.final_output)
    
    if approved:
        # Execute plan
        executor = Agent(name="Executor", instructions="Execute plan precisely")
        result = await Runner.run(executor, plan.final_output)
        return result.final_output
    else:
        return "Plan rejected"
```

## Choosing the Right Pattern

| Pattern | Use When | Pros | Cons |
|---------|----------|------|------|
| Triage | Clear specialist domains | Simple, scalable | Routing can fail |
| Sequential | Linear workflow | Predictable | Inflexible |
| Hierarchical | Complex coordination | Powerful | More overhead |
| Supervisor | Dynamic task allocation | Flexible | Complex to debug |
| Reflection | Quality matters | High quality | Slow, expensive |
| Parallel | Independent subtasks | Fast | Coordination needed |

## Best Practices

1. **Start Simple**: Begin with triage or sequential, add complexity as needed
2. **Clear Instructions**: Each agent should have well-defined responsibilities
3. **Test Handoffs**: Verify routing logic works correctly
4. **Monitor Costs**: More agents = more API calls
5. **Use Guardrails**: Validate outputs at each stage
6. **Implement Fallbacks**: Handle routing failures gracefully

## Resources

- [Multi-Agent Examples](https://github.com/openai/openai-agents-python/tree/main/examples)
- [Agent Patterns Blog](https://www.anthropic.com/research/building-effective-agents)
