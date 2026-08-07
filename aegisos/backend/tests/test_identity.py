"""Tests for Decentralized Identity — Phase 29."""

import pytest
from app.services.identity import (
    IdentityService, get_identity_service,
    CredentialType, CredentialStatus, DIDMethod
)


class TestDID:
    def test_create_did(self):
        service = IdentityService()
        doc, key = service.create_did("Alice", "alice@test.com", "user")
        assert doc.id.startswith("did:verdis:")
        assert len(key) == 64  # 32 bytes hex
        assert len(doc.verification_method) == 1
        assert doc.verification_method[0]["type"] == "Ed25519VerificationKey2020"
        assert doc.authentication == [f"{doc.id}#key-1"]
        assert len(doc.service) == 1
        assert "verdischain.com" in doc.service[0]["service_endpoint"]

    def test_get_did(self):
        service = IdentityService()
        doc, _ = service.create_did("Bob", "bob@test.com")
        found = service.get_did(doc.id)
        assert found is not None
        assert found.id == doc.id

    def test_get_nonexistent_did(self):
        service = IdentityService()
        assert service.get_did("did:verdis:nonexistent") is None

    def test_list_dids(self):
        service = IdentityService()
        service.create_did("A", "a@test.com")
        service.create_did("B", "b@test.com")
        dids = service.list_dids()
        assert len(dids) == 2

    def test_did_format(self):
        service = IdentityService()
        doc, _ = service.create_did("Test", "test@test.com")
        parts = doc.id.split(":")
        assert parts[0] == "did"
        assert parts[1] == "verdis"
        assert len(parts[2]) == 32  # 16 bytes hex

    def test_did_context(self):
        service = IdentityService()
        doc, _ = service.create_did("Test", "test@test.com")
        d = doc.to_dict()
        assert "@context" in d
        assert "https://www.w3.org/ns/did/v1" in d["@context"]


class TestProfile:
    def test_get_profile(self):
        service = IdentityService()
        doc, _ = service.create_did("Alice", "alice@test.com", "validator")
        profile = service.get_profile(doc.id)
        assert profile.name == "Alice"
        assert profile.role == "validator"
        assert profile.verified is False

    def test_get_profile_by_email(self):
        service = IdentityService()
        doc, _ = service.create_did("Alice", "alice@test.com")
        profile = service.get_profile_by_email("alice@test.com")
        assert profile is not None
        assert profile.did == doc.id

    def test_update_profile(self):
        service = IdentityService()
        doc, _ = service.create_did("Alice", "alice@test.com", "user")
        updated = service.update_profile(doc.id, name="Alice Smith", role="developer")
        assert updated.name == "Alice Smith"
        assert updated.role == "developer"

    def test_verify_identity(self):
        service = IdentityService()
        doc, _ = service.create_did("Alice", "alice@test.com")
        assert service.verify_identity(doc.id) is True
        profile = service.get_profile(doc.id)
        assert profile.verified is True

    def test_verify_nonexistent(self):
        service = IdentityService()
        assert service.verify_identity("did:verdis:nonexistent") is False


class TestCredentials:
    def test_issue_credential(self):
        service = IdentityService()
        issuer_doc, issuer_key = service.create_did("Issuer", "issuer@test.com", "admin")
        subject_doc, _ = service.create_did("Subject", "subject@test.com")
        cred = service.issue_credential(
            issuer_doc.id, subject_doc.id, CredentialType.KYC,
            {"country": "Spain", "verified": True}, issuer_key=issuer_key
        )
        assert cred.issuer == issuer_doc.id
        assert cred.subject == subject_doc.id
        assert "VerifiableCredential" in cred.type
        assert "kyc" in cred.type
        assert cred.claims == {"country": "Spain", "verified": True}
        assert cred.status == "active"
        assert "proof_value" in cred.proof

    def test_get_credential(self):
        service = IdentityService()
        issuer_doc, _ = service.create_did("Issuer", "issuer@test.com")
        subject_doc, _ = service.create_did("Subject", "subject@test.com")
        cred = service.issue_credential(
            issuer_doc.id, subject_doc.id, CredentialType.DEVELOPER, {"level": "senior"}
        )
        found = service.get_credential(cred.id)
        assert found is not None
        assert found.id == cred.id

    def test_verify_credential(self):
        service = IdentityService()
        issuer_doc, _ = service.create_did("Issuer", "issuer@test.com")
        subject_doc, _ = service.create_did("Subject", "subject@test.com")
        cred = service.issue_credential(
            issuer_doc.id, subject_doc.id, CredentialType.CARBON_CREDIT,
            {"credits": 100, "project": "Amazon"}
        )
        result = service.verify_credential(cred.id)
        assert result["valid"] is True

    def test_verify_nonexistent_credential(self):
        service = IdentityService()
        result = service.verify_credential("nonexistent")
        assert result["valid"] is False

    def test_revoke_credential(self):
        service = IdentityService()
        issuer_doc, _ = service.create_did("Issuer", "issuer@test.com")
        subject_doc, _ = service.create_did("Subject", "subject@test.com")
        cred = service.issue_credential(
            issuer_doc.id, subject_doc.id, CredentialType.GREEN_VALIDATOR, {"score": 95}
        )
        assert service.revoke_credential(cred.id) is True
        result = service.verify_credential(cred.id)
        assert result["valid"] is False
        assert "revoked" in result["reason"]

    def test_list_credentials(self):
        service = IdentityService()
        issuer_doc, _ = service.create_did("Issuer", "issuer@test.com")
        subject_doc, _ = service.create_did("Subject", "subject@test.com")
        service.issue_credential(issuer_doc.id, subject_doc.id, CredentialType.KYC, {})
        service.issue_credential(issuer_doc.id, subject_doc.id, CredentialType.DEVELOPER, {})
        creds = service.list_credentials(subject_doc.id)
        assert len(creds) == 2

    def test_credential_linked_to_profile(self):
        service = IdentityService()
        issuer_doc, _ = service.create_did("Issuer", "issuer@test.com")
        subject_doc, _ = service.create_did("Subject", "subject@test.com")
        cred = service.issue_credential(
            issuer_doc.id, subject_doc.id, CredentialType.REFORESTATION, {"trees": 1000}
        )
        profile = service.get_profile(subject_doc.id)
        assert cred.id in profile.credentials


