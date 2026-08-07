"""Tests for real LLM execution + monitoring integration — Phase 18 addendum."""

import pytest
from unittest.mock import patch, MagicMock
from app.services.agent_collaboration import (
    get_collaboration_service, COLLAB_PATTERNS,
)
from app.services.realtime_monitor import get_realtime_monitor
from app.ai.agents.base_agent import AgentResult, AgentStatus, TaskType


class TestRealLLMExecution:
    def test_execute_session_real_not_found(self):
        svc = get_collaboration_service()
        result = svc.execute_session_real("nonexistent")
        assert "error" in result

    def test_execute_session_real_with_mock_llm(self):
        """Test real execution path with mocked workflow engine."""
        svc = get_collaboration_service()
        session = svc.create_session(
            name="Real Exec Test", pattern="review_then_fix",
        )

        # Mock the workflow engine's execute_task
        mock_result = AgentResult(
            task_id="test", agent_name="reviewer_agent",
            status=AgentStatus.COMPLETED,
            content="Review complete",
            structured_data={"summary": "Code looks good", "verdict": "GO"},
            score=8.5,
            findings=[{"severity": "Low", "description": "Minor issue"}],
            recommendations=["Fix minor issue"],
            tokens_used=500,
            latency_ms=1500.0,
        )

        with patch("app.ai.workflow_engine.AIWorkflowEngine.execute_task", return_value=mock_result):
            result = svc.execute_session_real(session.id, use_verdis_context=False)

        assert result["status"] == "completed"
        assert result["execution_mode"] == "real_llm"
        assert len(result["steps"]) == 2
        assert result["steps"][0]["status"] == "completed"
        assert result["steps"][0]["score"] == 8.5
        assert result["final_result"]["overall_verdict"] == "GO"

    def test_execute_session_real_emits_monitor_events(self):
        """Test that real execution emits monitoring events."""
        svc = get_collaboration_service()
        monitor = get_realtime_monitor()
        monitor.clear_events()

        session = svc.create_session(
            name="Monitor Test", pattern="review_then_fix",
        )

        mock_result = AgentResult(
            task_id="test", agent_name="reviewer_agent",
            status=AgentStatus.COMPLETED,
            content="Done",
            structured_data={"verdict": "GO"},
            score=9.0,
            tokens_used=300,
        )

        with patch("app.ai.workflow_engine.AIWorkflowEngine.execute_task", return_value=mock_result):
            svc.execute_session_real(session.id, use_verdis_context=False)

        events = monitor.get_events(limit=50)
        types = [e["type"] for e in events]
        assert "collaboration_started" in types
        assert "agent_started" in types
        assert "agent_completed" in types
        assert "collaboration_completed" in types

    def test_execute_session_real_handles_failure(self):
        """Test that real execution handles agent failures gracefully."""
        svc = get_collaboration_service()
        session = svc.create_session(
            name="Failure Test", pattern="review_then_fix",
        )

        mock_result = AgentResult(
            task_id="test", agent_name="reviewer_agent",
            status=AgentStatus.FAILED,
            content="LLM call failed",
        )

        with patch("app.ai.workflow_engine.AIWorkflowEngine.execute_task", return_value=mock_result):
            result = svc.execute_session_real(session.id, use_verdis_context=False)

        assert result["status"] == "completed"
        assert result["steps"][0]["status"] == "failed"

    def test_execute_session_real_records_metrics(self):
        """Test that real execution records latency and token metrics."""
        svc = get_collaboration_service()
        monitor = get_realtime_monitor()

        session = svc.create_session(
            name="Metrics Test", pattern="review_then_fix",
        )

        mock_result = AgentResult(
            task_id="test", agent_name="reviewer_agent",
            status=AgentStatus.COMPLETED,
            content="Done",
            structured_data={"verdict": "GO"},
            score=8.0,
            tokens_used=750,
        )

        with patch("app.ai.workflow_engine.AIWorkflowEngine.execute_task", return_value=mock_result):
            svc.execute_session_real(session.id, use_verdis_context=False)

        latency_metrics = monitor.get_metrics(name="agent_latency_ms")
        token_metrics = monitor.get_metrics(name="agent_tokens")
        assert len(latency_metrics) >= 2  # 2 steps
        assert len(token_metrics) >= 2
        assert token_metrics[0]["value"] == 750

    def test_execute_with_verdis_context(self):
        """Test that Verdis context is injected when enabled."""
        svc = get_collaboration_service()
        session = svc.create_session(
            name="Verdis Context Test", pattern="parallel_review",
        )

        captured_data = []

        def mock_execute(self, task_type, data):
            captured_data.append(data)
            return AgentResult(
                task_id="test", agent_name="test",
                status=AgentStatus.COMPLETED,
                content="Done",
                structured_data={"verdict": "GO"},
                score=8.0,
                tokens_used=100,
            )

        with patch("app.ai.workflow_engine.AIWorkflowEngine.execute_task", mock_execute):
            svc.execute_session_real(session.id, use_verdis_context=True)

        # Check Verdis context was injected
        assert any("verdis_context" in d for d in captured_data)
        assert any("chain_name" in d.get("verdis_context", {}) for d in captured_data)


class TestExecuteAPI:
    def test_execute_session_api(self, client, test_user):
        """Test the real execution API endpoint."""
        # Create session
        create = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "API Exec Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        sid = create.json()["id"]

        # Mock the workflow engine
        mock_result = AgentResult(
            task_id="test", agent_name="reviewer_agent",
            status=AgentStatus.COMPLETED,
            content="Done",
            structured_data={"verdict": "GO"},
            score=8.5,
            tokens_used=500,
        )

        with patch("app.ai.workflow_engine.AIWorkflowEngine.execute_task", return_value=mock_result):
            resp = client.post(
                f"/api/v1/collab-monitor/sessions/{sid}/execute?use_verdis_context=false",
                headers=test_user["headers"],
            )
        assert resp.status_code == 200
        assert resp.json()["execution_mode"] == "real_llm"
        assert resp.json()["status"] == "completed"

    def test_execute_nonexistent_session_api(self, client, test_user):
        resp = client.post(
            "/api/v1/collab-monitor/sessions/nonexistent/execute",
            headers=test_user["headers"],
        )
        assert resp.status_code == 200
        assert "error" in resp.json()


class TestMonitorWebSocketIntegration:
    def test_monitor_events_after_collaboration(self, client, test_user):
        """Test that monitor events are recorded after collaboration activity."""
        monitor = get_realtime_monitor()
        monitor.clear_events()

        # Create and simulate a session (emits events)
        create = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "Event Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        sid = create.json()["id"]

        client.post(
            f"/api/v1/collab-monitor/sessions/{sid}/simulate",
            headers=test_user["headers"],
        )

        # Check events were emitted
        events = monitor.get_events(limit=50)
        types = [e["type"] for e in events]
        assert "collaboration_started" in types
        assert "collaboration_completed" in types
