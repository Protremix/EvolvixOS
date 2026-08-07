"""Tests for Agent Simulation + Verdis Enhancement — Phase 17."""

import pytest
from app.services.agent_simulation import (
    AgentSimulationService, SimulationScenario, BUILTIN_SCENARIOS,
    get_simulation_service,
)
from app.services.verdis_agent_enhancer import (
    VerdisAgentEnhancer, VerdisAgentContext, AgentActivity,
    VERDIS_TASK_TYPES, get_verdis_enhancer,
)


class TestSimulationScenarios:
    def test_builtin_scenarios_exist(self):
        assert len(BUILTIN_SCENARIOS) == 8
        names = [s.name for s in BUILTIN_SCENARIOS]
        assert "Verdis Runtime Upgrade Review" in names
        assert "Bridge Security Audit" in names
        assert "AMM DEX Performance Analysis" in names
        assert "CI Failure Diagnosis" in names

    def test_scenario_to_dict(self):
        s = BUILTIN_SCENARIOS[0]
        d = s.to_dict()
        assert d["name"] == s.name
        assert d["agent_name"] == s.agent_name
        assert "mock_output" in d

    def test_list_scenarios(self):
        svc = AgentSimulationService()
        scenarios = svc.list_scenarios()
        assert len(scenarios) >= 8

    def test_list_scenarios_by_agent(self):
        svc = AgentSimulationService()
        cto_scenarios = svc.list_scenarios(agent_name="cto_agent")
        assert len(cto_scenarios) >= 2

    def test_list_scenarios_by_tag(self):
        svc = AgentSimulationService()
        blockchain = svc.list_scenarios(tag="blockchain")
        assert len(blockchain) >= 1

    def test_get_scenario(self):
        svc = AgentSimulationService()
        s = svc.get_scenario("sim-001")
        assert s is not None
        assert s.name == "Verdis Runtime Upgrade Review"

    def test_get_nonexistent_scenario(self):
        svc = AgentSimulationService()
        assert svc.get_scenario("nonexistent") is None

    def test_create_custom_scenario(self):
        svc = AgentSimulationService()
        scenario = SimulationScenario(
            name="Test Scenario", agent_name="cto_agent",
            task_type="architecture_review", mock_input={"x": 1},
        )
        result = svc.create_scenario(scenario)
        assert result.id is not None
        assert "custom-" in result.id

    def test_run_simulation(self):
        svc = AgentSimulationService()
        result = svc.run_simulation("sim-001")
        assert result["scenario_name"] == "Verdis Runtime Upgrade Review"
        assert result["agent_name"] == "cto_agent"
        assert result["score"] == 8.6
        assert result["verdict"] == "GO"
        assert result["is_simulation"] is True
        assert len(result["findings"]) == 2
        assert len(result["recommendations"]) == 3

    def test_run_simulation_not_found(self):
        svc = AgentSimulationService()
        result = svc.run_simulation("nonexistent")
        assert "error" in result

    def test_run_agent_simulation_match(self):
        svc = AgentSimulationService()
        result = svc.run_agent_simulation("cto_agent", "architecture_review", {})
        assert result["is_simulation"] is True
        assert "score" in result

    def test_run_agent_simulation_no_match(self):
        svc = AgentSimulationService()
        result = svc.run_agent_simulation("unknown_agent", "unknown_task", {})
        assert result["is_simulation"] is True
        assert result["verdict"] == "GO"

    def test_simulation_history(self):
        svc = AgentSimulationService()
        svc.run_simulation("sim-001")
        svc.run_simulation("sim-002")
        history = svc.get_history()
        assert len(history) >= 2

    def test_simulation_stats(self):
        svc = AgentSimulationService()
        stats = svc.get_stats()
        assert stats["builtin_scenarios"] >= 8
        assert stats["total_scenarios"] >= 8
        assert "agents_covered" in stats
        assert "tags" in stats

    def test_simulation_singleton(self):
        svc1 = get_simulation_service()
        svc2 = get_simulation_service()
        assert svc1 is svc2


