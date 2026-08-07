"""
GitHub Integration — enables EvolvixOS AI agents to interact with
repositories: read issues, create PRs, fetch file contents, and
receive webhook events from GitHub Actions CI runs.
"""

import json
import logging
import os
import urllib.request
from typing import Any

logger = logging.getLogger("evolvixos")


class GitHubIntegration:
    """GitHub API client for EvolvixOS agent operations."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method: str, path: str, data: dict = None) -> Any:
        url = f"{self.BASE_URL}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 204:
                    return None
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")[:200]
            logger.error(f"github_api_error: {method} {path} status={e.code} error={err_body}")
            return None
        except Exception as e:
            logger.error(f"github_request_failed: {path} error={str(e)}")
            return None

    # ---- Repository Operations ----

    def get_repo(self, owner: str, repo: str) -> dict | None:
        """Get repository info."""
        return self._request("GET", f"/repos/{owner}/{repo}")

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> dict | None:
        """Get file content from a repository."""
        return self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")

    def list_commits(self, owner: str, repo: str, per_page: int = 10) -> list[dict]:
        """List recent commits."""
        result = self._request("GET", f"/repos/{owner}/{repo}/commits?per_page={per_page}")
        return result if isinstance(result, list) else []

    def get_branch(self, owner: str, repo: str, branch: str) -> dict | None:
        """Get branch info."""
        return self._request("GET", f"/repos/{owner}/{repo}/branches/{branch}")

    # ---- Issue Operations ----

    def list_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 20) -> list[dict]:
        """List repository issues."""
        result = self._request("GET", f"/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}")
        return result if isinstance(result, list) else []

    def get_issue(self, owner: str, repo: str, issue_number: int) -> dict | None:
        """Get a specific issue."""
        return self._request("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")

    def create_issue(self, owner: str, repo: str, title: str, body: str, labels: list[str] = None) -> dict | None:
        """Create a new issue."""
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        return self._request("POST", f"/repos/{owner}/{repo}/issues", data)

    # ---- Pull Request Operations ----

    def list_prs(self, owner: str, repo: str, state: str = "open", per_page: int = 20) -> list[dict]:
        """List pull requests."""
        result = self._request("GET", f"/repos/{owner}/{repo}/pulls?state={state}&per_page={per_page}")
        return result if isinstance(result, list) else []

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict | None:
        """Get a specific pull request."""
        return self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}")

    def create_pr(self, owner: str, repo: str, title: str, head: str, base: str = "main",
                  body: str = "") -> dict | None:
        """Create a pull request."""
        return self._request("POST", f"/repos/{owner}/{repo}/pulls", data={
            "title": title, "head": head, "base": base, "body": body,
        })

    def add_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict | None:
        """Add a comment to a PR."""
        return self._request("POST", f"/repos/{owner}/{repo}/issues/{pr_number}/comments", data={"body": body})

    # ---- CI/CD Operations ----

    def list_workflows(self, owner: str, repo: str) -> list[dict]:
        """List GitHub Actions workflows."""
        result = self._request("GET", f"/repos/{owner}/{repo}/actions/workflows")
        return result.get("workflows", []) if result else []

    def list_workflow_runs(self, owner: str, repo: str, per_page: int = 10) -> list[dict]:
        """List recent workflow runs."""
        result = self._request("GET", f"/repos/{owner}/{repo}/actions/runs?per_page={per_page}")
        return result.get("workflow_runs", []) if result else []

    def get_workflow_run_logs(self, owner: str, repo: str, run_id: int) -> dict | None:
        """Get workflow run details (including logs URL)."""
        return self._request("GET", f"/repos/{owner}/{repo}/actions/runs/{run_id}")

    def rerun_failed_jobs(self, owner: str, repo: str, run_id: int) -> dict | None:
        """Re-run failed jobs from a workflow run."""
        return self._request("POST", f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs")

    # ---- Webhook Event Processing ----

    def process_webhook(self, event_type: str, payload: dict) -> dict:
        """Process a GitHub webhook event and return structured data for AI agents."""
        result = {"event_type": event_type, "action": payload.get("action", "")}

        if event_type == "push":
            result.update({
                "ref": payload.get("ref", ""),
                "repo": payload.get("repository", {}).get("full_name", ""),
                "commits": len(payload.get("commits", [])),
                "head_commit": payload.get("head_commit", {}).get("id", ""),
                "message": payload.get("head_commit", {}).get("message", ""),
            })

        elif event_type == "pull_request":
            pr = payload.get("pull_request", {})
            result.update({
                "pr_number": pr.get("number"),
                "pr_title": pr.get("title"),
                "pr_state": pr.get("state"),
                "pr_url": pr.get("html_url"),
                "repo": payload.get("repository", {}).get("full_name", ""),
                "head_branch": pr.get("head", {}).get("ref"),
                "base_branch": pr.get("base", {}).get("ref"),
            })

        elif event_type == "issues":
            issue = payload.get("issue", {})
            result.update({
                "issue_number": issue.get("number"),
                "issue_title": issue.get("title"),
                "issue_body": issue.get("body", "")[:500],
                "repo": payload.get("repository", {}).get("full_name", ""),
            })

        elif event_type == "workflow_run":
            wf = payload.get("workflow_run", {})
            result.update({
                "run_id": wf.get("id"),
                "run_name": wf.get("name"),
                "run_status": wf.get("status"),
                "run_conclusion": wf.get("conclusion"),
                "repo": payload.get("repository", {}).get("full_name", ""),
                "head_branch": wf.get("head_branch"),
            })

        return result


# Singleton (uses GITHUB_TOKEN env var)
github = GitHubIntegration()
