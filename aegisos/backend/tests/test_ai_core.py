"""
Tests for AI Core — workflow engine, agent registration, and API endpoints.

Uses mocked LLM calls to avoid real API usage in tests.
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ============================================================
# Test Agent (mock agent for testing)
# ============================================================

from app.ai.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    AgentStatus,
    TaskType,
)


class MockAgent(BaseAgent):
    """Test agent that returns a predictable response without LLM calls."""
    name = "mock_agent"
    description = "Mock agent for testing"
    handled_task_types = {TaskType.ARCHITECTURE_REVIEW, TaskType.SECURITY_REVIEW}

    @property
    def system_prompt(self) -> str:
        return "You are a mock agent for testing."

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=f"Mock result for {task.type.value}",
            structured_data={"mock": True, "task_type": task.type.value},
            score=8.5,
            findings=[{"severity": "low", "description": "Test finding"}],
            recommendations=["Test recommendation"],
            tokens_used=100,
            latency_ms=50.0,
        )


# ============================================================
# Workflow Engine Tests
# ============================================================

class TestWorkflowEngine:
    """Tests for the AI Workflow Engine."""

    def test_register_agent(self):
        """Test registering an agent."""
        from app.ai.workflow_engine import AIWorkflowEngine
        engine = AIWorkflowEngine()
        agent = MockAgent()
        engine.register_agent(agent)

        assert "mock_agent" in engine._agents
        assert engine.route_task(TaskType.ARCHITECTURE_REVIEW) is agent
        assert engine.route_task(TaskType.SECURITY_REVIEW) is agent

    def test_route_task_no_agent(self):
        """Test routing when no agent is registered for the task type."""
        from app.ai.workflow_engine import AIWorkflowEngine
        engine = AIWorkflowEngine()
        result = engine.route_task(TaskType.TEST_GENERATION)
        assert result is None

    def test_execute_task(self):
        """Test executing a task through the workflow engine."""
        from app.ai.workflow_engine import AIWorkflowEngine
        engine = AIWorkflowEngine()
        engine.register_agent(MockAgent())

        result = engine.execute_task(TaskType.ARCHITECTURE_REVIEW, {"test": "data"})

        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "mock_agent"
        assert "Mock result" in result.content
        assert result.score == 8.5
        assert len(result.findings) == 1
        assert len(result.recommendations) == 1

    def test_execute_task_no_agent(self):
        """Test executing a task when no agent is available."""
        from app.ai.workflow_engine import AIWorkflowEngine
        engine = AIWorkflowEngine()

        result = engine.execute_task(TaskType.TEST_GENERATION, {"test": "data"})

        assert result.status == AgentStatus.FAILED
        assert "No agent" in result.content

    def test_list_agents(self):
        """Test listing registered agents."""
        from app.ai.workflow_engine import AIWorkflowEngine
        engine = AIWorkflowEngine()
        engine.register_agent(MockAgent())

        agents = engine.list_agents()

        assert len(agents) == 1
        assert agents[0]["name"] == "mock_agent"
        assert "architecture_review" in agents[0]["task_types"]
        assert "security_review" in agents[0]["task_types"]


# ============================================================
# Base Agent Tests
# ============================================================

class TestBaseAgent:
    """Tests for the BaseAgent class."""

    def test_agent_can_handle(self):
        """Test the can_handle method."""
        agent = MockAgent()
        assert agent.can_handle(TaskType.ARCHITECTURE_REVIEW) is True
        assert agent.can_handle(TaskType.SECURITY_REVIEW) is True
        assert agent.can_handle(TaskType.TEST_GENERATION) is False

    def test_agent_name(self):
        """Test agent name."""
        agent = MockAgent()
        assert agent.name == "mock_agent"

    def test_agent_system_prompt(self):
        """Test the system prompt property."""
        agent = MockAgent()
        assert "mock agent" in agent.system_prompt.lower()


# ============================================================
# API Endpoint Tests
# ============================================================

class TestAIAPI:
    """Tests for the AI Core API endpoints."""

    def test_list_agents(self, client, test_user):
        """Test listing agents via API."""
        with patch("app.ai.workflow_engine.get_workflow_engine") as mock_get:
            mock_engine = MagicMock()
            mock_engine.list_agents.return_value = [
                {
                    "name": "cto_agent",
                    "description": "AI CTO",
                    "task_types": ["architecture_review"],
                }
            ]
            mock_get.return_value = mock_engine

            response = client.get(
                "/api/v1/ai/agents",
                headers=test_user["headers"],
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "cto_agent"

    def test_list_agents_unauthorized(self, client):
        """Test listing agents without auth."""
        response = client.get("/api/v1/ai/agents")
        assert response.status_code == 401

    def test_execute_task_invalid_type(self, client, test_user):
        """Test executing a task with an invalid type."""
        response = client.post(
            "/api/v1/ai/tasks",
            json={"task_type": "invalid_type", "data": {}},
            headers=test_user["headers"],
        )
        assert response.status_code == 400

    def test_execute_task_success(self, client, test_user):
        """Test executing a task successfully via API."""
        with patch("app.ai.workflow_engine.get_workflow_engine") as mock_get:
            mock_engine = MagicMock()
            mock_engine.route_task.return_value = MockAgent()
            mock_engine.execute_task.return_value = AgentResult(
                task_id="test-123",
                agent_name="mock_agent",
                status=AgentStatus.COMPLETED,
                content="Test result content",
                structured_data={"result": "ok"},
                score=9.0,
                findings=[],
                recommendations=["Do X"],
                tokens_used=150,
                latency_ms=75.0,
            )
            mock_get.return_value = mock_engine

            response = client.post(
                "/api/v1/ai/tasks",
                json={"task_type": "architecture_review", "data": {"code": "test"}},
                headers=test_user["headers"],
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["agent_name"] == "mock_agent"
        assert data["content"] == "Test result content"
        assert data["score"] == 9.0

    def test_ai_health(self, client, test_user):
        """Test AI health endpoint."""
        with patch("app.ai.workflow_engine.get_workflow_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.list_agents.return_value = [
                {"name": "cto_agent", "description": "CTO", "task_types": ["architecture_review"]}
            ]
            mock_get_engine.return_value = mock_engine

            with patch("app.ai.llm_client.get_llm_client") as mock_get_llm:
                mock_llm = MagicMock()
                mock_llm.model = "gpt-4o"
                mock_llm.api_key = "test-key"
                mock_get_llm.return_value = mock_llm

                response = client.get(
                    "/api/v1/ai/health",
                    headers=test_user["headers"],
                )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agents_registered"] == 1
        assert data["llm_model"] == "gpt-4o"
