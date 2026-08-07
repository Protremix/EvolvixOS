"""API for Faucet — Phase 46."""

from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.faucet import get_faucet_service

router = APIRouter(prefix="/faucet", tags=["faucet"])


class ClaimRequest(BaseModel):
    address: str
    captcha_id: str = ""
    captcha_answer: str = ""


class UpdateConfigRequest(BaseModel):
    drip_amount: Optional[float] = None
    cooldown_hours: Optional[int] = None
    ip_cooldown_hours: Optional[int] = None
    daily_limit: Optional[float] = None
    max_pending: Optional[int] = None
    min_balance: Optional[float] = None
    captcha_required: Optional[bool] = None
    whitelist_enabled: Optional[bool] = None


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().get_dashboard()

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().get_stats()

@router.get("/config")
async def get_config(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().get_config()

@router.patch("/config")
async def update_config(req: UpdateConfigRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    return get_faucet_service().update_config(**kwargs)

# === Claim ===

@router.post("/claim")
async def claim_tokens(req: ClaimRequest, request: Request,
                       current_user: User = Depends(get_current_active_user)):
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")
    return get_faucet_service().request_tokens(
        req.address, ip, ua, req.captcha_id, req.captcha_answer
    )

@router.post("/captcha")
async def generate_captcha(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().generate_captcha()

@router.post("/captcha/verify")
async def verify_captcha(captcha_id: str, answer: str,
                          current_user: User = Depends(get_current_active_user)):
    return {"verified": get_faucet_service().verify_captcha(captcha_id, answer)}

# === Requests ===

@router.get("/requests")
async def list_requests(address: Optional[str] = None, status: Optional[str] = None,
                          limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_faucet_service().list_requests(address, status, limit)]

@router.get("/requests/{request_id}")
async def get_request(request_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_faucet_service().get_request(request_id)
    return r.to_dict() if r else {"error": "Request not found"}

@router.get("/address/{address}")
async def get_address_info(address: str, current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().get_address_info(address)

# === Admin ===

@router.post("/pause")
async def pause_faucet(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().pause()

@router.post("/resume")
async def resume_faucet(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().resume()

@router.post("/refill")
async def refill_faucet(amount: float, current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().refill(amount)

# === Whitelist ===

@router.post("/whitelist/{address}")
async def add_whitelist(address: str, current_user: User = Depends(get_current_active_user)):
    return {"added": get_faucet_service().add_to_whitelist(address)}

@router.delete("/whitelist/{address}")
async def remove_whitelist(address: str, current_user: User = Depends(get_current_active_user)):
    get_faucet_service().remove_from_whitelist(address)
    return {"removed": True}

@router.get("/whitelist")
async def get_whitelist(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().get_whitelist()

# === Blacklist ===

@router.post("/blacklist/{address}")
async def add_blacklist(address: str, current_user: User = Depends(get_current_active_user)):
    return {"added": get_faucet_service().add_to_blacklist(address)}

@router.delete("/blacklist/{address}")
async def remove_blacklist(address: str, current_user: User = Depends(get_current_active_user)):
    get_faucet_service().remove_from_blacklist(address)
    return {"removed": True}

@router.get("/blacklist")
async def get_blacklist(current_user: User = Depends(get_current_active_user)):
    return get_faucet_service().get_blacklist()

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 300, current_user: User = Depends(get_current_active_user)):
    get_faucet_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_faucet_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_faucet_service().is_monitoring()}
