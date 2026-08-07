"""API for Identity Privacy & Recovery — Phase 32."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.identity_privacy import get_identity_privacy_service

router = APIRouter(prefix="/identity-privacy", tags=["identity-privacy"])


class UpdatePrivacyRequest(BaseModel):
    profile_visible: Optional[bool] = None
    credentials_visible: Optional[bool] = None
    reputation_visible: Optional[bool] = None
    email_visible: Optional[bool] = None
    visibility_level: Optional[str] = None


class SetGuardiansRequest(BaseModel):
    did: str
    guardians: list[str]
    threshold: int = 2


class RequestRecoveryRequest(BaseModel):
    did: str
    new_public_key: str


class ApproveRecoveryRequest(BaseModel):
    guardian_did: str


class CreateDelegationRequest(BaseModel):
    delegator_did: str
    delegate_did: str
    permissions: list[str]
    expires_days: int = 30


class ZKPRequest(BaseModel):
    prover_did: str
    verifier_did: str
    claim_type: str
    claim_value: str
    secret: str


@router.get("/settings/{did}")
async def get_privacy(did: str, current_user: User = Depends(get_current_active_user)):
    return get_identity_privacy_service().get_privacy_settings(did).to_dict()

@router.patch("/settings/{did}")
async def update_privacy(did: str, req: UpdatePrivacyRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    return get_identity_privacy_service().update_privacy_settings(did, **kwargs).to_dict()

@router.post("/settings/{did}/allow/{verifier_did}")
async def allow_verifier(did: str, verifier_did: str, current_user: User = Depends(get_current_active_user)):
    return get_identity_privacy_service().add_allowed_verifier(did, verifier_did).to_dict()

@router.post("/settings/{did}/block/{blocked_did}")
async def block_did(did: str, blocked_did: str, current_user: User = Depends(get_current_active_user)):
    return get_identity_privacy_service().block_did(did, blocked_did).to_dict()

@router.get("/access/{target_did}/{requester_did}")
async def check_access(target_did: str, requester_did: str, current_user: User = Depends(get_current_active_user)):
    return {"can_access": get_identity_privacy_service().can_access(target_did, requester_did)}

@router.post("/key-rotate/{did}")
async def rotate_key(did: str, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().rotate_key(did, current_user.email)
    return result.to_dict() if result else {"error": "DID not found"}

@router.get("/key-rotate/{did}/history")
async def rotation_history(did: str, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_identity_privacy_service().get_rotation_history(did)]

@router.post("/guardians")
async def set_guardians(req: SetGuardiansRequest, current_user: User = Depends(get_current_active_user)):
    return {"success": get_identity_privacy_service().set_guardians(req.did, req.guardians, req.threshold)}

@router.get("/guardians/{did}")
async def get_guardians(did: str, current_user: User = Depends(get_current_active_user)):
    return {"guardians": get_identity_privacy_service().get_guardians(did)}

@router.post("/recovery/request")
async def request_recovery(req: RequestRecoveryRequest, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().request_recovery(req.did, req.new_public_key)
    return result.to_dict() if result else {"error": "No guardians set"}

@router.post("/recovery/{req_id}/approve")
async def approve_recovery(req_id: str, req: ApproveRecoveryRequest, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().approve_recovery(req_id, req.guardian_did)
    return result.to_dict() if result else {"error": "Recovery request not found"}

@router.post("/recovery/{req_id}/cancel")
async def cancel_recovery(req_id: str, current_user: User = Depends(get_current_active_user)):
    return {"cancelled": get_identity_privacy_service().cancel_recovery(req_id)}

@router.get("/recovery/{req_id}")
async def get_recovery(req_id: str, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().get_recovery_request(req_id)
    return result.to_dict() if result else {"error": "Not found"}

@router.get("/recovery/list/{did}")
async def list_recoveries(did: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_identity_privacy_service().list_recovery_requests(did)]

@router.post("/delegation/create")
async def create_delegation(req: CreateDelegationRequest, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().create_delegation(
        req.delegator_did, req.delegate_did, req.permissions, req.expires_days
    )
    return result.to_dict() if result else {"error": "DID not found"}

@router.post("/delegation/{del_id}/revoke")
async def revoke_delegation(del_id: str, current_user: User = Depends(get_current_active_user)):
    return {"revoked": get_identity_privacy_service().revoke_delegation(del_id)}

@router.get("/delegation/{del_id}")
async def get_delegation(del_id: str, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().get_delegation(del_id)
    return result.to_dict() if result else {"error": "Not found"}

@router.get("/delegations")
async def list_delegations(did: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [d.to_dict() for d in get_identity_privacy_service().list_delegations(did)]

@router.get("/delegation/check/{delegator}/{delegate}/{permission}")
async def check_delegation(delegator: str, delegate: str, permission: str, current_user: User = Depends(get_current_active_user)):
    return {"valid": get_identity_privacy_service().check_delegation(delegator, delegate, permission)}

@router.post("/revocation-registry/{credential_id}")
async def add_revocation(credential_id: str, current_user: User = Depends(get_current_active_user)):
    return {"added": get_identity_privacy_service().add_to_revocation_registry(credential_id)}

@router.get("/revocation-registry/check/{credential_id}")
async def check_revocation(credential_id: str, current_user: User = Depends(get_current_active_user)):
    return {"revoked": get_identity_privacy_service().is_revoked(credential_id)}

@router.get("/revocation-registry")
async def get_revocation_registry(current_user: User = Depends(get_current_active_user)):
    return {"revoked": get_identity_privacy_service().get_revocation_registry()}

@router.post("/zkp/create")
async def create_zkp(req: ZKPRequest, current_user: User = Depends(get_current_active_user)):
    proof = get_identity_privacy_service().create_zkp_proof(
        req.prover_did, req.verifier_did, req.claim_type, req.claim_value, req.secret
    )
    return proof.to_dict()

@router.get("/zkp/{proof_id}/verify")
async def verify_zkp(proof_id: str, expected_response: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return get_identity_privacy_service().verify_zkp_proof(proof_id, expected_response)

@router.get("/zkp/{proof_id}")
async def get_zkp(proof_id: str, current_user: User = Depends(get_current_active_user)):
    result = get_identity_privacy_service().get_zkp_proof(proof_id)
    return result.to_dict() if result else {"error": "Not found"}

@router.get("/zkp/list")
async def list_zkps(did: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_identity_privacy_service().list_zkp_proofs(did)]

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_identity_privacy_service().get_privacy_stats()
