"""Tests for Agent Configuration — Post-MVP Phase 7."""

import pytest
from app.services.agent_config import (
    AgentConfig, AgentConfigManager, get_agent_config_manager,
    validate_config, DEFAULT_AGENT_CONFIGS, VALID_MODELS,
)


class TestDefaultConfigs:
    def test_all_agents_have_defaults(self):
        assert len(DEFAULT_AGENT_CONFIGS) >= 11
        for name, config in DEFAULT_AGENT_CONFIGS.items():
            assert "model" in config
            assert "temperature" in config
            assert "max_retries" in config
            assert "timeout_seconds" in config
            assert "enabled" in config

    def test_security_agent_low_temperature(self):
        assert DEFAULT_AGENT_CONFIGS["security_agent"]["temperature"] == 0.1

    def test_all_enabled_by_default(self):
        for config in DEFAULT_AGENT_CONFIGS.values():
            assert config["enabled"] is True


class TestConfigValidation:
    def test_valid_config(self):
        config = AgentConfig(agent_name="cto_agent", model="gpt-4o", temperature=0.3, max_retries=2, timeout_seconds=120)
        errors = validate_config(config)
        assert len(errors) == 0

    def test_unknown_agent(self):
        config = AgentConfig(agent_name="unknown_agent")
        errors = validate_config(config)
        assert any("Unknown agent" in e for e in errors)

    def test_invalid_model(self):
        config = AgentConfig(agent_name="cto_agent", model="gpt-99")
        errors = validate_config(config)
        assert any("Invalid model" in e for e in errors)

    def test_temperature_out_of_range(self):
        config = AgentConfig(agent_name="cto_agent", temperature=3.0)
        errors = validate_config(config)
        assert any("Temperature" in e for e in errors)

    def test_negative_retries(self):
        config = AgentConfig(agent_name="cto_agent", max_retries=-1)
        errors = validate_config(config)
        assert any("max_retries" in e for e in errors)

    def test_timeout_too_short(self):
        config = AgentConfig(agent_name="cto_agent", timeout_seconds=5)
        errors = validate_config(config)
        assert any("timeout_seconds" in e for e in errors)

    def test_timeout_too_long(self):
        config = AgentConfig(agent_name="cto_agent", timeout_seconds=700)
        errors = validate_config(config)
        assert any("timeout_seconds" in e for e in errors)


class TestConfigManager:
    def test_get_default_config(self):
        manager = AgentConfigManager()
        config = manager.get_default_config("cto_agent")
        assert config.agent_name == "cto_agent"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.3
        assert config.enabled is True

    def test_get_effective_config_no_overrides(self):
        manager = AgentConfigManager()
        config = manager.get_effective_config("cto_agent")
        assert config.model == "gpt-4o"
        assert config.temperature == 0.3

    def test_set_global_override(self):
        manager = AgentConfigManager()
        override = AgentConfig(agent_name="cto_agent", model="gpt-4o-mini", temperature=0.5, max_retries=3, timeout_seconds=60, system_prompt_prefix="Extra: ", enabled=True)
        manager.set_global_override("cto_agent", override)
        config = manager.get_effective_config("cto_agent")
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.5
        assert config.max_retries == 3

    def test_global_override_affects_all(self):
        manager = AgentConfigManager()
        manager.set_global_override("cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o-mini", temperature=0.1, max_retries=1, timeout_seconds=30, system_prompt_prefix="", enabled=False))
        # Should affect project lookup too
        config = manager.get_effective_config("cto_agent", project_id="proj-1")
        assert config.model == "gpt-4o-mini"
        assert config.enabled is False

    def test_project_override_takes_priority(self):
        manager = AgentConfigManager()
        # Set global override
        manager.set_global_override("cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o-mini", temperature=0.5, max_retries=3, timeout_seconds=60, system_prompt_prefix="", enabled=True))
        # Set project override (higher priority)
        manager.set_project_config("proj-1", "cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o", temperature=0.2, max_retries=1, timeout_seconds=120, system_prompt_prefix="Project: ", enabled=True))
        config = manager.get_effective_config("cto_agent", project_id="proj-1")
        assert config.model == "gpt-4o"  # project wins
        assert config.temperature == 0.2
        assert config.system_prompt_prefix == "Project: "

    def test_delete_project_config(self):
        manager = AgentConfigManager()
        manager.set_project_config("proj-1", "cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o-mini"))
        assert manager.delete_project_config("proj-1", "cto_agent") is True
        config = manager.get_effective_config("cto_agent", project_id="proj-1")
        assert config.model == "gpt-4o"  # reverted to default

    def test_delete_nonexistent_project_config(self):
        manager = AgentConfigManager()
        assert manager.delete_project_config("nonexistent", "cto_agent") is False

    def test_delete_global_override(self):
        manager = AgentConfigManager()
        manager.set_global_override("cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o-mini", temperature=0.5, max_retries=3, timeout_seconds=60, system_prompt_prefix="", enabled=True))
        assert manager.delete_global_override("cto_agent") is True
        config = manager.get_effective_config("cto_agent")
        assert config.model == "gpt-4o"  # reverted to default

    def test_delete_nonexistent_global_override(self):
        manager = AgentConfigManager()
        assert manager.delete_global_override("cto_agent") is False

    def test_invalid_config_raises(self):
        manager = AgentConfigManager()
        with pytest.raises(ValueError):
            manager.set_global_override("cto_agent", AgentConfig(agent_name="cto_agent", temperature=5.0, model="gpt-4o", max_retries=2, timeout_seconds=120, system_prompt_prefix="", enabled=True))

    def test_list_all_agents(self):
        manager = AgentConfigManager()
        agents = manager.list_all_agents()
        assert len(agents) >= 11

    def test_list_enabled_agents(self):
        manager = AgentConfigManager()
        enabled = manager.list_enabled_agents()
        assert len(enabled) >= 11

    def test_list_enabled_agents_with_project(self):
        manager = AgentConfigManager()
        manager.set_project_config("proj-1", "cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o", temperature=0.3, max_retries=2, timeout_seconds=120, system_prompt_prefix="", enabled=False))
        enabled = manager.list_enabled_agents(project_id="proj-1")
        assert "cto_agent" not in enabled

    def test_reset_project_configs(self):
        manager = AgentConfigManager()
        manager.set_project_config("proj-1", "cto_agent", AgentConfig(agent_name="cto_agent", model="gpt-4o-mini", temperature=0.3, max_retries=2, timeout_seconds=120, system_prompt_prefix="", enabled=True))
        assert manager.reset_project_configs("proj-1") is True
        config = manager.get_effective_config("cto_agent", project_id="proj-1")
        assert config.model == "gpt-4o"

    def test_reset_nonexistent_project(self):
        manager = AgentConfigManager()
        assert manager.reset_project_configs("nonexistent") is False


