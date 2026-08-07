"""API for Cross-Chain Analytics — Phase 42."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.cross_chain_analytics import get_cross_chain_analytics_service

router = APIRouter(prefix="/cross-chain", tags=["cross-chain-analytics"])


class RecordTransferRequest(BaseModel):
    source_chain: str
    target_chain: str
    token: str
    amount: float
    sender: str
    recipient: str
    bridge_protocol: str = "verdis-bridge"
    status: str = "confirmed"
    tx_hash_source: str = ""
    tx_hash_target: str = ""
    gas_paid: float = 0.0
    duration_seconds: int = 0
    block_number: int = 0
    metadata: dict = {}


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().get_dashboard()

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().get_stats()

# === Transfers ===

@router.post("/transfers")
async def record_transfer(req: RecordTransferRequest, current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().record_transfer(
        req.source_chain, req.target_chain, req.token, req.amount,
        req.sender, req.recipient, req.bridge_protocol, req.status,
        req.tx_hash_source, req.tx_hash_target, req.gas_paid,
        req.duration_seconds, req.block_number, req.metadata,
    ).to_dict()

@router.get("/transfers")
async def list_transfers(source_chain: Optional[str] = None, target_chain: Optional[str] = None,
                          token: Optional[str] = None, status: Optional[str] = None,
                          bridge_protocol: Optional[str] = None,
                          min_amount: Optional[float] = None, max_amount: Optional[float] = None,
                          limit: int = 50, sort_by: str = "timestamp",
                          current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_cross_chain_analytics_service().list_transfers(
        source_chain, target_chain, token, status, bridge_protocol,
        min_amount, max_amount, limit, sort_by,
    )]

@router.get("/transfers/{transfer_id}")
async def get_transfer(transfer_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_cross_chain_analytics_service().get_transfer(transfer_id)
    return t.to_dict() if t else {"error": "Transfer not found"}

# === Chain Metrics ===

@router.get("/chains")
async def list_chains(current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().list_chains()

@router.get("/chains/metrics")
async def list_chain_metrics(current_user: User = Depends(get_current_active_user)):
    return [m.to_dict() for m in get_cross_chain_analytics_service().list_chain_metrics()]

@router.get("/chains/{chain}/metrics")
async def get_chain_metrics(chain: str, current_user: User = Depends(get_current_active_user)):
    m = get_cross_chain_analytics_service().get_chain_metrics(chain)
    return m.to_dict() if m else {"error": "Chain not found"}

@router.get("/chains/compare")
async def compare_chains(chains: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    chain_list = chains.split(",") if chains else None
    return get_cross_chain_analytics_service().compare_chains(chain_list)

# === Corridors ===

@router.get("/corridors")
async def list_corridors(sort_by: str = "total_volume", limit: int = 50,
                          current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_cross_chain_analytics_service().list_corridors(sort_by, limit)]

@router.get("/corridors/{source}/{target}")
async def get_corridor(source: str, target: str, current_user: User = Depends(get_current_active_user)):
    c = get_cross_chain_analytics_service().get_corridor(source, target)
    return c.to_dict() if c else {"error": "Corridor not found"}

# === Flow Analysis ===

@router.get("/flow")
async def get_flow(hours: int = 24, current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().get_flow_analysis(hours)

# === Trends ===

@router.get("/trends/volume")
async def get_volume_trend(days: int = 7, current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().get_volume_trend(days)

# === Token Distribution ===

@router.get("/tokens/distribution")
async def get_token_distribution(current_user: User = Depends(get_current_active_user)):
    return get_cross_chain_analytics_service().get_token_distribution()

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 60, current_user: User = Depends(get_current_active_user)):
    get_cross_chain_analytics_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_cross_chain_analytics_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_cross_chain_analytics_service().is_monitoring()}
