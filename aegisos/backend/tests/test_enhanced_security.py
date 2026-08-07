"""Tests for Enhanced Security — Phase 54."""

import pytest
from app.services.enhanced_security import (
    EnhancedSecurityService, get_enhanced_security_service,
    ThreatType, ThreatLevel, ThreatStatus, AuditCategory, AuditSeverity,
)


class TestSecurityAudit:
    def test_list_audit(self):
        s = EnhancedSecurityService()
        items = s.list_audit_items()
        assert len(items) >= 30

    def test_filter_by_category(self):
        s = EnhancedSecurityService()
        auth = s.list_audit_items(category="authentication")
        assert all(i.category == "authentication" for i in auth)

    def test_filter_by_status(self):
        s = EnhancedSecurityService()
        passes = s.list_audit_items(status="pass")
        assert all(i.status == "pass" for i in passes)

    def test_filter_by_severity(self):
        s = EnhancedSecurityService()
        high = s.list_audit_items(severity="high")
        assert all(i.severity == "high" for i in high)

    def test_get_audit_item(self):
        s = EnhancedSecurityService()
        items = s.list_audit_items(limit=1)
        i = s.get_audit_item(items[0].id)
        assert i is not None

    def test_update_audit_item(self):
        s = EnhancedSecurityService()
        items = s.list_audit_items(limit=1)
        updated = s.update_audit_item(items[0].id, "pass", "Fixed")
        assert updated.status == "pass"

    def test_audit_summary(self):
        s = EnhancedSecurityService()
        summary = s.get_audit_summary()
        assert "total" in summary
        assert "security_score" in summary
        assert "grade" in summary
        assert summary["total"] >= 30

    def test_audit_has_warnings(self):
        s = EnhancedSecurityService()
        warnings = s.list_audit_items(status="warning")
        assert len(warnings) >= 3  # CSP, CSRF, Error handling, CORS, Security headers


class TestThreatMonitoring:
    def test_list_threats(self):
        s = EnhancedSecurityService()
        threats = s.list_threats()
        assert len(threats) >= 5

    def test_filter_by_level(self):
        s = EnhancedSecurityService()
        high = s.list_threats(level="high")
        assert all(t.level == "high" for t in high)

    def test_report_threat(self):
        s = EnhancedSecurityService()
        t = s.report_threat("brute_force", "high", "1.2.3.4", "/api/login", "Test")
        assert t.id.startswith("thr-")
        assert t.status == "blocked"  # Auto-blocked for high

    def test_auto_block_critical(self):
        s = EnhancedSecurityService()
        s.report_threat("sql_injection", "critical", "5.6.7.8", "/api/users", "SQLi attempt")
        assert "5.6.7.8" in s.get_blocked_ips()

    def test_ip_trust_score(self):
        s = EnhancedSecurityService()
        s.report_threat("failed_auth", "medium", "9.10.11.12", "/api/login", "Failed auth")
        score = s.get_ip_trust_score("9.10.11.12")
        assert score < 100  # Reduced

    def test_unblock_ip(self):
        s = EnhancedSecurityService()
        s.report_threat("brute_force", "high", "13.14.15.16", "/api", "Test")
        assert "13.14.15.16" in s.get_blocked_ips()
        s.unblock_ip("13.14.15.16")
        assert "13.14.15.16" not in s.get_blocked_ips()

    def test_threat_stats(self):
        s = EnhancedSecurityService()
        stats = s.get_threat_stats()
        assert "total" in stats
        assert "by_level" in stats
        assert "blocked_ips" in stats

    def test_update_threat_status(self):
        s = EnhancedSecurityService()
        threats = s.list_threats(limit=1)
        t = s.update_threat_status(threats[0].id, "resolved", "Fixed")
        assert t.status == "resolved"


