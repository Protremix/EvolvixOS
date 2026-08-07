"""
Tests for the GitHub integration.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.integrations.github import GitHubIntegration


class TestGitHubIntegration:
    """Test the GitHub integration client."""

    def test_init_with_token(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")
        assert gh.token == "ghp_TEST_PLACEHOLDER"

    def test_init_without_token(self):
        gh = GitHubIntegration()
        # Will fall back to env var or empty string
        assert gh.token is not None  # Could be "" or env value

    def test_get_repo_success(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"full_name":"verdischain/Verdis","private":false}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = gh.get_repo("verdischain", "Verdis")
            assert result["full_name"] == "verdischain/Verdis"

    def test_get_repo_failure(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        with patch('urllib.request.urlopen', side_effect=Exception("Network error")):
            result = gh.get_repo("verdischain", "Verdis")
            assert result is None

    def test_list_issues(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        mock_response = MagicMock()
        mock_response.read.return_value = b'[{"number":1,"title":"Bug"},{"number":2,"title":"Feature"}]'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = gh.list_issues("verdischain", "Verdis")
            assert len(result) == 2
            assert result[0]["number"] == 1

    def test_create_issue(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"number":42,"title":"Test Issue","html_url":"https://github.com/Protremix/Verdischain-/issues/42"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 201

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = gh.create_issue("verdischain", "Verdis", "Test Issue", "Body text", ["bug"])
            assert result["number"] == 42
            assert result["html_url"].endswith("/42")

    def test_create_pr(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"number":5,"title":"New PR","head":{"ref":"feature"}}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 201

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = gh.create_pr("verdischain", "Verdis", "New PR", "feature", "main", "Description")
            assert result["number"] == 5
            assert result["head"]["ref"] == "feature"

    def test_list_workflow_runs(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"workflow_runs":[{"id":123,"status":"completed","conclusion":"success"}]}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = gh.list_workflow_runs("verdischain", "Verdis")
            assert len(result) == 1
            assert result[0]["conclusion"] == "success"

    def test_rerun_failed_jobs(self):
        gh = GitHubIntegration(token="ghp_TEST_PLACEHOLDER")

        mock_response = MagicMock()
        mock_response.read.return_value = b''
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 204

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = gh.rerun_failed_jobs("verdischain", "Verdis", 123)
            assert result is None  # 204 returns None

    def test_process_webhook_push(self):
        gh = GitHubIntegration()
        payload = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "verdischain/Verdis"},
            "commits": [{"id": "abc"}],
            "head_commit": {"id": "abc123", "message": "feat: new feature"},
        }
        result = gh.process_webhook("push", payload)
        assert result["event_type"] == "push"
        assert result["ref"] == "refs/heads/main"
        assert result["commits"] == 1
        assert result["message"] == "feat: new feature"

    def test_process_webhook_pull_request(self):
        gh = GitHubIntegration()
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 5,
                "title": "New Feature",
                "state": "open",
                "html_url": "https://github.com/Protremix/Verdischain-/pull/5",
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"},
            },
            "repository": {"full_name": "verdischain/Verdis"},
        }
        result = gh.process_webhook("pull_request", payload)
        assert result["pr_number"] == 5
        assert result["pr_title"] == "New Feature"
        assert result["head_branch"] == "feature-branch"
        assert result["base_branch"] == "main"

    def test_process_webhook_issues(self):
        gh = GitHubIntegration()
        payload = {
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Bug report",
                "body": "Something is broken",
            },
            "repository": {"full_name": "verdischain/Verdis"},
        }
        result = gh.process_webhook("issues", payload)
        assert result["issue_number"] == 42
        assert result["issue_title"] == "Bug report"

    def test_process_webhook_workflow_run(self):
        gh = GitHubIntegration()
        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 999,
                "name": "CI",
                "status": "completed",
                "conclusion": "failure",
                "head_branch": "feature",
            },
            "repository": {"full_name": "verdischain/Verdis"},
        }
        result = gh.process_webhook("workflow_run", payload)
        assert result["run_id"] == 999
        assert result["run_conclusion"] == "failure"

    def test_process_webhook_unknown(self):
        gh = GitHubIntegration()
        result = gh.process_webhook("unknown_event", {"action": "test"})
        assert result["event_type"] == "unknown_event"


class TestGitHubAPI:
    """Test GitHub API endpoints."""

    def test_get_repo_unauthorized(self, client):
        response = client.get("/api/v1/github/repos/verdischain/Verdis")
        assert response.status_code == 401

    def test_list_issues_unauthorized(self, client):
        response = client.get("/api/v1/github/repos/verdischain/Verdis/issues")
        assert response.status_code == 401

    def test_webhook_no_auth(self, client):
        """Webhook endpoint should not require JWT auth."""
        response = client.post("/api/v1/github/webhook",
                              json={"action": "test"},
                              headers={"X-GitHub-Event": "push"})
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] is True
        assert data["event"]["event_type"] == "push"

    def test_webhook_invalid_signature(self, client, monkeypatch):
        """Webhook should reject invalid signature when secret is configured."""
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test_secret")
        response = client.post("/api/v1/github/webhook",
                              json={"action": "test"},
                              headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=invalid"})
        assert response.status_code == 403

    def test_webhook_valid_signature(self, client, monkeypatch):
        """Webhook should accept valid signature."""
        import hmac, hashlib, json
        secret = "test_secret"
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)
        payload = json.dumps({"action": "opened", "repository": {"full_name": "test/repo"}, "commits": [], "head_commit": {"id": "abc", "message": "test"}}).encode()
        sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        response = client.post("/api/v1/github/webhook",
                              content=payload,
                              headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": sig, "Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.json()
        assert data["event"]["message"] == "test"
