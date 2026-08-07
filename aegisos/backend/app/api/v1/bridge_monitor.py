"""API for Bridge Monitoring — Phase 38."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.bridge_monitor import get_bridge_monitor_service

router = APIRouter(prefix="/bridge", tags=["bridge-monitor"])


class CreateTransferRequest(BaseModel):
    direction: str
    source_chain: str
    target_chain: str
    sender: str
    recipient: str
    amount: float
    token: str = "VRS"
    tx_hash_source: str = ""
    block_height_source: int = 0
    fee: float = 0.0


class ValidateTransferRequest(BaseModel):
    relayer_id: str


class RegisterRelayerRequest(BaseModel):
    address: str
    name: str


class CreateAlertRequest(BaseModel):
    alert_type: str
    severity: str
    message: str
    threshold: float = 0.0


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_bridge_monitor_service().get_dashboard()

@router.get("/health")
async def get_health(current_user: User = Depends(get_current_active_user)):
    return get_bridge_monitor_service().get_bridge_health()

# === Transfers ===

@router.post("/transfers")
async def create_transfer(req: CreateTransferRequest, current_user: User = Depends(get_current_active_user)):
    return get_bridge_monitor_service().create_transfer(
        req.direction, req.source_chain, req.target_chain,
        req.sender, req.recipient, req.amount, req.token,
        req.tx_hash_source, req.block_height_source, req.fee,
    ).to_dict()

@router.get("/transfers")
async def list_transfers(status: Optional[str] = None, direction: Optional[str] = None,
                         source_chain: Optional[str] = None, target_chain: Optional[str] = None,
                         limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_bridge_monitor_service().list_transfers(status, direction, source_chain, target_chain, limit)]

@router.get("/transfers/{transfer_id}")
async def get_transfer(transfer_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_bridge_monitor_service().get_transfer(transfer_id)
    return t.to_dict() if t else {"error": "Transfer not found"}

@router.post("/transfers/{transfer_id}/validate")
async def validate_transfer(transfer_id: str, req: ValidateTransferRequest, current_user: User = Depends(get_current_active_user)):
    t = get_bridge_monitor_service().validate_transfer(transfer_id, req.relayer_id)
    return t.to_dict() if t else {"error": "Cannot validate transfer"}

@router.post("/transfers/{transfer_id}/execute")
async def execute_transfer(transfer_id: str, tx_hash_target: str = "", block_height_target: int = 0,
                           current_user: User = Depends(get_current_active_user)):
    t = get_bridge_monitor_service().execute_transfer(transfer_id, tx_hash_target, block_height_target)
    return t.to_dict() if t else {"error": "Cannot execute transfer"}

@router.post("/transfers/{transfer_id}/fail")
async def fail_transfer(transfer_id: str, error: str = "", current_user: User = Depends(get_current_active_user)):
    t = get_bridge_monitor_service().fail_transfer(transfer_id, error)
    return t.to_dict() if t else {"error": "Transfer not found"}

@router.post("/transfers/{transfer_id}/refund")
async def refund_transfer(transfer_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_bridge_monitor_service().refund_transfer(transfer_id)
    return t.to_dict() if t else {"error": "Cannot refund transfer"}

@router.get("/transfers/stats")
async def transfer_stats(current_user: User = Depends(get_current_active_user)):
    return get_bridge_monitor_service().get_transfer_stats()

# === Relayers ===

@router.post("/relayers")
async def register_relayer(req: RegisterRelayerRequest, current_user: User = Depends(get_current_active_user)):
    return get_bridge_monitor_service().register_relayer(req.address, req.name).to_dict()

@router.get("/relayers")
async def list_relayers(active_only: bool = True, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_bridge_monitor_service().list_relayers(active_only)]

@router.get("/relayers/{relayer_id}")
async def get_relayer(relayer_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_bridge_monitor_service().get_relayer(relayer_id)
    return r.to_dict() if r else {"error": "Relayer not found"}

@router.post("/relayers/{relayer_id}/activate")
async def activate_relayer(relayer_id: str, current_user: User = Depends(get_current_active_user)):
    return {"activated": get_bridge_monitor_service().activate_relayer(relayer_id)}

@router.delete("/relayers/{relayer_id}")
async def remove_relayer(relayer_id: str, current_user: User = Depends(get_current_active_user)):
    return {"removed": get_bridge_monitor_service().remove_relayer(relayer_id)}

# === Alerts ===

@router.post("/alerts")
async def create_alert(req: CreateAlertRequest, current_user: User = Depends(get_current_active_user)):
    return get_bridge_monitor_service().create_alert(req.alert_type, req.severity, req.message, req.threshold).to_dict()

@router.get("/alerts")
async def list_alerts(triggered: Optional[bool] = None, current_user: User = Depends(get_current_active_user)):
    return [a.to_dict() for a in get_bridge_monitor_service().list_alerts(triggered)]

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deleted": get_bridge_monitor_service().delete_alert(alert_id)}

@router.post("/alerts/{alert_id}/reset")
async def reset_alert(alert_id: str, current_user: User = Depends(get_current_active_user)):
    return {"reset": get_bridge_monitor_service().reset_alert(alert_id)}

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 10, current_user: User = Depends(get_current_active_user)):
    get_bridge_monitor_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_bridge_monitor_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_bridge_monitor_service().is_monitoring()}
