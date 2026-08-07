"""
Advanced Identity Privacy & Recovery — Phase 32

Privacy controls, key rotation, social recovery, delegation,
revocation registry, and ZKP-style proof simulation.
"""

import hashlib
import json
import secrets
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
from app.core.logging import get_logger
from app.services.identity import get_identity_service

logger = get_logger("service.identity_privacy")


class VisibilityLevel(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SELECTIVE = "selective"


class RecoveryStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


@dataclass
class PrivacySettings:
    """Privacy controls for a DID."""
    did: str
    profile_visible: bool = True
    credentials_visible: bool = False  # credentials hidden by default
    reputation_visible: bool = True
    email_visible: bool = False
    allowed_verifiers: list[str] = field(default_factory=list)  # DIDs that can query
    blocked_dids: list[str] = field(default_factory=list)
    visibility_level: str = VisibilityLevel.SELECTIVE.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class KeyRotation:
    """Key rotation record."""
    did: str
    old_key_id: str
    new_key_id: str
    new_public_key: str
    rotated_at: str
    rotated_by: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RecoveryRequest:
    """Social recovery request for a lost key."""
    id: str
    did: str
    guardians: list[str]  # DIDs of guardians
    approvals: list[str] = field(default_factory=list)  # guardian DIDs that approved
    threshold: int = 2  # M-of-N required
    new_public_key: str = ""
    status: str = RecoveryStatus.PENDING.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Delegation:
    """Identity delegation — one DID delegates authority to another."""
    id: str
    delegator_did: str
    delegate_did: str
    permissions: list[str]  # issue_credential, verify_identity, update_profile, etc.
    expires_at: str
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    revoked: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ZKPProof:
    """Simulated zero-knowledge proof."""
    id: str
    prover_did: str
    verifier_did: str
    claim_type: str  # e.g., "age_over_18", "country_is_es", "score_above_80"
    proof_data: str  # hash commitment
    verified: bool = False
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class IdentityPrivacyService:
    """Advanced identity privacy, recovery, delegation, and ZKP features."""

    def __init__(self):
        self._privacy: dict[str, PrivacySettings] = {}
        self._rotations: list[KeyRotation] = []
        self._recovery_requests: dict[str, RecoveryRequest] = {}
        self._delegations: dict[str, Delegation] = {}
        self._zkp_proofs: dict[str, ZKPProof] = {}
        self._revocation_registry: set[str] = set()  # set of revoked credential IDs
        self._guardians: dict[str, list[str]] = {}  # DID -> list of guardian DIDs

    # === Privacy Controls ===

    def get_privacy_settings(self, did: str) -> PrivacySettings:
        """Get or create privacy settings for a DID."""
        if did not in self._privacy:
            self._privacy[did] = PrivacySettings(did=did)
        return self._privacy[did]

    def update_privacy_settings(self, did: str, **kwargs) -> PrivacySettings:
        """Update privacy settings."""
        settings = self.get_privacy_settings(did)
        for k, v in kwargs.items():
            if hasattr(settings, k):
                setattr(settings, k, v)
        settings.updated = datetime.utcnow().isoformat()
        return settings

    def add_allowed_verifier(self, did: str, verifier_did: str) -> PrivacySettings:
        """Allow a verifier to query this DID's information."""
        settings = self.get_privacy_settings(did)
        if verifier_did not in settings.allowed_verifiers:
            settings.allowed_verifiers.append(verifier_did)
        settings.updated = datetime.utcnow().isoformat()
        return settings

    def block_did(self, did: str, blocked_did: str) -> PrivacySettings:
        """Block a DID from querying information."""
        settings = self.get_privacy_settings(did)
        if blocked_did not in settings.blocked_dids:
            settings.blocked_dids.append(blocked_did)
        settings.updated = datetime.utcnow().isoformat()
        return settings

    def can_access(self, target_did: str, requester_did: str) -> bool:
        """Check if a requester can access a target DID's information."""
        settings = self.get_privacy_settings(target_did)
        if requester_did in settings.blocked_dids:
            return False
        if settings.visibility_level == VisibilityLevel.PUBLIC.value:
            return True
        if settings.visibility_level == VisibilityLevel.PRIVATE.value:
            return requester_did == target_did
        # SELECTIVE: allowed verifiers or self
        return requester_did == target_did or requester_did in settings.allowed_verifiers

    # === Key Rotation ===

    def rotate_key(self, did: str, rotated_by: str) -> Optional[KeyRotation]:
        """Rotate the key for a DID."""
        id_service = get_identity_service()
        doc = id_service.get_did(did)
        if not doc:
            return None

        old_key_id = doc.verification_method[0]["id"] if doc.verification_method else ""
        new_private, new_public = id_service._generate_key()
        new_key_id = f"{did}#key-{len(doc.verification_method) + 1}"

        doc.verification_method.append({
            "id": new_key_id,
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "public_key_multibase": new_public,
        })
        doc.authentication = [new_key_id]
        doc.updated = datetime.utcnow().isoformat()

        rotation = KeyRotation(
            did=did, old_key_id=old_key_id, new_key_id=new_key_id,
            new_public_key=new_public,
            rotated_at=datetime.utcnow().isoformat(),
            rotated_by=rotated_by,
        )
        self._rotations.append(rotation)
        logger.info("key_rotated", did=did, old=old_key_id, new=new_key_id)
        return rotation

    def get_rotation_history(self, did: str) -> list[KeyRotation]:
        """Get key rotation history for a DID."""
        return [r for r in self._rotations if r.did == did]

    # === Social Recovery ===

    def set_guardians(self, did: str, guardian_dids: list[str], threshold: int = 2) -> bool:
        """Set guardians for social recovery."""
        if threshold > len(guardian_dids):
            return False
        self._guardians[did] = guardian_dids
        return True

    def get_guardians(self, did: str) -> list[str]:
        """Get guardians for a DID."""
        return self._guardians.get(did, [])

    def request_recovery(self, did: str, new_public_key: str) -> Optional[RecoveryRequest]:
        """Request key recovery via guardians."""
        guardians = self._guardians.get(did, [])
        if not guardians:
            return None
        req_id = f"rec-{secrets.token_hex(8)}"
        request = RecoveryRequest(
            id=req_id, did=did, guardians=guardians,
            threshold=min(2, len(guardians)),
            new_public_key=new_public_key,
        )
        self._recovery_requests[req_id] = request
        logger.info("recovery_requested", did=did, req_id=req_id)
        return request

    def approve_recovery(self, req_id: str, guardian_did: str) -> Optional[RecoveryRequest]:
        """A guardian approves a recovery request."""
        req = self._recovery_requests.get(req_id)
        if not req or req.status != RecoveryStatus.PENDING.value:
            return None
        if guardian_did not in req.guardians:
            return None
        if guardian_did not in req.approvals:
            req.approvals.append(guardian_did)

        if len(req.approvals) >= req.threshold:
            req.status = RecoveryStatus.APPROVED.value
            # Execute recovery
            id_service = get_identity_service()
            doc = id_service.get_did(req.did)
            if doc:
                new_key_id = f"{req.did}#key-recovered"
                doc.verification_method.append({
                    "id": new_key_id,
                    "type": "Ed25519VerificationKey2020",
                    "controller": req.did,
                    "public_key_multibase": req.new_public_key,
                })
                doc.authentication = [new_key_id]
                doc.updated = datetime.utcnow().isoformat()
                req.status = RecoveryStatus.EXECUTED.value
                req.completed = datetime.utcnow().isoformat()

        return req

    def cancel_recovery(self, req_id: str) -> bool:
        """Cancel a recovery request."""
        req = self._recovery_requests.get(req_id)
        if req and req.status == RecoveryStatus.PENDING.value:
            req.status = RecoveryStatus.CANCELLED.value
            return True
        return False

    def get_recovery_request(self, req_id: str) -> Optional[RecoveryRequest]:
        return self._recovery_requests.get(req_id)

    def list_recovery_requests(self, did: str = None) -> list[RecoveryRequest]:
        if did:
            return [r for r in self._recovery_requests.values() if r.did == did]
        return list(self._recovery_requests.values())

    # === Delegation ===

    def create_delegation(
        self, delegator_did: str, delegate_did: str,
        permissions: list[str], expires_days: int = 30,
    ) -> Optional[Delegation]:
        """Delegate authority from one DID to another."""
        id_service = get_identity_service()
        if not id_service.get_did(delegator_did) or not id_service.get_did(delegate_did):
            return None
        del_id = f"del-{secrets.token_hex(8)}"
        expiration = datetime.fromtimestamp(datetime.utcnow().timestamp() + expires_days * 86400)
        delegation = Delegation(
            id=del_id, delegator_did=delegator_did, delegate_did=delegate_did,
            permissions=permissions, expires_at=expiration.isoformat(),
        )
        self._delegations[del_id] = delegation
        logger.info("delegation_created", delegator=delegator_did, delegate=delegate_did)
        return delegation

    def revoke_delegation(self, del_id: str) -> bool:
        """Revoke a delegation."""
        if del_id in self._delegations:
            self._delegations[del_id].revoked = True
            return True
        return False

    def get_delegation(self, del_id: str) -> Optional[Delegation]:
        return self._delegations.get(del_id)

    def list_delegations(self, did: str = None) -> list[Delegation]:
        if did:
            return [d for d in self._delegations.values()
                    if d.delegator_did == did or d.delegate_did == did]
        return list(self._delegations.values())

    def check_delegation(self, delegator_did: str, delegate_did: str, permission: str) -> bool:
        """Check if a delegation is valid for a specific permission."""
        for d in self._delegations.values():
            if d.delegator_did == delegator_did and d.delegate_did == delegate_did:
                if d.revoked:
                    return False
                if permission not in d.permissions:
                    return False
                exp = datetime.fromisoformat(d.expires_at.replace("Z", "+00:00"))
                if datetime.utcnow() > exp:
                    return False
                return True
        return False

    # === Revocation Registry ===

    def add_to_revocation_registry(self, credential_id: str) -> bool:
        """Add a credential to the public revocation registry."""
        self._revocation_registry.add(credential_id)
        return True

    def is_revoked(self, credential_id: str) -> bool:
        """Check if a credential is in the revocation registry."""
        return credential_id in self._revocation_registry

    def get_revocation_registry(self) -> list[str]:
        """Get all revoked credential IDs."""
        return list(self._revocation_registry)

    def remove_from_revocation_registry(self, credential_id: str) -> bool:
        """Remove a credential from the revocation registry (un-revoke)."""
        if credential_id in self._revocation_registry:
            self._revocation_registry.remove(credential_id)
            return True
        return False

    # === ZKP-Style Proofs ===

    def create_zkp_proof(
        self, prover_did: str, verifier_did: str, claim_type: str, claim_value: str, secret: str,
    ) -> ZKPProof:
        """Create a simulated zero-knowledge proof.

        The prover proves they know a value that satisfies a claim
        without revealing the actual value.
        """
        # Create a commitment: hash(claim_type + secret + nonce)
        nonce = secrets.token_hex(16)
        commitment = hashlib.sha256(f"{claim_type}:{secret}:{nonce}".encode()).hexdigest()

        # Create challenge: hash(commitment + verifier_did)
        challenge = hashlib.sha256(f"{commitment}:{verifier_did}".encode()).hexdigest()

        # Create response: hash(challenge + claim_value)
        response = hashlib.sha256(f"{challenge}:{claim_value}".encode()).hexdigest()

        proof_id = f"zkp-{secrets.token_hex(8)}"
        proof = ZKPProof(
            id=proof_id, prover_did=prover_did, verifier_did=verifier_did,
            claim_type=claim_type,
            proof_data=json.dumps({
                "commitment": commitment,
                "challenge": challenge,
                "response": response,
                "nonce": nonce,
            }),
        )
        self._zkp_proofs[proof_id] = proof
        logger.info("zkp_created", prover=prover_did, claim=claim_type)
        return proof

    def verify_zkp_proof(self, proof_id: str, expected_response: str = None) -> dict:
        """Verify a ZKP proof."""
        proof = self._zkp_proofs.get(proof_id)
        if not proof:
            return {"valid": False, "reason": "Proof not found"}

        # Parse proof data
        try:
            data = json.loads(proof.proof_data)
        except Exception:
            return {"valid": False, "reason": "Invalid proof format"}

        # Recompute challenge from commitment
        expected_challenge = hashlib.sha256(
            f"{data['commitment']}:{proof.verifier_did}".encode()
        ).hexdigest()

        if data["challenge"] != expected_challenge:
            return {"valid": False, "reason": "Challenge mismatch"}

        # If expected_response provided, check it
        if expected_response:
            expected_resp = hashlib.sha256(
                f"{expected_challenge}:{expected_response}".encode()
            ).hexdigest()
            if data["response"] != expected_resp:
                return {"valid": False, "reason": "Response mismatch"}

        proof.verified = True
        return {
            "valid": True,
            "proof_id": proof_id,
            "prover": proof.prover_did,
            "claim_type": proof.claim_type,
            "verified_at": datetime.utcnow().isoformat(),
        }

    def get_zkp_proof(self, proof_id: str) -> Optional[ZKPProof]:
        return self._zkp_proofs.get(proof_id)

    def list_zkp_proofs(self, did: str = None) -> list[ZKPProof]:
        if did:
            return [p for p in self._zkp_proofs.values()
                    if p.prover_did == did or p.verifier_did == did]
        return list(self._zkp_proofs.values())

    # === Stats ===

    def get_privacy_stats(self) -> dict:
        return {
            "total_privacy_settings": len(self._privacy),
            "public_profiles": sum(1 for p in self._privacy.values() if p.visibility_level == "public"),
            "private_profiles": sum(1 for p in self._privacy.values() if p.visibility_level == "private"),
            "selective_profiles": sum(1 for p in self._privacy.values() if p.visibility_level == "selective"),
            "total_key_rotations": len(self._rotations),
            "total_recoveries": len(self._recovery_requests),
            "total_delegations": len(self._delegations),
            "active_delegations": sum(1 for d in self._delegations.values() if not d.revoked),
            "total_zkp_proofs": len(self._zkp_proofs),
            "verified_zkp_proofs": sum(1 for p in self._zkp_proofs.values() if p.verified),
            "revoked_credentials": len(self._revocation_registry),
            "total_guardians_set": len(self._guardians),
        }


_service: Optional[IdentityPrivacyService] = None

def get_identity_privacy_service() -> IdentityPrivacyService:
    global _service
    if _service is None:
        _service = IdentityPrivacyService()
    return _service
