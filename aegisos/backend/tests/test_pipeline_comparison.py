"""Tests for Pipeline Comparison — Post-MVP Phase 7."""

import pytest
from unittest.mock import MagicMock
from app.services.pipeline_comparison import compare_pipeline_runs, StageDiff, PipelineComparison


def _make_stage(stage, agent, status="passed", duration_ms=100, retry_count=0, error=None):
    s = MagicMock()
    s.stage = stage
    s.agent = agent
    s.status = status
    s.duration_ms = duration_ms
    s.retry_count = retry_count
    s.error = error
    return s


def _make_run(id="run-1", title="Test", status="completed", stages=None, duration_ms=1000):
    r = MagicMock()
    r.id = id
    r.title = title
    r.status = status
    r.stages = stages or []
    r.total_duration_ms = duration_ms
    return r


class TestPipelineComparison:
    def test_identical_runs(self):
        stages = [_make_stage("prd", "cto", "passed", 500), _make_stage("impl", "coder", "passed", 1000)]
        run_a = _make_run("a", "Run A", "completed", stages, 1500)
        run_b = _make_run("b", "Run B", "completed", stages, 1500)
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.run_a_id == "a"
        assert comparison.run_b_id == "b"
        assert comparison.total_duration_delta_ms == 0
        assert len(comparison.stages) == 2
        assert all(not s.status_changed for s in comparison.stages)

    def test_status_change(self):
        run_a = _make_run("a", stages=[_make_stage("qa", "qa_agent", "passed", 500)])
        run_b = _make_run("b", stages=[_make_stage("qa", "qa_agent", "failed", 300)])
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.stages[0].status_changed is True
        assert "now fails" in comparison.regressions[0]

    def test_improvement_from_fail_to_pass(self):
        run_a = _make_run("a", stages=[_make_stage("qa", "qa_agent", "failed", 500)])
        run_b = _make_run("b", stages=[_make_stage("qa", "qa_agent", "passed", 300)])
        comparison = compare_pipeline_runs(run_a, run_b)
        assert "now passes" in comparison.improvements[0]

    def test_duration_delta(self):
        run_a = _make_run("a", stages=[_make_stage("prd", "cto", "passed", 500)], duration_ms=500)
        run_b = _make_run("b", stages=[_make_stage("prd", "cto", "passed", 800)], duration_ms=800)
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.stages[0].duration_delta_ms == 300
        assert comparison.total_duration_delta_ms == 300
        assert any("slower" in r for r in comparison.regressions)

    def test_duration_improvement(self):
        run_a = _make_run("a", stages=[_make_stage("prd", "cto", "passed", 800)], duration_ms=800)
        run_b = _make_run("b", stages=[_make_stage("prd", "cto", "passed", 500)], duration_ms=500)
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.stages[0].duration_delta_ms == -300
        assert any("faster" in i for i in comparison.improvements)

    def test_retry_change(self):
        run_a = _make_run("a", stages=[_make_stage("impl", "coder", "passed", 1000, retry_count=3)])
        run_b = _make_run("b", stages=[_make_stage("impl", "coder", "passed", 1000, retry_count=0)])
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.stages[0].retries_changed is True
        assert any("retries reduced" in i for i in comparison.improvements)

    def test_retry_increase(self):
        run_a = _make_run("a", stages=[_make_stage("impl", "coder", "passed", 1000, retry_count=0)])
        run_b = _make_run("b", stages=[_make_stage("impl", "coder", "passed", 1000, retry_count=2)])
        comparison = compare_pipeline_runs(run_a, run_b)
        assert any("retries increased" in r for r in comparison.regressions)

    def test_stage_only_in_a(self):
        run_a = _make_run("a", stages=[_make_stage("prd", "cto", "passed", 500), _make_stage("extra", "agent", "passed", 100)])
        run_b = _make_run("b", stages=[_make_stage("prd", "cto", "passed", 500)])
        comparison = compare_pipeline_runs(run_a, run_b)
        extra_stage = [s for s in comparison.stages if s.stage == "extra"][0]
        assert extra_stage.only_in_a is True
        assert extra_stage.only_in_b is False

    def test_stage_only_in_b(self):
        run_a = _make_run("a", stages=[_make_stage("prd", "cto", "passed", 500)])
        run_b = _make_run("b", stages=[_make_stage("prd", "cto", "passed", 500), _make_stage("extra", "agent", "passed", 100)])
        comparison = compare_pipeline_runs(run_a, run_b)
        extra_stage = [s for s in comparison.stages if s.stage == "extra"][0]
        assert extra_stage.only_in_b is True
        assert extra_stage.only_in_a is False

    def test_error_change(self):
        run_a = _make_run("a", stages=[_make_stage("qa", "qa", "failed", 100, error="null pointer")])
        run_b = _make_run("b", stages=[_make_stage("qa", "qa", "failed", 100, error="timeout")])
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.stages[0].error_changed is True

    def test_to_dict_structure(self):
        run_a = _make_run("a", "Title A", "completed", [_make_stage("prd", "cto", "passed", 500)], 500)
        run_b = _make_run("b", "Title B", "completed", [_make_stage("prd", "cto", "passed", 300)], 300)
        comparison = compare_pipeline_runs(run_a, run_b)
        d = comparison.to_dict()
        assert "run_a_id" in d
        assert "stages" in d
        assert "improvements" in d
        assert "regressions" in d

    def test_stages_passed_count(self):
        run_a = _make_run("a", stages=[_make_stage("s1", "a1", "passed"), _make_stage("s2", "a2", "failed")])
        run_b = _make_run("b", stages=[_make_stage("s1", "a1", "passed"), _make_stage("s2", "a2", "passed")])
        comparison = compare_pipeline_runs(run_a, run_b)
        assert comparison.run_a_stages_passed == 1
        assert comparison.run_b_stages_passed == 2
        assert comparison.run_a_stages_failed == 1
        assert comparison.run_b_stages_failed == 0


class TestPipelineComparisonAPI:
    def test_compare_api(self, client, test_user):
        from app.api.v1.feature_pipeline import _pipeline_runs
        
        run_a = MagicMock(id="run-a-comp", title="A", status="completed",
                         stages=[_make_stage("prd", "cto", "passed", 500)],
                         total_duration_ms=500)
        run_b = MagicMock(id="run-b-comp", title="B", status="completed",
                         stages=[_make_stage("prd", "cto", "passed", 300)],
                         total_duration_ms=300)
        _pipeline_runs[run_a.id] = run_a
        _pipeline_runs[run_b.id] = run_b

        resp = client.get(f"/api/v1/pipeline-comparison/{run_a.id}/{run_b.id}", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["run_a_id"] == "run-a-comp"

    def test_compare_not_found(self, client, test_user):
        resp = client.get("/api/v1/pipeline-comparison/nonexistent/also-nonexistent", headers=test_user["headers"])
        assert resp.status_code == 404
