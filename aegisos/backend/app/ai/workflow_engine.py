"""
AI Workflow Engine — orchestrates task routing between AI agents.

Routes tasks to the appropriate agent based on task type,
manages agent lifecycle, and coordinates multi-agent pipelines.
"""

import uuid
from datetime import datetime, UTC
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from structlog import get_logger

from app.ai.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    AgentStatus,
    TaskType,
)

logger = get_logger(__name__)


class PipelineStatus(str, Enum):
    """Status of a multi-step agent pipeline."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStep:
    """A single step in an agent pipeline."""
    task_type: TaskType
    agent_name: str
    depends_on: list[str] = field(default_factory=list)  # Previous step IDs
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    result: Optional[AgentResult] = None


@dataclass
class Pipeline:
    """A multi-step agent pipeline."""
    name: str
    steps: list[PipelineStep]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = PipelineStatus.PENDING
    results: dict[str, AgentResult] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: Optional[str] = None


class AIWorkflowEngine:
    """
    Orchestrates AI agent task routing and pipeline execution.

    Responsibilities:
    - Route tasks to the appropriate agent based on task type
    - Execute single-agent tasks
    - Execute multi-step pipelines with dependencies
    - Track all agent results
    - Publish events to the Redis event bus
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._task_type_map: dict[TaskType, BaseAgent] = {}
        self._pipelines: dict[str, Pipeline] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the workflow engine."""
        self._agents[agent.name] = agent
        for task_type in agent.handled_task_types:
            self._task_type_map[task_type] = agent
        logger.info("agent_registered", agent=agent.name, task_types=len(agent.handled_task_types))

    def route_task(self, task_type: TaskType) -> Optional[BaseAgent]:
        """Find the agent that can handle the given task type."""
        return self._task_type_map.get(task_type)

    def execute_task(self, task_type: TaskType, data: dict) -> AgentResult:
        """
        Execute a single task by routing it to the appropriate agent.

        Args:
            task_type: The type of task to execute
            data: Task data payload

        Returns:
            AgentResult from the agent execution
        """
        agent = self.route_task(task_type)
        if not agent:
            logger.error("no_agent_for_task_type", task_type=task_type.value)
            return AgentResult(
                task_id=str(uuid.uuid4()),
                agent_name="none",
                status=AgentStatus.FAILED,
                content=f"No agent registered for task type: {task_type.value}",
            )

        task = AgentTask(type=task_type, data=data, agent_name=agent.name)
        result = agent.execute(task)

        # Publish event
        self._publish_event(f"agent.{agent.name}.task_completed", {
            "task_id": result.task_id,
            "status": result.status.value,
            "tokens_used": result.tokens_used,
        })

        return result

    def execute_pipeline(self, name: str, steps: list[dict]) -> dict:
        """
        Execute a multi-step pipeline with dependencies.

        Args:
            name: Pipeline name
            steps: List of step dicts with 'task_type' and optional 'depends_on'

        Returns:
            Dict of step_id -> AgentResult
        """
        pipeline = Pipeline(
            name=name,
            steps=[
                PipelineStep(
                    task_type=TaskType(step["task_type"]),
                    agent_name=step.get("agent_name", ""),
                    depends_on=step.get("depends_on", []),
                )
                for step in steps
            ],
        )

        self._pipelines[pipeline.id] = pipeline
        pipeline.status = PipelineStatus.RUNNING

        logger.info("pipeline_started", pipeline_id=pipeline.id, name=name, steps=len(steps))

        # Execute steps in dependency order
        for step in pipeline.steps:
            # Check dependencies are complete
            if step.depends_on:
                for dep_id in step.depends_on:
                    dep_result = pipeline.results.get(dep_id)
                    if not dep_result or dep_result.status != AgentStatus.COMPLETED:
                        logger.error(
                            "pipeline_dependency_not_met",
                            step_id=step.step_id,
                            dependency=dep_id,
                        )
                        pipeline.status = PipelineStatus.FAILED
                        return {"pipeline_id": pipeline.id, "status": "failed", "results": pipeline.results}

            # Execute the step
            data = {}
            # Pass results from dependencies as context
            for dep_id in step.depends_on:
                dep_result = pipeline.results.get(dep_id)
                if dep_result and dep_result.structured_data:
                    data[f"previous_{dep_id}"] = dep_result.structured_data

            result = self.execute_task(step.task_type, data)
            pipeline.results[step.step_id] = result
            step.result = result

        pipeline.status = PipelineStatus.COMPLETED
        pipeline.completed_at = datetime.now(UTC).isoformat()

        logger.info("pipeline_completed", pipeline_id=pipeline.id, name=name)

        return {
            "pipeline_id": pipeline.id,
            "status": "completed",
            "results": {
                step_id: {
                    "agent": result.agent_name,
                    "status": result.status.value,
                    "content": result.content[:500],
                    "tokens_used": result.tokens_used,
                }
                for step_id, result in pipeline.results.items()
            },
        }

    def list_agents(self) -> list[dict]:
        """List all registered agents."""
        return [
            {
                "name": agent.name,
                "display_name": getattr(agent, 'display_name', agent.name.replace('_', ' ').title()),
                "description": agent.description,
                "task_types": [t.value for t in agent.handled_task_types],
                "supported_types": [t.value for t in agent.handled_task_types],
                "status": "active",
                "model": getattr(agent, 'model', 'GPT-4o'),
                "tasks_completed": getattr(agent, 'tasks_completed', 0),
            }
            for agent in self._agents.values()
        ]

    def _publish_event(self, channel: str, data: dict) -> None:
        """Publish an event to the Redis event bus."""
        try:
            from app.core.events import event_publisher
            event_publisher.publish(channel, data)
        except Exception as e:
            logger.warn("event_publish_failed", channel=channel, error=str(e))


# Global workflow engine instance
_workflow_engine: Optional[AIWorkflowEngine] = None


def get_workflow_engine() -> AIWorkflowEngine:
    """Get or create the global workflow engine singleton."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = AIWorkflowEngine()
        _register_default_agents(_workflow_engine)
    return _workflow_engine


