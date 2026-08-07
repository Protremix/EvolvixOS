"""Tests for Deployment Dashboard — Phase 30."""

import pytest
from app.services.deployment import (
    DeploymentService, get_deployment_service,
    DeploymentStatus, DeploymentTarget, DeploymentComponent,
)


class TestDeployment:
    def test_create_deployment(self):
        service = DeploymentService()
        dep = service.create_deployment(
            component="blockchain", target="staging", version="v1.0.0",
            commit_sha="abc123", commit_message="test", branch="main",
            triggered_by="test@test.com",
        )
        assert dep.id.startswith("dep-")
        assert dep.status == "pending"
        assert dep.component == "blockchain"
        assert dep.version == "v1.0.0"

    def test_get_deployment(self):
        service = DeploymentService()
        dep = service.create_deployment("blockchain", "staging", "v1.0", "abc", "msg", "main", "user@test.com")
        found = service.get_deployment(dep.id)
        assert found is not None
        assert found.id == dep.id

    def test_update_deployment_status(self):
        service = DeploymentService()
        dep = service.create_deployment("backend", "production", "v2.0", "abc", "msg", "main", "user@test.com")
        updated = service.update_deployment(dep.id, status="success")
        assert updated.status == "success"
        assert updated.completed_at != ""
        assert updated.duration_seconds > 0

    def test_add_log(self):
        service = DeploymentService()
        dep = service.create_deployment("frontend", "staging", "v1.0", "abc", "msg", "main", "user@test.com")
        assert service.add_log(dep.id, "info", "Starting build") is True
        dep = service.get_deployment(dep.id)
        assert len(dep.logs) == 1
        assert dep.logs[0]["message"] == "Starting build"

    def test_list_deployments(self):
        service = DeploymentService()
        service.create_deployment("blockchain", "staging", "v1", "a", "m", "main", "t@t.com")
        service.create_deployment("backend", "production", "v2", "b", "m", "main", "t@t.com")
        deps = service.list_deployments()
        assert len(deps) == 2

    def test_list_filter_by_component(self):
        service = DeploymentService()
        service.create_deployment("blockchain", "staging", "v1", "a", "m", "main", "t@t.com")
        service.create_deployment("backend", "production", "v2", "b", "m", "main", "t@t.com")
        deps = service.list_deployments(component="blockchain")
        assert len(deps) == 1
        assert deps[0].component == "blockchain"

    def test_list_filter_by_target(self):
        service = DeploymentService()
        service.create_deployment("blockchain", "staging", "v1", "a", "m", "main", "t@t.com")
        service.create_deployment("backend", "production", "v2", "b", "m", "main", "t@t.com")
        deps = service.list_deployments(target="production")
        assert len(deps) == 1
        assert deps[0].target == "production"

    def test_list_filter_by_status(self):
        service = DeploymentService()
        dep = service.create_deployment("blockchain", "staging", "v1", "a", "m", "main", "t@t.com")
        service.update_deployment(dep.id, status="success")
        service.create_deployment("backend", "production", "v2", "b", "m", "main", "t@t.com")
        deps = service.list_deployments(status="success")
        assert len(deps) == 1
        assert deps[0].status == "success"

    def test_rollback(self):
        service = DeploymentService()
        dep = service.create_deployment(
            "blockchain", "staging", "v2.0", "abc", "upgrade", "main", "t@t.com",
            previous_version="v1.0",
        )
        service.update_deployment(dep.id, status="success")
        rollback = service.rollback_deployment(dep.id)
        assert rollback is not None
        assert rollback.version == "v1.0"
        assert rollback.status == "in_progress"
        original = service.get_deployment(dep.id)
        assert original.status == "rollback"

    def test_rollback_no_previous(self):
        service = DeploymentService()
        dep = service.create_deployment("blockchain", "staging", "v1.0", "abc", "first", "main", "t@t.com")
        result = service.rollback_deployment(dep.id)
        assert result is None

    def test_rollback_nonexistent(self):
        service = DeploymentService()
        assert service.rollback_deployment("nonexistent") is None


