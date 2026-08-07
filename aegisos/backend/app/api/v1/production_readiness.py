"""API for Production Readiness — Phase 49."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.production_readiness import get_production_readiness_service

router = APIRouter(prefix="/readiness", tags=["production-readiness"])


class LoadTestRequest(BaseModel):
    endpoint: str
    method: str = "GET"
    concurrent_users: int = 10
    duration_seconds: int = 10


class UpdateCheckRequest(BaseModel):
    status: str
    details: str = ""


class AddFindingRequest(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    location: str = ""
    recommendation: str = ""
    cwe: str = ""


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().get_dashboard()

# === Security ===

@router.get("/security/scan")
async def run_security_scan(current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().run_security_scan()

@router.get("/findings")
async def list_findings(category: Optional[str] = None, severity: Optional[str] = None,
                         status: Optional[str] = None, limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [f.to_dict() for f in get_production_readiness_service().list_findings(category, severity, status, limit)]

@router.get("/findings/{finding_id}")
async def get_finding(finding_id: str, current_user: User = Depends(get_current_active_user)):
    f = get_production_readiness_service().get_finding(finding_id)
    return f.to_dict() if f else {"error": "Finding not found"}

@router.post("/findings")
async def add_finding(req: AddFindingRequest, current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().add_finding(
        req.category, req.severity, req.title, req.description,
        req.location, req.recommendation, req.cwe,
    ).to_dict()

@router.post("/findings/{finding_id}/fix")
async def fix_finding(finding_id: str, notes: str = "", current_user: User = Depends(get_current_active_user)):
    f = get_production_readiness_service().fix_finding(finding_id, notes)
    return f.to_dict() if f else {"error": "Finding not found"}

@router.post("/findings/{finding_id}/accept")
async def accept_finding(finding_id: str, current_user: User = Depends(get_current_active_user)):
    f = get_production_readiness_service().accept_finding(finding_id)
    return f.to_dict() if f else {"error": "Finding not found"}

# === Readiness Checks ===

@router.get("/checks")
async def list_checks(category: Optional[str] = None, status: Optional[str] = None,
                       current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_production_readiness_service().list_checks(category, status)]

@router.get("/checks/{check_id}")
async def get_check(check_id: str, current_user: User = Depends(get_current_active_user)):
    c = get_production_readiness_service().get_check(check_id)
    return c.to_dict() if c else {"error": "Check not found"}

@router.patch("/checks/{check_id}")
async def update_check(check_id: str, req: UpdateCheckRequest, current_user: User = Depends(get_current_active_user)):
    c = get_production_readiness_service().update_check(check_id, req.status, req.details)
    return c.to_dict() if c else {"error": "Check not found"}

@router.post("/checks/run-auto")
async def run_auto_checks(current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().run_auto_checks()

@router.get("/score")
async def readiness_score(current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().get_readiness_score()

# === Load Testing ===

@router.post("/load-test")
async def run_load_test(req: LoadTestRequest, current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().run_load_test(
        req.endpoint, req.method, req.concurrent_users, req.duration_seconds,
    ).to_dict()

@router.get("/load-tests")
async def list_load_tests(endpoint: Optional[str] = None, limit: int = 50,
                           current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_production_readiness_service().list_load_tests(endpoint, limit)]

@router.get("/load-tests/{test_id}")
async def get_load_test(test_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_production_readiness_service().get_load_test(test_id)
    return t.to_dict() if t else {"error": "Load test not found"}

@router.get("/performance/summary")
async def performance_summary(current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().get_performance_summary()

# === Deployment Checklist ===

@router.get("/checklist")
async def list_checklist(category: Optional[str] = None, completed: Optional[bool] = None,
                          current_user: User = Depends(get_current_active_user)):
    return [i.to_dict() for i in get_production_readiness_service().list_checklist(category, completed)]

@router.post("/checklist/{item_id}/complete")
async def complete_item(item_id: str, notes: str = "", current_user: User = Depends(get_current_active_user)):
    i = get_production_readiness_service().complete_checklist_item(item_id, notes)
    return i.to_dict() if i else {"error": "Item not found"}

@router.post("/checklist/{item_id}/reset")
async def reset_item(item_id: str, current_user: User = Depends(get_current_active_user)):
    i = get_production_readiness_service().reset_checklist_item(item_id)
    return i.to_dict() if i else {"error": "Item not found"}

@router.get("/checklist/progress")
async def checklist_progress(current_user: User = Depends(get_current_active_user)):
    return get_production_readiness_service().get_checklist_progress()

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 300, current_user: User = Depends(get_current_active_user)):
    get_production_readiness_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_production_readiness_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_production_readiness_service().is_monitoring()}
