"""API for Enhanced Identity — Phase 31."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.identity_enhanced import get_identity_enhanced_service

router = APIRouter(prefix="/identity-enhanced", tags=["identity-enhanced"])


class CreatePresentationRequest(BaseModel):
    holder_did: str
    credential_ids: list[str]
    verifier_did: str = ""
    selective_fields: Optional[dict] = None
    challenge: Optional[str] = None


class CreateSchemaRequest(BaseModel):
    type_name: str
    name: str
    description: str
    required_fields: list[str]
    optional_fields: list[str] = []
    field_types: dict = {}


class ValidateClaimsRequest(BaseModel):
    credential_type: str
    claims: dict


@router.get("/schema/{credential_type}")
async def get_schema(credential_type: str, current_user: User = Depends(get_current_active_user)):
    """Get credential schema."""
    schema = get_identity_enhanced_service().get_schema(credential_type)
    return schema.to_dict() if schema else {"error": "Schema not found"}

@router.get("/schemas")
async def list_schemas(current_user: User = Depends(get_current_active_user)):
    """List all credential schemas."""
    return [s.to_dict() for s in get_identity_enhanced_service().list_schemas()]

@router.post("/schemas/custom")
async def create_custom_schema(req: CreateSchemaRequest, current_user: User = Depends(get_current_active_user)):
    """Create a custom credential schema."""
    schema = get_identity_enhanced_service().create_custom_schema(
        req.type_name, req.name, req.description,
        req.required_fields, req.optional_fields, req.field_types,
    )
    return schema.to_dict()

@router.post("/validate")
async def validate_claims(req: ValidateClaimsRequest, current_user: User = Depends(get_current_active_user)):
    """Validate claims against a credential schema."""
    valid, errors = get_identity_enhanced_service().validate_claims(req.credential_type, req.claims)
    return {"valid": valid, "errors": errors}

@router.get("/resolve/{did}")
async def resolve_did(did: str, current_user: User = Depends(get_current_active_user)):
    """Resolve a DID to its document and profile."""
    result = get_identity_enhanced_service().resolve_did(did)
    return result.to_dict()

@router.post("/presentation/create")
async def create_presentation(req: CreatePresentationRequest, current_user: User = Depends(get_current_active_user)):
    """Create a verifiable presentation."""
    try:
        pres = get_identity_enhanced_service().create_presentation(
            req.holder_did, req.credential_ids, req.verifier_did,
            req.selective_fields, req.challenge,
        )
        return pres.to_dict()
    except ValueError as e:
        return {"error": str(e)}

@router.get("/presentation/{pres_id}")
async def get_presentation(pres_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a presentation."""
    pres = get_identity_enhanced_service().get_presentation(pres_id)
    return pres.to_dict() if pres else {"error": "Presentation not found"}

@router.get("/presentation/{pres_id}/verify")
async def verify_presentation(pres_id: str, current_user: User = Depends(get_current_active_user)):
    """Verify a presentation."""
    return get_identity_enhanced_service().verify_presentation(pres_id)

@router.get("/presentations")
async def list_presentations(holder_did: Optional[str] = None, limit: int = 50, current_user: User = Depends(get_current_active_user)):
    """List presentations."""
    return [p.to_dict() for p in get_identity_enhanced_service().list_presentations(holder_did, limit)]

@router.get("/sdk-info")
async def get_sdk_info():
    """Get developer SDK information (public, no auth)."""
    return get_identity_enhanced_service().get_developer_sdk_info()