class TestAgentConfigAPI:
    def test_list_agents_api(self, client, test_user):
        resp = client.get("/api/v1/agent-config/agents", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 11

    def test_list_models_api(self, client, test_user):
        resp = client.get("/api/v1/agent-config/models", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "gpt-4o" in resp.json()

    def test_effective_config_api(self, client, test_user):
        resp = client.get("/api/v1/agent-config/effective/cto_agent", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["agent_name"] == "cto_agent"

    def test_effective_config_not_found(self, client, test_user):
        resp = client.get("/api/v1/agent-config/effective/unknown_agent", headers=test_user["headers"])
        assert resp.status_code == 404

    def test_set_project_config_api(self, client, test_user):
        resp = client.put("/api/v1/agent-config/project/proj-1/cto_agent", json={
            "agent_name": "cto_agent", "model": "gpt-4o", "temperature": 0.3,
            "max_retries": 2, "timeout_seconds": 120, "system_prompt_prefix": "", "enabled": True,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["agent_name"] == "cto_agent"

    def test_get_project_config_api(self, client, test_user):
        client.put("/api/v1/agent-config/project/proj-1/cto_agent", json={
            "agent_name": "cto_agent", "model": "gpt-4o-mini", "temperature": 0.5,
            "max_retries": 1, "timeout_seconds": 60, "system_prompt_prefix": "", "enabled": True,
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/agent-config/project/proj-1", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "cto_agent" in resp.json()["configs"]

    def test_delete_project_config_api(self, client, test_user):
        client.put("/api/v1/agent-config/project/proj-1/cto_agent", json={
            "agent_name": "cto_agent", "model": "gpt-4o", "temperature": 0.3,
            "max_retries": 2, "timeout_seconds": 120, "system_prompt_prefix": "", "enabled": True,
        }, headers=test_user["headers"])
        resp = client.delete("/api/v1/agent-config/project/proj-1/cto_agent", headers=test_user["headers"])
        assert resp.status_code == 204

    def test_set_global_override_api(self, client, test_user):
        resp = client.put("/api/v1/agent-config/global/cto_agent", json={
            "agent_name": "cto_agent", "model": "gpt-4o-mini", "temperature": 0.4,
            "max_retries": 2, "timeout_seconds": 120, "system_prompt_prefix": "", "enabled": True,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["model"] == "gpt-4o-mini"

    def test_invalid_config_api(self, client, test_user):
        resp = client.put("/api/v1/agent-config/global/cto_agent", json={
            "agent_name": "cto_agent", "model": "gpt-4o", "temperature": 5.0,
            "max_retries": 2, "timeout_seconds": 120, "system_prompt_prefix": "", "enabled": True,
        }, headers=test_user["headers"])
        assert resp.status_code == 422

    def test_list_enabled_agents_api(self, client, test_user):
        resp = client.get("/api/v1/agent-config/enabled/list", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
