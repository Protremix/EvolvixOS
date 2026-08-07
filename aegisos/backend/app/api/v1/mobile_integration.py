"""API for Mobile Wallet EvolvixOS Integration — Phase 48."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.mobile_integration import get_mobile_integration_service

router = APIRouter(prefix="/mobile", tags=["mobile-integration"])


class RegisterSessionRequest(BaseModel):
    wallet_address: str
    device_id: str
    platform: str = "android"
    app_version: str = "2.5.3"
    push_token: str = ""
    language: str = "en"
    biometric: bool = False


class UpdateSessionRequest(BaseModel):
    app_version: Optional[str] = None
    push_token: Optional[str] = None
    battery_level: Optional[int] = None
    network_type: Optional[str] = None
    biometric_enabled: Optional[bool] = None
    pin_enabled: Optional[bool] = None
    language: Optional[str] = None


class SendNotificationRequest(BaseModel):
    title: str
    body: str
    feature: str = ""
    priority: str = "normal"
    action_url: str = ""


class SyncRequest(BaseModel):
    feature: str
    data_size: int = 0


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_mobile_integration_service().get_dashboard()

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_mobile_integration_service().get_stats()

@router.get("/app-config")
async def get_app_config(app_version: str = "2.5.3", current_user: User = Depends(get_current_active_user)):
    return get_mobile_integration_service().get_app_config(app_version)

# === Sessions ===

@router.post("/sessions")
async def register_session(req: RegisterSessionRequest, current_user: User = Depends(get_current_active_user)):
    return get_mobile_integration_service().register_session(
        req.wallet_address, req.device_id, req.platform,
        req.app_version, req.push_token, req.language, req.biometric,
    ).to_dict()

@router.get("/sessions")
async def list_sessions(platform: Optional[str] = None, limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_mobile_integration_service().list_sessions(platform, limit)]

@router.get("/sessions/{session_id}")
async def get_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_mobile_integration_service().get_session(session_id)
    return s.to_dict() if s else {"error": "Session not found"}

@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    s = get_mobile_integration_service().update_session(session_id, **kwargs)
    return s.to_dict() if s else {"error": "Session not found"}

@router.delete("/sessions/{session_id}")
async def deactivate_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deactivated": get_mobile_integration_service().deactivate_session(session_id)}

@router.get("/wallet/{wallet_address}/sessions")
async def wallet_sessions(wallet_address: str, current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_mobile_integration_service().get_wallet_sessions(wallet_address)]

# === Features ===

@router.get("/features")
async def list_features(app_version: str = "2.5.3", current_user: User = Depends(get_current_active_user)):
    return [f.to_dict() for f in get_mobile_integration_service().list_features(app_version)]

@router.get("/features/{key}")
async def get_feature(key: str, current_user: User = Depends(get_current_active_user)):
    f = get_mobile_integration_service().get_feature(key)
    return f.to_dict() if f else {"error": "Feature not found"}

@router.post("/sessions/{session_id}/features/{feature_key}")
async def toggle_feature(session_id: str, feature_key: str, enabled: bool,
                           current_user: User = Depends(get_current_active_user)):
    s = get_mobile_integration_service().toggle_feature(session_id, feature_key, enabled)
    return s.to_dict() if s else {"error": "Session not found"}

# === Quick Actions ===

@router.get("/quick-actions")
async def list_quick_actions(current_user: User = Depends(get_current_active_user)):
    return [a.to_dict() for a in get_mobile_integration_service().list_quick_actions()]

# === Sync ===

@router.post("/sessions/{session_id}/sync")
async def sync_feature(session_id: str, req: SyncRequest, current_user: User = Depends(get_current_active_user)):
    return get_mobile_integration_service().sync_feature(session_id, req.feature, req.data_size).to_dict()

@router.get("/sync/history")
async def sync_history(session_id: Optional[str] = None, feature: Optional[str] = None,
                        limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_mobile_integration_service().get_sync_history(session_id, feature, limit)]

# === Notifications ===

@router.post("/sessions/{session_id}/notifications")
async def send_notification(session_id: str, req: SendNotificationRequest,
                             current_user: User = Depends(get_current_active_user)):
    n = get_mobile_integration_service().send_notification(
        session_id, req.title, req.body, req.feature, req.priority, req.action_url
    )
    return n.to_dict() if n else {"error": "Session not found"}

@router.post("/wallet/{wallet_address}/notify")
async def broadcast_notification(wallet_address: str, req: SendNotificationRequest,
                                   current_user: User = Depends(get_current_active_user)):
    results = get_mobile_integration_service().broadcast_notification(
        wallet_address, req.title, req.body, req.feature, req.priority
    )
    return [n.to_dict() for n in results]

@router.get("/sessions/{session_id}/notifications")
async def get_notifications(session_id: str, unread_only: bool = False,
                              limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [n.to_dict() for n in get_mobile_integration_service().get_notifications(session_id, unread_only, limit)]

@router.post("/sessions/{session_id}/notifications/{notif_id}/read")
async def mark_read(session_id: str, notif_id: str, current_user: User = Depends(get_current_active_user)):
    return {"read": get_mobile_integration_service().mark_read(session_id, notif_id)}

@router.post("/sessions/{session_id}/notifications/read-all")
async def mark_all_read(session_id: str, current_user: User = Depends(get_current_active_user)):
    return {"read_count": get_mobile_integration_service().mark_all_read(session_id)}

# === Mobile Dashboard ===

@router.get("/sessions/{session_id}/dashboard")
async def mobile_dashboard(session_id: str, current_user: User = Depends(get_current_active_user)):
    return get_mobile_integration_service().get_mobile_dashboard(session_id)

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 120, current_user: User = Depends(get_current_active_user)):
    get_mobile_integration_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_mobile_integration_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_mobile_integration_service().is_monitoring()}
