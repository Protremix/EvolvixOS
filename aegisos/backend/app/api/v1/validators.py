"""API for Validator Management — Phase 37."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.validators import get_validator_service, ValidatorStatus

router = APIRouter(prefix="/validators", tags=["validators"])


class RegisterValidatorRequest(BaseModel):
    address: str
    name: str
    energy_source: str = "unknown"
    green_score: float = 0.0
    carbon_offset: float = 0.0
    certified: bool = False
    total_stake: float = 0
    self_stake: float = 0
    commission_rate: float = 0.0
    website: str = ""
    description: str = ""


class DelegateRequest(BaseModel):
    delegator: str
    validator_id: str
    amount: float


class UpdateGreenScoreRequest(BaseModel):
    score: float
    energy_source: Optional[str] = None
    carbon_offset: Optional[float] = None


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_validator_service().get_dashboard()

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_validator_service().get_network_stats()

@router.post("/")
async def register_validator(req: RegisterValidatorRequest, current_user: User = Depends(get_current_active_user)):
    try:
        return get_validator_service().register_validator(
            req.address, req.name, req.energy_source, req.green_score,
            req.carbon_offset, req.certified, req.total_stake, req.self_stake,
            req.commission_rate, req.website, req.description,
        ).to_dict()
    except ValueError as e:
        return {"error": str(e)}

@router.get("/")
async def list_validators(status: Optional[str] = None, certified: Optional[bool] = None,
                           sort_by: str = "stake", limit: int = 101,
                           current_user: User = Depends(get_current_active_user)):
    return [v.to_dict() for v in get_validator_service().list_validators(status, certified, sort_by, limit)]

@router.get("/{validator_id}")
async def get_validator(validator_id: str, current_user: User = Depends(get_current_active_user)):
    v = get_validator_service().get_validator(validator_id)
    return v.to_dict() if v else {"error": "Validator not found"}

@router.get("/address/{address}")
async def get_by_address(address: str, current_user: User = Depends(get_current_active_user)):
    v = get_validator_service().get_validator_by_address(address)
    return v.to_dict() if v else {"error": "Validator not found"}

@router.get("/{validator_id}/grade")
async def get_grade(validator_id: str, current_user: User = Depends(get_current_active_user)):
    return {"grade": get_validator_service().get_validator_grade(validator_id)}

@router.post("/{validator_id}/pause")
async def pause_validator(validator_id: str, current_user: User = Depends(get_current_active_user)):
    return {"paused": get_validator_service().pause_validator(validator_id)}

@router.post("/{validator_id}/activate")
async def activate_validator(validator_id: str, current_user: User = Depends(get_current_active_user)):
    return {"activated": get_validator_service().activate_validator(validator_id)}

@router.post("/{validator_id}/slash")
async def slash_validator(validator_id: str, reason: str = "misbehavior", current_user: User = Depends(get_current_active_user)):
    return {"slashed": get_validator_service().slash_validator(validator_id, reason)}

@router.delete("/{validator_id}")
async def remove_validator(validator_id: str, current_user: User = Depends(get_current_active_user)):
    return {"removed": get_validator_service().remove_validator(validator_id)}

@router.patch("/{validator_id}/green-score")
async def update_green_score(validator_id: str, req: UpdateGreenScoreRequest, current_user: User = Depends(get_current_active_user)):
    v = get_validator_service().update_green_score(validator_id, req.score, req.energy_source, req.carbon_offset)
    return v.to_dict() if v else {"error": "Validator not found"}

@router.post("/{validator_id}/certify")
async def certify_validator(validator_id: str, current_user: User = Depends(get_current_active_user)):
    return {"certified": get_validator_service().certify_validator(validator_id)}

@router.post("/delegate")
async def delegate(req: DelegateRequest, current_user: User = Depends(get_current_active_user)):
    d = get_validator_service().delegate(req.delegator, req.validator_id, req.amount)
    return d.to_dict() if d else {"error": "Cannot delegate to this validator"}

@router.post("/undelegate/{delegation_id}")
async def undelegate(delegation_id: str, current_user: User = Depends(get_current_active_user)):
    return {"undelegated": get_validator_service().undelegate(delegation_id)}

@router.get("/delegations")
async def list_delegations(validator_id: Optional[str] = None, delegator: Optional[str] = None,
                           current_user: User = Depends(get_current_active_user)):
    return [d.to_dict() for d in get_validator_service().list_delegations(validator_id, delegator)]

@router.get("/{validator_id}/events")
async def get_events(validator_id: str, limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [e.to_dict() for e in get_validator_service().get_validator_events(validator_id, limit)]

@router.get("/events/recent")
async def get_recent_events(limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [e.to_dict() for e in get_validator_service().get_recent_events(limit)]

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 6, current_user: User = Depends(get_current_active_user)):
    get_validator_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_validator_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_validator_service().is_monitoring()}
