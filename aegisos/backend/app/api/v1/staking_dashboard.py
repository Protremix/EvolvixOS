"""API for Staking Dashboard — Phase 41."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.staking_dashboard import get_staking_dashboard_service

router = APIRouter(prefix="/staking", tags=["staking-dashboard"])


class StakeRequest(BaseModel):
    delegator: str
    validator_id: str
    amount: float
    auto_compound: bool = False


class CalculateRequest(BaseModel):
    amount: float
    apy: float
    days: int
    compound: bool = False


@router.get("/dashboard")
async def get_dashboard(delegator: str = "0xverdis", current_user: User = Depends(get_current_active_user)):
    return get_staking_dashboard_service().get_dashboard(delegator)

@router.get("/network/stats")
async def get_network_stats(current_user: User = Depends(get_current_active_user)):
    return get_staking_dashboard_service().get_network_stats()

# === Positions ===

@router.post("/stake")
async def stake(req: StakeRequest, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().stake(req.delegator, req.validator_id, req.amount, req.auto_compound)
    return p.to_dict() if p else {"error": "Cannot stake"}

@router.post("/positions/{position_id}/unstake")
async def unstake(position_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().unstake(position_id)
    return p.to_dict() if p else {"error": "Cannot unstake"}

@router.post("/positions/{position_id}/withdraw")
async def withdraw(position_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().withdraw(position_id)
    return p.to_dict() if p else {"error": "Cannot withdraw (still unbonding or not found)"}

@router.post("/positions/{position_id}/slash")
async def slash(position_id: str, percentage: float = 5.0, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().slash(position_id, percentage)
    return p.to_dict() if p else {"error": "Cannot slash"}

@router.post("/positions/{position_id}/auto-compound")
async def toggle_auto_compound(position_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().toggle_auto_compound(position_id)
    return p.to_dict() if p else {"error": "Position not found"}

@router.get("/positions")
async def list_positions(delegator: Optional[str] = None, validator_id: Optional[str] = None,
                         status: Optional[str] = None, limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_staking_dashboard_service().list_positions(delegator, validator_id, status, limit)]

@router.get("/positions/{position_id}")
async def get_position(position_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().get_position(position_id)
    return p.to_dict() if p else {"error": "Position not found"}

@router.get("/positions/{position_id}/rewards")
async def calculate_position_rewards(position_id: str, current_user: User = Depends(get_current_active_user)):
    return {"pending_rewards": get_staking_dashboard_service().calculate_rewards(position_id)}

# === Rewards ===

@router.post("/positions/{position_id}/claim")
async def claim_rewards(position_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_staking_dashboard_service().claim_rewards(position_id)
    return r.to_dict() if r else {"error": "No rewards to claim"}

@router.post("/positions/{position_id}/compound")
async def compound_rewards(position_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_staking_dashboard_service().compound_rewards(position_id)
    return p.to_dict() if p else {"error": "Cannot compound"}

@router.get("/rewards")
async def list_rewards(delegator: str, status: Optional[str] = None, limit: int = 50,
                       current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_staking_dashboard_service().list_rewards(delegator, status, limit)]

@router.get("/rewards/total")
async def get_total_rewards(delegator: str, current_user: User = Depends(get_current_active_user)):
    return get_staking_dashboard_service().get_total_rewards(delegator)

# === Validators ===

@router.get("/validators")
async def list_validators(active_only: bool = True, sort_by: str = "total_staked",
                           limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [v.to_dict() for v in get_staking_dashboard_service().list_validators(active_only, sort_by, limit)]

@router.get("/validators/{validator_id}")
async def get_validator(validator_id: str, current_user: User = Depends(get_current_active_user)):
    v = get_staking_dashboard_service().get_validator(validator_id)
    return v.to_dict() if v else {"error": "Validator not found"}

# === Calculator ===

@router.post("/calculate")
async def calculate_projection(req: CalculateRequest, current_user: User = Depends(get_current_active_user)):
    return get_staking_dashboard_service().calculate_staking_projection(req.amount, req.apy, req.days, req.compound)

# === History ===

@router.get("/history")
async def list_history(delegator: Optional[str] = None, event_type: Optional[str] = None,
                        limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [h.to_dict() for h in get_staking_dashboard_service().list_history(delegator, event_type, limit)]

# === User ===

@router.get("/user/{delegator}")
async def get_user_dashboard(delegator: str, current_user: User = Depends(get_current_active_user)):
    return get_staking_dashboard_service().get_user_dashboard(delegator)

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 30, current_user: User = Depends(get_current_active_user)):
    get_staking_dashboard_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_staking_dashboard_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_staking_dashboard_service().is_monitoring()}
