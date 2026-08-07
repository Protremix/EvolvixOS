"""
Distributed task execution for the AI Workflow Engine.

Supports concurrent agent execution via async task dispatch,
with configurable concurrency limits and result aggregation.
"""

import asyncio
import uuid
from datetime import datetime, UTC
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from structlog import get_logger

from app.ai.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    AgentStatus,
    TaskType,
)

logger = get_logger(__name__)


class ExecutionMode(str, Enum):
    """Execution mode for distributed tasks."""
    SYNC = "sync"          # Execute sequentially (default)
    ASYNC = "async"        # Execute concurrently with asyncio
    THREADED = "threaded"  # Execute in thread pool


@dataclass
class DistributedTask:
    """A task dispatched for distributed execution."""
    task_type: TaskType
    data: dict
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: Optional[str] = None
    status: AgentStatus = AgentStatus.PENDING
    result: Optional[AgentResult] = None
    future: Optional[Future] = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: Optional[str] = None


class DistributedExecutor:
    """
    Executes AI agent tasks concurrently using a thread pool.

    The LLM calls in BaseAgent are HTTP requests (blocking I/O),
    so threads provide real concurrency without GIL issues.

    Features:
    - Configurable max concurrent tasks
    - Fire-and-forget dispatch with future result collection
    - Batch execution of multiple tasks at once
    - Timeout handling per task
    - Graceful shutdown
    """

    def __init__(self, max_workers: int = 4, timeout: int = 120):
        """
        Initialize the distributed executor.

        Args:
            max_workers: Maximum concurrent task executions
            timeout: Default timeout per task in seconds
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._pending: dict[str, DistributedTask] = {}
        self._completed: dict[str, AgentResult] = {}
        self._running_count = 0
        self._lock = threading.Lock()  # Thread-safe state management

        logger.info("distributed_executor_init", max_workers=max_workers, timeout=timeout)

    def dispatch(
        self,
        engine,
        task_type: TaskType,
        data: dict,
        timeout: Optional[int] = None,
    ) -> str:
        """
        Dispatch a task for concurrent execution.

        Args:
            engine: The AIWorkflowEngine instance to route the task
            task_type: Type of task to execute
            data: Task data payload
            timeout: Optional timeout override

        Returns:
            Task ID for retrieving the result later
        """
        agent = engine.route_task(task_type)
        if not agent:
            logger.error("no_agent_for_dispatch", task_type=task_type.value)
            return ""

        task = DistributedTask(task_type=task_type, data=data, agent_name=agent.name)
        effective_timeout = timeout or self.timeout

        def _execute():
            return engine.execute_task(task_type, data)

        task.future = self._executor.submit(_execute)
        task.status = AgentStatus.RUNNING
        with self._lock:
            self._pending[task.id] = task
            self._running_count += 1

        logger.info(
            "task_dispatched",
            task_id=task.id,
            task_type=task_type.value,
            agent=agent.name,
        )

        return task.id

    def dispatch_batch(
        self,
        engine,
        tasks: list[tuple[TaskType, dict]],
    ) -> list[str]:
        """
        Dispatch multiple tasks concurrently.

        Args:
            engine: The AIWorkflowEngine instance
            tasks: List of (task_type, data) tuples

        Returns:
            List of task IDs
        """
        task_ids = []
        for task_type, data in tasks:
            task_id = self.dispatch(engine, task_type, data)
            if task_id:
                task_ids.append(task_id)

        logger.info("batch_dispatched", count=len(task_ids))
        return task_ids

    def get_result(self, task_id: str, timeout: Optional[int] = None) -> Optional[AgentResult]:
        """
        Get the result of a dispatched task (blocks until complete).

        Args:
            task_id: The task ID returned by dispatch()
            timeout: How long to wait (seconds)

        Returns:
            AgentResult or None if task not found
        """
        task = self._pending.get(task_id)
        if not task:
            # Already completed and collected?
            return self._completed.get(task_id)

        if task.future is None:
            return None

        effective_timeout = timeout or self.timeout
        try:
            result = task.future.result(timeout=effective_timeout)
            task.result = result
            task.status = AgentStatus.COMPLETED
            task.completed_at = datetime.now(UTC).isoformat()
            with self._lock:
                self._completed[task_id] = result
                self._running_count -= 1
            return result
        except Exception as e:
            task.status = AgentStatus.FAILED
            task.completed_at = datetime.now(UTC).isoformat()
            with self._lock:
                self._running_count -= 1
            logger.error("task_execution_failed", task_id=task_id, error=str(e))
            return AgentResult(
                task_id=task_id,
                agent_name=task.agent_name or "unknown",
                status=AgentStatus.FAILED,
                content=f"Execution failed: {str(e)}",
            )

    def collect_all(self, timeout: Optional[int] = None) -> dict[str, AgentResult]:
        """
        Collect results from all pending tasks.

        Args:
            timeout: How long to wait per task

        Returns:
            Dict of task_id -> AgentResult
        """
        results = {}
        for task_id in list(self._pending.keys()):
            result = self.get_result(task_id, timeout)
            if result:
                results[task_id] = result
        return results

    def get_status(self) -> dict:
        """Get current execution status."""
        return {
            "max_workers": self.max_workers,
            "pending": len(self._pending),
            "completed": len(self._completed),
            "running": self._running_count,
        }

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the executor, optionally waiting for pending tasks."""
        self._executor.shutdown(wait=wait)
        logger.info("distributed_executor_shutdown", wait=wait)


# Global distributed executor instance
_distributed_executor: Optional[DistributedExecutor] = None


def get_distributed_executor() -> DistributedExecutor:
    """Get or create the global distributed executor singleton."""
    global _distributed_executor
    if _distributed_executor is None:
        _distributed_executor = DistributedExecutor(max_workers=4)
    return _distributed_executor
