"""
EvolvixOS User Onboarding API.

Provides endpoints for the guided onboarding wizard:
- Get onboarding steps and templates
- Track user progress
- Complete/skip steps
- Create sample projects
- Get recommended agents

All endpoints require JWT authentication.
"""

import logging
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.config import settings
from app.services.onboarding import onboarding

logger = logging.getLogger("evolvixos")
router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


async def get_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Validate JWT token and return user ID without database lookup."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject",
            )
        return user_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# === Public endpoints (no auth needed for browsing) ===

@router.get("/steps")
async def get_onboarding_steps():
    """Get all onboarding steps."""
    return onboarding.get_onboarding_steps()


@router.get("/templates")
async def get_project_templates():
    """Get available project templates for the wizard."""
    return onboarding.get_project_templates()


@router.get("/agents")
async def get_agent_presets():
    """Get available AI agent presets."""
    return onboarding.get_agent_presets()


@router.get("/agents/recommended/{project_type}")
async def get_recommended_agents(project_type: str):
    """Get recommended AI agents for a project type."""
    return onboarding.get_recommended_agents(project_type)


# === Authenticated endpoints (require JWT) ===

@router.get("/progress")
async def get_onboarding_progress(user_id: str = Depends(get_user_id)):
    """Get onboarding progress for the authenticated user."""
    return onboarding.get_progress(user_id)


@router.post("/start")
async def start_onboarding(user_id: str = Depends(get_user_id)):
    """Start the onboarding flow for the authenticated user."""
    return onboarding.start_onboarding(user_id)


@router.post("/complete/{step_id}")
async def complete_step(
    step_id: str,
    data: dict = Body(default={}),
    user_id: str = Depends(get_user_id),
):
    """Complete an onboarding step."""
    return onboarding.complete_step(user_id, step_id, data)


@router.post("/skip/{step_id}")
async def skip_step(step_id: str, user_id: str = Depends(get_user_id)):
    """Skip an optional onboarding step."""
    return onboarding.skip_step(user_id, step_id)


@router.post("/create-project")
async def create_sample_project(
    template_id: str = Body(default="generic", embed=True),
    name: str = Body(default="My First Project", embed=True),
    description: str = Body(default="", embed=True),
    user_id: str = Depends(get_user_id),
):
    """Create a sample project from a template."""
    return onboarding.create_sample_project(user_id, template_id, name, description)
