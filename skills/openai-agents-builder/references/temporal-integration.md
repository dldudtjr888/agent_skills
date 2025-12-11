# Temporal Integration

Build durable, fault-tolerant agents with Temporal's durable execution.

## Overview

Temporal integration adds crash-proof execution to OpenAI Agents SDK:
- Automatic retry on failures
- State persistence
- Crash recovery
- Long-running workflows
- Human-in-the-loop tasks

## Installation

```bash
pip install temporal
pip install openai-agents
```

## Basic Setup

```python
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib import openai_agents
from agents import Agent, Runner

# Define activities as tools
@activity.defn
async def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny"

# Define workflow
@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, prompt: str) -> str:
        agent = Agent(
            name="Assistant",
            instructions="You are helpful",
            tools=[
                openai_agents.workflow.activity_as_tool(
                    get_weather,
                    start_to_close_timeout=timedelta(seconds=10)
                )
            ]
        )
        
        result = await Runner.run(agent, prompt)
        return result.final_output
```

## Running Workflows

```python
async def main():
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # Start worker
    worker = Worker(
        client,
        task_queue="agents-queue",
        workflows=[AgentWorkflow],
        activities=[get_weather],
    )
    
    # Start workflow
    handle = await client.start_workflow(
        AgentWorkflow.run,
        "What's the weather in Tokyo?",
        id="workflow-1",
        task_queue="agents-queue",
    )
    
    result = await handle.result()
    print(result)
```

## Human-in-the-Loop

```python
@workflow.defn
class ApprovalWorkflow:
    @workflow.run
    async def run(self, task: str) -> str:
        # Agent generates plan
        planner = Agent(name="Planner", instructions="Create plan")
        plan_result = await Runner.run(planner, task)
        
        # Wait for human approval
        await workflow.wait_condition(
            lambda: self.approved is not None
        )
        
        if self.approved:
            # Execute plan
            executor = Agent(name="Executor", instructions="Execute")
            result = await Runner.run(executor, plan_result.final_output)
            return result.final_output
        else:
            return "Rejected"
    
    @workflow.signal
    def approve(self, approved: bool):
        self.approved = approved
```

## Resources

- [Temporal Docs](https://docs.temporal.io/ai-cookbook/durable-agent-with-tools)
- [Integration Blog](https://temporal.io/blog/announcing-openai-agents-sdk-integration)
