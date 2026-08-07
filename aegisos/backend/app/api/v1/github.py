"""
GitHub Integration API endpoints.

Provides REST access to GitHub repository operations for
EvolvixOS AI agents and the dashboard.
"""

import hmac
import hashlib
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/github", tags=["github-integration"])


class CreateIssueRequest(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Issue title")
    body: str = Field("", description="Issue body (markdown)")
    labels: list[str] = Field(default_factory=list)


class CreatePRRequest(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="PR title")
    head: str = Field(..., description="Head branch")
    base: str = Field("main", description="Base branch")
    body: str = Field("", description="PR body (markdown)")


class AddCommentRequest(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="PR number")
    body: str = Field(..., description="Comment body (markdown)")


@router.get("/repos/{owner}/{repo}")
async def get_repo(
    owner: str, repo: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get repository info."""
    from app.integrations.github import github
    result = github.get_repo(owner, repo)
    if not result:
        raise HTTPException(status_code=404, detail="Repository not found or token missing")
    return result


@router.get("/repos/{owner}/{repo}/issues")
async def list_issues(
    owner: str, repo: str,
    state: str = "open",
    current_user: User = Depends(get_current_active_user),
):
    """List repository issues."""
    from app.integrations.github import github
    return github.list_issues(owner, repo, state)


@router.post("/repos/{owner}/{repo}/issues")
async def create_issue(
    request: CreateIssueRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new issue."""
    from app.integrations.github import github
    result = github.create_issue(request.owner, request.repo, request.title, request.body, request.labels)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create issue")
    return result


@router.get("/repos/{owner}/{repo}/pulls")
async def list_prs(
    owner: str, repo: str,
    state: str = "open",
    current_user: User = Depends(get_current_active_user),
):
    """List pull requests."""
    from app.integrations.github import github
    return github.list_prs(owner, repo, state)


@router.post("/repos/{owner}/{repo}/pulls")
async def create_pr(
    request: CreatePRRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a pull request."""
    from app.integrations.github import github
    result = github.create_pr(request.owner, request.repo, request.title, request.head, request.base, request.body)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create PR")
    return result


@router.get("/repos/{owner}/{repo}/commits")
async def list_commits(
    owner: str, repo: str,
    per_page: int = 10,
    current_user: User = Depends(get_current_active_user),
):
    """List recent commits."""
    from app.integrations.github import github
    return github.list_commits(owner, repo, per_page)


@router.get("/repos/{owner}/{repo}/actions/runs")
async def list_workflow_runs(
    owner: str, repo: str,
    per_page: int = 10,
    current_user: User = Depends(get_current_active_user),
):
    """List recent GitHub Actions workflow runs."""
    from app.integrations.github import github
    return github.list_workflow_runs(owner, repo, per_page)


@router.post("/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed")
async def rerun_failed_jobs(
    owner: str, repo: str, run_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Re-run failed jobs from a workflow run."""
    from app.integrations.github import github
    result = github.rerun_failed_jobs(owner, repo, run_id)
    return {"status": "rerun requested", "run_id": run_id}


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """Receive GitHub webhook events. Validates HMAC-SHA256 signature."""
    body = await request.body()

    # Validate webhook signature if secret is configured
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if webhook_secret and x_hub_signature_256:
        expected = "sha256=" + hmac.new(
            webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    import json
    payload = json.loads(body.decode("utf-8"))
    from app.integrations.github import github
    result = github.process_webhook(x_github_event or "unknown", payload)
    return {"processed": True, "event": result}
