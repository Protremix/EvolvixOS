"""
Integration tests for EvolvixOS — end-to-end workflows spanning multiple modules.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json
import os


class TestAuthProjectWorkflow:
    """Integration: register → login → create project → add task → complete task."""

    def test_full_user_lifecycle(self, client, test_user):
        headers = test_user["headers"]

        # Create a project
        resp = client.post("/api/v1/projects/", json={
            "name": "Integration Test Project",
            "description": "End-to-end test",
        }, headers=headers)
        assert resp.status_code == 201
        project = resp.json()
        project_id = project["id"]

        # Create a task in the project
        resp = client.post("/api/v1/tasks/", json={
            "title": "Write tests",
            "description": "Integration tests",
            "project_id": project_id,
            "task_type": "code_review",
            "priority": "high",
        }, headers=headers)
        assert resp.status_code == 201
        task = resp.json()
        task_id = task["id"]

        # Update the task to completed
        resp = client.put(f"/api/v1/tasks/{task_id}", json={
            "title": "Write tests",
            "description": "Integration tests",
            "project_id": project_id,
            "task_type": "code_review",
            "priority": "high",
            "status": "completed",
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        # Verify project shows up in list
        resp = client.get("/api/v1/projects/", headers=headers)
        assert resp.status_code == 200
        assert any(p["id"] == project_id for p in resp.json())

        # Verify task shows up in list
        resp = client.get("/api/v1/tasks/", headers=headers)
        assert resp.status_code == 200
        assert any(t["id"] == task_id for t in resp.json())

    def test_organization_member_workflow(self, client, test_user):
        headers = test_user["headers"]

        # Create organization
        resp = client.post("/api/v1/organizations/", json={
            "name": "Test Org",
            "description": "Test org for integration",
        }, headers=headers)
        assert resp.status_code == 201
        org_id = resp.json()["id"]

        # List members (should be just the creator)
        resp = client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Create a second user
        resp = client.post("/api/v1/auth/register", json={
            "username": "testmember",
            "email": "member@test.com",
            "password": "Test1234!",
        })
        assert resp.status_code == 201
        member_id = resp.json()["id"]

        # Add member to org (role is admin/member/viewer)
        resp = client.post(f"/api/v1/organizations/{org_id}/members", json={
            "user_id": member_id,
            "role": "member",
        }, headers=headers)
        assert resp.status_code == 201

        # Verify member shows up
        resp = client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
        assert resp.status_code == 200
        assert any(m["user_id"] == member_id for m in resp.json())

        # Remove member
        resp = client.delete(f"/api/v1/organizations/{org_id}/members/{member_id}", headers=headers)
        assert resp.status_code == 204


class TestEventsWorkflow:
    """Integration: create events → list → verify event bus."""

    def test_create_and_list_events(self, client, test_user):
        headers = test_user["headers"]

        # Create an event — schema uses `type` and `payload`
        resp = client.post("/api/v1/events/", json={
            "type": "test.event",
            "payload": {"message": "hello world"},
        }, headers=headers)
        assert resp.status_code == 201

        # List events
        resp = client.get("/api/v1/events/", headers=headers)
        assert resp.status_code == 200
        events = resp.json()
        assert any(e["type"] == "test.event" for e in events)


class TestAIWorkflowIntegration:
    """Integration: AI task dispatch → agent routing → result."""

    def test_dispatch_code_review(self, client, test_user):
        headers = test_user["headers"]

        with patch("app.ai.llm_client.LLMClient.chat") as mock_chat:
            mock_chat.return_value = {
                "content": "Code review complete. No issues found.",
                "model": "gpt-4o",
                "usage": {"total_tokens": 100},
            }

            resp = client.post("/api/v1/ai/dispatch", json={
                "task_type": "code_review",
                "data": {
                    "code": "def foo():\n    pass\n",
                    "language": "python",
                },
            }, headers=headers)
            assert resp.status_code == 200
            assert "task_id" in resp.json()

    def test_dispatch_batch(self, client, test_user):
        """Test batch dispatch of multiple tasks."""
        headers = test_user["headers"]

        with patch("app.ai.llm_client.LLMClient.chat") as mock_chat:
            mock_chat.return_value = {
                "content": "Result",
                "model": "gpt-4o",
                "usage": {"total_tokens": 50},
            }

            # BatchDispatchRequest uses `tasks` field
            resp = client.post("/api/v1/ai/dispatch/batch", json={
                "tasks": [
                    {"task_type": "code_review", "data": {"code": "x = 1"}},
                    {"task_type": "security_scan", "data": {"code": "y = 2"}},
                ],
            }, headers=headers)
            assert resp.status_code == 200
            assert len(resp.json()) == 2

    def test_list_agents(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/ai/agents", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 5

    def test_executor_status(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/ai/executor/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "max_workers" in data
        assert "pending" in data
        assert "completed" in data


class TestCodeOpsIntegration:
    """Integration: code analysis + test generation + CI healing."""

    def test_code_ops_generate_tests(self, client, test_user):
        headers = test_user["headers"]

        with patch("app.ai.agents.test_generator_agent.AITestGeneratorAgent.generate_tests", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "test_code": "def test_foo():\n    assert True\n",
                "language": "python",
                "test_count": 1,
            }

            resp = client.post("/api/v1/code-ops/generate-tests", json={
                "source_code": "def foo(): return 1",
                "language": "python",
            }, headers=headers)
            assert resp.status_code == 200

    def test_ci_diagnose(self, client, test_user):
        headers = test_user["headers"]

        with patch("app.ai.llm_client.LLMClient.chat") as mock_chat:
            mock_chat.return_value = {
                "content": json.dumps({
                    "diagnosis": "Import error",
                    "fix": "Add missing import",
                    "confidence": 0.9,
                }),
                "model": "gpt-4o",
                "usage": {"total_tokens": 50},
            }

            resp = client.post("/api/v1/code-ops/diagnose-ci", json={
                "error_logs": "ModuleNotFoundError: No module named 'foo'",
            }, headers=headers)
            assert resp.status_code == 200


class TestGitHubIntegration:
    """Integration: GitHub API + webhook processing."""

    def test_github_webhook_push(self, client, test_user):
        """Test GitHub webhook with push event."""
        headers = test_user["headers"]
        webhook_data = {
            "event": "push",
            "ref": "refs/heads/main",
            "repository": {"name": "test-repo", "full_name": "owner/test-repo"},
            "commits": [{"id": "abc123", "message": "test commit"}],
        }
        resp = client.post("/api/v1/github/webhook", json=webhook_data, headers=headers)
        assert resp.status_code in (200, 202)


class TestVerdisIntegration:
    """Integration: Verdis blockchain monitoring."""

    def test_verdis_health(self, client, test_user):
        headers = test_user["headers"]
        with patch("app.integrations.verdis.verdis") as mock_verdis:
            mock_verdis.get_chain_health.return_value = {
                "connected": True,
                "block_height": 100,
                "peers": 14,
                "validators": 14,
            }
            resp = client.get("/api/v1/verdis/health", headers=headers)
            assert resp.status_code == 200

    def test_verdis_summary(self, client, test_user):
        headers = test_user["headers"]
        with patch("app.integrations.verdis.verdis") as mock_verdis:
            mock_verdis.get_health_summary.return_value = {
                "status": "healthy",
                "block_height": 100,
                "peers": 14,
                "validators": 14,
                "spec_version": 11,
            }
            resp = client.get("/api/v1/verdis/summary", headers=headers)
            assert resp.status_code == 200


class TestDepGraphAndASTDiffIntegration:
    """Integration: analyze code → build dep graph → diff changes."""

    def test_dep_graph_build_and_query(self, client, test_user, tmp_path):
        headers = test_user["headers"]

        proj = tmp_path / "testproj"
        proj.mkdir()
        (proj / "__init__.py").write_text("")
        (proj / "main.py").write_text("import os\n\ndef main():\n    return os.getcwd()\n")
        (proj / "utils.py").write_text("from main import main\n\ndef helper():\n    return main()\n")

        resp = client.post("/api/v1/dep-graph/build", json={
            "project_path": str(proj),
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_files"] >= 2

        resp = client.get(f"/api/v1/dep-graph/stats?project_path={proj}", headers=headers)
        assert resp.status_code == 200

        resp = client.get(f"/api/v1/dep-graph/cycles?project_path={proj}", headers=headers)
        assert resp.status_code == 200

    def test_ast_diff_workflow(self, client, test_user):
        headers = test_user["headers"]

        resp = client.post("/api/v1/ast-diff/compare", json={
            "old_code": "def foo():\n    return 1\n",
            "new_code": "def foo(a, b):\n    return a + b\n",
            "language": "python",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["signature_changed"] >= 1


class TestSpecCompilerIntegration:
    """Integration: compile spec → validate → get generated code."""

    def test_compile_and_validate(self, client, test_user):
        headers = test_user["headers"]

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Integration API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "operationId": "listItems",
                        "summary": "List items",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
            "components": {
                "schemas": {
                    "Item": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                        "required": ["id", "name"],
                    }
                }
            }
        }

        resp = client.post("/api/v1/spec-compiler/compile", json={
            "spec": spec,
            "spec_format": "openapi",
        }, headers=headers)
        assert resp.status_code == 200
        compiled = resp.json()
        assert compiled["stats"]["total_models"] == 1
        assert compiled["stats"]["total_endpoints"] == 1

        resp = client.post("/api/v1/spec-compiler/validate", json={
            "spec": spec,
            "spec_format": "openapi",
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["valid"] is True


class TestHealthAndMetrics:
    """Integration: health check + Prometheus metrics."""

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_metrics(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "text" in resp.headers.get("content-type", "")


class TestSecurityRBAC:
    """Integration: RBAC role enforcement across endpoints."""

    def test_admin_can_create_project(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/projects/", json={
            "name": "Test",
            "description": "Test",
        }, headers=headers)
        assert resp.status_code == 201

    def test_no_auth_denied(self, client):
        """All protected endpoints should deny without auth."""
        endpoints = [
            ("GET", "/api/v1/projects/"),
            ("GET", "/api/v1/tasks/"),
            ("GET", "/api/v1/ai/agents"),
            ("GET", "/api/v1/ast-diff/info"),
            ("GET", "/api/v1/spec-compiler/info"),
            ("GET", "/api/v1/verdis/health"),
            ("GET", "/api/v1/organizations/"),
            ("GET", "/api/v1/events/"),
        ]
        for method, path in endpoints:
            resp = client.request(method, path)
            assert resp.status_code == 401, f"{method} {path} should require auth, got {resp.status_code}"

    def test_expired_token_denied(self, client):
        headers = {"Authorization": "Bearer expired.token.here"}
        resp = client.get("/api/v1/projects/", headers=headers)
        assert resp.status_code == 401


