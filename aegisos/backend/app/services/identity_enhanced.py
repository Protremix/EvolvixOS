"""
Enhanced Identity Features — Phase 31

Verifiable Presentations, DID Resolution, Credential Schemas,
Selective Disclosure, Presentation Verification.
"""

import hashlib
import json
import secrets
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger
from app.services.identity import get_identity_service, CredentialType

logger = get_logger("service.identity_enhanced")


@dataclass
class CredentialSchema:
    """Defines the structure of claims for a credential type."""
    type: str
    name: str
    description: str
    required_fields: list[str]
    optional_fields: list[str] = field(default_factory=list)
    field_types: dict = field(default_factory=dict)  # field_name -> "string"|"number"|"boolean"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def validate_claims(self, claims: dict) -> tuple[bool, list[str]]:
        """Validate claims against this schema."""
        errors = []
        for field_name in self.required_fields:
            if field_name not in claims:
                errors.append(f"Missing required field: {field_name}")
        for field_name, field_type in self.field_types.items():
            if field_name in claims:
                val = claims[field_name]
                if field_type == "string" and not isinstance(val, str):
                    errors.append(f"Field '{field_name}' must be string")
                elif field_type == "number" and not isinstance(val, (int, float)):
                    errors.append(f"Field '{field_name}' must be number")
                elif field_type == "boolean" and not isinstance(val, bool):
                    errors.append(f"Field '{field_name}' must be boolean")
        return len(errors) == 0, errors


@dataclass
class VerifiablePresentation:
    """W3C Verifiable Presentation — holder presents credentials to a verifier."""
    id: str
    type: list[str]
    holder: str  # DID of holder
    verifier: str  # DID of verifier (optional, can be empty)
    credentials: list[dict]  # embedded credentials
    challenge: str  # challenge nonce from verifier
    proof: dict
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["@context"] = ["https://www.w3.org/2018/credentials/v1"]
        return d


