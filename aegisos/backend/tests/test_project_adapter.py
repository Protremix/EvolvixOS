"""Tests for the Project Adapter Framework — MVP Feature #13."""

import pytest
from app.services.project_adapter import (
    list_adapters, get_adapter, register_adapter,
    validate_project_config, get_quality_gate_commands,
    get_adapter_summary, ProjectTypeConfig,
    BLOCKCHAIN_ADAPTER, WEB_BACKEND_ADAPTER, FRONTEND_ADAPTER,
    MOBILE_ADAPTER, INFRASTRUCTURE_ADAPTER, AI_ML_ADAPTER, GENERIC_ADAPTER,
)


class TestAdapterRegistry:
    """Test the adapter registry."""

    def test_list_adapters_returns_all(self):
        adapters = list_adapters()
        assert len(adapters) >= 7

    def test_list_adapters_types(self):
        adapters = list_adapters()
        type_ids = [a.type_id for a in adapters]
        assert "blockchain" in type_ids
        assert "web_backend" in type_ids
        assert "frontend" in type_ids
        assert "mobile" in type_ids
        assert "infrastructure" in type_ids
        assert "ai_ml" in type_ids
        assert "generic" in type_ids

    def test_get_adapter_blockchain(self):
        adapter = get_adapter("blockchain")
        assert adapter.type_id == "blockchain"
        assert adapter.display_name == "Blockchain / Web3"
        assert "rust" in adapter.supported_languages
        assert "solidity" in adapter.supported_languages
        assert "cargo_test" in adapter.quality_gates
        assert "consensus_audit" in adapter.security_checks

    def test_get_adapter_web_backend(self):
        adapter = get_adapter("web_backend")
        assert adapter.type_id == "web_backend"
        assert "python" in adapter.supported_languages
        assert "api_design" in adapter.task_types

    def test_get_adapter_frontend(self):
        adapter = get_adapter("frontend")
        assert adapter.type_id == "frontend"
        assert "typescript" in adapter.supported_languages
        assert "accessibility_check" in adapter.task_types

    def test_get_adapter_mobile(self):
        adapter = get_adapter("mobile")
        assert adapter.type_id == "mobile"
        assert "dart" in adapter.supported_languages
        assert "flutter" in adapter.quality_gates[0] or "analyze" in adapter.quality_gates

    def test_get_adapter_infrastructure(self):
        adapter = get_adapter("infrastructure")
        assert adapter.type_id == "infrastructure"
        assert "yaml" in adapter.supported_languages
        assert "config_audit" in adapter.task_types

    def test_get_adapter_ai_ml(self):
        adapter = get_adapter("ai_ml")
        assert adapter.type_id == "ai_ml"
        assert "model_audit" in adapter.task_types
        assert "drift_score" in adapter.monitoring_metrics

    def test_get_adapter_generic_fallback(self):
        adapter = get_adapter("nonexistent_type")
        assert adapter.type_id == "generic"

    def test_get_adapter_generic(self):
        adapter = get_adapter("generic")
        assert adapter.type_id == "generic"
        assert adapter.display_name == "Generic Project"

    def test_register_custom_adapter(self):
        custom = ProjectTypeConfig(
            type_id="custom_game",
            display_name="Game Development",
            description="Unity, Unreal, Godot game projects",
            default_language="csharp",
            supported_languages=["csharp", "cpp", "python"],
            task_types=["code_review", "performance_audit"],
            quality_gates=["build", "test"],
        )
        register_adapter(custom)
        adapter = get_adapter("custom_game")
        assert adapter.type_id == "custom_game"
        assert adapter.display_name == "Game Development"
        assert "csharp" in adapter.supported_languages


class TestAdapterConfig:
    """Test ProjectTypeConfig properties."""

    def test_blockchain_file_structure(self):
        assert "runtime/" in BLOCKCHAIN_ADAPTER.file_structure
        assert "pallets/" in BLOCKCHAIN_ADAPTER.file_structure
        assert "node/" in BLOCKCHAIN_ADAPTER.file_structure

    def test_blockchain_agent_overrides(self):
        assert "cto_agent" in BLOCKCHAIN_ADAPTER.agent_overrides
        assert BLOCKCHAIN_ADAPTER.agent_overrides["cto_agent"] == "blockchain_architecture"

    def test_web_backend_ci_template(self):
        assert "stages" in WEB_BACKEND_ADAPTER.ci_template
        assert "test" in WEB_BACKEND_ADAPTER.ci_template["stages"]

    def test_mobile_monitoring(self):
        assert "app_size" in MOBILE_ADAPTER.monitoring_metrics
        assert "crash_rate" in MOBILE_ADAPTER.monitoring_metrics

    def test_all_adapters_have_required_fields(self):
        for adapter in list_adapters():
            assert adapter.type_id
            assert adapter.display_name
            assert adapter.default_language
            assert len(adapter.supported_languages) > 0
            assert len(adapter.task_types) > 0
            assert len(adapter.quality_gates) > 0
            assert len(adapter.security_checks) > 0


