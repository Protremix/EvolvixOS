"""Tests for Verdis Project Manager — Phase 16."""

import pytest
from app.services.verdis_manager import (
    VerdisProjectManager, VerdisHealthSnapshot, VerdisAlert,
    VerdisEcosystemComponent, VERDIS_PIPELINE_TEMPLATE, VERDIS_AGENT_CONTEXT,
    VERDIS_COMPONENTS, get_verdis_manager,
)


class TestVerdisProjectManager:
    def test_register_project(self):
        mgr = VerdisProjectManager()
        result = mgr.register_project()
        assert result["status"] == "registered"
        assert result["project"]["name"] == "Verdis Blockchain"
        assert result["project"]["type"] == "blockchain"
        assert "components" in result["project"]

    def test_register_already_registered(self):
        mgr = VerdisProjectManager()
        mgr.register_project()
        result = mgr.register_project()
        assert result["status"] == "already_registered"

    def test_get_agent_context(self):
        mgr = VerdisProjectManager()
        ctx = mgr.get_agent_context()
        assert "Verdis" in ctx
        assert "DPoS" in ctx
        assert "BABE/GRANDPA" in ctx
        assert "carbon-negative" in ctx
        assert "100B" in ctx

    def test_get_pipeline_template(self):
        assert VERDIS_PIPELINE_TEMPLATE["name"] == "Verdis Blockchain Audit"
        assert VERDIS_PIPELINE_TEMPLATE["default_project_type"] == "blockchain"
        assert "security" in VERDIS_PIPELINE_TEMPLATE["stage_overrides"]
        assert len(VERDIS_PIPELINE_TEMPLATE["default_constraints"]) >= 5
        assert len(VERDIS_PIPELINE_TEMPLATE["default_acceptance_criteria"]) >= 5

    def test_agent_context_contains_key_info(self):
        ctx = VERDIS_AGENT_CONTEXT
        assert "14 validators" in ctx
        assert "Spec v11" in ctx
        assert "133 tests" in ctx
        assert "13 pallets" in ctx
        assert "AmmDex" in ctx
        assert "CarbonCredits" in ctx
        assert "GreenValidator" in ctx
        assert "Reforestation" in ctx
        assert "100B total" in ctx
        assert "verdischain.com" in ctx

    def test_ecosystem_components(self):
        assert len(VERDIS_COMPONENTS) == 7
        types = [c.type for c in VERDIS_COMPONENTS]
        assert "blockchain" in types
        assert "sdk" in types
        assert "cli" in types
        assert "bridge" in types
        assert "explorer" in types
        assert "wallet" in types
        assert "docs" in types

    def test_get_components(self):
        mgr = VerdisProjectManager()
        components = mgr.get_components()
        assert len(components) == 7
        for c in components:
            assert c.name is not None
            assert c.type is not None

    def test_update_component_status(self):
        mgr = VerdisProjectManager()
        mgr.update_component_status("Verdis Chain (Core)", "healthy", "All systems go")
        components = mgr.get_components()
        core = [c for c in components if c.name == "Verdis Chain (Core)"][0]
        assert core.status == "healthy"
        assert "All systems go" in core.notes

    def test_get_project_overview(self):
        mgr = VerdisProjectManager()
        mgr.register_project()
        overview = mgr.get_project_overview()
        assert overview["project_name"] == "Verdis Blockchain"
        assert overview["project_type"] == "blockchain"
        assert overview["domain"] == "verdischain.com"
        assert overview["registered"] is True
        assert "components" in overview
        assert "pipeline_template" in overview

    def test_get_stats(self):
        mgr = VerdisProjectManager()
        stats = mgr.get_stats()
        assert "registered" in stats
        assert "monitoring_enabled" in stats
        assert "total_snapshots" in stats
        assert "total_alerts" in stats
        assert "active_alerts" in stats
        assert "components_tracked" in stats

    def test_enable_disable_monitoring(self):
        mgr = VerdisProjectManager()
        mgr.disable_monitoring()
        assert mgr._monitoring_enabled is False
        mgr.enable_monitoring()
        assert mgr._monitoring_enabled is True

    def test_health_snapshot_to_dict(self):
        snap = VerdisHealthSnapshot(
            connected=True, block_height="1000", peers=14,
            validator_count=14, spec_version=11,
        )
        d = snap.to_dict()
        assert d["connected"] is True
        assert d["block_height"] == "1000"
        assert d["peers"] == 14
        assert d["validator_count"] == 14

    def test_alert_to_dict(self):
        alert = VerdisAlert(severity="critical", category="connectivity", message="Down")
        d = alert.to_dict()
        assert d["severity"] == "critical"
        assert d["category"] == "connectivity"
        assert d["resolved"] is False

    def test_component_to_dict(self):
        comp = VerdisEcosystemComponent(name="Test", type="blockchain", status="healthy")
        d = comp.to_dict()
        assert d["name"] == "Test"
        assert d["type"] == "blockchain"
        assert d["status"] == "healthy"

    def test_create_alert_deduplication(self):
        mgr = VerdisProjectManager()
        mgr._create_alert("critical", "connectivity", "Test alert")
        mgr._create_alert("critical", "connectivity", "Test alert")  # Duplicate
        alerts = mgr.get_alerts(resolved=False)
        assert len(alerts) == 1

    def test_resolve_alert(self):
        mgr = VerdisProjectManager()
        mgr._create_alert("warning", "validators", "Low count")
        alerts = mgr.get_alerts(resolved=False)
        assert len(alerts) == 1
        assert mgr.resolve_alert(alerts[0].id) is True
        resolved = mgr.get_alerts(resolved=False)
        assert len(resolved) == 0
        resolved_alerts = mgr.get_alerts(resolved=True)
        assert len(resolved_alerts) == 1

    def test_resolve_nonexistent_alert(self):
        mgr = VerdisProjectManager()
        assert mgr.resolve_alert("nonexistent") is False

    def test_get_snapshots_empty(self):
        mgr = VerdisProjectManager()
        snapshots = mgr.get_snapshots()
        assert len(snapshots) == 0

    def test_get_latest_snapshot_empty(self):
        mgr = VerdisProjectManager()
        assert mgr.get_latest_snapshot() is None

    def test_health_summary(self):
        mgr = VerdisProjectManager()
        summary = mgr.get_health_summary()
        assert isinstance(summary, str)
        assert "Verdis" in summary


class TestVerdisProjectAPI:
    def test_register_api(self, client, test_user):
        resp = client.post("/api/v1/verdis-project/register", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] in ("registered", "already_registered")

    def test_overview_api(self, client, test_user):
        client.post("/api/v1/verdis-project/register", headers=test_user["headers"])
        resp = client.get("/api/v1/verdis-project/overview", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["project_name"] == "Verdis Blockchain"

    def test_components_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/components", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 7

    def test_update_component_api(self, client, test_user):
        resp = client.put("/api/v1/verdis-project/components", json={
            "name": "Verdis Chain (Core)", "status": "healthy", "notes": "OK",
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_agent_context_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/agent-context", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "Verdis" in resp.json()["context"]

    def test_pipeline_template_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/pipeline-template", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "Verdis Blockchain Audit"

    def test_stats_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "components_tracked" in resp.json()

    def test_alerts_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/alerts", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_monitoring_toggle_api(self, client, test_user):
        resp = client.post("/api/v1/verdis-project/monitoring/false", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["monitoring_enabled"] is False

    def test_health_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/health", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_health_history_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/health/history", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_health_summary_api(self, client, test_user):
        resp = client.get("/api/v1/verdis-project/health-summary", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "Verdis" in resp.json()["summary"]
