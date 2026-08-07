"""API for Local Monitoring — Phase 28."""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.services.local_monitor import get_local_monitor

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/health")
async def get_health():
    """Get health of all services (unauthenticated for load balancers)."""
    return get_local_monitor().get_all_health()

@router.get("/services")
async def get_services(current_user=Depends(get_current_active_user)):
    """Get service health list."""
    return get_local_monitor().get_all_health()

@router.get("/system")
async def get_system(current_user=Depends(get_current_active_user)):
    """Get system metrics."""
    return get_local_monitor().get_system_metrics()

@router.get("/metrics/{metric_name}")
async def get_metrics(metric_name: str, limit: int = 100, current_user=Depends(get_current_active_user)):
    """Get historical metric data."""
    return get_local_monitor().get_metrics_history(metric_name, limit)

@router.post("/check")
async def run_check(current_user=Depends(get_current_active_user)):
    """Run an immediate health check."""
    return get_local_monitor().check_all()

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 30, current_user=Depends(get_current_active_user)):
    """Start background monitoring."""
    get_local_monitor().start_monitoring(interval)
    return {"monitoring": True, "interval": interval}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user=Depends(get_current_active_user)):
    """Stop background monitoring."""
    get_local_monitor().stop_monitoring()
    return {"monitoring": False}
