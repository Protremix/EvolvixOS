"""Tests for Verdis Benchmark Service — Phase 16."""

import pytest
from app.services.verdis_benchmark import (
    VerdisBenchmarkService, BenchmarkResult, get_benchmark_service,
)


class TestVerdisBenchmark:
    def test_benchmark_result_to_dict(self):
        r = BenchmarkResult(benchmark_type="test", duration_seconds=1.0, metrics={"x": 1})
        d = r.to_dict()
        assert d["benchmark_type"] == "test"
        assert d["metrics"]["x"] == 1

    def test_rpc_latency_benchmark(self):
        svc = VerdisBenchmarkService()
        result = svc.run_rpc_latency_benchmark(iterations=5)
        assert result.benchmark_type == "rpc_latency"
        assert result.duration_seconds > 0
        assert "avg_latency_ms" in result.metrics
        assert "p50_latency_ms" in result.metrics
        assert "p95_latency_ms" in result.metrics

    def test_validator_benchmark(self):
        svc = VerdisBenchmarkService()
        result = svc.run_validator_benchmark()
        assert result.benchmark_type == "validator_score"
        assert "validator_count" in result.metrics
        assert "overall_score" in result.metrics
        assert "grade" in result.metrics
        assert result.metrics["grade"] in ("A", "B", "C", "D")

    def test_run_all_benchmarks(self):
        svc = VerdisBenchmarkService()
        results = svc.run_all_benchmarks()
        assert len(results) >= 2
        types = [r.benchmark_type for r in results]
        assert "rpc_latency" in types
        assert "validator_score" in types

    def test_benchmark_service_singleton(self):
        svc1 = get_benchmark_service()
        svc2 = get_benchmark_service()
        assert svc1 is svc2


class TestVerdisBenchmarkAPI:
    def test_results_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-benchmark/results", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
