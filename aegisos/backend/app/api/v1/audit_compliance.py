"""API for Audit & Compliance — Phase 44."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.audit_compliance import get_audit_compliance_service

router = APIRouter(prefix="/audit", tags=["audit-compliance"])


class RecordAuditRequest(BaseModel):
    category: str
    action: str
    actor: str
    resource: str
    details: str = ""
    severity: str = "info"
    ip_address: str = ""
    user_agent: str = ""
    result: str = "success"
    metadata: dict = {}
    correlation_id: str = ""


class CreatePolicyRequest(BaseModel):
    name: str
    description: str
    framework: str
    rule_type: str
    metadata: dict = {}


class CreateRiskRequest(BaseModel):
    title: str
    description: str
    probability: float = 0.5
    impact: float = 0.5
    mitigation: str = ""
    owner: str = ""


class UpdateCheckRequest(BaseModel):
    status: Optional[str] = None
    remediation: Optional[str] = None
    risk_level: Optional[str] = None


class UpdatePolicyRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    enforced: Optional[bool] = None


class UpdateRiskRequest(BaseModel):
    probability: Optional[float] = None
    impact: Optional[float] = None
    mitigation: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None


class GenerateReportRequest(BaseModel):
    framework: str
    title: str
    period_days: int = 30


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().get_dashboard()

# === Audit ===

@router.post("/audit")
async def record_audit(req: RecordAuditRequest, current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().record_audit(
        req.category, req.action, req.actor, req.resource, req.details,
        req.severity, req.ip_address, req.user_agent, req.result, req.metadata, req.correlation_id,
    ).to_dict()

@router.get("/audit")
async def list_audit(category: Optional[str] = None, actor: Optional[str] = None,
                      severity: Optional[str] = None, result: Optional[str] = None,
                      start_date: Optional[str] = None, end_date: Optional[str] = None,
                      limit: int = 50, sort_by: str = "timestamp",
                      current_user: User = Depends(get_current_active_user)):
    return [e.to_dict() for e in get_audit_compliance_service().list_audit(
        category, actor, severity, result, start_date, end_date, limit, sort_by)]

@router.get("/audit/{audit_id}")
async def get_audit(audit_id: str, current_user: User = Depends(get_current_active_user)):
    e = get_audit_compliance_service().get_audit(audit_id)
    return e.to_dict() if e else {"error": "Audit entry not found"}

@router.get("/audit/stats")
async def audit_stats(hours: int = 24, current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().get_audit_stats(hours)

# === Compliance Checks ===

@router.get("/checks")
async def list_checks(framework: Optional[str] = None, status: Optional[str] = None,
                       current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_audit_compliance_service().list_compliance_checks(framework, status)]

@router.get("/checks/{check_id}")
async def get_check(check_id: str, current_user: User = Depends(get_current_active_user)):
    c = get_audit_compliance_service().get_compliance_check(check_id)
    return c.to_dict() if c else {"error": "Check not found"}

@router.patch("/checks/{check_id}")
async def update_check(check_id: str, req: UpdateCheckRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    c = get_audit_compliance_service().update_compliance_check(check_id, **kwargs)
    return c.to_dict() if c else {"error": "Check not found"}

@router.post("/checks/{check_id}/run")
async def run_check(check_id: str, current_user: User = Depends(get_current_active_user)):
    c = get_audit_compliance_service().run_compliance_check(check_id)
    return c.to_dict() if c else {"error": "Check not found"}

@router.post("/checks/run-all")
async def run_all_checks(framework: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().run_all_checks(framework)

# === Reports ===

@router.post("/reports")
async def generate_report(req: GenerateReportRequest, current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().generate_report(req.framework, req.title, req.period_days).to_dict()

@router.get("/reports")
async def list_reports(framework: Optional[str] = None, limit: int = 50,
                        current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_audit_compliance_service().list_reports(framework, limit)]

@router.get("/reports/{report_id}")
async def get_report(report_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_audit_compliance_service().get_report(report_id)
    return r.to_dict() if r else {"error": "Report not found"}

# === Policies ===

@router.get("/policies")
async def list_policies(framework: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_audit_compliance_service().list_policies(framework)]

@router.post("/policies")
async def create_policy(req: CreatePolicyRequest, current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().create_policy(
        req.name, req.description, req.framework, req.rule_type, req.metadata
    ).to_dict()

@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_audit_compliance_service().get_policy(policy_id)
    return p.to_dict() if p else {"error": "Policy not found"}

@router.patch("/policies/{policy_id}")
async def update_policy(policy_id: str, req: UpdatePolicyRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    p = get_audit_compliance_service().update_policy(policy_id, **kwargs)
    return p.to_dict() if p else {"error": "Policy not found"}

@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deleted": get_audit_compliance_service().delete_policy(policy_id)}

@router.post("/policies/{policy_id}/violation")
async def record_violation(policy_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_audit_compliance_service().record_policy_violation(policy_id)
    return p.to_dict() if p else {"error": "Policy not found"}

# === Risks ===

@router.get("/risks")
async def list_risks(status: Optional[str] = None, risk_level: Optional[str] = None,
                      current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_audit_compliance_service().list_risks(status, risk_level)]

@router.post("/risks")
async def create_risk(req: CreateRiskRequest, current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().create_risk(
        req.title, req.description, req.probability, req.impact, req.mitigation, req.owner
    ).to_dict()

@router.get("/risks/{risk_id}")
async def get_risk(risk_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_audit_compliance_service().get_risk(risk_id)
    return r.to_dict() if r else {"error": "Risk not found"}

@router.patch("/risks/{risk_id}")
async def update_risk(risk_id: str, req: UpdateRiskRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    r = get_audit_compliance_service().update_risk(risk_id, **kwargs)
    return r.to_dict() if r else {"error": "Risk not found"}

@router.delete("/risks/{risk_id}")
async def delete_risk(risk_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deleted": get_audit_compliance_service().delete_risk(risk_id)}

# === Frameworks ===

@router.get("/frameworks")
async def list_frameworks(current_user: User = Depends(get_current_active_user)):
    return get_audit_compliance_service().list_frameworks()

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 300, current_user: User = Depends(get_current_active_user)):
    get_audit_compliance_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_audit_compliance_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_audit_compliance_service().is_monitoring()}