class TestVerdisAgentEnhancer:
    def test_context_to_prompt(self):
        ctx = VerdisAgentContext()
        prompt = ctx.to_prompt()
        assert "Verdis" in prompt
        assert "100,000,000,000" in prompt
        assert "BABE/GRANDPA" in prompt
        assert "14" in prompt  # validator count
        assert "AmmDex" in prompt
        assert "CarbonCredits" in prompt

    def test_context_to_dict(self):
        ctx = VerdisAgentContext()
        d = ctx.to_dict()
        assert d["chain_name"] == "Verdis"
        assert d["total_supply"] == "100,000,000,000 VRS"
        assert len(d["pallets"]) == 13

    def test_enhance_prompt(self):
        enhancer = VerdisAgentEnhancer()
        original = "You are a CTO agent."
        enhanced = enhancer.enhance_prompt(original)
        assert "Verdis" in enhanced
        assert "BABE/GRANDPA" in enhanced
        assert original in enhanced

    def test_enhance_prompt_disabled(self):
        enhancer = VerdisAgentEnhancer()
        enhancer.disable()
        original = "You are a CTO agent."
        enhanced = enhancer.enhance_prompt(original)
        assert enhanced == original
        enhancer.enable()

    def test_enhance_prompt_wrong_project(self):
        enhancer = VerdisAgentEnhancer()
        original = "You are a CTO agent."
        enhanced = enhancer.enhance_prompt(original, project="OtherProject")
        assert enhanced == original

    def test_enhance_prompt_verdis_project(self):
        enhancer = VerdisAgentEnhancer()
        original = "You are a CTO agent."
        enhanced = enhancer.enhance_prompt(original, project="Verdis")
        assert "Verdis" in enhanced

    def test_record_activity(self):
        enhancer = VerdisAgentEnhancer()
        activity = AgentActivity(
            agent_name="cto_agent", task_type="architecture_review",
            status="completed", score=8.5, verdict="GO",
        )
        enhancer.record_activity(activity)
        activities = enhancer.get_activities()
        assert len(activities) == 1
        assert activities[0].agent_name == "cto_agent"

    def test_get_activities_by_agent(self):
        enhancer = VerdisAgentEnhancer()
        enhancer.record_activity(AgentActivity(agent_name="cto_agent", task_type="t1"))
        enhancer.record_activity(AgentActivity(agent_name="security_agent", task_type="t2"))
        cto_only = enhancer.get_activities(agent_name="cto_agent")
        assert len(cto_only) == 1

    def test_agent_stats(self):
        enhancer = VerdisAgentEnhancer()
        enhancer.record_activity(AgentActivity(
            agent_name="cto_agent", task_type="architecture_review",
            status="completed", score=8.5, verdict="GO", tokens_used=1000,
        ))
        enhancer.record_activity(AgentActivity(
            agent_name="cto_agent", task_type="security_review",
            status="completed", score=7.5, verdict="NO-GO", tokens_used=500,
        ))
        stats = enhancer.get_agent_stats()
        assert len(stats) == 1
        assert stats[0]["total_tasks"] == 2
        assert stats[0]["completed"] == 2
        assert stats[0]["go_verdicts"] == 1
        assert stats[0]["nogo_verdicts"] == 1
        assert stats[0]["total_tokens"] == 1500

    def test_get_overview(self):
        enhancer = VerdisAgentEnhancer()
        overview = enhancer.get_overview()
        assert "total_activities" in overview
        assert "agent_stats" in overview
        assert "context" in overview
        assert "verdis_task_types" in overview
        assert overview["enhancement_enabled"] is True

    def test_update_context(self):
        enhancer = VerdisAgentEnhancer()
        enhancer.update_context(validator_count=16, spec_version=12)
        ctx = enhancer.get_context()
        assert ctx.validator_count == 16
        assert ctx.spec_version == 12

    def test_enable_disable(self):
        enhancer = VerdisAgentEnhancer()
        enhancer.disable()
        assert enhancer._enhancement_enabled is False
        enhancer.enable()
        assert enhancer._enhancement_enabled is True

    def test_verdis_task_types(self):
        assert len(VERDIS_TASK_TYPES) == 10
        assert "consensus_review" in VERDIS_TASK_TYPES
        assert "pallet_audit" in VERDIS_TASK_TYPES
        assert "supply_invariant_check" in VERDIS_TASK_TYPES
        assert "dex_safety_review" in VERDIS_TASK_TYPES

    def test_enhancer_singleton(self):
        e1 = get_verdis_enhancer()
        e2 = get_verdis_enhancer()
        assert e1 is e2


class TestAgentEnhancementAPI:
    def test_list_simulations_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/simulations", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 8

    def test_get_scenario_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/simulations/sim-001", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "Verdis Runtime Upgrade Review"

    def test_run_simulation_api(self, client, test_user):
        resp = client.post("/api/v1/agent-enhancement/simulations/sim-002/run", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["score"] == 8.0
        assert resp.json()["verdict"] == "GO"

    def test_run_agent_simulation_api(self, client, test_user):
        resp = client.post("/api/v1/agent-enhancement/simulations/run-agent?agent_name=cto_agent&task_type=architecture_review", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["is_simulation"] is True

    def test_simulation_stats_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/simulations/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["builtin_scenarios"] >= 8

    def test_simulation_history_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/simulations/history", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_verdis_context_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/verdis-context", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["chain_name"] == "Verdis"

    def test_verdis_context_prompt_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/verdis-context/prompt", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "Verdis" in resp.json()["prompt"]

    def test_verdis_task_types_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/verdis-task-types", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "consensus_review" in resp.json()

    def test_activities_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/activities", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_record_activity_api(self, client, test_user):
        resp = client.post("/api/v1/agent-enhancement/activities", json={
            "agent_name": "cto_agent", "task_type": "architecture_review",
            "status": "completed", "score": 8.5, "verdict": "GO",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_agent_stats_api(self, client, test_user):
        # Record an activity first
        client.post("/api/v1/agent-enhancement/activities", json={
            "agent_name": "cto_agent", "task_type": "t1",
            "status": "completed", "score": 9.0, "verdict": "GO",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/agent-enhancement/activities/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_overview_api(self, client, test_user):
        resp = client.get("/api/v1/agent-enhancement/overview", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "agent_stats" in resp.json()
        assert "context" in resp.json()

    def test_toggle_enhancement_api(self, client, test_user):
        resp = client.post("/api/v1/agent-enhancement/enhancement/false", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["enhancement_enabled"] is False
        # Re-enable
        client.post("/api/v1/agent-enhancement/enhancement/true", headers=test_user["headers"])

    def test_create_scenario_api(self, client, test_user):
        resp = client.post("/api/v1/agent-enhancement/simulations", json={
            "name": "Test", "agent_name": "cto_agent",
            "task_type": "architecture_review", "mock_input": {},
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "custom-" in resp.json()["id"]
