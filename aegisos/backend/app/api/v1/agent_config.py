"""API for Agent Configuration — Post-MVP Phase 7."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.agent_config import (
    AgentConfig, get_agent_config_manager, validate_config,
    DEFAULT_AGENT_CONFIGS, VALID_MODELS,
)

router = APIRouter(prefix="/agent-config", tags=["agent-config"])


@router.get("/agents")
async def list_agents(current_user: User = Depends(get_current_active_user)):
    """List all known agents with default configs."""
    return get_agent_config_manager().list_all_agents()


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_active_user)):
    """List valid AI models."""
    return list(VALID_MODELS)


@router.get("/effective/{agent_name}")
async def get_effective_config(
    agent_name: str,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get effective config for an agent (project > global > default)."""
    if agent_name not in DEFAULT_AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail="Agent not found")
    config = get_agent_config_manager().get_effective_config(agent_name, project_id)
    return config.to_dict()


@router.get("/project/{project_id}")
async def get_project_config(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get all agent configs for a project."""
    config = get_agent_config_manager().get_project_config(project_id)
    if not config:
        raise HTTPException(status_code=404, detail="No project config found")
    return config.to_dict()


@router.put("/project/{project_id}/{agent_name}")
async def set_project_config(
    project_id: str,
    agent_name: str,
    config: AgentConfig,
    current_user: User = Depends(get_current_active_user),
):
    """Set agent config for a specific project."""
    if agent_name not in DEFAULT_AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail="Agent not found")
    config.agent_name = agent_name
    try:
        result = get_agent_config_manager().set_project_config(project_id, agent_name, config)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/project/{project_id}/{agent_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_config(
    project_id: str,
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete project-specific agent config (reverts to global/default)."""
    if not get_agent_config_manager().delete_project_config(project_id, agent_name):
        raise HTTPException(status_code=404, detail="Config not found")


@router.get("/global/{agent_name}")
async def get_global_override(
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get global override for an agent."""
    config = get_agent_config_manager().get_global_override(agent_name)
    if not config:
        raise HTTPException(status_code=404, detail="No global override")
    return config.to_dict()


@router.put("/global/{agent_name}")
async def set_global_override(
    agent_name: str,
    config: AgentConfig,
    current_user: User = Depends(get_current_active_user),
):
    """Set global override for an agent."""
    if agent_name not in DEFAULT_AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail="Agent not found")
    config.agent_name = agent_name
    try:
        result = get_agent_config_manager().set_global_override(agent_name, config)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/global/{agent_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_override(
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete global override (reverts to defaults)."""
    if not get_agent_config_manager().delete_global_override(agent_name):
        raise HTTPException(status_code=404, detail="No global override")


@router.get("/enabled/list")
async def list_enabled_agents(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List enabled agents for a project (or globally)."""
    return get_agent_config_manager().list_enabled_agents(project_id)
