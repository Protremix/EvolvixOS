"""API for System Settings — Post-MVP Phase 9."""

from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.system_settings import get_settings_manager

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


class SetSettingRequest(BaseModel):
    key: str
    value: Union[str, int, float, bool, None] = None


@router.get("/")
async def list_settings(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List all system settings."""
    mgr = get_settings_manager()
    if category:
        return mgr.list_by_category(category)
    return mgr.list_all()


@router.get("/categories")
async def list_categories(current_user: User = Depends(get_current_active_user)):
    """List all setting categories."""
    return get_settings_manager().get_categories()


@router.get("/{key}")
async def get_setting(
    key: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific setting."""
    mgr = get_settings_manager()
    value = mgr.get(key)
    if value is None and key not in mgr._settings:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": key, "value": value}


@router.put("/")
async def set_setting(
    req: SetSettingRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Set a setting override."""
    try:
        get_settings_manager().set(req.key, req.value)
        return {"key": req.key, "value": get_settings_manager().get(req.key)}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{key}")
async def reset_setting(
    key: str,
    current_user: User = Depends(get_current_active_user),
):
    """Reset a setting to its default."""
    if not get_settings_manager().reset(key):
        raise HTTPException(status_code=404, detail="No override found")
    return {"key": key, "value": get_settings_manager().get(key)}


@router.post("/reset-all")
async def reset_all_settings(current_user: User = Depends(get_current_active_user)):
    """Reset all setting overrides."""
    get_settings_manager().reset_all()
    return {"status": "all settings reset to defaults"}


@router.get("/export/all")
async def export_settings(current_user: User = Depends(get_current_active_user)):
    """Export all settings as a dict."""
    return get_settings_manager().export_settings()


@router.post("/import")
async def import_settings(
    settings: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Import settings from a dict."""
    count = get_settings_manager().import_settings(settings)
    return {"imported": count}
