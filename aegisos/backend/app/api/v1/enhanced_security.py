"""API for Enhanced Security — Phase 54."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.enhanced_security import get_enhanced_security_service

router = APIRouter(prefix="/enhanced-security", tags=["enhanced-security"])


class ReportThreatRequest(BaseModel):
    type: str
    level: str
    source_ip: str = ""
    target: str = ""
    description: str = ""
    metadata: dict = {}


class UpdateThreatRequest(BaseModel):
    status: str
    mitigation: str = ""


class CreateProofRequest(BaseModel):
    prover: str
    claim: str
    secret: str = ""


class VerifyProofRequest(BaseModel):
    secret: str = ""


class SetupMFARequest(BaseModel):
    user_address: str
    method: str = "totp"


class VerifyMFARequest(BaseModel):
    user_address: str
    code: str


class UpdateAuditRequest(BaseModel):
    status: str
    recommendation: str = ""


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_enhanced_security_service().get_dashboard()

# === Audit ===

@router.get("/audit")
async def list_audit(category: Optional[str] = None, status: Optional[str] = None,
                      severity: Optional[str] = None, limit: int = 100,
                      current_user: User = Depends(get_current_active_user)):
    return [i.to_dict() for i in get_enhanced_security_service().list_audit_items(category, status, severity, limit)]

@router.get("/audit/summary")
async def audit_summary(current_user: User = Depends(get_current_active_user)):
    return get_enhanced_security_service().get_audit_summary()

@router.get("/audit/{item_id}")
async def get_audit_item(item_id: str, current_user: User = Depends(get_current_active_user)):
    i = get_enhanced_security_service().get_audit_item(item_id)
    return i.to_dict() if i else {"error": "Audit item not found"}

@router.patch("/audit/{item_id}")
async def update_audit_item(item_id: str, req: UpdateAuditRequest, current_user: User = Depends(get_current_active_user)):
    i = get_enhanced_security_service().update_audit_item(item_id, req.status, req.recommendation)
    return i.to_dict() if i else {"error": "Audit item not found"}

# === Threats ===

@router.get("/threats")
async def list_threats(level: Optional[str] = None, status: Optional[str] = None,
                         limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_enhanced_security_service().list_threats(level, status, limit)]

@router.get("/threats/stats")
async def threat_stats(current_user: User = Depends(get_current_active_user)):
    return get_enhanced_security_service().get_threat_stats()

@router.get("/threats/{threat_id}")
async def get_threat(threat_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_enhanced_security_service().get_threat(threat_id)
    return t.to_dict() if t else {"error": "Threat not found"}

@router.post("/threats")
async def report_threat(req: ReportThreatRequest, current_user: User = Depends(get_current_active_user)):
    return get_enhanced_security_service().report_threat(
        req.type, req.level, req.source_ip, req.target, req.description, req.metadata
    ).to_dict()

@router.patch("/threats/{threat_id}")
async def update_threat(threat_id: str, req: UpdateThreatRequest, current_user: User = Depends(get_current_active_user)):
    t = get_enhanced_security_service().update_threat_status(threat_id, req.status, req.mitigation)
    return t.to_dict() if t else {"error": "Threat not found"}

@router.get("/threats/blocked-ips")
async def blocked_ips(current_user: User = Depends(get_current_active_user)):
    return {"blocked_ips": get_enhanced_security_service().get_blocked_ips()}

@router.delete("/threats/blocked-ips/{ip}")
async def unblock_ip(ip: str, current_user: User = Depends(get_current_active_user)):
    return {"unblocked": get_enhanced_security_service().unblock_ip(ip)}

@router.get("/threats/ip-score/{ip}")
async def ip_score(ip: str, current_user: User = Depends(get_current_active_user)):
    return {"ip": ip, "trust_score": get_enhanced_security_service().get_ip_trust_score(ip)}

@router.post("/monitoring/start")
async def start_monitoring(current_user: User = Depends(get_current_active_user)):
    get_enhanced_security_service().start_monitoring()
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_enhanced_security_service().stop_monitoring()
    return {"monitoring": False}

# === ZKP ===

@router.get("/zkp")
async def list_proofs(current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_enhanced_security_service().list_proofs()]

@router.post("/zkp")
async def create_proof(req: CreateProofRequest, current_user: User = Depends(get_current_active_user)):
    return get_enhanced_security_service().create_proof(req.prover, req.claim, req.secret).to_dict()

@router.get("/zkp/{proof_id}")
async def get_proof(proof_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_enhanced_security_service().get_proof(proof_id)
    return p.to_dict() if p else {"error": "Proof not found"}

@router.post("/zkp/{proof_id}/verify")
async def verify_proof(proof_id: str, req: VerifyProofRequest, current_user: User = Depends(get_current_active_user)):
    result = get_enhanced_security_service().verify_proof(proof_id, req.secret)
    return {"verified": result}

# === MFA ===

@router.get("/mfa")
async def list_mfa(current_user: User = Depends(get_current_active_user)):
    return [m.to_dict() for m in get_enhanced_security_service().list_mfa_configs()]

@router.post("/mfa")
async def setup_mfa(req: SetupMFARequest, current_user: User = Depends(get_current_active_user)):
    return get_enhanced_security_service().setup_mfa(req.user_address, req.method).to_dict()

@router.post("/mfa/verify")
async def verify_mfa(req: VerifyMFARequest, current_user: User = Depends(get_current_active_user)):
    return {"verified": get_enhanced_security_service().verify_mfa(req.user_address, req.code)}

@router.delete("/mfa/{user_address}")
async def disable_mfa(user_address: str, current_user: User = Depends(get_current_active_user)):
    return {"disabled": get_enhanced_security_service().disable_mfa(user_address)}

# === Encryption ===

@router.get("/encryption")
async def list_encryption(current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_enhanced_security_service().list_encryption_configs()]

@router.get("/encryption/{component}")
async def get_encryption(component: str, current_user: User = Depends(get_current_active_user)):
    c = get_enhanced_security_service().get_encryption_config(component)
    return c.to_dict() if c else {"error": "Encryption config not found"}

@router.post("/encryption/{component}/rotate")
async def rotate_key(component: str, current_user: User = Depends(get_current_active_user)):
    c = get_enhanced_security_service().rotate_encryption_key(component)
    return c.to_dict() if c else {"error": "Encryption config not found"}
