"""Tests for Identity Privacy & Recovery — Phase 32."""

import pytest
from app.services.identity import get_identity_service
from app.services.identity_privacy import (
    IdentityPrivacyService, get_identity_privacy_service, VisibilityLevel, RecoveryStatus,
)


class TestPrivacy:
    def test_get_default_privacy(self):
        service = IdentityPrivacyService()
        settings = service.get_privacy_settings("did:verdis:test")
        assert settings.profile_visible is True
        assert settings.credentials_visible is False
        assert settings.visibility_level == "selective"

    def test_update_privacy(self):
        service = IdentityPrivacyService()
        settings = service.update_privacy_settings("did:verdis:test", profile_visible=False, email_visible=True)
        assert settings.profile_visible is False
        assert settings.email_visible is True

    def test_allow_verifier(self):
        service = IdentityPrivacyService()
        settings = service.add_allowed_verifier("did:verdis:a", "did:verdis:b")
        assert "did:verdis:b" in settings.allowed_verifiers

    def test_block_did(self):
        service = IdentityPrivacyService()
        settings = service.block_did("did:verdis:a", "did:verdis:c")
        assert "did:verdis:c" in settings.blocked_dids

    def test_can_access_public(self):
        service = IdentityPrivacyService()
        service.update_privacy_settings("did:verdis:a", visibility_level="public")
        assert service.can_access("did:verdis:a", "did:verdis:anyone") is True

    def test_can_access_private(self):
        service = IdentityPrivacyService()
        service.update_privacy_settings("did:verdis:a", visibility_level="private")
        assert service.can_access("did:verdis:a", "did:verdis:a") is True
        assert service.can_access("did:verdis:a", "did:verdis:b") is False

    def test_can_access_selective(self):
        service = IdentityPrivacyService()
        service.add_allowed_verifier("did:verdis:a", "did:verdis:b")
        assert service.can_access("did:verdis:a", "did:verdis:b") is True
        assert service.can_access("did:verdis:a", "did:verdis:c") is False

    def test_can_access_blocked(self):
        service = IdentityPrivacyService()
        service.update_privacy_settings("did:verdis:a", visibility_level="public")
        service.block_did("did:verdis:a", "did:verdis:b")
        assert service.can_access("did:verdis:a", "did:verdis:b") is False