class TestReputation:
    def test_update_reputation(self):
        service = IdentityService()
        doc, _ = service.create_did("Alice", "alice@test.com")
        result = service.update_reputation(doc.id, 10.0)
        assert result == 10.0
        result = service.update_reputation(doc.id, 5.0)
        assert result == 15.0

    def test_reputation_bounds(self):
        service = IdentityService()
        doc, _ = service.create_did("Alice", "alice@test.com")
        service.update_reputation(doc.id, 200.0)
        profile = service.get_profile(doc.id)
        assert profile.reputation == 100.0  # capped at 100
        service.update_reputation(doc.id, -200.0)
        assert profile.reputation == 0.0  # floored at 0


class TestStats:
    def test_stats(self):
        service = IdentityService()
        service.create_did("A", "a@test.com", "user")
        service.create_did("B", "b@test.com", "validator")
        stats = service.get_stats()
        assert stats["total_dids"] == 2
        assert stats["total_profiles"] == 2
        assert stats["by_role"]["user"] == 1
        assert stats["by_role"]["validator"] == 1


class TestIdentityAPI:
    def test_create_did(self, client, test_user):
        resp = client.post("/api/v1/identity/did/create", json={
            "name": "Test User", "email": "test@test.com", "role": "user"
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "did_document" in resp.json()

    def test_get_did(self, client, test_user):
        create = client.post("/api/v1/identity/did/create", json={
            "name": "Test", "email": "get@test.com"
        }, headers=test_user["headers"])
        did = create.json()["did_document"]["id"]
        resp = client.get(f"/api/v1/identity/did/{did}", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"] == did

    def test_get_profile(self, client, test_user):
        create = client.post("/api/v1/identity/did/create", json={
            "name": "Profile Test", "email": "profile@test.com"
        }, headers=test_user["headers"])
        did = create.json()["did_document"]["id"]
        resp = client.get(f"/api/v1/identity/profile/{did}", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "Profile Test"

    def test_verify_identity(self, client, test_user):
        create = client.post("/api/v1/identity/did/create", json={
            "name": "Verify", "email": "verify@test.com"
        }, headers=test_user["headers"])
        did = create.json()["did_document"]["id"]
        resp = client.post(f"/api/v1/identity/profile/{did}/verify", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

    def test_issue_credential(self, client, test_user):
        issuer = client.post("/api/v1/identity/did/create", json={
            "name": "Issuer", "email": "issuer2@test.com", "role": "admin"
        }, headers=test_user["headers"])
        subject = client.post("/api/v1/identity/did/create", json={
            "name": "Subject", "email": "subject2@test.com"
        }, headers=test_user["headers"])
        resp = client.post("/api/v1/identity/credential/issue", json={
            "issuer_did": issuer.json()["did_document"]["id"],
            "subject_did": subject.json()["did_document"]["id"],
            "credential_type": "kyc",
            "claims": {"country": "Spain"},
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "VerifiableCredential" in resp.json()["type"]

    def test_verify_credential(self, client, test_user):
        issuer = client.post("/api/v1/identity/did/create", json={
            "name": "I", "email": "i@test.com", "role": "admin"
        }, headers=test_user["headers"])
        subject = client.post("/api/v1/identity/did/create", json={
            "name": "S", "email": "s@test.com"
        }, headers=test_user["headers"])
        cred = client.post("/api/v1/identity/credential/issue", json={
            "issuer_did": issuer.json()["did_document"]["id"],
            "subject_did": subject.json()["did_document"]["id"],
            "credential_type": "developer",
            "claims": {"level": "senior"},
        }, headers=test_user["headers"])
        cred_id = cred.json()["id"]
        resp = client.get(f"/api/v1/identity/credential/{cred_id}/verify", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_identity_stats(self, client, test_user):
        resp = client.get("/api/v1/identity/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_dids" in resp.json()

    def test_singleton(self):
        assert get_identity_service() is get_identity_service()
