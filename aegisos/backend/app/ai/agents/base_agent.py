"""
Base agent class for all EvolvixOS AI agents.

Provides the common interface and utilities that all specialized
AI agents inherit:
- LLM client access
- Event bus subscription/publishing
- Result storage in PostgreSQL
- Error handling and logging
- Task execution lifecycle
"""

import json
import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field

from structlog import get_logger

logger = get_logger(__name__)


class AgentStatus(str, Enum):
    """Status of an agent task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of tasks that agents can handle."""
    # AI CTO tasks
    ARCHITECTURE_REVIEW = "architecture_review"
    TECHNOLOGY_DECISION = "technology_decision"
    STRATEGIC_PLANNING = "strategic_planning"

    # AI Architect tasks
    SYSTEM_DESIGN = "system_design"
    ADR_GENERATION = "adr_generation"
    TECHNOLOGY_SELECTION = "technology_selection"

    # AI Security tasks
    SECURITY_REVIEW = "security_review"
    THREAT_MODELING = "threat_modeling"
    VULNERABILITY_SCAN = "vulnerability_scan"

    # AI QA tasks
    TEST_GENERATION = "test_generation"
    QUALITY_GATE = "quality_gate"
    COVERAGE_ANALYSIS = "coverage_analysis"

    # AI Memory tasks
    CONTEXT_STORE = "context_store"
    CONTEXT_RETRIEVAL = "context_retrieval"
    KNOWLEDGE_INDEX = "knowledge_index"

    # AI Planner tasks
    SPRINT_PLANNING = "sprint_planning"
    TASK_DECOMPOSITION = "task_decomposition"
    DEPENDENCY_ANALYSIS = "dependency_analysis"

    # AI Reviewer tasks
    CODE_REVIEW = "code_review"
    PR_REVIEW = "pr_review"

    # AI Implementation tasks
    CODE_GENERATION = "code_generation"
    IMPLEMENTATION = "implementation"
    REFACTORING = "refactoring"

    # AI Documentation tasks
    DOC_GENERATION = "doc_generation"
    API_DOC_GENERATION = "api_doc_generation"


@dataclass
class AgentTask:
    """A task to be executed by an AI agent."""
    type: TaskType
    data: dict
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: Optional[str] = None
    status: AgentStatus = AgentStatus.PENDING
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0


@dataclass
class AgentResult:
    """Result from an agent task execution."""
    task_id: str
    agent_name: str
    status: AgentStatus
    content: str
    structured_data: Optional[dict] = None
    recommendations: list = field(default_factory=list)
    score: Optional[float] = None
    findings: list = field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0


