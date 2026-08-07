"""Tests for Local Monitor — Phase 28."""

import pytest
from app.services.local_monitor import LocalMonitor, get_local_monitor


class TestLocalMonitor:
    def test_check_service_offline(self):
        monitor = LocalMonitor()
        health = monitor.check_service("Test", "http://localhost:99999/nonexistent")
        assert health.status == "offline"
        assert health.name == "Test"

    def test_check_all(self):
        monitor = LocalMonitor()
        results = monitor.check_all()
        assert len(results) == 4
        assert all(r.name in ["EvolvixOS Backend", "EvolvixOS Frontend", "Redis", "Verdis Node"] for r in results)

    def test_get_system_metrics(self):
        monitor = LocalMonitor()
        metrics = monitor.get_system_metrics()
        assert "timestamp" in metrics
        # May fail if psutil not available, but should return timestamp

    def test_get_all_health(self):
        monitor = LocalMonitor()
        monitor.check_all()
        health = monitor.get_all_health()
        assert "services" in health
        assert "system" in health
        assert "summary" in health
        assert health["summary"]["total"] == 4

    def test_get_metrics_history_empty(self):
        monitor = LocalMonitor()
        history = monitor.get_metrics_history("cpu")
        assert isinstance(history, list)

    def test_singleton(self):
        assert get_local_monitor() is get_local_monitor()


class TestMonitorAPI:
    def test_health_endpoint(self, client):
        resp = client.get("/api/v1/monitor/health")
        assert resp.status_code == 200
        assert "services" in resp.json()
        assert "summary" in resp.json()

    def test_services_endpoint(self, client, test_user):
        resp = client.get("/api/v1/monitor/services", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_system_endpoint(self, client, test_user):
        resp = client.get("/api/v1/monitor/system", headers=test_user["headers"])
        assert resp.status_code == 200