class TestEnvironments:
    def test_list_environments(self):
        service = DeploymentService()
        envs = service.list_environments()
        assert len(envs) == 3
        names = [e.name for e in envs]
        assert "Staging" in names
        assert "Production" in names
        assert "Mainnet" in names

    def test_get_environment(self):
        service = DeploymentService()
        env = service.get_environment("production")
        assert env is not None
        assert env.name == "Production"
        assert env.url == "https://verdischain.com"

    def test_get_nonexistent_environment(self):
        service = DeploymentService()
        assert service.get_environment("nonexistent") is None

    def test_update_environment(self):
        service = DeploymentService()
        env = service.update_environment("staging", status="healthy", version="v2.0")
        assert env.status == "healthy"
        assert env.version == "v2.0"

    def test_environment_components(self):
        service = DeploymentService()
        env = service.get_environment("production")
        assert "blockchain" in env.components
        assert env.components["blockchain"] == "deployed"


class TestStats:
    def test_stats_empty(self):
        service = DeploymentService()
        stats = service.get_deployment_stats()
        assert stats["total_deployments"] == 0

    def test_stats_with_deployments(self):
        service = DeploymentService()
        dep1 = service.create_deployment("blockchain", "staging", "v1", "a", "m", "main", "t@t.com")
        service.update_deployment(dep1.id, status="success")
        dep2 = service.create_deployment("backend", "production", "v2", "b", "m", "main", "t@t.com")
        service.update_deployment(dep2.id, status="failed")
        stats = service.get_deployment_stats()
        assert stats["total_deployments"] == 2
        assert stats["by_status"]["success"] == 1
        assert stats["by_status"]["failed"] == 1
        assert stats["success_rate"] == 50.0

    def test_stats_avg_duration(self):
        service = DeploymentService()
        dep = service.create_deployment("blockchain", "staging", "v1", "a", "m", "main", "t@t.com")
        service.update_deployment(dep.id, status="success")
        stats = service.get_deployment_stats()
        assert stats["avg_duration_seconds"] > 0


class TestWorkflows:
    def test_get_workflows(self):
        service = DeploymentService()
        workflows = service.get_github_actions_workflows()
        assert len(workflows) == 5
        assert any(w["component"] == "blockchain" for w in workflows)

    def test_workflow_structure(self):
        service = DeploymentService()
        workflows = service.get_github_actions_workflows()
        for w in workflows:
            assert "name" in w
            assert "file" in w
            assert "trigger" in w
            assert "targets" in w
            assert "component" in w


class TestDeploymentAPI:
    def test_create_deployment(self, client, test_user):
        resp = client.post("/api/v1/deployment/create", json={
            "component": "blockchain", "target": "staging", "version": "v1.0.0",
            "commit_sha": "abc123", "commit_message": "test deploy",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_get_deployment(self, client, test_user):
        create = client.post("/api/v1/deployment/create", json={
            "component": "backend", "target": "production", "version": "v2.0",
        }, headers=test_user["headers"])
        dep_id = create.json()["id"]
        resp = client.get(f"/api/v1/deployment/{dep_id}", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"] == dep_id

    def test_update_deployment(self, client, test_user):
        create = client.post("/api/v1/deployment/create", json={
            "component": "frontend", "target": "staging", "version": "v1.0",
        }, headers=test_user["headers"])
        dep_id = create.json()["id"]
        resp = client.patch(f"/api/v1/deployment/{dep_id}", json={"status": "success"},
            headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_list_deployments(self, client, test_user):
        client.post("/api/v1/deployment/create", json={
            "component": "blockchain", "target": "staging", "version": "v1",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/deployment/list/deployments", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_environments(self, client, test_user):
        resp = client.get("/api/v1/deployment/environments", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/deployment/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_deployments" in resp.json()

    def test_workflows(self, client, test_user):
        resp = client.get("/api/v1/deployment/workflows", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 5

    def test_rollback(self, client, test_user):
        create = client.post("/api/v1/deployment/create", json={
            "component": "blockchain", "target": "staging", "version": "v2.0",
            "previous_version": "v1.0",
        }, headers=test_user["headers"])
        dep_id = create.json()["id"]
        client.patch(f"/api/v1/deployment/{dep_id}", json={"status": "success"}, headers=test_user["headers"])
        resp = client.post(f"/api/v1/deployment/{dep_id}/rollback", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["version"] == "v1.0"

    def test_singleton(self):
        assert get_deployment_service() is get_deployment_service()
