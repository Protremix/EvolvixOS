"""API for Activity Log — Post-MVP Phase 7."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.activity_log import get_activity_log, log_activity, ActivityEntry

router = APIRouter(prefix="/activity-log", tags=["activity-log"])


@router.get("/")
async def list_entries(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    severity: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    """List activity entries with filters."""
    return [e.to_dict() for e in get_activity_log().list(
        user_id=user_id, action=action, entity_type=entity_type,
        entity_id=entity_id, severity=severity, since=since, until=until,
        limit=limit, offset=offset,
    )]


@router.get("/search")
async def search_entries(
    q: str = "",
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    """Search activity log."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    return [e.to_dict() for e in get_activity_log().search(q, limit)]


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get activity log statistics."""
    return get_activity_log().get_stats()


@router.get("/errors/recent")
async def recent_errors(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
):
    """Get recent error-level entries."""
    return [e.to_dict() for e in get_activity_log().get_recent_errors(limit)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry: ActivityEntry,
    current_user: User = Depends(get_current_active_user),
):
    """Manually log an activity entry."""
    result = get_activity_log().log(
        action=entry.action,
        user_id=entry.user_id or str(current_user.id),
        user_email=entry.user_email or current_user.email,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        entity_name=entry.entity_name,
        details=entry.details,
        severity=entry.severity,
    )
    return result.to_dict()


@router.post("/cleanup")
async def cleanup_old(
    max_age_days: int = 90,
    current_user: User = Depends(get_current_active_user),
):
    """Remove entries older than max_age_days."""
    removed = get_activity_log().cleanup_old(max_age_days)
    return {"removed": removed}