def _register_default_agents(engine: AIWorkflowEngine) -> None:
    """Register all default AI agents with the workflow engine."""
    try:
        from app.ai.agents.cto_agent import AICTOAgent
        engine.register_agent(AICTOAgent())
    except Exception as e:
        logger.warn("failed_to_register_cto_agent", error=str(e))

    try:
        from app.ai.agents.architect_agent import AIArchitectAgent
        engine.register_agent(AIArchitectAgent())
    except Exception as e:
        logger.warn("failed_to_register_architect_agent", error=str(e))

    try:
        from app.ai.agents.security_agent import AISecurityAgent
        engine.register_agent(AISecurityAgent())
    except Exception as e:
        logger.warn("failed_to_register_security_agent", error=str(e))

    try:
        from app.ai.agents.qa_agent import AIQAAgent
        engine.register_agent(AIQAAgent())
    except Exception as e:
        logger.warn("failed_to_register_qa_agent", error=str(e))

    try:
        from app.ai.agents.memory_agent import AIMemoryAgent
        engine.register_agent(AIMemoryAgent())
    except Exception as e:
        logger.warn("failed_to_register_memory_agent", error=str(e))

    # Phase 4 agents
    try:
        from app.ai.agents.planner_agent import AIPlannerAgent
        engine.register_agent(AIPlannerAgent())
    except Exception as e:
        logger.warn("failed_to_register_planner_agent", error=str(e))

    try:
        from app.ai.agents.reviewer_agent import AIReviewerAgent
        engine.register_agent(AIReviewerAgent())
    except Exception as e:
        logger.warn("failed_to_register_reviewer_agent", error=str(e))

    try:
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        engine.register_agent(AIDocumentationAgent())
    except Exception as e:
        logger.warn("failed_to_register_documentation_agent", error=str(e))
