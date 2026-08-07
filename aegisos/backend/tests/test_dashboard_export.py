"""Tests for Dashboard + Export — Post-MVP Phase 8."""

import pytest
import json
from app.services.dashboard import (
    DashboardService, PerformanceTracker, get_dashboard_service, get_performance_tracker,
)
from app.services.export_service import ExportService, get_export_service


class TestPerformanceTracker:
    def test_record_metric(self):
        tracker = PerformanceTracker()
        tracker.record("/api/test", "GET", 50.5, 200)
        assert len(tracker._metrics) == 1
        assert tracker._metrics[0].endpoint == "/api/test"
        assert tracker._metrics[0].duration_ms == 50.5

    def test_get_stats_empty(self):
        tracker = PerformanceTracker()
        stats = tracker.get_stats()
        assert stats["total_requests"] == 0

    def test_get_stats_with_metrics(self):
        tracker = PerformanceTracker()
        tracker.record("/api/test", "GET", 100, 200)
        tracker.record("/api/test", "GET", 200, 200)
        tracker.record("/api/error", "POST", 50, 500)
        stats = tracker.get_stats()
        assert stats["total_requests"] == 3
        assert stats["avg_duration_ms"] == pytest.approx(116.67, 0.1)
        assert stats["max_duration_ms"] == 200
        assert stats["min_duration_ms"] == 50
        assert stats["error_rate"] == pytest.approx(33.3, 0.1)

    def test_slowest_endpoints(self):
        tracker = PerformanceTracker()
        tracker.record("/api/fast", "GET", 10, 200)
        tracker.record("/api/slow", "GET", 500, 200)
        stats = tracker.get_stats()
        assert stats["slowest_endpoints"][0]["endpoint"] == "GET /api/slow"

    def test_max_entries_ring_buffer(self):
        tracker = PerformanceTracker(max_metrics=3)
        for i in range(5):
            tracker.record(f"/api/{i}", "GET", 100, 200)
        assert len(tracker._metrics) == 3

    def test_clear(self):
        tracker = PerformanceTracker()
        tracker.record("/api/test", "GET", 50, 200)
        tracker.clear()
        assert len(tracker._metrics) == 0

    def test_thread_safe(self):
        import threading
        tracker = PerformanceTracker(max_metrics=10000)
        
        def record_many():
            for i in range(100):
                tracker.record(f"/api/{i}", "GET", 50, 200)
        
        threads = [threading.Thread(target=record_many) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        assert len(tracker._metrics) == 500


class TestDashboardService:
    def test_get_overview_structure(self):
        svc = DashboardService()
        overview = svc.get_overview()
        assert "timestamp" in overview
        assert "subsystems" in overview
        assert "pipeline_stats" in overview
        assert "agent_stats" in overview
        assert "knowledge_stats" in overview
        assert "activity_stats" in overview
        assert "performance_stats" in overview
        assert "verdis_stats" in overview

    def test_subsystem_health(self):
        svc = DashboardService()
        overview = svc.get_overview()
        subsystems = overview["subsystems"]
        assert "authentication" in subsystems
        assert "ai_engine" in subsystems
        assert "pipelines" in subsystems
        assert "knowledge_base" in subsystems
        assert "agent_config" in subsystems
        assert "activity_log" in subsystems
        # Each should have a status
        for name, health in subsystems.items():
            assert "status" in health

    def test_pipeline_stats_structure(self):
        svc = DashboardService()
        stats = svc.get_overview()["pipeline_stats"]
        assert "total" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert "running" in stats
        assert "pending" in stats

    def test_agent_stats(self):
        svc = DashboardService()
        stats = svc.get_overview()["agent_stats"]
        assert stats["total_agents"] >= 11
        assert stats["enabled"] >= 0
        assert len(stats["agent_names"]) >= 11


class TestExportService:
    def test_export_pipelines_json(self):
        svc = ExportService()
        data = svc.export_pipelines("json")
        parsed = json.loads(data)
        assert isinstance(parsed, list)

    def test_export_pipelines_csv(self):
        svc = ExportService()
        data = svc.export_pipelines("csv")
        assert "id" in data  # CSV header

    def test_export_knowledge_base_json(self):
        svc = ExportService()
        data = svc.export_knowledge_base("json")
        parsed = json.loads(data)
        assert isinstance(parsed, list)
        assert len(parsed) >= 6  # built-in entries

    def test_export_knowledge_base_csv(self):
        svc = ExportService()
        data = svc.export_knowledge_base("csv")
        assert "category" in data
        assert "title" in data

    def test_export_agent_configs_json(self):
        svc = ExportService()
        data = svc.export_agent_configs("json")
        parsed = json.loads(data)
        assert len(parsed) >= 11

    def test_export_agent_configs_csv(self):
        svc = ExportService()
        data = svc.export_agent_configs("csv")
        assert "agent_name" in data
        assert "model" in data

    def test_export_activity_log_json(self):
        svc = ExportService()
        data = svc.export_activity_log("json", limit=10)
        parsed = json.loads(data)
        assert isinstance(parsed, list)

    def test_export_activity_log_csv(self):
        svc = ExportService()
        data = svc.export_activity_log("csv", limit=10)
        assert "action" in data

    def test_export_full_snapshot(self):
        svc = ExportService()
        data = svc.export_full_snapshot()
        parsed = json.loads(data)
        assert "exported_at" in parsed
        assert "system" in parsed
        assert "data" in parsed
        assert "pipelines" in parsed["data"]
        assert "knowledge_base" in parsed["data"]
        assert "agent_configs" in parsed["data"]

    def test_csv_special_chars(self):
        """Test that CSV handles special characters in content."""
        from app.services.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        kb.add_entry(__import__('app.services.knowledge_base', fromlist=['KnowledgeEntry']).KnowledgeEntry(
            title='Test, with "quotes"',
            content='Line 1\nLine 2',
            category='general',
        ))
        svc = ExportService()
        data = svc.export_knowledge_base("csv")
        assert "quotes" in data


class TestDashboardAPI:
    def test_overview_api(self, client, test_user):
        resp = client.get("/api/v1/dashboard/overview", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "subsystems" in resp.json()

    def test_performance_api(self, client, test_user):
        resp = client.get("/api/v1/dashboard/performance", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_requests" in resp.json()

    def test_clear_performance_api(self, client, test_user):
        resp = client.delete("/api/v1/dashboard/performance", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_export_pipelines_json_api(self, client, test_user):
        resp = client.get("/api/v1/export/pipelines?format=json", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_export_pipelines_csv_api(self, client, test_user):
        resp = client.get("/api/v1/export/pipelines?format=csv", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_export_knowledge_base_json_api(self, client, test_user):
        resp = client.get("/api/v1/export/knowledge-base?format=json", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_export_knowledge_base_csv_api(self, client, test_user):
        resp = client.get("/api/v1/export/knowledge-base?format=csv", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_export_agent_configs_api(self, client, test_user):
        resp = client.get("/api/v1/export/agent-configs?format=json", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_export_activity_log_api(self, client, test_user):
        resp = client.get("/api/v1/export/activity-log?format=json", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_export_snapshot_api(self, client, test_user):
        resp = client.get("/api/v1/export/snapshot", headers=test_user["headers"])
        assert resp.status_code == 200
        parsed = resp.json()
        assert "exported_at" in parsed
