"""API for Global Search + System Health + Backup — Post-MVP Phase 10."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.global_search import get_search_service
from app.services.backup_restore import get_backup_service
from app.services.dashboard import get_dashboard_service
import json

# --- Global Search ---
search_router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    entity_types: Optional[list[str]] = None
    limit: int = 50


@search_router.get("/")
async def search(
    q: str = Query(..., min_length=1),
    entity_types: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Search across all EvolvixOS entities."""
    types = entity_types.split(",") if entity_types else None
    results = get_search_service().search(q, types, limit)
    return [r.to_dict() for r in results]


@search_router.post("/")
async def search_post(
    req: SearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Search across all EvolvixOS entities (POST)."""
    results = get_search_service().search(req.query, req.entity_types, req.limit)
    return [r.to_dict() for r in results]


@search_router.get("/types")
async def search_types(current_user: User = Depends(get_current_active_user)):
    """List searchable entity types."""
    return get_search_service().get_searchable_types()


# --- System Health (unauthenticated) ---
health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def system_health():
    """Unauthenticated health check for load balancers."""
    try:
        overview = get_dashboard_service().get_overview()
        subsystems = overview.get("subsystems", {})
        healthy = sum(1 for s in subsystems.values() if s.get("status") == "healthy")
        total = len(subsystems)
        status_val = "healthy" if healthy == total else "degraded" if healthy > total // 2 else "unhealthy"
        return {
            "status": status_val,
            "healthy_subsystems": healthy,
            "total_subsystems": total,
            "timestamp": overview.get("timestamp"),
        }
    except Exception:
        return {"status": "unhealthy", "error": "health check failed"}


@health_router.get("/health/detail")
async def system_health_detail(current_user: User = Depends(get_current_active_user)):
    """Detailed health check (authenticated)."""
    overview = get_dashboard_service().get_overview()
    return overview


# --- Backup & Restore ---
backup_router = APIRouter(prefix="/backup", tags=["backup"])


class CreateBackupRequest(BaseModel):
    description: str = ""


class RestoreBackupRequest(BaseModel):
    data: dict
    restore_types: Optional[list[str]] = None


@backup_router.post("/")
async def create_backup(
    req: CreateBackupRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a full system backup."""
    return get_backup_service().create_backup(req.description)


@backup_router.post("/restore")
async def restore_backup(
    req: RestoreBackupRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Restore from a backup."""
    return get_backup_service().restore_backup(req.data, req.restore_types)


@backup_router.get("/history")
async def backup_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    """Get backup history."""
    return [b.to_dict() for b in get_backup_service().get_backup_history(limit)]


@backup_router.get("/stats")
async def backup_stats(current_user: User = Depends(get_current_active_user)):
    """Get backup statistics."""
    return get_backup_service().get_stats()


@backup_router.get("/last")
async def last_backup(current_user: User = Depends(get_current_active_user)):
    """Get last backup metadata."""
    b = get_backup_service().get_last_backup()
    return b.to_dict() if b else {"message": "No backups yet"}