@dataclass
class DIDResolutionResult:
    """Result of resolving a DID."""
    did: str
    did_document: Optional[dict]
    profile: Optional[dict]
    resolved: bool
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class IdentityEnhancedService:
    """Enhanced identity features on top of base IdentityService."""

    # Default credential schemas for all 6 types
    DEFAULT_SCHEMAS = {
        "kyc": {
            "type": "kyc",
            "name": "KYC Verification",
            "description": "Know Your Customer verification credential",
            "required_fields": ["country", "verified"],
            "optional_fields": ["document_type", "verification_date"],
            "field_types": {"country": "string", "verified": "boolean", "document_type": "string", "verification_date": "string"},
        },
        "green_validator": {
            "type": "green_validator",
            "name": "Green Validator Certificate",
            "description": "Certifies a validator as eco-friendly",
            "required_fields": ["score", "certified"],
            "optional_fields": ["energy_source", "carbon_offset"],
            "field_types": {"score": "number", "certified": "boolean", "energy_source": "string", "carbon_offset": "number"},
        },
        "carbon_credit": {
            "type": "carbon_credit",
            "name": "Carbon Credit Certificate",
            "description": "Represents carbon credits from ecological projects",
            "required_fields": ["credits", "project"],
            "optional_fields": ["location", "verification_body", "issued_date"],
            "field_types": {"credits": "number", "project": "string", "location": "string", "verification_body": "string", "issued_date": "string"},
        },
        "reforestation": {
            "type": "reforestation",
            "name": "Reforestation Certificate",
            "description": "Tracks reforestation efforts",
            "required_fields": ["trees_planted", "location"],
            "optional_fields": ["species", "area_hectares", "survival_rate"],
            "field_types": {"trees_planted": "number", "location": "string", "species": "string", "area_hectares": "number", "survival_rate": "number"},
        },
        "developer": {
            "type": "developer",
            "name": "Developer Credential",
            "description": "Certifies a developer in the Verdis ecosystem",
            "required_fields": ["level"],
            "optional_fields": ["specialization", "projects", "github_username"],
            "field_types": {"level": "string", "specialization": "string", "github_username": "string"},
        },
        "ecosystem_partner": {
            "type": "ecosystem_partner",
            "name": "Ecosystem Partner Credential",
            "description": "Official ecosystem partnership",
            "required_fields": ["partnership_type", "active"],
            "optional_fields": ["start_date", "end_date", "description"],
            "field_types": {"partnership_type": "string", "active": "boolean", "start_date": "string", "end_date": "string", "description": "string"},
        },
    }

    def __init__(self):
        self._schemas: dict[str, CredentialSchema] = {}
        self._presentations: dict[str, VerifiablePresentation] = {}
        self._custom_schemas: dict[str, dict] = {}
        self._lock = None  # will use identity service lock
        self._init_default_schemas()

    def _init_default_schemas(self):
        for type_name, schema_data in self.DEFAULT_SCHEMAS.items():
            self._schemas[type_name] = CredentialSchema(**schema_data)

    def get_schema(self, credential_type: str) -> Optional[CredentialSchema]:
        """Get the schema for a credential type."""
        return self._schemas.get(credential_type)

    def list_schemas(self) -> list[CredentialSchema]:
        """List all credential schemas."""
        return list(self._schemas.values())

    def create_custom_schema(self, type_name: str, name: str, description: str,
                             required_fields: list[str], optional_fields: list[str] = None,
                             field_types: dict = None) -> CredentialSchema:
        """Create a custom credential schema."""
        schema = CredentialSchema(
            type=type_name, name=name, description=description,
            required_fields=required_fields,
            optional_fields=optional_fields or [],
            field_types=field_types or {},
        )
        self._schemas[type_name] = schema
        self._custom_schemas[type_name] = schema.to_dict()
        logger.info("custom_schema_created", type=type_name, name=name)
        return schema

    def validate_claims(self, credential_type: str, claims: dict) -> tuple[bool, list[str]]:
        """Validate claims against a credential schema."""
        schema = self._schemas.get(credential_type)
        if not schema:
            return True, []  # No schema = accept
        return schema.validate_claims(claims)

    def resolve_did(self, did: str) -> DIDResolutionResult:
        """Resolve a DID to its DID document and profile."""
        service = get_identity_service()
        doc = service.get_did(did)
        profile = service.get_profile(did)

        if not doc:
            return DIDResolutionResult(
                did=did, did_document=None, profile=None,
                resolved=False, error="DID not found"
            )

        return DIDResolutionResult(
            did=did,
            did_document=doc.to_dict(),
            profile=profile.to_dict() if profile else None,
            resolved=True,
        )

    def create_presentation(
        self,
        holder_did: str,
        credential_ids: list[str],
        verifier_did: str = "",
        selective_fields: dict = None,  # cred_id -> list of fields to include
        challenge: str = None,
    ) -> VerifiablePresentation:
        """Create a verifiable presentation from multiple credentials."""
        service = get_identity_service()

        # Verify holder exists
        holder_profile = service.get_profile(holder_did)
        if not holder_profile:
            raise ValueError("Holder DID not found")

        # Gather credentials
        credentials = []
        for cred_id in credential_ids:
            cred = service.get_credential(cred_id)
            if not cred:
                raise ValueError(f"Credential {cred_id} not found")
            if cred.subject != holder_did:
                raise ValueError(f"Credential {cred_id} does not belong to holder")
            if cred.status != "active":
                raise ValueError(f"Credential {cred_id} is not active")

            cred_dict = cred.to_dict()

            # Selective disclosure — only include specified fields
            if selective_fields and cred_id in selective_fields:
                allowed = set(selective_fields[cred_id])
                # Always keep structural fields
                keep = {"id", "type", "issuer", "subject", "issuance_date",
                       "expiration_date", "proof", "status", "@context"}
                keep.update(allowed)
                filtered_claims = {k: v for k, v in cred_dict.get("claims", {}).items() if k in allowed}
                cred_dict["claims"] = filtered_claims
                cred_dict["_selective_disclosure"] = True

            credentials.append(cred_dict)

        # Generate challenge if not provided
        if not challenge:
            challenge = secrets.token_hex(16)

        # Create proof
        pres_data = {
            "holder": holder_did,
            "verifier": verifier_did,
            "credentials": credentials,
            "challenge": challenge,
        }
        proof = {
            "type": "Ed25519Signature2020",
            "created": datetime.utcnow().isoformat(),
            "verification_method": f"{holder_did}#key-1",
            "challenge": challenge,
            "proof_value": hashlib.sha256(json.dumps(pres_data, sort_keys=True).encode()).hexdigest(),
        }

        pres_id = f"urn:uuid:{secrets.token_hex(16)}"
        presentation = VerifiablePresentation(
            id=pres_id,
            type=["VerifiablePresentation"],
            holder=holder_did,
            verifier=verifier_did,
            credentials=credentials,
            challenge=challenge,
            proof=proof,
        )

        self._presentations[pres_id] = presentation
        logger.info("presentation_created", pres_id=pres_id, holder=holder_did, credentials=len(credentials))
        return presentation

    def verify_presentation(self, pres_id: str) -> dict:
        """Verify a verifiable presentation."""
        pres = self._presentations.get(pres_id)
        if not pres:
            return {"valid": False, "reason": "Presentation not found"}

        service = get_identity_service()

        # Verify holder exists
        holder = service.get_profile(pres.holder)
        if not holder:
            return {"valid": False, "reason": "Holder DID not found"}

        # Verify all credentials
        results = []
        all_valid = True
        for cred in pres.credentials:
            cred_id = cred.get("id", "")
            verify_result = service.verify_credential(cred_id)
            results.append({
                "credential_id": cred_id,
                "valid": verify_result.get("valid", False),
                "reason": verify_result.get("reason", ""),
            })
            if not verify_result.get("valid", False):
                all_valid = False

        # Check selective disclosure markers
        selective_disclosed = [c.get("id") for c in pres.credentials if c.get("_selective_disclosure")]

        return {
            "valid": all_valid,
            "presentation_id": pres_id,
            "holder": pres.holder,
            "verifier": pres.verifier,
            "credential_count": len(pres.credentials),
            "credential_results": results,
            "selective_disclosure_used": len(selective_disclosed) > 0,
            "selectively_disclosed": selective_disclosed,
        }

    def get_presentation(self, pres_id: str) -> Optional[VerifiablePresentation]:
        """Get a presentation by ID."""
        return self._presentations.get(pres_id)

    def list_presentations(self, holder_did: str = None, limit: int = 50) -> list[VerifiablePresentation]:
        """List presentations, optionally filtered by holder."""
        if holder_did:
            return [p for p in self._presentations.values() if p.holder == holder_did][:limit]
        return list(self._presentations.values())[:limit]

    def get_developer_sdk_info(self) -> dict:
        """Return SDK information for third-party developers."""
        return {
            "version": "1.0.0",
            "did_method": "did:verdis",
            "credential_types": list(self.DEFAULT_SCHEMAS.keys()),
            "presentation_types": ["VerifiablePresentation"],
            "crypto_suites": ["Ed25519Signature2020"],
            "endpoints": {
                "create_did": "POST /api/v1/identity/did/create",
                "resolve_did": "GET /api/v1/identity/did/{did}",
                "issue_credential": "POST /api/v1/identity/credential/issue",
                "verify_credential": "GET /api/v1/identity/credential/{id}/verify",
                "create_presentation": "POST /api/v1/identity-enhanced/presentation/create",
                "verify_presentation": "GET /api/v1/identity-enhanced/presentation/{id}/verify",
                "get_schema": "GET /api/v1/identity-enhanced/schema/{type}",
                "list_schemas": "GET /api/v1/identity-enhanced/schemas",
                "validate_claims": "POST /api/v1/identity-enhanced/validate",
            },
            "example": {
                "create_did": {"name": "Alice", "email": "alice@example.com", "role": "user"},
                "issue_kyc": {
                    "issuer_did": "did:verdis:...",
                    "subject_did": "did:verdis:...",
                    "credential_type": "kyc",
                    "claims": {"country": "Spain", "verified": True},
                },
                "create_presentation": {
                    "holder_did": "did:verdis:...",
                    "credential_ids": ["urn:uuid:..."],
                    "selective_fields": {"urn:uuid:...": ["country"]},
                },
            },
        }


_service: Optional[IdentityEnhancedService] = None

def get_identity_enhanced_service() -> IdentityEnhancedService:
    global _service
    if _service is None:
        _service = IdentityEnhancedService()
    return _service
