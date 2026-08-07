"""Tests for Production Readiness — Phase 49."""

import pytest
import time
from app.services.production_readiness import (
    ProductionReadinessService, get_production_readiness_service, Severity, CheckStatus, ReadinessLevel,
)


class TestSecurityScan:
    def test_run_scan(self):
        service = ProductionReadinessService()
        result = service.run_security_scan()
        assert "total_findings" in result
        assert result["total_findings"] > 0
        assert "security_score" in result

    def test_list_findings(self):
        service = ProductionReadinessService()
        findings = service.list_findings()
        assert len(findings) > 0

    def test_filter_by_severity(self):
        service = ProductionReadinessService()
        medium = service.list_findings(severity="medium")
        assert all(f.severity == "medium" for f in medium)

    def test_filter_by_category(self):
        service = ProductionReadinessService()
        security = service.list_findings(category="security")
        assert all(f.category == "security" for f in security)

    def test_get_finding(self):
        service = ProductionReadinessService()
        findings = service.list_findings(limit=1)
        found = service.get_finding(findings[0].id)
        assert found is not None

    def test_fix_finding(self):
        service = ProductionReadinessService()
        findings = service.list_findings(limit=1)
        fixed = service.fix_finding(findings[0].id, "Applied fix")
        assert fixed.status == "fixed"

    def test_accept_finding(self):
        service = ProductionReadinessService()
        findings = service.list_findings(limit=1)
        accepted = service.accept_finding(findings[0].id)
        assert accepted.status == "accepted"

    def test_add_finding(self):
        service = ProductionReadinessService()
        f = service.add_finding("security", "high", "Test Finding", "Test desc")
        assert f.id.startswith("fnd-")
        assert f.title == "Test Finding"


class TestReadinessChecks:
    def test_list_checks(self):
        service = ProductionReadinessService()
        checks = service.list_checks()
        assert len(checks) > 0

    def test_filter_by_category(self):
        service = ProductionReadinessService()
        security = service.list_checks(category="security")
        assert all(c.category == "security" for c in security)

    def test_get_check(self):
        service = ProductionReadinessService()
        checks = service.list_checks(limit=1)
        found = service.get_check(checks[0].id)
        assert found is not None

    def test_update_check(self):
        service = ProductionReadinessService()
        checks = service.list_checks(limit=1)
        updated = service.update_check(checks[0].id, "pass", "All good")
        assert updated.status == "pass"

    def test_run_auto_checks(self):
        service = ProductionReadinessService()
        result = service.run_auto_checks()
        assert "total_auto" in result
        assert result["total_auto"] > 0

    def test_readiness_score(self):
        service = ProductionReadinessService()
        service.run_auto_checks()
        score = service.get_readiness_score()
        assert "overall_score" in score
        assert "readiness_level" in score
        assert "category_scores" in score


class TestLoadTesting:
    def test_run_load_test(self):
        service = ProductionReadinessService()
        result = service.run_load_test("/api/v1/dashboard", "GET", 10, 5)
        assert result.id.startswith("lt-")
        assert result.total_requests > 0
        assert result.rps > 0

    def test_list_load_tests(self):
        service = ProductionReadinessService()
        service.run_load_test("/api/v1/test", "GET", 5, 3)
        tests = service.list_load_tests()
        assert len(tests) > 0

    def test_get_load_test(self):
        service = ProductionReadinessService()
        result = service.run_load_test("/api/v1/test2", "GET", 5, 3)
        found = service.get_load_test(result.id)
        assert found is not None

    def test_filter_by_endpoint(self):
        service = ProductionReadinessService()
        service.run_load_test("/api/v1/filter", "GET", 5, 3)
        tests = service.list_load_tests(endpoint="/api/v1/filter")
        assert all(t.endpoint == "/api/v1/filter" for t in tests)

    def test_performance_summary(self):
        service = ProductionReadinessService()
        service.run_load_test("/api/v1/perf", "GET", 10, 5)
        summary = service.get_performance_summary()
        assert "total_tests" in summary


class TestDeploymentChecklist:
    def test_list_checklist(self):
        service = ProductionReadinessService()
        items = service.list_checklist()
        assert len(items) > 0

    def test_complete_item(self):
        service = ProductionReadinessService()
        items = service.list_checklist(limit=1)
        completed = service.complete_checklist_item(items[0].id, "Done")
        assert completed.completed is True

    def test_reset_item(self):
        service = ProductionReadinessService()
        items = service.list_checklist(limit=1)
        service.complete_checklist_item(items[0].id)
        reset = service.reset_checklist_item(items[0].id)
        assert reset.completed is False

    def test_progress(self):
        service = ProductionReadinessService()
        progress = service.get_checklist_progress()
        assert "total" in progress
        assert "percentage" in progress
        assert "ready_to_deploy" in progress

    def test_filter_completed(self):
        service = ProductionReadinessService()
        items = service.list_checklist(limit=3)
        for item in items:
            service.complete_checklist_item(item.id)
        completed = service.list_checklist(completed=True)
        assert all(i.completed for i in completed)


class TestDashboard:
    def test_dashboard(self):
        service = ProductionReadinessService()
        service.run_auto_checks()
        dash = service.get_dashboard()
        assert "security_scan" in dash
        assert "readiness_score" in dash
        assert "checklist" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = ProductionReadinessService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestReadinessAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/readiness/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_security_scan(self, client, test_user):
        resp = client.get("/api/v1/readiness/security/scan", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_findings"] > 0

    def test_list_findings(self, client, test_user):
        resp = client.get("/api/v1/readiness/findings", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_list_checks(self, client, test_user):
        resp = client.get("/api/v1/readiness/checks", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_run_auto_checks(self, client, test_user):
        resp = client.post("/api/v1/readiness/checks/run-auto", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_readiness_score(self, client, test_user):
        resp = client.get("/api/v1/readiness/score", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_run_load_test(self, client, test_user):
        resp = client.post("/api/v1/readiness/load-test", json={
            "endpoint": "/api/v1/dashboard", "concurrent_users": 5, "duration_seconds": 3,
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_checklist(self, client, test_user):
        resp = client.get("/api/v1/readiness/checklist", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_checklist_progress(self, client, test_user):
        resp = client.get("/api/v1/readiness/checklist/progress", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_production_readiness_service() is get_production_readiness_service()
