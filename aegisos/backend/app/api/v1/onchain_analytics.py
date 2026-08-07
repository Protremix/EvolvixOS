"""API for On-chain Analytics — Phase 34."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.onchain_analytics import get_onchain_analytics_service, MetricType

router = APIRouter(prefix="/onchain", tags=["onchain-analytics"])


class CreateAlertRequest(BaseModel):
    metric_type: str
    condition: str  # "gt", "lt", "eq"
    threshold: float
    message: str = ""


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    """Get complete analytics dashboard."""
    return get_onchain_analytics_service().get_dashboard()

@router.get("/metrics")
async def get_metrics(current_user: User = Depends(get_current_active_user)):
    """Get latest values of all metrics."""
    return get_onchain_analytics_service().get_all_metrics()

@router.get("/metrics/{metric_type}/history")
async def get_metric_history(metric_type: str, limit: int = 100, current_user: User = Depends(get_current_active_user)):
    """Get historical values for a specific metric."""
    return [m.to_dict() for m in get_onchain_analytics_service().get_metric_history(metric_type, limit)]

@router.get("/blocks/latest")
async def get_latest_block(current_user: User = Depends(get_current_active_user)):
    """Get latest block."""
    block = get_onchain_analytics_service().get_latest_block()
    return block.to_dict() if block else {"error": "No blocks yet"}

@router.get("/blocks/recent")
async def get_recent_blocks(limit: int = 20, current_user: User = Depends(get_current_active_user)):
    """Get recent blocks."""
    return [b.to_dict() for b in get_onchain_analytics_service().get_recent_blocks(limit)]

@router.post("/collect")
async def collect_metrics(current_user: User = Depends(get_current_active_user)):
    """Manually trigger metric collection."""
    return get_onchain_analytics_service().collect_metrics()

@router.get("/tps/trend")
async def get_tps_trend(window: int = 50, current_user: User = Depends(get_current_active_user)):
    """Get TPS trend analysis."""
    return get_onchain_analytics_service().get_tps_trend(window)

@router.get("/gas/analytics")
async def get_gas_analytics(window: int = 50, current_user: User = Depends(get_current_active_user)):
    """Get gas usage analytics."""
    return get_onchain_analytics_service().get_gas_analytics(window)

@router.get("/blocks/analytics")
async def get_block_analytics(window: int = 50, current_user: User = Depends(get_current_active_user)):
    """Get block statistics."""
    return get_onchain_analytics_service().get_block_analytics(window)

@router.post("/alerts")
async def create_alert(req: CreateAlertRequest, current_user: User = Depends(get_current_active_user)):
    """Create an analytics alert."""
    return get_onchain_analytics_service().create_alert(
        req.metric_type, req.condition, req.threshold, req.message
    ).to_dict()

@router.get("/alerts")
async def list_alerts(triggered: Optional[bool] = None, current_user: User = Depends(get_current_active_user)):
    """List alerts."""
    return [a.to_dict() for a in get_onchain_analytics_service().list_alerts(triggered)]

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, current_user: User = Depends(get_current_active_user)):
    """Delete an alert."""
    return {"deleted": get_onchain_analytics_service().delete_alert(alert_id)}

@router.post("/alerts/{alert_id}/reset")
async def reset_alert(alert_id: str, current_user: User = Depends(get_current_active_user)):
    """Reset a triggered alert."""
    return {"reset": get_onchain_analytics_service().reset_alert(alert_id)}

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 6, current_user: User = Depends(get_current_active_user)):
    """Start background monitoring."""
    get_onchain_analytics_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    """Stop background monitoring."""
    get_onchain_analytics_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    """Get monitoring status."""
    return {"monitoring": get_onchain_analytics_service().is_monitoring()}

@router.get("/metric-types")
async def get_metric_types():
    """List all available metric types."""
    return [{"value": m.value, "name": m.value.replace("_", " ").title()} for m in MetricType]

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get analytics service statistics."""
    return get_onchain_analytics_service().get_stats()
