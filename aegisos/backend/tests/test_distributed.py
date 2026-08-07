"""
Tests for distributed task execution and Phase 4 agents.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from app.ai.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    AgentStatus,
    TaskType,
)
from app.ai.distributed_executor import (
    DistributedExecutor,
    DistributedTask,
    ExecutionMode,
    get_distributed_executor,
)


# ============================================================
# Test Agent (mock)
# ============================================================

class FastMockAgent(BaseAgent):
    """Fast mock agent that returns a result without LLM calls."""
    name = "fast_mock_agent"
    description = "Fast mock for testing"
    handled_task_types = {TaskType.CODE_REVIEW, TaskType.DOC_GENERATION}

    @property
    def system_prompt(self) -> str:
        return "Fast mock agent"

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=f"Mock result for {task.type.value}",
            structured_data={"mock": True, "task_type": task.type.value},
            tokens_used=50,
            latency_ms=10.0,
        )


class SlowMockAgent(BaseAgent):
    """Mock agent with delay for testing concurrent execution."""
    name = "slow_mock_agent"
    description = "Slow mock for concurrency testing"
    handled_task_types = {TaskType.SPRINT_PLANNING}

    @property
    def system_prompt(self) -> str:
        return "Slow mock agent"

    def execute(self, task: AgentTask) -> AgentResult:
        time.sleep(0.5)  # Simulate work
        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=f"Slow result for {task.type.value}",
            tokens_used=100,
            latency_ms=500.0,
        )


# ============================================================
# Distributed Executor Tests
# ============================================================

class TestDistributedExecutor:
    """Tests for the distributed task executor."""

    def test_executor_init(self):
        """Test executor initialization."""
        executor = DistributedExecutor(max_workers=4, timeout=60)
        assert executor.max_workers == 4
        assert executor.timeout == 60

    def test_dispatch_single(self):
        """Test dispatching a single task."""
        from app.ai.workflow_engine import AIWorkflowEngine

        engine = AIWorkflowEngine()
        engine.register_agent(FastMockAgent())
        executor = DistributedExecutor(max_workers=2)

        task_id = executor.dispatch(engine, TaskType.CODE_REVIEW, {"code": "test"})
        assert task_id != ""
        assert task_id in executor._pending

        result = executor.get_result(task_id, timeout=10)
        assert result is not None
        assert result.status == AgentStatus.COMPLETED
        assert "Mock result" in result.content

        executor.shutdown(wait=False)

    def test_dispatch_batch(self):
        """Test dispatching multiple tasks concurrently."""
        from app.ai.workflow_engine import AIWorkflowEngine

        engine = AIWorkflowEngine()
        engine.register_agent(FastMockAgent())
        executor = DistributedExecutor(max_workers=4)

        task_ids = executor.dispatch_batch(engine, [
            (TaskType.CODE_REVIEW, {"code": "test1"}),
            (TaskType.DOC_GENERATION, {"doc": "test2"}),
            (TaskType.CODE_REVIEW, {"code": "test3"}),
        ])

        assert len(task_ids) == 3

        results = executor.collect_all(timeout=10)
        assert len(results) == 3
        for result in results.values():
            assert result.status == AgentStatus.COMPLETED

        executor.shutdown(wait=False)

    def test_concurrent_vs_sequential(self):
        """Test that concurrent execution is faster than sequential."""
        from app.ai.workflow_engine import AIWorkflowEngine

        engine = AIWorkflowEngine()
        engine.register_agent(SlowMockAgent())
        executor = DistributedExecutor(max_workers=4)

        # Dispatch 3 tasks concurrently (each takes 0.5s)
        start = time.time()
        task_ids = executor.dispatch_batch(engine, [
            (TaskType.SPRINT_PLANNING, {"sprint": 1}),
            (TaskType.SPRINT_PLANNING, {"sprint": 2}),
            (TaskType.SPRINT_PLANNING, {"sprint": 3}),
        ])
        results = executor.collect_all(timeout=30)
        concurrent_time = time.time() - start

        # 3 tasks × 0.5s = 1.5s sequential, should be ~0.5s concurrent
        assert concurrent_time < 1.2, f"Concurrent execution took {concurrent_time:.2f}s, expected < 1.2s"
        assert len(results) == 3

        executor.shutdown(wait=False)

    def test_get_status(self):
        """Test getting executor status."""
        executor = DistributedExecutor(max_workers=2)
        status = executor.get_status()

        assert status["max_workers"] == 2
        assert status["pending"] == 0
        assert status["completed"] == 0
        assert status["running"] == 0

        executor.shutdown(wait=False)

    def test_dispatch_no_agent(self):
        """Test dispatching when no agent is available."""
        from app.ai.workflow_engine import AIWorkflowEngine

        engine = AIWorkflowEngine()  # No agents registered
        executor = DistributedExecutor(max_workers=2)

        task_id = executor.dispatch(engine, TaskType.CODE_REVIEW, {"code": "test"})
        assert task_id == ""

        executor.shutdown(wait=False)

    def test_get_distributed_executor_singleton(self):
        """Test the global executor singleton."""
        executor1 = get_distributed_executor()
        executor2 = get_distributed_executor()
        assert executor1 is executor2


# ============================================================
# Test Agent Task Type Coverage
# ============================================================

class TestTaskTypeCoverage:
    """Test that all task types can be routed after Phase 4."""

    def test_all_task_types_defined(self):
        """Test that all 22 task types are defined."""
        assert len(list(TaskType)) == 25  # 22 original + CODE_GENERATION + IMPLEMENTATION + REFACTORING

    def test_phase4_task_types_exist(self):
        """Test that Phase 4 task types exist."""
        assert TaskType.SPRINT_PLANNING is not None
        assert TaskType.TASK_DECOMPOSITION is not None
        assert TaskType.DEPENDENCY_ANALYSIS is not None
        assert TaskType.CODE_REVIEW is not None
        assert TaskType.PR_REVIEW is not None
        assert TaskType.DOC_GENERATION is not None
        assert TaskType.API_DOC_GENERATION is not None