class BaseAgent:
    """
    Base class for all EvolvixOS AI agents.

    Subclasses must implement:
    - system_prompt: The system prompt defining agent behavior
    - can_handle(task_type): Whether this agent can handle a task type
    - execute(task): The actual agent logic

    Optional overrides:
    - preprocess(task): Transform input data before LLM call
    - postprocess(result): Transform LLM output before storage
    """

    name: str = "base_agent"
    description: str = "Base AI agent"
    handled_task_types: set[TaskType] = set()

    def __init__(self, llm_client=None):
        """
        Initialize the agent.

        Args:
            llm_client: LLM client instance. If None, gets global instance.
        """
        if llm_client is None:
            from app.ai.llm_client import get_llm_client
            llm_client = get_llm_client()
        self.llm = llm_client
        self.logger = get_logger(f"agent.{self.name}")

    @property
    def system_prompt(self) -> str:
        """System prompt defining this agent's behavior. Override in subclass."""
        raise NotImplementedError("Subclasses must define system_prompt")

    def can_handle(self, task_type: TaskType) -> bool:
        """Check if this agent can handle the given task type."""
        return task_type in self.handled_task_types

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute the agent task.

        Override in subclass for custom logic, or use the default
        which makes a single LLM call with the system prompt and task data.

        Learning loop integration: if learning data exists for this agent,
        past performance feedback is injected into the system prompt.

        Args:
            task: The task to execute

        Returns:
            AgentResult with the agent's output
        """
        import time

        self.logger.info("agent_executing", task_id=task.id, task_type=task.type.value)
        task.status = AgentStatus.RUNNING
        start = time.time()

        try:
            # Preprocess task data
            user_prompt = self.preprocess(task)

            # Build system prompt with optional learning feedback
            system_prompt = self.system_prompt
            try:
                from app.services.agent_learning import get_learning_loop
                from app.services.verdis_agent_enhancer import get_verdis_enhancer

                # Inject Verdis context
                enhancer = get_verdis_enhancer()
                system_prompt = enhancer.enhance_prompt(system_prompt)

                # Inject learning feedback
                learning = get_learning_loop()
                feedback = learning.get_feedback_for_agent(self.name, task.type.value)
                if feedback.get("applied"):
                    system_prompt += f"\n\n=== LEARNING FEEDBACK ===\n{feedback['feedback']}\n=== END FEEDBACK ===\n"
            except Exception:
                pass  # Learning injection is best-effort, don't fail the task

            # Make LLM call
            response = self.llm.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.get_temperature(task.type),
                max_tokens=self.get_max_tokens(task.type),
            )

            latency_ms = (time.time() - start) * 1000

            # Postprocess LLM response
            result = self.postprocess(response.content, task)

            task.status = AgentStatus.COMPLETED
            task.result = result.structured_data or {"content": result.content}
            task.tokens_used = response.tokens_used
            task.latency_ms = latency_ms
            task.completed_at = datetime.now(UTC).isoformat()

            # Record execution for learning loop
            try:
                from app.services.agent_learning import get_learning_loop, AgentExecution
                learning = get_learning_loop()
                learning.record_execution(AgentExecution(
                    agent_name=self.name,
                    task_type=task.type.value,
                    status="completed",
                    score=result.score,
                    verdict=result.structured_data.get("verdict") if result.structured_data else None,
                    tokens_used=response.tokens_used,
                    latency_ms=latency_ms,
                    findings_count=len(result.findings) if result.findings else 0,
                    recommendations_count=len(result.recommendations) if result.recommendations else 0,
                ))
            except Exception:
                pass  # Best-effort

            self.logger.info(
                "agent_completed",
                task_id=task.id,
                tokens=response.tokens_used,
                latency_ms=round(latency_ms, 2),
            )

            result.tokens_used = response.tokens_used
            result.latency_ms = latency_ms
            return result

        except Exception as e:
            task.status = AgentStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(UTC).isoformat()

            self.logger.error("agent_failed", task_id=task.id, error=str(e))

            return AgentResult(
                task_id=task.id,
                agent_name=self.name,
                status=AgentStatus.FAILED,
                content=f"Agent execution failed: {str(e)}",
            )

    def preprocess(self, task: AgentTask) -> str:
        """
        Transform task data into a user prompt for the LLM.
        Override in subclass for custom formatting.

        Default: JSON-serialize the task data.
        """
        return json.dumps(task.data, indent=2, default=str)

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Transform LLM output into an AgentResult.
        Override in subclass for custom parsing.

        Default: Try to parse as JSON, fallback to raw content.
        """
        structured = None
        try:
            structured = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    structured = json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=content,
            structured_data=structured,
        )

    def get_temperature(self, task_type: TaskType) -> float:
        """Get the appropriate temperature for a task type."""
        if task_type in (TaskType.SECURITY_REVIEW, TaskType.THREAT_MODELING, TaskType.VULNERABILITY_SCAN):
            return 0.1  # Low temperature for security tasks
        if task_type in (TaskType.ARCHITECTURE_REVIEW, TaskType.SYSTEM_DESIGN, TaskType.ADR_GENERATION):
            return 0.3  # Moderate for analysis
        if task_type in (TaskType.TEST_GENERATION, TaskType.QUALITY_GATE):
            return 0.2  # Low for precision
        if task_type in (TaskType.DOC_GENERATION, TaskType.API_DOC_GENERATION):
            return 0.4  # Slightly higher for natural language
        return 0.3  # Default

    def get_max_tokens(self, task_type: TaskType) -> int:
        """Get the max tokens for a task type."""
        if task_type in (TaskType.ARCHITECTURE_REVIEW, TaskType.SYSTEM_DESIGN):
            return 6000
        if task_type in (TaskType.SECURITY_REVIEW, TaskType.THREAT_MODELING):
            return 5000
        if task_type in (TaskType.TEST_GENERATION, TaskType.CODE_REVIEW):
            return 4000
        if task_type in (TaskType.DOC_GENERATION,):
            return 6000
        return 4000  # Default