class TestKeyRotation:
    def test_rotate_key(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        doc, _ = id_service.create_did("Rotate", "rotate_key@test.com")
        rotation = privacy.rotate_key(doc.id, "admin@test.com")
        assert rotation is not None
        assert rotation.old_key_id != rotation.new_key_id
        assert rotation.new_public_key is not None

    def test_rotate_nonexistent(self):
        privacy = IdentityPrivacyService()
        assert privacy.rotate_key("did:verdis:nonexistent", "admin") is None

    def test_rotation_history(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        doc, _ = id_service.create_did("History", "rotate_history@test.com")
        privacy.rotate_key(doc.id, "admin@test.com")
        history = privacy.get_rotation_history(doc.id)
        assert len(history) == 1


class TestRecovery:
    def test_set_guardians(self):
        service = IdentityPrivacyService()
        assert service.set_guardians("did:verdis:a", ["did:verdis:g1", "did:verdis:g2"], 2) is True

    def test_set_guardians_threshold_too_high(self):
        service = IdentityPrivacyService()
        assert service.set_guardians("did:verdis:a", ["did:verdis:g1"], 2) is False

    def test_request_recovery_no_guardians(self):
        service = IdentityPrivacyService()
        assert service.request_recovery("did:verdis:no_guardians", "new_key") is None

    def test_full_recovery_flow(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        # Create DIDs
        owner_doc, _ = id_service.create_did("Owner", "recovery_owner@test.com")
        g1_doc, _ = id_service.create_did("G1", "recovery_g1@test.com")
        g2_doc, _ = id_service.create_did("G2", "recovery_g2@test.com")
        # Set guardians
        privacy.set_guardians(owner_doc.id, [g1_doc.id, g2_doc.id], 2)
        # Request recovery
        req = privacy.request_recovery(owner_doc.id, "new_public_key_123")
        assert req is not None
        assert req.status == RecoveryStatus.PENDING.value
        # First guardian approves
        req = privacy.approve_recovery(req.id, g1_doc.id)
        assert len(req.approvals) == 1
        assert req.status == RecoveryStatus.PENDING.value  # Not enough yet
        # Second guardian approves
        req = privacy.approve_recovery(req.id, g2_doc.id)
        assert req.status == RecoveryStatus.EXECUTED.value
        assert req.completed != ""

    def test_cancel_recovery(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        owner_doc, _ = id_service.create_did("Cancel", "recovery_cancel@test.com")
        g1_doc, _ = id_service.create_did("G1C", "recovery_g1c@test.com")
        privacy.set_guardians(owner_doc.id, [g1_doc.id], 1)
        req = privacy.request_recovery(owner_doc.id, "new_key")
        assert privacy.cancel_recovery(req.id) is True
        assert privacy.get_recovery_request(req.id).status == RecoveryStatus.CANCELLED.value

    def test_non_guardian_approval(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        owner_doc, _ = id_service.create_did("NG", "recovery_ng@test.com")
        g1_doc, _ = id_service.create_did("G1NG", "recovery_g1ng@test.com")
        other_doc, _ = id_service.create_did("Other", "recovery_other@test.com")
        privacy.set_guardians(owner_doc.id, [g1_doc.id], 1)
        req = privacy.request_recovery(owner_doc.id, "new_key")
        result = privacy.approve_recovery(req.id, other_doc.id)
        assert result is None  # Non-guardian can't approve


class TestDelegation:
    def test_create_delegation(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        d1, _ = id_service.create_did("Del1", "del1@test.com")
        d2, _ = id_service.create_did("Del2", "del2@test.com")
        delegation = privacy.create_delegation(d1.id, d2.id, ["issue_credential", "verify_identity"])
        assert delegation is not None
        assert delegation.delegator_did == d1.id
        assert delegation.delegate_did == d2.id
        assert "issue_credential" in delegation.permissions

    def test_revoke_delegation(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        d1, _ = id_service.create_did("Rev1", "rev1@test.com")
        d2, _ = id_service.create_did("Rev2", "rev2@test.com")
        delegation = privacy.create_delegation(d1.id, d2.id, ["issue_credential"])
        assert privacy.revoke_delegation(delegation.id) is True
        assert privacy.get_delegation(delegation.id).revoked is True

    def test_check_delegation_valid(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        d1, _ = id_service.create_did("Chk1", "chk1@test.com")
        d2, _ = id_service.create_did("Chk2", "chk2@test.com")
        privacy.create_delegation(d1.id, d2.id, ["issue_credential"])
        assert privacy.check_delegation(d1.id, d2.id, "issue_credential") is True

    def test_check_delegation_wrong_permission(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        d1, _ = id_service.create_did("WP1", "wp1@test.com")
        d2, _ = id_service.create_did("WP2", "wp2@test.com")
        privacy.create_delegation(d1.id, d2.id, ["issue_credential"])
        assert privacy.check_delegation(d1.id, d2.id, "revoke_credential") is False

    def test_check_delegation_revoked(self):
        id_service = get_identity_service()
        privacy = IdentityPrivacyService()
        d1, _ = id_service.create_did("RD1", "rd1@test.com")
        d2, _ = id_service.create_did("RD2", "rd2@test.com")
        delegation = privacy.create_delegation(d1.id, d2.id, ["issue_credential"])
        privacy.revoke_delegation(delegation.id)
        assert privacy.check_delegation(d1.id, d2.id, "issue_credential") is False


class TestRevocationRegistry:
    def test_add_and_check(self):
        service = IdentityPrivacyService()
        service.add_to_revocation_registry("cred-123")
        assert service.is_revoked("cred-123") is True
        assert service.is_revoked("cred-456") is False

    def test_remove(self):
        service = IdentityPrivacyService()
        service.add_to_revocation_registry("cred-789")
        assert service.remove_from_revocation_registry("cred-789") is True
        assert service.is_revoked("cred-789") is False

    def test_get_all(self):
        service = IdentityPrivacyService()
        service.add_to_revocation_registry("a")
        service.add_to_revocation_registry("b")
        registry = service.get_revocation_registry()
        assert "a" in registry
        assert "b" in registry


class TestZKP:
    def test_create_zkp(self):
        service = IdentityPrivacyService()
        proof = service.create_zkp_proof("did:verdis:prover", "did:verdis:verifier", "age_over_18", "true", "secret123")
        assert proof.id.startswith("zkp-")
        assert proof.prover_did == "did:verdis:prover"
        assert proof.claim_type == "age_over_18"
        assert proof.verified is False

    def test_verify_zkp(self):
        service = IdentityPrivacyService()
        proof = service.create_zkp_proof("did:verdis:p", "did:verdis:v", "country_is_es", "yes", "secret")
        result = service.verify_zkp_proof(proof.id)
        assert result["valid"] is True

    def test_verify_nonexistent_zkp(self):
        service = IdentityPrivacyService()
        result = service.verify_zkp_proof("nonexistent")
        assert result["valid"] is False

    def test_zkp_with_expected_response(self):
        service = IdentityPrivacyService()
        proof = service.create_zkp_proof("did:verdis:p", "did:verdis:v", "score_above_80", "true", "secret")
        result = service.verify_zkp_proof(proof.id, expected_response="true")
        assert result["valid"] is True

    def test_zkp_wrong_response(self):
        service = IdentityPrivacyService()
        proof = service.create_zkp_proof("did:verdis:p", "did:verdis:v", "score_above_80", "true", "secret")
        result = service.verify_zkp_proof(proof.id, expected_response="false")
        assert result["valid"] is False

    def test_list_zkps(self):
        service = IdentityPrivacyService()
        service.create_zkp_proof("did:verdis:p1", "did:verdis:v", "claim", "val", "secret")
        proofs = service.list_zkp_proofs("did:verdis:p1")
        assert len(proofs) == 1


class TestStats:
    def test_stats(self):
        service = IdentityPrivacyService()
        stats = service.get_privacy_stats()
        assert "total_privacy_settings" in stats
        assert "total_key_rotations" in stats
        assert "total_delegations" in stats
        assert "total_zkp_proofs" in stats
        assert "revoked_credentials" in stats


class TestPrivacyAPI:
    def test_get_privacy(self, client, test_user):
        resp = client.get("/api/v1/identity-privacy/settings/did:verdis:test", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "visibility_level" in resp.json()

    def test_update_privacy(self, client, test_user):
        resp = client.patch("/api/v1/identity-privacy/settings/did:verdis:test", json={
            "profile_visible": False,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["profile_visible"] is False

    def test_check_access(self, client, test_user):
        resp = client.get("/api/v1/identity-privacy/access/did:verdis:a/did:verdis:b", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "can_access" in resp.json()

    def test_zkp_flow(self, client, test_user):
        create = client.post("/api/v1/identity-privacy/zkp/create", json={
            "prover_did": "did:verdis:p", "verifier_did": "did:verdis:v",
            "claim_type": "age_over_18", "claim_value": "true", "secret": "s123",
        }, headers=test_user["headers"])
        assert create.status_code == 200
        proof_id = create.json()["id"]
        verify = client.get(f"/api/v1/identity-privacy/zkp/{proof_id}/verify", headers=test_user["headers"])
        assert verify.status_code == 200
        assert verify.json()["valid"] is True

    def test_delegation_flow(self, client, test_user):
        d1 = client.post("/api/v1/identity/did/create", json={"name": "D1", "email": "del_api_1@test.com"}, headers=test_user["headers"])
        d2 = client.post("/api/v1/identity/did/create", json={"name": "D2", "email": "del_api_2@test.com"}, headers=test_user["headers"])
        create = client.post("/api/v1/identity-privacy/delegation/create", json={
            "delegator_did": d1.json()["did_document"]["id"],
            "delegate_did": d2.json()["did_document"]["id"],
            "permissions": ["issue_credential"],
        }, headers=test_user["headers"])
        assert create.status_code == 200
        del_id = create.json()["id"]
        check = client.get(f"/api/v1/identity-privacy/delegation/check/{d1.json()['did_document']['id']}/{d2.json()['did_document']['id']}/issue_credential", headers=test_user["headers"])
        assert check.status_code == 200
        assert check.json()["valid"] is True

    def test_revocation_registry(self, client, test_user):
        client.post("/api/v1/identity-privacy/revocation-registry/cred-test-123", headers=test_user["headers"])
        resp = client.get("/api/v1/identity-privacy/revocation-registry/check/cred-test-123", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["revoked"] is True

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/identity-privacy/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_zkp_proofs" in resp.json()

    def test_singleton(self):
        assert get_identity_privacy_service() is get_identity_privacy_service()
