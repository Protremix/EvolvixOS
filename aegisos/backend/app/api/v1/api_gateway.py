"""API for API Gateway — Phase 43."""

from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.api_gateway import get_api_gateway_service

router = APIRouter(prefix="/gateway", tags=["api-gateway"])


class CreateKeyRequest(BaseModel):
    name: str
    scopes: list = ["*"]
    rate_limit: int = 1000
    expires_days: int = 0
    metadata: dict = {}


class CreateRouteRequest(BaseModel):
    path: str
    target_service: str
    target_path: str = ""
    methods: list = ["GET", "POST", "PUT", "DELETE"]
    cache_ttl: int = 0
    auth_required: bool = True
    allowed_scopes: list = []


class UpdateKeyRequest(BaseModel):
    name: Optional[str] = None
    scopes: Optional[list] = None
    rate_limit: Optional[int] = None


class UpdateRouteRequest(BaseModel):
    methods: Optional[list] = None
    cache_ttl: Optional[int] = None
    auth_required: Optional[bool] = None
    allowed_scopes: Optional[list] = None
    status: Optional[str] = None


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().get_dashboard()

# === API Keys ===

@router.get("/keys")
async def list_keys(status: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [k.to_dict() for k in get_api_gateway_service().list_keys(status)]

@router.post("/keys")
async def create_key(req: CreateKeyRequest, current_user: User = Depends(get_current_active_user)):
    key, plaintext = get_api_gateway_service().create_key(
        req.name, req.scopes, req.rate_limit, req.expires_days, req.metadata
    )
    return {"key_id": key.key_id, "api_key": plaintext, "info": key.to_dict()}

@router.get("/keys/{key_id}")
async def get_key(key_id: str, current_user: User = Depends(get_current_active_user)):
    k = get_api_gateway_service().get_key(key_id)
    return k.to_dict() if k else {"error": "Key not found"}

@router.patch("/keys/{key_id}")
async def update_key(key_id: str, req: UpdateKeyRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    k = get_api_gateway_service().update_key(key_id, **kwargs)
    return k.to_dict() if k else {"error": "Key not found"}

@router.delete("/keys/{key_id}")
async def revoke_key(key_id: str, current_user: User = Depends(get_current_active_user)):
    return {"revoked": get_api_gateway_service().revoke_key(key_id)}

@router.post("/keys/validate")
async def validate_key(api_key: str, current_user: User = Depends(get_current_active_user)):
    k = get_api_gateway_service().validate_key(api_key)
    return k.to_dict() if k else {"error": "Invalid key"}

# === Routes ===

@router.get("/routes")
async def list_routes(status: Optional[str] = None, target_service: Optional[str] = None,
                       current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_api_gateway_service().list_routes(status, target_service)]

@router.post("/routes")
async def create_route(req: CreateRouteRequest, current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().create_route(
        req.path, req.target_service, req.target_path, req.methods,
        req.cache_ttl, req.auth_required, req.allowed_scopes,
    ).to_dict()

@router.get("/routes/{route_id}")
async def get_route(route_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_api_gateway_service().get_route(route_id)
    return r.to_dict() if r else {"error": "Route not found"}

@router.patch("/routes/{route_id}")
async def update_route(route_id: str, req: UpdateRouteRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    r = get_api_gateway_service().update_route(route_id, **kwargs)
    return r.to_dict() if r else {"error": "Route not found"}

@router.delete("/routes/{route_id}")
async def delete_route(route_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deleted": get_api_gateway_service().delete_route(route_id)}

@router.get("/routes/match")
async def match_route(path: str, method: str = "GET", current_user: User = Depends(get_current_active_user)):
    r = get_api_gateway_service().match_route(path, method)
    return r.to_dict() if r else {"error": "No matching route"}

# === Rate Limiting ===

@router.get("/rate-limit/check/{key_id}")
async def check_rate_limit(key_id: str, current_user: User = Depends(get_current_active_user)):
    allowed, remaining = get_api_gateway_service().check_rate_limit(key_id)
    return {"allowed": allowed, "remaining": remaining}

# === Cache ===

@router.get("/cache/stats")
async def cache_stats(current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().get_cache_stats()

@router.delete("/cache")
async def clear_cache(route_id: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return {"cleared": get_api_gateway_service().clear_cache(route_id)}

# === Usage ===

@router.get("/usage")
async def list_usage(key_id: Optional[str] = None, route_id: Optional[str] = None,
                      limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().list_usage(key_id, route_id, limit)

@router.get("/usage/stats")
async def usage_stats(hours: int = 24, current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().get_usage_stats(hours)

# === Circuit Breaker ===

@router.get("/circuits")
async def list_circuits(current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().list_circuits()

@router.get("/circuits/{route_id}")
async def get_circuit(route_id: str, current_user: User = Depends(get_current_active_user)):
    return {"route_id": route_id, "state": get_api_gateway_service().get_circuit_state(route_id)}

@router.post("/circuits/{route_id}/reset")
async def reset_circuit(route_id: str, current_user: User = Depends(get_current_active_user)):
    return {"reset": get_api_gateway_service().reset_circuit(route_id)}

# === Health ===

@router.get("/health")
async def list_service_health(current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().list_service_health()

@router.get("/health/{service}")
async def check_service_health(service: str, current_user: User = Depends(get_current_active_user)):
    return get_api_gateway_service().check_service_health(service)

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 60, current_user: User = Depends(get_current_active_user)):
    get_api_gateway_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_api_gateway_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_api_gateway_service().is_monitoring()}
