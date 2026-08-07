"""Tests for Multi-Project + Learning Loop Integration — Phase 20."""

import pytest
from app.services.multi_project import (
    MultiProjectManager, ManagedProject, get_multi_project_manager,
)
from app.services.agent_learning import (
    AgentLearningLoop, AgentExecution, get_learning_loop,
)


class TestMultiProjectManager:
    def test_register_project(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="TestProj", project_type="web_backend",
                                   description="A test project")
        assert p.name == "TestProj"
        assert p.type == "web_backend"
        assert p.status == "active"
        assert p.id.startswith("proj-")

    def test_register_duplicate_fails(self):
        mgr = MultiProjectManager()
        mgr.register_project(name="Dup", project_type="web_backend")
        with pytest.raises(ValueError):
            mgr.register_project(name="Dup", project_type="web_backend")

    def test_get_project(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="Test", project_type="mobile")
        got = mgr.get_project(p.id)
        assert got is not None
        assert got.name == "Test"

    def test_get_project_by_name(self):
        mgr = MultiProjectManager()
        mgr.register_project(name="FindMe", project_type="frontend")
        p = mgr.get_project_by_name("FindMe")
        assert p is not None
        assert p.type == "frontend"

    def test_get_nonexistent_project(self):
        mgr = MultiProjectManager()
        assert mgr.get_project("nonexistent") is None
        assert mgr.get_project_by_name("nonexistent") is None

    def test_list_projects(self):
        mgr = MultiProjectManager()
        mgr.register_project(name="P1", project_type="web_backend")
        mgr.register_project(name="P2", project_type="blockchain")
        projects = mgr.list_projects()
        assert len(projects) >= 2

    def test_list_projects_by_type(self):
        mgr = MultiProjectManager()
        mgr.register_project(name="W1", project_type="web_backend")
        mgr.register_project(name="B1", project_type="blockchain")
        web = mgr.list_projects(project_type="web_backend")
        assert len(web) == 1
        assert web[0].name == "W1"

    def test_list_projects_by_status(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="S1", project_type="generic")
        mgr.pause_project(p.id)
        active = mgr.list_projects(status="active")
        paused = mgr.list_projects(status="paused")
        assert all(p.status == "active" for p in active)
        assert all(p.status == "paused" for p in paused)

    def test_update_project(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="Update", project_type="generic")
        updated = mgr.update_project(p.id, description="Updated desc", domain="example.com")
        assert updated.description == "Updated desc"
        assert updated.domain == "example.com"

    def test_archive_project(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="Archive", project_type="generic")
        assert mgr.archive_project(p.id) is True
        assert mgr.get_project(p.id).status == "archived"

    def test_pause_resume_project(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="PauseTest", project_type="generic")
        assert mgr.pause_project(p.id) is True
        assert mgr.get_project(p.id).status == "paused"
        assert mgr.resume_project(p.id) is True
        assert mgr.get_project(p.id).status == "active"

    def test_get_agent_config(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="AgentConf", project_type="blockchain",
                                   agent_overrides={"cto_agent": {"temperature": 0.1}})
        config = mgr.get_agent_config(p.id, "cto_agent")
        assert config["temperature"] == 0.1

    def test_get_agent_config_no_override(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="NoOverride", project_type="generic")
        config = mgr.get_agent_config(p.id, "cto_agent")
        assert config == {}

    def test_get_learning_context(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="LearnCtx", project_type="blockchain",
                                   config={"consensus": "DPoS"})
        ctx = mgr.get_learning_context(p.id)
        assert ctx["project_name"] == "LearnCtx"
        assert ctx["project_type"] == "blockchain"
        assert ctx["project_config"]["consensus"] == "DPoS"

    def test_update_health_status(self):
        mgr = MultiProjectManager()
        p = mgr.register_project(name="Health", project_type="generic")
        assert mgr.update_health_status(p.id, "healthy") is True
        assert mgr.get_project(p.id).health_status == "healthy"
        assert mgr.get_project(p.id).last_health_check is not None

    def test_get_stats(self):
        mgr = MultiProjectManager()
        mgr.register_project(name="S1", project_type="web_backend")
        mgr.register_project(name="S2", project_type="blockchain")
        stats = mgr.get_stats()
        assert stats["total_projects"] >= 2
        assert "by_type" in stats
        assert "by_status" in stats

    def test_register_verdis(self):
        mgr = MultiProjectManager()
        p = mgr.register_verdis()
        assert p.name == "Verdis"
        assert p.type == "blockchain"
        assert p.domain == "verdischain.com"
        assert "github.com" in p.repository

    def test_register_verdis_idempotent(self):
        mgr = MultiProjectManager()
        p1 = mgr.register_verdis()
        p2 = mgr.register_verdis()
        assert p1.id == p2.id

    def test_singleton_includes_verdis(self):
        mgr = get_multi_project_manager()
        verdis = mgr.get_project_by_name("Verdis")
        assert verdis is not None
        assert verdis.type == "blockchain"


