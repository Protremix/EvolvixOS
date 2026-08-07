"""API for Decentralized Identity — Phase 29."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.identity import get_identity_service, CredentialType

router = APIRouter(prefix="/identity", tags=["identity"])


class CreateDIDRequest(BaseModel):
    name: str
    email: str
    role: str = "user"


class IssueCredentialRequest(BaseModel):
    issuer_did: str
    subject_did: str
    credential_type: str
    claims: dict
    expiration_days: int = 365


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None


@router.post("/did/create")
async def create_did(req: CreateDIDRequest, current_user: User = Depends(get_current_active_user)):
    """Create a new decentralized identity."""
    service = get_identity_service()
    doc, private_key = service.create_did(req.name, req.email, req.role)
    return {"did_document": doc.to_dict(), "private_key": private_key, "warning": "Store private_key securely"}

@router.get("/did/{did}")
async def get_did(did: str, current_user: User = Depends(get_current_active_user)):
    """Get a DID document."""
    service = get_identity_service()
    doc = service.get_did(did)
    return doc.to_dict() if doc else {"error": "DID not found"}

@router.get("/did/list")
async def list_dids(limit: int = 50, offset: int = 0, current_user: User = Depends(get_current_active_user)):
    """List all DIDs."""
    service = get_identity_service()
    return [doc.to_dict() for doc in service.list_dids(limit, offset)]

@router.get("/profile/{did}")
async def get_profile(did: str, current_user: User = Depends(get_current_active_user)):
    """Get identity profile."""
    service = get_identity_service()
    profile = service.get_profile(did)
    return profile.to_dict() if profile else {"error": "Profile not found"}

@router.patch("/profile/{did}")
async def update_profile(did: str, req: UpdateProfileRequest, current_user: User = Depends(get_current_active_user)):
    """Update identity profile."""
    service = get_identity_service()
    profile = service.update_profile(did, req.name, req.role)
    return profile.to_dict() if profile else {"error": "Profile not found"}

@router.post("/profile/{did}/verify")
async def verify_identity(did: str, current_user: User = Depends(get_current_active_user)):
    """Verify an identity."""
    service = get_identity_service()
    return {"verified": service.verify_identity(did)}

@router.post("/credential/issue")
async def issue_credential(req: IssueCredentialRequest, current_user: User = Depends(get_current_active_user)):
    """Issue a verifiable credential."""
    service = get_identity_service()
    try:
        cred_type = CredentialType(req.credential_type)
        cred = service.issue_credential(
            req.issuer_did, req.subject_did, cred_type,
            req.claims, req.expiration_days
        )
        return cred.to_dict()
    except ValueError as e:
        return {"error": str(e)}

@router.get("/credential/{cred_id}")
async def get_credential(cred_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a credential."""
    service = get_identity_service()
    cred = service.get_credential(cred_id)
    return cred.to_dict() if cred else {"error": "Credential not found"}

@router.get("/credential/{cred_id}/verify")
async def verify_credential(cred_id: str, current_user: User = Depends(get_current_active_user)):
    """Verify a credential."""
    service = get_identity_service()
    return service.verify_credential(cred_id)

@router.post("/credential/{cred_id}/revoke")
async def revoke_credential(cred_id: str, current_user: User = Depends(get_current_active_user)):
    """Revoke a credential."""
    service = get_identity_service()
    return {"revoked": service.revoke_credential(cred_id)}

@router.get("/credentials")
async def list_credentials(did: Optional[str] = None, limit: int = 50, current_user: User = Depends(get_current_active_user)):
    """List credentials."""
    service = get_identity_service()
    return [c.to_dict() for c in service.list_credentials(did, limit)]

@router.post("/reputation/{did}")
async def update_reputation(did: str, delta: float, current_user: User = Depends(get_current_active_user)):
    """Update reputation."""
    service = get_identity_service()
    result = service.update_reputation(did, delta)
    return {"reputation": result} if result is not None else {"error": "DID not found"}

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get identity system stats."""
    return get_identity_service().get_stats()