class TestValidation:
    """Test project config validation."""

    def test_valid_language_no_warnings(self):
        warnings = validate_project_config("web_backend", {"language": "python"})
        assert len(warnings) == 0

    def test_invalid_language_warning(self):
        warnings = validate_project_config("frontend", {"language": "rust"})
        assert len(warnings) == 1
        assert "rust" in warnings[0]

    def test_valid_task_type_no_warnings(self):
        warnings = validate_project_config("blockchain", {"task_type": "code_review"})
        assert len(warnings) == 0

    def test_invalid_task_type_warning(self):
        warnings = validate_project_config("blockchain", {"task_type": "ui_audit"})
        assert len(warnings) == 1
        assert "ui_audit" in warnings[0]

    def test_generic_accepts_anything(self):
        warnings = validate_project_config("generic", {"language": "python"})
        assert len(warnings) == 0

    def test_unknown_type_uses_generic(self):
        warnings = validate_project_config("unknown_type", {"language": "python"})
        assert len(warnings) == 0


class TestQualityGates:
    """Test quality gate command generation."""

    def test_blockchain_quality_gates(self):
        commands = get_quality_gate_commands("blockchain")
        assert "cargo_test" in commands
        assert "cargo build --release" in commands["cargo_build"]
        assert "cargo test --release --workspace" in commands["cargo_test"]
        assert "cargo clippy -- -D warnings" in commands["cargo_clippy"]

    def test_web_backend_quality_gates(self):
        commands = get_quality_gate_commands("web_backend")
        assert "lint" in commands
        assert "test" in commands
        assert "build" in commands

    def test_frontend_quality_gates(self):
        commands = get_quality_gate_commands("frontend")
        assert "type_check" in commands
        assert commands["type_check"] == "tsc --noEmit"

    def test_generic_quality_gates(self):
        commands = get_quality_gate_commands("generic")
        assert "lint" in commands
        assert "test" in commands
        assert "build" in commands

    def test_unknown_type_quality_gates(self):
        commands = get_quality_gate_commands("nonexistent")
        assert len(commands) > 0

    def test_all_adapters_have_quality_gate_commands(self):
        for adapter in list_adapters():
            commands = get_quality_gate_commands(adapter.type_id)
            assert len(commands) == len(adapter.quality_gates)


class TestAdapterSummary:
    """Test the adapter summary helper."""

    def test_summary_has_all_fields(self):
        summary = get_adapter_summary(BLOCKCHAIN_ADAPTER)
        assert summary["type_id"] == "blockchain"
        assert summary["display_name"] == "Blockchain / Web3"
        assert "supported_languages" in summary
        assert "task_types" in summary
        assert "quality_gates" in summary
        assert "security_checks" in summary
        assert "monitoring_metrics" in summary
        assert "file_structure" in summary

    def test_summary_languages(self):
        summary = get_adapter_summary(WEB_BACKEND_ADAPTER)
        assert "python" in summary["supported_languages"]


class TestAdapterAPI:
    """Test the API endpoints."""

    def test_list_adapters_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/project-adapters/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 7
        assert len(data["adapters"]) >= 7

    def test_get_adapter_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/project-adapters/blockchain", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["type_id"] == "blockchain"
        assert data["display_name"] == "Blockchain / Web3"

    def test_get_adapter_not_found_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/project-adapters/nonexistent", headers=headers)
        assert resp.status_code == 404

    def test_register_adapter_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/project-adapters/", json={
            "type_id": "test_iot",
            "display_name": "IoT Project",
            "description": "Internet of Things projects",
            "default_language": "c",
            "supported_languages": ["c", "python"],
            "task_types": ["code_review", "firmware_audit"],
            "quality_gates": ["build", "test"],
            "security_checks": ["firmware_scan"],
        }, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["type_id"] == "test_iot"

    def test_validate_config_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/project-adapters/validate", json={
            "project_type": "frontend",
            "config": {"language": "rust"},
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert len(data["warnings"]) > 0

    def test_validate_config_valid_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/project-adapters/validate", json={
            "project_type": "web_backend",
            "config": {"language": "python"},
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert len(data["warnings"]) == 0

    def test_quality_gates_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/project-adapters/blockchain/quality-gates", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "cargo_test" in data["commands"]
        assert "cargo_build" in data["commands"]

    def test_list_adapters_unauthorized(self, client):
        resp = client.get("/api/v1/project-adapters/")
        assert resp.status_code == 401

    def test_register_adapter_unauthorized(self, client):
        resp = client.post("/api/v1/project-adapters/", json={
            "type_id": "test",
            "display_name": "Test",
        })
        assert resp.status_code == 401