class TestLearningLoopIntegration:
    def test_feedback_injects_into_agent_prompt(self):
        """Test that learning feedback is injected into agent system prompts."""
        from app.ai.agents.base_agent import BaseAgent, AgentTask, TaskType
        from unittest.mock import MagicMock, patch

        # Record some executions first
        loop = get_learning_loop()
        for score in [5.0, 5.5, 6.0, 6.5, 6.0, 5.5]:
            loop.record_execution(AgentExecution(
                agent_name="test_agent", task_type="architecture_review",
                score=score, verdict="NO-GO", tokens_used=500, latency_ms=1000,
            ))

        # Create a mock agent and verify feedback injection
        captured_prompts = []

        class TestAgent(BaseAgent):
            name = "test_agent"
            description = "Test agent"
            handled_task_types = {TaskType.ARCHITECTURE_REVIEW}

            @property
            def system_prompt(self):
                return "You are a test agent."

        agent = TestAgent(llm_client=MagicMock())
        agent.llm.chat = MagicMock(side_effect=lambda system_prompt, **kw: captured_prompts.append(system_prompt) or type('R', (), {'content': '{}', 'tokens_used': 100})())

        task = AgentTask(type=TaskType.ARCHITECTURE_REVIEW, data={"test": True})
        agent.execute(task)

        # Check that the system prompt was enhanced with learning feedback
        assert len(captured_prompts) > 0
        assert "LEARNING FEEDBACK" in captured_prompts[0]

    def test_agent_records_execution_after_llm_call(self):
        """Test that agent executions are recorded after LLM calls."""
        from app.ai.agents.base_agent import BaseAgent, AgentTask, TaskType
        from unittest.mock import MagicMock

        loop = get_learning_loop()
        loop.clear()

        class TestAgent2(BaseAgent):
            name = "test_record_agent"
            description = "Test"
            handled_task_types = {TaskType.ARCHITECTURE_REVIEW}

            @property
            def system_prompt(self):
                return "You are a test agent."

            def postprocess(self, content, task):
                from app.ai.agents.base_agent import AgentResult, AgentStatus
                return AgentResult(
                    task_id=task.id, agent_name=self.name,
                    status=AgentStatus.COMPLETED, content=content,
                    structured_data={"verdict": "GO"}, score=8.5,
                )

        agent = TestAgent2(llm_client=MagicMock())
        agent.llm.chat = MagicMock(return_value=type('R', (), {'content': '{"verdict": "GO"}', 'tokens_used': 200})())

        task = AgentTask(type=TaskType.ARCHITECTURE_REVIEW, data={})
        agent.execute(task)

        # Verify execution was recorded
        executions = list(loop._executions)
        recorded = [e for e in executions if e.agent_name == "test_record_agent"]
        assert len(recorded) >= 1
        assert recorded[0].score == 8.5
        assert recorded[0].verdict == "GO"


class TestMultiProjectAPI:
    def test_register_project_api(self, client, test_user):
        resp = client.post("/api/v1/multi-project/projects", json={
            "name": "API Test Project", "type": "web_backend",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "API Test Project"

    def test_list_projects_api(self, client, test_user):
        resp = client.get("/api/v1/multi-project/projects", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        # Verdis should be pre-registered
        names = [p["name"] for p in resp.json()]
        assert "Verdis" in names

    def test_get_project_api(self, client, test_user):
        create = client.post("/api/v1/multi-project/projects", json={
            "name": "Get Test", "type": "generic",
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        resp = client.get(f"/api/v1/multi-project/projects/{pid}", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_get_project_by_name_api(self, client, test_user):
        resp = client.get("/api/v1/multi-project/projects/by-name/Verdis", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "Verdis"

    def test_update_project_api(self, client, test_user):
        create = client.post("/api/v1/multi-project/projects", json={
            "name": "Update Me", "type": "generic",
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        resp = client.put(f"/api/v1/multi-project/projects/{pid}", json={
            "description": "Updated description",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

    def test_archive_project_api(self, client, test_user):
        create = client.post("/api/v1/multi-project/projects", json={
            "name": "Archive Me", "type": "generic",
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        resp = client.post(f"/api/v1/multi-project/projects/{pid}/archive", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["archived"] is True

    def test_pause_resume_api(self, client, test_user):
        create = client.post("/api/v1/multi-project/projects", json={
            "name": "Pause Me", "type": "generic",
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        client.post(f"/api/v1/multi-project/projects/{pid}/pause", headers=test_user["headers"])
        resp = client.post(f"/api/v1/multi-project/projects/{pid}/resume", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["resumed"] is True

    def test_agent_config_api(self, client, test_user):
        create = client.post("/api/v1/multi-project/projects", json={
            "name": "Agent Config Test", "type": "blockchain",
            "agent_overrides": {"cto_agent": {"temperature": 0.1}},
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        resp = client.get(f"/api/v1/multi-project/projects/{pid}/agent-config/cto_agent", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["temperature"] == 0.1

    def test_learning_context_api(self, client, test_user):
        create = client.post("/api/v1/multi-project/projects", json={
            "name": "Learn Ctx API", "type": "blockchain",
        }, headers=test_user["headers"])
        pid = create.json()["id"]
        resp = client.get(f"/api/v1/multi-project/projects/{pid}/learning-context", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["project_name"] == "Learn Ctx API"

    def test_stats_api(self, client, test_user):
        resp = client.get("/api/v1/multi-project/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_projects" in resp.json()
        assert resp.json()["total_projects"] >= 1  # At least Verdis
