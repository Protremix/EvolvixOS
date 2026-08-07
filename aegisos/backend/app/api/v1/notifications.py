"""API for Notification Center — Phase 40."""

from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.notifications import get_notification_service, NotificationType, NotificationSeverity

router = APIRouter(prefix="/notifications", tags=["notifications"])


class CreateNotificationRequest(BaseModel):
    user_address: str
    type: str
    severity: str
    title: str
    message: str
    action_url: str = ""
    action_label: str = ""
    metadata: dict = {}
    expires_hours: int = 0


class BroadcastRequest(BaseModel):
    type: str
    severity: str
    title: str
    message: str
    action_url: str = ""
    action_label: str = ""
    metadata: dict = {}


class UpdatePreferencesRequest(BaseModel):
    enabled: Optional[bool] = None
    channels: Optional[dict] = None
    type_filters: Optional[dict] = None
    min_severity: Optional[str] = None


# === Static routes FIRST (before parameterized) ===

@router.get("/dashboard")
async def get_dashboard(user_address: str = "0xverdis", current_user: User = Depends(get_current_active_user)):
    return get_notification_service().get_dashboard(user_address)

@router.get("/")
async def list_notifications(user_address: str = "0xverdis", unread_only: bool = False,
                              type: Optional[str] = None, severity: Optional[str] = None,
                              limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [n.to_dict() for n in get_notification_service().list_notifications(user_address, unread_only, type, severity, limit)]

@router.get("/unread/count")
async def get_unread_count(user_address: str = "0xverdis", current_user: User = Depends(get_current_active_user)):
    return {"count": get_notification_service().get_unread_count(user_address)}

@router.get("/stats")
async def get_stats(user_address: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return get_notification_service().get_stats(user_address)

@router.post("/")
async def create_notification(req: CreateNotificationRequest, current_user: User = Depends(get_current_active_user)):
    n = get_notification_service().create_notification(
        req.user_address, req.type, req.severity, req.title, req.message,
        req.action_url, req.action_label, req.metadata, req.expires_hours,
    )
    return n.to_dict() if n else {"error": "Notification filtered by preferences"}

@router.post("/broadcast")
async def broadcast(req: BroadcastRequest, current_user: User = Depends(get_current_active_user)):
    results = get_notification_service().broadcast_notification(
        req.type, req.severity, req.title, req.message,
        req.action_url, req.action_label, req.metadata,
    )
    return {"sent": len(results)}

@router.post("/read-all")
async def mark_all_read(user_address: str = "0xverdis", current_user: User = Depends(get_current_active_user)):
    return {"read": get_notification_service().mark_all_read(user_address)}

@router.delete("/clear/all")
async def clear_all(user_address: str = "0xverdis", current_user: User = Depends(get_current_active_user)):
    return {"cleared": get_notification_service().clear_all(user_address)}

@router.delete("/clear/read")
async def clear_read(user_address: str = "0xverdis", current_user: User = Depends(get_current_active_user)):
    return {"cleared": get_notification_service().clear_read(user_address)}

@router.get("/templates/list")
async def get_templates():
    return get_notification_service().get_templates()

@router.get("/types/list")
async def get_types():
    return [{"value": t.value, "name": t.value.title()} for t in NotificationType]

@router.get("/severities/list")
async def get_severities():
    return [{"value": s.value, "name": s.value.title()} for s in NotificationSeverity]

# === Preferences ===

@router.get("/preferences/{user_address}")
async def get_preferences(user_address: str, current_user: User = Depends(get_current_active_user)):
    return get_notification_service().get_preferences(user_address).to_dict()

@router.patch("/preferences/{user_address}")
async def update_preferences(user_address: str, req: UpdatePreferencesRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    return get_notification_service().update_preferences(user_address, **kwargs).to_dict()

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 60, current_user: User = Depends(get_current_active_user)):
    get_notification_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_notification_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_notification_service().is_monitoring()}

# === Parameterized routes LAST ===

@router.get("/{notif_id}")
async def get_notification(notif_id: str, current_user: User = Depends(get_current_active_user)):
    n = get_notification_service().get_notification(notif_id)
    return n.to_dict() if n else {"error": "Notification not found"}

@router.post("/{notif_id}/read")
async def mark_read(notif_id: str, current_user: User = Depends(get_current_active_user)):
    return {"read": get_notification_service().mark_read(notif_id)}

@router.delete("/{notif_id}")
async def delete_notification(notif_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deleted": get_notification_service().delete_notification(notif_id)}
