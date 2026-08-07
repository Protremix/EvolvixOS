"""Tests for Audit & Compliance — Phase 44."""

import pytest
import time
from app.services.audit_compliance import (
    AuditComplianceService, get_audit_compliance_service, AuditCategory, AuditSeverity,
    ComplianceStatus, RiskLevel, ComplianceFramework,
)


class TestAuditTrail:
    def test_record_audit(self):
        service = AuditComplianceService()
        entry = service.record_audit("authentication", "login", "0xuser", "/api/v1/auth")
        assert entry.id.startswith("aud-")
        assert entry.action == "login"

    def test_get_audit(self):
        service = AuditComplianceService()
        entry = service.record_audit("security", "alert", "system", "/system")
        found = service.get_audit(entry.id)
        assert found is not None

    def test_list_audit(self):
        service = AuditComplianceService()
        entries = service.list_audit(limit=10)
        assert len(entries) > 0

    def test_filter_by_category(self):
        service = AuditComplianceService()
        entries = service.list_audit(category="security")
        assert all(e.category == "security" for e in entries)

    def test_filter_by_severity(self):
        service = AuditComplianceService()
        entries = service.list_audit(severity="critical")
        assert all(e.severity == "critical" for e in entries)

    def test_filter_by_actor(self):
        service = AuditComplianceService()
        service.record_audit("system", "test", "0xtestactor", "/test")
        entries = service.list_audit(actor="0xtestactor")
        assert all(e.actor == "0xtestactor" for e in entries)

    def test_filter_by_result(self):
        service = AuditComplianceService()
        entries = service.list_audit(result="failure")
        assert all(e.result == "failure" for e in entries)

    def test_audit_stats(self):
        service = AuditComplianceService()
        stats = service.get_audit_stats(720)  # Include all sample data
        assert "total_entries" in stats
        assert "by_category" in stats
        assert "by_severity" in stats


class TestComplianceChecks:
    def test_list_checks(self):
        service = AuditComplianceService()
        checks = service.list_compliance_checks()
        assert len(checks) >= 20

    def test_list_by_framework(self):
        service = AuditComplianceService()
        gdpr = service.list_compliance_checks(framework="gdpr")
        assert all(c.framework == "gdpr" for c in gdpr)

    def test_get_check(self):
        service = AuditComplianceService()
        checks = service.list_compliance_checks()
        found = service.get_compliance_check(checks[0].id)
        assert found is not None

    def test_run_check(self):
        service = AuditComplianceService()
        checks = service.list_compliance_checks()
        original_count = checks[0].check_count
        result = service.run_compliance_check(checks[0].id)
        assert result is not None
        assert result.check_count > original_count

    def test_run_all_checks(self):
        service = AuditComplianceService()
        result = service.run_all_checks("gdpr")
        assert result["total"] > 0

    def test_update_check(self):
        service = AuditComplianceService()
        checks = service.list_compliance_checks()
        updated = service.update_compliance_check(checks[0].id, status="compliant")
        assert updated.status == "compliant"


class TestReports:
    def test_generate_report(self):
        service = AuditComplianceService()
        report = service.generate_report("gdpr", "Q3 2026 GDPR Report", 30)
        assert report.id.startswith("rpt-")
        assert report.total_controls > 0
        assert report.compliance_score >= 0

    def test_list_reports(self):
        service = AuditComplianceService()
        service.generate_report("gdpr", "Report 1")
        reports = service.list_reports()
        assert len(reports) >= 1

    def test_get_report(self):
        service = AuditComplianceService()
        report = service.generate_report("soc2", "SOC2 Report")
        found = service.get_report(report.id)
        assert found is not None


class TestPolicies:
    def test_list_policies(self):
        service = AuditComplianceService()
        policies = service.list_policies()
        assert len(policies) >= 8

    def test_create_policy(self):
        service = AuditComplianceService()
        p = service.create_policy("Test Policy", "Test", "gdpr", "test_rule")
        assert p.id.startswith("pol-")

    def test_update_policy(self):
        service = AuditComplianceService()
        p = service.create_policy("Test", "Desc", "soc2", "test")
        updated = service.update_policy(p.id, name="Updated")
        assert updated.name == "Updated"

    def test_delete_policy(self):
        service = AuditComplianceService()
        p = service.create_policy("Test", "Desc", "gdpr", "test")
        assert service.delete_policy(p.id) is True

    def test_record_violation(self):
        service = AuditComplianceService()
        p = service.create_policy("Test", "Desc", "gdpr", "test")
        service.record_policy_violation(p.id)
        updated = service.get_policy(p.id)
        assert updated.violations == 1


class TestRisks:
    def test_create_risk(self):
        service = AuditComplianceService()
        r = service.create_risk("Test Risk", "Desc", 0.8, 0.9)
        assert r.id.startswith("rsk-")
        assert r.risk_level in ["high", "critical"]

    def test_list_risks(self):
        service = AuditComplianceService()
        service.create_risk("Risk 1", "Desc")
        service.create_risk("Risk 2", "Desc")
        risks = service.list_risks()
        assert len(risks) >= 2

    def test_list_risks_by_level(self):
        service = AuditComplianceService()
        service.create_risk("Critical Risk", "Desc", 0.9, 0.9)
        critical = service.list_risks(risk_level="critical")
        assert all(r.risk_level == "critical" for r in critical)

    def test_update_risk(self):
        service = AuditComplianceService()
        r = service.create_risk("Risk", "Desc", 0.3, 0.3)
        updated = service.update_risk(r.id, probability=0.9, impact=0.9)
        assert updated.risk_level == "critical"

    def test_delete_risk(self):
        service = AuditComplianceService()
        r = service.create_risk("Risk", "Desc")
        assert service.delete_risk(r.id) is True


class TestDashboard:
    def test_dashboard(self):
        service = AuditComplianceService()
        dash = service.get_dashboard()
        assert "audit_stats_24h" in dash
        assert "frameworks" in dash
        assert "total_checks" in dash
        assert "total_policies" in dash
        assert "total_risks" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = AuditComplianceService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestAuditAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/audit/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_audit(self, client, test_user):
        resp = client.get("/api/v1/audit/audit", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_record_audit(self, client, test_user):
        resp = client.post("/api/v1/audit/audit", json={
            "category": "security", "action": "test", "actor": "0xtest",
            "resource": "/test",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("aud-")

    def test_list_checks(self, client, test_user):
        resp = client.get("/api/v1/audit/checks", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 20

    def test_list_policies(self, client, test_user):
        resp = client.get("/api/v1/audit/policies", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_generate_report(self, client, test_user):
        resp = client.post("/api/v1/audit/reports", json={
            "framework": "gdpr", "title": "Test Report",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("rpt-")

    def test_create_risk(self, client, test_user):
        resp = client.post("/api/v1/audit/risks", json={
            "title": "Test Risk", "description": "Test", "probability": 0.8, "impact": 0.9,
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_frameworks(self, client, test_user):
        resp = client.get("/api/v1/audit/frameworks", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_audit_compliance_service() is get_audit_compliance_service()
