"""API for Dashboard + Export — Post-MVP Phase 8."""

from fastapi import APIRouter, Depends, Query, Response
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.dashboard import get_dashboard_service, get_performance_tracker
from app.services.export_service import get_export_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
export_router = APIRouter(prefix="/export", tags=["export"])


# --- Dashboard ---

@router.get("/overview")
async def get_overview(current_user: User = Depends(get_current_active_user)):
    """Get complete system overview."""
    return get_dashboard_service().get_overview()


@router.get("/performance")
async def get_performance_stats(
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    """Get API performance metrics."""
    return get_performance_tracker().get_stats(limit)


@router.delete("/performance")
async def clear_performance(current_user: User = Depends(get_current_active_user)):
    """Clear performance metrics."""
    get_performance_tracker().clear()
    return {"status": "cleared"}


# --- Export ---

@export_router.get("/pipelines")
async def export_pipelines(
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_active_user),
):
    """Export pipeline runs."""
    data = get_export_service().export_pipelines(format)
    if format == "csv":
        return Response(content=data, media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=pipelines.csv"})
    return Response(content=data, media_type="application/json")


@export_router.get("/analytics")
async def export_analytics(
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_active_user),
):
    """Export analytics."""
    data = get_export_service().export_analytics(format)
    if format == "csv":
        return Response(content=data, media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=analytics.csv"})
    return Response(content=data, media_type="application/json")


@export_router.get("/knowledge-base")
async def export_knowledge_base(
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_active_user),
):
    """Export knowledge base."""
    data = get_export_service().export_knowledge_base(format)
    if format == "csv":
        return Response(content=data, media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=knowledge_base.csv"})
    return Response(content=data, media_type="application/json")


@export_router.get("/activity-log")
async def export_activity_log(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = 1000,
    current_user: User = Depends(get_current_active_user),
):
    """Export activity log."""
    data = get_export_service().export_activity_log(format, limit)
    if format == "csv":
        return Response(content=data, media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=activity_log.csv"})
    return Response(content=data, media_type="application/json")


@export_router.get("/agent-configs")
async def export_agent_configs(
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_active_user),
):
    """Export agent configurations."""
    data = get_export_service().export_agent_configs(format)
    if format == "csv":
        return Response(content=data, media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=agent_configs.csv"})
    return Response(content=data, media_type="application/json")


@export_router.get("/snapshot")
async def export_full_snapshot(current_user: User = Depends(get_current_active_user)):
    """Export complete system snapshot."""
    data = get_export_service().export_full_snapshot()
    return Response(content=data, media_type="application/json",
                    headers={"Content-Disposition": "attachment; filename=evolvixos_snapshot.json"})
