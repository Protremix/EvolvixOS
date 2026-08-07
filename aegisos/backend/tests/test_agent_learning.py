"""Tests for Agent Learning Loop — Phase 19."""

import pytest
from app.services.agent_learning import (
    AgentLearningLoop, AgentExecution, LearningInsight,
    PromptOptimization, get_learning_loop,
)


class TestAgentExecution:
    def test_execution_defaults(self):
        e = AgentExecution(agent_name="cto_agent", task_type="architecture_review")
        assert e.agent_name == "cto_agent"
        assert e.status == "completed"
        assert e.score is None
        assert e.id.startswith("exec-")

    def test_to_dict(self):
        e = AgentExecution(agent_name="cto", task_type="review", score=8.5)
        d = e.to_dict()
        assert d["agent_name"] == "cto"
        assert d["score"] == 8.5


class TestLearningLoop:
    def test_record_execution(self):
        loop = AgentLearningLoop()
        e = AgentExecution(agent_name="cto_agent", task_type="architecture_review",
                           score=8.5, verdict="GO", tokens_used=500, latency_ms=1200)
        loop.record_execution(e)
        assert loop._agent_stats["cto_agent"]["total"] == 1
        assert loop._agent_stats["cto_agent"]["completed"] == 1
        assert 8.5 in loop._agent_stats["cto_agent"]["scores"]

    def test_record_failed_execution(self):
        loop = AgentLearningLoop()
        e = AgentExecution(agent_name="cto", task_type="review", status="failed")
        loop.record_execution(e)
        assert loop._agent_stats["cto"]["failed"] == 1

    def test_record_multiple_executions(self):
        loop = AgentLearningLoop()
        for score in [7.0, 8.0, 9.0, 8.5, 7.5]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score, verdict="GO",
            ))
        stats = loop._agent_stats["cto"]
        assert stats["total"] == 5
        assert stats["completed"] == 5
        assert len(stats["scores"]) == 5

    def test_analyze_no_data(self):
        loop = AgentLearningLoop()
        insights = loop.analyze()
        assert insights == []

    def test_analyze_insufficient_data(self):
        loop = AgentLearningLoop()
        loop.record_execution(AgentExecution(agent_name="cto", task_type="review", score=8.0))
        loop.record_execution(AgentExecution(agent_name="cto", task_type="review", score=8.5))
        insights = loop.analyze()
        assert insights == []  # Need at least 3 executions

    def test_analyze_performance_trend_improving(self):
        loop = AgentLearningLoop()
        # Scores improving over time
        for score in [6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score, verdict="GO",
            ))
        insights = loop.analyze()
        trend_insights = [i for i in insights if i.insight_type == "performance_trend"]
        assert len(trend_insights) >= 1
        assert "improving" in trend_insights[0].description.lower()

    def test_analyze_performance_trend_regressing(self):
        loop = AgentLearningLoop()
        # Scores declining
        for score in [9.0, 8.5, 8.0, 7.0, 6.5, 6.0, 5.5, 5.0]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score, verdict="GO",
            ))
        insights = loop.analyze()
        regression = [i for i in insights if i.insight_type == "score_regression"]
        assert len(regression) >= 1
        assert "regressing" in regression[0].description.lower()
        assert regression[0].actionable is True

    def test_analyze_failure_pattern(self):
        loop = AgentLearningLoop()
        for i in range(7):
            status = "failed" if i % 2 == 0 else "completed"
            loop.record_execution(AgentExecution(
                agent_name="security", task_type="security_review",
                status=status, score=7.0 if status == "completed" else None,
            ))
        insights = loop.analyze()
        failures = [i for i in insights if i.insight_type == "failure_pattern"]
        assert len(failures) >= 1
        assert failures[0].actionable is True

    def test_analyze_verdict_too_lenient(self):
        loop = AgentLearningLoop()
        for _ in range(10):
            loop.record_execution(AgentExecution(
                agent_name="reviewer", task_type="code_review",
                score=9.0, verdict="GO",
            ))
        insights = loop.analyze()
        lenient = [i for i in insights if i.insight_type == "success_pattern"]
        assert len(lenient) >= 1
        assert "lenient" in lenient[0].description.lower()

    def test_analyze_verdict_too_strict(self):
        loop = AgentLearningLoop()
        for _ in range(10):
            loop.record_execution(AgentExecution(
                agent_name="reviewer", task_type="code_review",
                score=4.0, verdict="NO-GO",
            ))
        insights = loop.analyze()
        strict = [i for i in insights if i.insight_type == "failure_pattern"]
        assert len(strict) >= 1

    def test_prompt_optimization_low_score(self):
        loop = AgentLearningLoop()
        for score in [5.0, 5.5, 6.0, 6.5, 6.0, 5.5]:
            loop.record_execution(AgentExecution(
                agent_name="qa", task_type="quality_gate", score=score, verdict="NO-GO",
            ))
        loop.analyze()
        opts = loop.get_prompt_optimizations("qa")
        assert len(opts) >= 1
        assert "below threshold" in opts[0].current_issue or "below" in opts[0].current_issue

    def test_prompt_optimization_too_lenient(self):
        loop = AgentLearningLoop()
        for _ in range(10):
            loop.record_execution(AgentExecution(
                agent_name="reviewer", task_type="code_review",
                score=9.5, verdict="GO",
            ))
        loop.analyze()
        opts = loop.get_prompt_optimizations("reviewer")
        assert len(opts) >= 1
        assert "critical" in opts[0].current_issue.lower() or "adversarial" in opts[0].suggested_improvement.lower()

    def test_get_agent_performance(self):
        loop = AgentLearningLoop()
        for score in [7.0, 8.0, 9.0]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score,
                verdict="GO", tokens_used=500, latency_ms=1000,
            ))
        perf = loop.get_agent_performance("cto")
        assert perf["total_executions"] == 3
        assert perf["avg_score"] == 8.0
        assert perf["success_rate"] == 100.0
        assert perf["avg_tokens"] == 500

    def test_get_agent_performance_no_data(self):
        loop = AgentLearningLoop()
        perf = loop.get_agent_performance("unknown")
        assert perf["total"] == 0

    def test_get_all_performance(self):
        loop = AgentLearningLoop()
        loop.record_execution(AgentExecution(agent_name="cto", task_type="review", score=8.0))
        loop.record_execution(AgentExecution(agent_name="security", task_type="audit", score=7.5))
        all_perf = loop.get_all_performance()
        assert len(all_perf) == 2

    def test_get_feedback(self):
        loop = AgentLearningLoop()
        for score in [5.0, 5.5, 6.0, 6.5, 6.0, 5.5]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score, verdict="NO-GO",
                tokens_used=500, latency_ms=1200,
            ))
        feedback = loop.get_feedback_for_agent("cto")
        assert feedback["applied"] is True
        assert "feedback" in feedback
        assert len(feedback["feedback"]) > 0

    def test_get_feedback_no_data(self):
        loop = AgentLearningLoop()
        feedback = loop.get_feedback_for_agent("unknown")
        assert feedback["applied"] is False

    def test_get_feedback_insufficient_data(self):
        loop = AgentLearningLoop()
        loop.record_execution(AgentExecution(agent_name="cto", task_type="review", score=8.0))
        feedback = loop.get_feedback_for_agent("cto")
        assert feedback["applied"] is False

    def test_get_feedback_includes_past_insight(self):
        loop = AgentLearningLoop()
        for score in [9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score, verdict="GO",
            ))
        loop.analyze()
        feedback = loop.get_feedback_for_agent("cto")
        assert "Past insight" in feedback["feedback"]

    def test_get_learning_summary(self):
        loop = AgentLearningLoop()
        loop.record_execution(AgentExecution(agent_name="cto", task_type="review", score=8.0))
        summary = loop.get_learning_summary()
        assert summary["total_executions"] == 1
        assert summary["agents_tracked"] == 1
        assert "task_performance" in summary

    def test_get_insights_filtered(self):
        loop = AgentLearningLoop()
        for score in [6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5]:
            loop.record_execution(AgentExecution(
                agent_name="cto", task_type="review", score=score, verdict="GO",
            ))
        loop.analyze()
        trend = loop.get_insights(insight_type="performance_trend")
        assert all(i.insight_type == "performance_trend" for i in trend)

    def test_clear(self):
        loop = AgentLearningLoop()
        loop.record_execution(AgentExecution(agent_name="cto", task_type="review", score=8.0))
        loop.clear()
        assert len(loop._executions) == 0
        assert len(loop._agent_stats) == 0

    def test_singleton(self):
        assert get_learning_loop() is get_learning_loop()


class TestLearningAPI:
    def test_record_execution_api(self, client, test_user):
        resp = client.post("/api/v1/agent-learning/executions", json={
            "agent_name": "cto_agent", "task_type": "architecture_review",
            "score": 8.5, "verdict": "GO", "tokens_used": 500,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_get_executions_api(self, client, test_user):
        client.post("/api/v1/agent-learning/executions", json={
            "agent_name": "cto", "task_type": "review", "score": 8.0,
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/agent-learning/executions", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_analyze_api(self, client, test_user):
        resp = client.post("/api/v1/agent-learning/analyze", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_insights_api(self, client, test_user):
        resp = client.get("/api/v1/agent-learning/insights", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_prompt_optimizations_api(self, client, test_user):
        resp = client.get("/api/v1/agent-learning/prompt-optimizations", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_performance_api(self, client, test_user):
        resp = client.get("/api/v1/agent-learning/performance", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_agent_performance_api(self, client, test_user):
        resp = client.get("/api/v1/agent-learning/performance/cto_agent", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_feedback_api(self, client, test_user):
        resp = client.get("/api/v1/agent-learning/feedback/cto_agent", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_summary_api(self, client, test_user):
        resp = client.get("/api/v1/agent-learning/summary", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_executions" in resp.json()