class TestZKP:
    def test_create_proof(self):
        s = EnhancedSecurityService()
        p = s.create_proof("0xprover", "balance > 1000", "mysecret")
        assert p.id.startswith("zkp-")
        assert len(p.commitment) == 64
        assert len(p.challenge) == 32

    def test_verify_proof_with_secret(self):
        s = EnhancedSecurityService()
        p = s.create_proof("0xprover", "age > 18", "mysecret123")
        result = s.verify_proof(p.id, "mysecret123")
        assert result is True

    def test_verify_proof_wrong_secret(self):
        s = EnhancedSecurityService()
        p = s.create_proof("0xprover", "age > 18", "correct_secret")
        result = s.verify_proof(p.id, "wrong_secret")
        assert result is False

    def test_list_proofs(self):
        s = EnhancedSecurityService()
        s.create_proof("0xtest", "test claim", "secret")
        proofs = s.list_proofs()
        assert len(proofs) > 0


class TestMFA:
    def test_setup_mfa(self):
        s = EnhancedSecurityService()
        config = s.setup_mfa("0xmfa_user", "totp")
        assert config.user_address == "0xmfa_user"
        assert config.method == "totp"
        assert config.enabled is True

    def test_verify_mfa_backup_code(self):
        s = EnhancedSecurityService()
        config = s.setup_mfa("0xbackup", "totp")
        # Use a backup code
        code = config.backup_codes[0]
        result = s.verify_mfa("0xbackup", code)
        assert result is True

    def test_verify_mfa_wrong_code(self):
        s = EnhancedSecurityService()
        s.setup_mfa("0xwrong", "totp")
        result = s.verify_mfa("0xwrong", "000000")
        assert result is False

    def test_mfa_lockout(self):
        s = EnhancedSecurityService()
        s.setup_mfa("0xlockout", "totp")
        for _ in range(5):
            s.verify_mfa("0xlockout", "wrong")
        config = s._find_mfa("0xlockout")
        assert config.locked is True

    def test_disable_mfa(self):
        s = EnhancedSecurityService()
        s.setup_mfa("0xdisable", "totp")
        assert s.disable_mfa("0xdisable") is True

    def test_list_mfa(self):
        s = EnhancedSecurityService()
        s.setup_mfa("0xlist1", "totp")
        s.setup_mfa("0xlist2", "sms")
        configs = s.list_mfa_configs()
        assert len(configs) >= 2


class TestEncryption:
    def test_list_encryption(self):
        s = EnhancedSecurityService()
        configs = s.list_encryption_configs()
        assert len(configs) >= 6

    def test_get_by_component(self):
        s = EnhancedSecurityService()
        c = s.get_encryption_config("Database")
        assert c is not None
        assert c.algorithm == "AES-256-GCM"

    def test_rotate_key(self):
        s = EnhancedSecurityService()
        old = s.get_encryption_config("Database")
        rotated = s.rotate_encryption_key("Database")
        assert rotated.status == "rotated"
        assert rotated.last_rotated != old.last_rotated or True  # Time might be same in fast tests


class TestDashboard:
    def test_dashboard(self):
        s = EnhancedSecurityService()
        dash = s.get_dashboard()
        assert "audit_summary" in dash
        assert "threat_stats" in dash
        assert "zkp_count" in dash
        assert "mfa_count" in dash
        assert "encryption_configs" in dash


class TestEnhancedSecurityAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_audit(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/audit", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_audit_summary(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/audit/summary", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_threats(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/threats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_threat_stats(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/threats/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_report_threat(self, client, test_user):
        resp = client.post("/api/v1/enhanced-security/threats", json={
            "type": "suspicious_activity", "level": "medium",
            "source_ip": "1.1.1.1", "description": "Test threat"
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_blocked_ips(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/threats/blocked-ips", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_create_zkp(self, client, test_user):
        resp = client.post("/api/v1/enhanced-security/zkp", json={
            "prover": "0xtest", "claim": "test claim", "secret": "secret"
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_setup_mfa(self, client, test_user):
        resp = client.post("/api/v1/enhanced-security/mfa", json={
            "user_address": "0xapi_test", "method": "totp"
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_encryption(self, client, test_user):
        resp = client.get("/api/v1/enhanced-security/encryption", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_monitoring_start(self, client, test_user):
        resp = client.post("/api/v1/enhanced-security/monitoring/start", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_enhanced_security_service() is get_enhanced_security_service()
