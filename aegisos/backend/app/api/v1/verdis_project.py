"""API for Verdis Project Management — Phase 16."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.verdis_manager import get_verdis_manager

router = APIRouter(prefix="/verdis-project", tags=["verdis-project"])


class UpdateComponentRequest(BaseModel):
    name: str
    status: str
    notes: str = ""


class ResolveAlertRequest(BaseModel):
    alert_id: str


@router.post("/register")
async def register_project(current_user: User = Depends(get_current_active_user)):
    """Register Verdis as a managed project."""
    return get_verdis_manager().register_project()


@router.post("/health-check")
async def run_health_check(current_user: User = Depends(get_current_active_user)):
    """Run a health check on the Verdis blockchain."""
    snapshot = get_verdis_manager().run_health_check()
    return snapshot.to_dict()


@router.get("/overview")
async def get_overview(current_user: User = Depends(get_current_active_user)):
    """Get complete Verdis project overview."""
    return get_verdis_manager().get_project_overview()


@router.get("/health")
async def get_latest_health(current_user: User = Depends(get_current_active_user)):
    """Get latest health snapshot."""
    snapshot = get_verdis_manager().get_latest_snapshot()
    return snapshot.to_dict() if snapshot else {"message": "No health checks run yet"}


@router.get("/health/history")
async def get_health_history(
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    """Get health check history."""
    return [s.to_dict() for s in get_verdis_manager().get_snapshots(limit)]


@router.get("/components")
async def get_components(current_user: User = Depends(get_current_active_user)):
    """Get all tracked Verdis ecosystem components."""
    return [c.to_dict() for c in get_verdis_manager().get_components()]


@router.put("/components")
async def update_component(
    req: UpdateComponentRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update a component status."""
    get_verdis_manager().update_component_status(req.name, req.status, req.notes)
    return {"status": "updated"}


@router.get("/alerts")
async def get_alerts(
    resolved: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get Verdis alerts."""
    return [a.to_dict() for a in get_verdis_manager().get_alerts(resolved, limit)]


@router.post("/alerts/resolve")
async def resolve_alert(
    req: ResolveAlertRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Resolve an alert."""
    if not get_verdis_manager().resolve_alert(req.alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved"}


@router.get("/agent-context")
async def get_agent_context(current_user: User = Depends(get_current_active_user)):
    """Get Verdis-specific AI agent context."""
    return {"context": get_verdis_manager().get_agent_context()}


@router.get("/health-summary")
async def get_health_summary(current_user: User = Depends(get_current_active_user)):
    """Get human-readable health summary."""
    return {"summary": get_verdis_manager().get_health_summary()}


@router.get("/pipeline-template")
async def get_pipeline_template(current_user: User = Depends(get_current_active_user)):
    """Get the Verdis-specific pipeline template."""
    from app.services.verdis_manager import VERDIS_PIPELINE_TEMPLATE
    return VERDIS_PIPELINE_TEMPLATE


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get monitoring statistics."""
    return get_verdis_manager().get_stats()


@router.post("/monitoring/{enabled}")
async def toggle_monitoring(
    enabled: bool,
    current_user: User = Depends(get_current_active_user),
):
    """Enable or disable monitoring."""
    if enabled:
        get_verdis_manager().enable_monitoring()
    else:
        get_verdis_manager().disable_monitoring()
    return {"monitoring_enabled": enabled}
