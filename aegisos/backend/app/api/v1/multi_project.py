"""API for Multi-Project Management — Phase 20."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.multi_project import get_multi_project_manager

router = APIRouter(prefix="/multi-project", tags=["multi-project"])


class RegisterProjectRequest(BaseModel):
    name: str
    type: str
    description: str = ""
    repository: str = ""
    domain: str = ""
    health_endpoint: str = ""
    config: dict = {}
    agent_overrides: dict = {}
    pipeline_template: str = ""
    tags: list = []


class UpdateProjectRequest(BaseModel):
    description: Optional[str] = None
    repository: Optional[str] = None
    domain: Optional[str] = None
    health_endpoint: Optional[str] = None
    config: Optional[dict] = None
    agent_overrides: Optional[dict] = None
    pipeline_template: Optional[str] = None
    tags: Optional[list] = None
    status: Optional[str] = None


@router.post("/projects")
async def register_project(
    req: RegisterProjectRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Register a new project."""
    try:
        project = get_multi_project_manager().register_project(
            name=req.name, project_type=req.type,
            description=req.description, repository=req.repository,
            domain=req.domain, health_endpoint=req.health_endpoint,
            config=req.config, agent_overrides=req.agent_overrides,
            pipeline_template=req.pipeline_template, tags=req.tags,
        )
        return project.to_dict()
    except ValueError as e:
        return {"error": str(e)}


@router.get("/projects")
async def list_projects(
    type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List all projects."""
    return [p.to_dict() for p in get_multi_project_manager().list_projects(type, status)]


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific project."""
    p = get_multi_project_manager().get_project(project_id)
    return p.to_dict() if p else {"error": "not found"}


@router.get("/projects/by-name/{name}")
async def get_project_by_name(
    name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a project by name."""
    p = get_multi_project_manager().get_project_by_name(name)
    return p.to_dict() if p else {"error": "not found"}


@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    req: UpdateProjectRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update a project."""
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    project = get_multi_project_manager().update_project(project_id, **data)
    return project.to_dict() if project else {"error": "not found"}


@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Archive a project."""
    success = get_multi_project_manager().archive_project(project_id)
    return {"archived": success}


@router.post("/projects/{project_id}/pause")
async def pause_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Pause a project."""
    success = get_multi_project_manager().pause_project(project_id)
    return {"paused": success}


@router.post("/projects/{project_id}/resume")
async def resume_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Resume a paused project."""
    success = get_multi_project_manager().resume_project(project_id)
    return {"resumed": success}


@router.get("/projects/{project_id}/agent-config/{agent_name}")
async def get_agent_config(
    project_id: str,
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get agent configuration for a project + agent."""
    return get_multi_project_manager().get_agent_config(project_id, agent_name)


@router.get("/projects/{project_id}/learning-context")
async def get_learning_context(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get learning context for a project."""
    return get_multi_project_manager().get_learning_context(project_id)


@router.put("/projects/{project_id}/health")
async def update_health_status(
    project_id: str,
    status: str,
    current_user: User = Depends(get_current_active_user),
):
    """Update a project's health status."""
    success = get_multi_project_manager().update_health_status(project_id, status)
    return {"updated": success}


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get multi-project statistics."""
    return get_multi_project_manager().get_stats()
