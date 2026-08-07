"""API for Deployment Preparation — Phase 52."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.deployment_prep import get_deployment_prep_service, ScriptStatus

router = APIRouter(prefix="/deploy", tags=["deployment-prep"])


class UpdateStatusRequest(BaseModel):
    status: str


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_deployment_prep_service().get_dashboard()

# === Scripts ===

@router.get("/scripts")
async def list_scripts(type: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_deployment_prep_service().list_scripts(type)]

@router.get("/scripts/generate-all")
async def generate_all_scripts(current_user: User = Depends(get_current_active_user)):
    return get_deployment_prep_service().generate_all_scripts()

@router.get("/scripts/{script_id}")
async def get_script(script_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_deployment_prep_service().get_script(script_id)
    return s.to_dict() if s else {"error": "Script not found"}

@router.get("/scripts/filename/{filename}")
async def get_script_by_filename(filename: str, current_user: User = Depends(get_current_active_user)):
    s = get_deployment_prep_service().get_script_by_filename(filename)
    return s.to_dict() if s else {"error": "Script not found"}

@router.patch("/scripts/{script_id}/status")
async def update_script_status(script_id: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    s = get_deployment_prep_service().update_script_status(script_id, req.status)
    return s.to_dict() if s else {"error": "Script not found"}

# === DNS ===

@router.get("/dns")
async def list_dns_records(current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_deployment_prep_service().list_dns_records()]

@router.get("/dns/{record_id}")
async def get_dns_record(record_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_deployment_prep_service().get_dns_record(record_id)
    return r.to_dict() if r else {"error": "DNS record not found"}

# === SSL ===

@router.get("/ssl")
async def list_ssl_configs(current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_deployment_prep_service().list_ssl_configs()]

@router.get("/ssl/{config_id}")
async def get_ssl_config(config_id: str, current_user: User = Depends(get_current_active_user)):
    c = get_deployment_prep_service().get_ssl_config(config_id)
    return c.to_dict() if c else {"error": "SSL config not found"}

# === Steps ===

@router.get("/steps")
async def list_steps(current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_deployment_prep_service().list_steps()]

@router.get("/steps/{step_id}")
async def get_step(step_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_deployment_prep_service().get_step(step_id)
    return s.to_dict() if s else {"error": "Step not found"}

@router.patch("/steps/{step_id}/status")
async def update_step_status(step_id: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    s = get_deployment_prep_service().update_step_status(step_id, req.status)
    return s.to_dict() if s else {"error": "Step not found"}

@router.get("/progress")
async def deployment_progress(current_user: User = Depends(get_current_active_user)):
    return get_deployment_prep_service().get_deployment_progress()
