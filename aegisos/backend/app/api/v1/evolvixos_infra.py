"""API for EvolvixOS Infrastructure — Separate Domain."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.evolvixos_infra import get_evolvixos_infra_service, ServiceStatus

router = APIRouter(prefix="/evolvixos-infra", tags=["evolvixos-infra"])


class UpdateStatusRequest(BaseModel):
    status: str


class SetIPRequest(BaseModel):
    ip: str


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_evolvixos_infra_service().get_dashboard()

@router.get("/components")
async def list_components(current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_evolvixos_infra_service().list_components()]

@router.get("/components/{cid}")
async def get_component(cid: str, current_user: User = Depends(get_current_active_user)):
    c = get_evolvixos_infra_service().get_component(cid)
    return c.to_dict() if c else {"error": "Component not found"}

@router.patch("/components/{cid}/status")
async def update_component(cid: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    c = get_evolvixos_infra_service().update_component_status(cid, req.status)
    return c.to_dict() if c else {"error": "Component not found"}

@router.get("/dns")
async def list_dns(current_user: User = Depends(get_current_active_user)):
    return [d.to_dict() for d in get_evolvixos_infra_service().list_dns()]

@router.get("/steps")
async def list_steps(current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_evolvixos_infra_service().list_steps()]

@router.patch("/steps/{sid}/status")
async def update_step(sid: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    s = get_evolvixos_infra_service().update_step_status(sid, req.status)
    return s.to_dict() if s else {"error": "Step not found"}

@router.get("/scripts")
async def get_scripts(current_user: User = Depends(get_current_active_user)):
    return get_evolvixos_infra_service().get_deployment_scripts()

@router.post("/set-ip")
async def set_server_ip(req: SetIPRequest, current_user: User = Depends(get_current_active_user)):
    get_evolvixos_infra_service().set_server_ip(req.ip)
    return {"message": f"Server IP set to {req.ip}"}

@router.get("/progress")
async def get_progress(current_user: User = Depends(get_current_active_user)):
    return get_evolvixos_infra_service().get_progress()
