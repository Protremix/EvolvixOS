"""Tests for Pipeline Analytics — Post-MVP Phase 5."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from app.services.pipeline_analytics import (
    compute_pipeline_summary, compute_stage_metrics, compute_agent_metrics,
    compute_throughput, detect_bottlenecks, get_trends, get_full_analytics,
    StageMetrics, AgentMetrics, PipelineSummary,
)


def _make_stage(stage, agent, status="passed", duration_ms=100, retry_count=0):
    """Create a mock stage result."""
    s = MagicMock()
    s.stage = stage
    s.agent = agent
    s.status = status
    s.duration_ms = duration_ms
    s.retry_count = retry_count
    return s


def _make_run(status="completed", stages=None, duration_ms=1000, created_at=None):
    """Create a mock pipeline run."""
    r = MagicMock()
    r.status = status
    r.stages = stages or []
    r.total_duration_ms = duration_ms
    r.created_at = created_at or datetime.utcnow().isoformat()
    return r


class TestPipelineSummary:
    def test_empty_runs(self):
        summary = compute_pipeline_summary([])
        assert summary.total_pipelines == 0
        assert summary.completed == 0
        assert summary.success_rate == 0.0

    def test_completed_pipeline(self):
        run = _make_run(status="completed", duration_ms=500,
                        stages=[_make_stage("prd", "cto", "passed", 100)])
        summary = compute_pipeline_summary([run])
        assert summary.total_pipelines == 1
        assert summary.completed == 1
        assert summary.success_rate == 100.0
        assert summary.avg_duration_ms == 500.0

    def test_failed_pipeline(self):
        run = _make_run(status="failed", stages=[_make_stage("impl", "coder", "failed")])
        summary = compute_pipeline_summary([run])
        assert summary.failed == 1
        assert summary.success_rate == 0.0

    def test_mixed_pipelines(self):
        runs = [
            _make_run("completed", duration_ms=1000),
            _make_run("completed", duration_ms=2000),
            _make_run("failed"),
            _make_run("cancelled"),
            _make_run("pending"),
            _make_run("running"),
        ]
        summary = compute_pipeline_summary(runs)
        assert summary.total_pipelines == 6
        assert summary.completed == 2
        assert summary.failed == 1
        assert summary.cancelled == 1
        assert summary.running == 1
        assert summary.pending == 1
        assert summary.success_rate == 66.7  # 2 completed / (2 completed + 1 failed)

    def test_avg_stages_passed(self):
        stages = [_make_stage("a", "agent1", "passed"), _make_stage("b", "agent1", "passed"),
                   _make_stage("c", "agent1", "failed")]
        run = _make_run("failed", stages=stages)
        summary = compute_pipeline_summary([run])
        # Only counts for completed pipelines
        assert summary.avg_stages_passed == 0.0

    def test_retries_counted(self):
        stages = [_make_stage("a", "agent1", "passed", retry_count=2),
                   _make_stage("b", "agent2", "passed", retry_count=1)]
        run = _make_run("completed", stages=stages)
        summary = compute_pipeline_summary([run])
        assert summary.total_retries == 3


class TestStageMetrics:
    def test_empty(self):
        metrics = compute_stage_metrics([])
        assert len(metrics) == 0

    def test_single_stage(self):
        run = _make_run(stages=[_make_stage("prd", "cto", "passed", 500)])
        metrics = compute_stage_metrics([run])
        assert len(metrics) == 1
        assert metrics[0].stage == "prd"
        assert metrics[0].agent == "cto"
        assert metrics[0].passed == 1
        assert metrics[0].success_rate == 100.0
        assert metrics[0].avg_duration_ms == 500.0

    def test_multiple_runs_same_stage(self):
        runs = [
            _make_run(stages=[_make_stage("prd", "cto", "passed", 500)]),
            _make_run(stages=[_make_stage("prd", "cto", "passed", 700)]),
            _make_run(stages=[_make_stage("prd", "cto", "failed", 200)]),
        ]
        metrics = compute_stage_metrics(runs)
        assert len(metrics) == 1
        assert metrics[0].total_runs == 3
        assert metrics[0].passed == 2
        assert metrics[0].failed == 1
        assert metrics[0].success_rate == 66.7
        assert metrics[0].avg_duration_ms == 600.0  # (500 + 700) / 2
        assert metrics[0].max_duration_ms == 700
        assert metrics[0].min_duration_ms == 500

    def test_skipped_stage(self):
        run = _make_run(stages=[_make_stage("perf", "perf_agent", "skipped")])
        metrics = compute_stage_metrics([run])
        assert metrics[0].skipped == 1
        assert metrics[0].success_rate == 0.0

    def test_retry_tracking(self):
        run = _make_run(stages=[_make_stage("qa", "qa_agent", "passed", 100, retry_count=2)])
        metrics = compute_stage_metrics([run])
        assert metrics[0].total_retries == 2


class TestAgentMetrics:
    def test_empty(self):
        metrics = compute_agent_metrics([])
        assert len(metrics) == 0

    def test_single_agent(self):
        run = _make_run(stages=[
            _make_stage("prd", "cto", "passed", 500),
            _make_stage("review", "cto", "passed", 300),
        ])
        metrics = compute_agent_metrics([run])
        assert len(metrics) == 1
        assert metrics[0].agent == "cto"
        assert metrics[0].total_tasks == 2
        assert metrics[0].passed == 2
        assert metrics[0].success_rate == 100.0
        assert "prd" in metrics[0].stages
        assert "review" in metrics[0].stages

    def test_multiple_agents(self):
        run = _make_run(stages=[
            _make_stage("prd", "cto", "passed", 500),
            _make_stage("impl", "coder", "passed", 1000),
            _make_stage("qa", "qa_agent", "failed", 200),
        ])
        metrics = compute_agent_metrics([run])
        assert len(metrics) == 3
        agents = [m.agent for m in metrics]
        assert "cto" in agents
        assert "coder" in agents
        assert "qa_agent" in agents

    def test_agent_avg_duration(self):
        runs = [
            _make_run(stages=[_make_stage("impl", "coder", "passed", 1000)]),
            _make_run(stages=[_make_stage("impl", "coder", "passed", 2000)]),
        ]
        metrics = compute_agent_metrics(runs)
        coder = [m for m in metrics if m.agent == "coder"][0]
        assert coder.avg_duration_ms == 1500.0

    def test_agent_retries(self):
        run = _make_run(stages=[
            _make_stage("qa", "qa_agent", "passed", 100, retry_count=3),
        ])
        metrics = compute_agent_metrics([run])
        assert metrics[0].total_retries == 3


class TestThroughput:
    def test_empty(self):
        throughput = compute_throughput([], "daily", 7)
        assert throughput.period == "daily"
        assert len(throughput.data) == 7
        # All days should have 0 counts
        for d in throughput.data:
            assert d["total"] == 0

    def test_today_pipeline(self):
        run = _make_run("completed", created_at=datetime.utcnow().isoformat())
        throughput = compute_throughput([run], "daily", 7)
        assert len(throughput.data) == 7
        # The last day should have 1 total
        today_data = throughput.data[-1]
        assert today_data["total"] == 1
        assert today_data["completed"] == 1

    def test_old_pipeline_excluded(self):
        old_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        run = _make_run("completed", created_at=old_date)
        throughput = compute_throughput([run], "daily", 7)
        for d in throughput.data:
            assert d["total"] == 0

    def test_weekly_period(self):
        throughput = compute_throughput([], "weekly", 14)
        assert throughput.period == "weekly"


class TestBottlenecks:
    def test_no_bottlenecks(self):
        run = _make_run(stages=[
            _make_stage("a", "agent", "passed", 100),
            _make_stage("b", "agent", "passed", 100),
        ])
        bottlenecks = detect_bottlenecks([run])
        assert len(bottlenecks) == 0

    def test_detect_bottleneck(self):
        run = _make_run(stages=[
            _make_stage("fast", "agent", "passed", 100),
            _make_stage("slow", "agent", "passed", 500),
        ])
        bottlenecks = detect_bottlenecks([run], threshold_pct=1.5)
        # 500 > (100+500)/2 * 1.5 = 300 * 1.5 = 450
        assert len(bottlenecks) >= 1
        assert bottlenecks[0]["stage"] == "slow"

    def test_empty_runs(self):
        bottlenecks = detect_bottlenecks([])
        assert len(bottlenecks) == 0

    def test_sorted_by_duration(self):
        run = _make_run(stages=[
            _make_stage("medium", "agent", "passed", 200),
            _make_stage("very_slow", "agent", "passed", 1000),
            _make_stage("slow", "agent", "passed", 500),
        ])
        bottlenecks = detect_bottlenecks([run], threshold_pct=1.0)
        if len(bottlenecks) >= 2:
            assert bottlenecks[0]["avg_duration_ms"] >= bottlenecks[1]["avg_duration_ms"]


class TestTrends:
    def test_empty_runs(self):
        trends = get_trends([])
        assert trends["recent"]["total_pipelines"] == 0
        assert trends["previous"]["total_pipelines"] == 0

    def test_recent_vs_previous(self):
        now = datetime.utcnow()
        recent_run = _make_run("completed", created_at=(now - timedelta(days=1)).isoformat(), duration_ms=1000)
        old_run = _make_run("completed", created_at=(now - timedelta(days=10)).isoformat(), duration_ms=2000)

        trends = get_trends([recent_run, old_run], days=7)
        assert trends["recent"]["total_pipelines"] == 1
        assert trends["previous"]["total_pipelines"] == 1
        assert "success_rate" in trends["trends"]


class TestFullAnalytics:
    def test_full_analytics_structure(self):
        run = _make_run("completed", stages=[
            _make_stage("prd", "cto", "passed", 500),
            _make_stage("impl", "coder", "passed", 1000),
        ], duration_ms=1500)
        
        result = get_full_analytics([run])
        assert "summary" in result
        assert "stages" in result
        assert "agents" in result
        assert "throughput" in result
        assert "bottlenecks" in result
        assert "trends" in result
        assert result["summary"]["total_pipelines"] == 1
        assert len(result["stages"]) == 2
        assert len(result["agents"]) == 2


class TestAnalyticsAPI:
    def test_overview_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "stages" in data
        assert "agents" in data
        assert "throughput" in data

    def test_summary_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/summary", headers=headers)
        assert resp.status_code == 200
        assert "total_pipelines" in resp.json()

    def test_stages_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/stages", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_agents_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/agents", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_throughput_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/throughput", headers=headers)
        assert resp.status_code == 200
        assert "period" in resp.json()

    def test_bottlenecks_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/bottlenecks", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_trends_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-analytics/trends", headers=headers)
        assert resp.status_code == 200
        assert "recent" in resp.json()
        assert "trends" in resp.json()
