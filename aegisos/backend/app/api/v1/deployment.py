"""API for Deployment Dashboard — Phase 30."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.deployment import get_deployment_service, DeploymentStatus, DeploymentTarget, DeploymentComponent

router = APIRouter(prefix="/deployment", tags=["deployment"])


class CreateDeploymentRequest(BaseModel):
    component: str
    target: str
    version: str
    commit_sha: str = ""
    commit_message: str = ""
    branch: str = "main"
    previous_version: str = ""


class UpdateDeploymentRequest(BaseModel):
    status: Optional[str] = None
    logs: Optional[list[dict]] = None
    artifacts: Optional[list[dict]] = None


class UpdateEnvironmentRequest(BaseModel):
    status: Optional[str] = None
    version: Optional[str] = None
    component_status: Optional[dict] = None


# --- Specific routes FIRST (before /{dep_id}) ---

@router.get("/list/deployments")
async def list_deployments(
    component: Optional[str] = None,
    target: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """List deployments."""
    deps = get_deployment_service().list_deployments(component, target, status, limit)
    return [d.to_dict() for d in deps]

@router.get("/environments")
async def list_environments(current_user: User = Depends(get_current_active_user)):
    """List all environments."""
    return [e.to_dict() for e in get_deployment_service().list_environments()]

@router.get("/environments/{target}")
async def get_environment(target: str, current_user: User = Depends(get_current_active_user)):
    """Get environment status."""
    env = get_deployment_service().get_environment(target)
    return env.to_dict() if env else {"error": "Environment not found"}

@router.patch("/environments/{target}")
async def update_environment(target: str, req: UpdateEnvironmentRequest, current_user: User = Depends(get_current_active_user)):
    """Update environment."""
    env = get_deployment_service().update_environment(target, req.status, req.version, req.component_status)
    return env.to_dict() if env else {"error": "Environment not found"}

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get deployment statistics."""
    return get_deployment_service().get_deployment_stats()

@router.get("/workflows")
async def get_workflows(current_user: User = Depends(get_current_active_user)):
    """List GitHub Actions deployment workflows."""
    return get_deployment_service().get_github_actions_workflows()

@router.get("/components")
async def get_components():
    """List all deployable components."""
    return [{"value": c.value, "name": c.value.replace("_", " ").title()} for c in DeploymentComponent]

@router.get("/targets")
async def get_targets():
    """List all deployment targets."""
    return [{"value": t.value, "name": t.value.title()} for t in DeploymentTarget]

# --- Parameterized routes AFTER ---

@router.post("/create")
async def create_deployment(req: CreateDeploymentRequest, current_user: User = Depends(get_current_active_user)):
    """Create a new deployment."""
    service = get_deployment_service()
    dep = service.create_deployment(
        component=req.component, target=req.target, version=req.version,
        commit_sha=req.commit_sha, commit_message=req.commit_message,
        branch=req.branch, triggered_by=current_user.email,
        previous_version=req.previous_version,
    )
    return dep.to_dict()

@router.get("/{dep_id}")
async def get_deployment(dep_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a deployment by ID."""
    dep = get_deployment_service().get_deployment(dep_id)
    return dep.to_dict() if dep else {"error": "Deployment not found"}

@router.patch("/{dep_id}")
async def update_deployment(dep_id: str, req: UpdateDeploymentRequest, current_user: User = Depends(get_current_active_user)):
    """Update a deployment."""
    dep = get_deployment_service().update_deployment(
        dep_id, status=req.status, logs=req.logs, artifacts=req.artifacts
    )
    return dep.to_dict() if dep else {"error": "Deployment not found"}

@router.post("/{dep_id}/log")
async def add_log(dep_id: str, level: str, message: str, current_user: User = Depends(get_current_active_user)):
    """Add a log entry."""
    return {"added": get_deployment_service().add_log(dep_id, level, message)}

@router.post("/{dep_id}/rollback")
async def rollback(dep_id: str, current_user: User = Depends(get_current_active_user)):
    """Rollback a deployment."""
    result = get_deployment_service().rollback_deployment(dep_id)
    return result.to_dict() if result else {"error": "Cannot rollback — no previous version"}
