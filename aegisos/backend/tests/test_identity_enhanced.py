"""Tests for Enhanced Identity — Phase 31."""

import pytest
from app.services.identity import get_identity_service, CredentialType
from app.services.identity_enhanced import get_identity_enhanced_service, CredentialSchema


class TestSchemas:
    def test_get_schema_kyc(self):
        service = get_identity_enhanced_service()
        schema = service.get_schema("kyc")
        assert schema is not None
        assert "country" in schema.required_fields
        assert "verified" in schema.required_fields

    def test_get_schema_green_validator(self):
        service = get_identity_enhanced_service()
        schema = service.get_schema("green_validator")
        assert schema is not None
        assert "score" in schema.required_fields

    def test_get_nonexistent_schema(self):
        service = get_identity_enhanced_service()
        assert service.get_schema("nonexistent") is None

    def test_list_schemas(self):
        service = get_identity_enhanced_service()
        schemas = service.list_schemas()
        assert len(schemas) >= 6  # 6 default schemas

    def test_create_custom_schema(self):
        service = get_identity_enhanced_service()
        schema = service.create_custom_schema(
            "custom_cert", "Custom Cert", "Test",
            ["name"], ["extra"], {"name": "string", "extra": "number"},
        )
        assert schema.type == "custom_cert"
        assert "name" in schema.required_fields

    def test_validate_claims_valid(self):
        service = get_identity_enhanced_service()
        valid, errors = service.validate_claims("kyc", {"country": "Spain", "verified": True})
        assert valid is True
        assert errors == []

    def test_validate_claims_missing_required(self):
        service = get_identity_enhanced_service()
        valid, errors = service.validate_claims("kyc", {"country": "Spain"})
        assert valid is False
        assert any("verified" in e for e in errors)

    def test_validate_claims_wrong_type(self):
        service = get_identity_enhanced_service()
        valid, errors = service.validate_claims("kyc", {"country": "Spain", "verified": "not_bool"})
        assert valid is False
        assert any("boolean" in e for e in errors)

    def test_validate_claims_no_schema(self):
        service = get_identity_enhanced_service()
        valid, errors = service.validate_claims("unknown_type", {"any": "thing"})
        assert valid is True

    def test_all_default_schemas_have_required_fields(self):
        service = get_identity_enhanced_service()
        for schema in service.list_schemas():
            assert len(schema.required_fields) > 0, f"Schema {schema.type} has no required fields"


class TestDIDResolution:
    def test_resolve_existing_did(self):
        id_service = get_identity_service()
        enhanced = get_identity_enhanced_service()
        doc, _ = id_service.create_did("Test", "resolve@test.com")
        result = enhanced.resolve_did(doc.id)
        assert result.resolved is True
        assert result.did_document is not None
        assert result.profile is not None
        assert result.profile["name"] == "Test"

    def test_resolve_nonexistent_did(self):
        enhanced = get_identity_enhanced_service()
        result = enhanced.resolve_did("did:verdis:nonexistent")
        assert result.resolved is False
        assert "not found" in result.error


class TestPresentations:
    def setup_method(self):
        self.id_service = get_identity_service()
        self.enhanced = get_identity_enhanced_service()
        # Create issuer and holder
        self.issuer_doc, self.issuer_key = self.id_service.create_did("Issuer", f"issuer_pres_{self.__class__.__name__}@test.com", "admin")
        self.holder_doc, _ = self.id_service.create_did("Holder", f"holder_pres_{self.__class__.__name__}@test.com")
        # Issue a credential
        self.cred = self.id_service.issue_credential(
            self.issuer_doc.id, self.holder_doc.id, CredentialType.KYC,
            {"country": "Spain", "verified": True}, issuer_key=self.issuer_key,
        )

    def test_create_presentation(self):
        pres = self.enhanced.create_presentation(
            self.holder_doc.id, [self.cred.id],
        )
        assert pres.holder == self.holder_doc.id
        assert len(pres.credentials) == 1
        assert "VerifiablePresentation" in pres.type
        assert pres.challenge is not None

    def test_create_presentation_with_verifier(self):
        verifier_doc, _ = self.id_service.create_did("Verifier", f"verifier_pres_{self.__class__.__name__}@test.com")
        pres = self.enhanced.create_presentation(
            self.holder_doc.id, [self.cred.id], verifier_did=verifier_doc.id,
        )
        assert pres.verifier == verifier_doc.id

    def test_create_presentation_selective_disclosure(self):
        # Issue a credential with more fields
        cred2 = self.id_service.issue_credential(
            self.issuer_doc.id, self.holder_doc.id, CredentialType.CARBON_CREDIT,
            {"credits": 100, "project": "Amazon", "location": "Brazil"},
            issuer_key=self.issuer_key,
        )
        pres = self.enhanced.create_presentation(
            self.holder_doc.id, [cred2.id],
            selective_fields={cred2.id: ["project"]},
        )
        assert pres.credentials[0]["claims"] == {"project": "Amazon"}
        assert pres.credentials[0].get("_selective_disclosure") is True

    def test_create_presentation_wrong_holder(self):
        other_doc, _ = self.id_service.create_did("Other", f"other_pres_{self.__class__.__name__}@test.com")
        with pytest.raises(ValueError, match="does not belong"):
            self.enhanced.create_presentation(other_doc.id, [self.cred.id])

    def test_create_presentation_nonexistent_holder(self):
        with pytest.raises(ValueError, match="Holder DID not found"):
            self.enhanced.create_presentation("did:verdis:nonexistent", [self.cred.id])

    def test_create_presentation_nonexistent_credential(self):
        with pytest.raises(ValueError, match="Credential"):
            self.enhanced.create_presentation(self.holder_doc.id, ["nonexistent-cred"])

    def test_verify_presentation(self):
        pres = self.enhanced.create_presentation(
            self.holder_doc.id, [self.cred.id],
        )
        result = self.enhanced.verify_presentation(pres.id)
        assert result["valid"] is True
        assert result["credential_count"] == 1

    def test_verify_presentation_with_challenge(self):
        pres = self.enhanced.create_presentation(
            self.holder_doc.id, [self.cred.id], challenge="my-challenge",
        )
        assert pres.challenge == "my-challenge"

    def test_verify_nonexistent_presentation(self):
        result = self.enhanced.verify_presentation("nonexistent")
        assert result["valid"] is False

    def test_get_presentation(self):
        pres = self.enhanced.create_presentation(self.holder_doc.id, [self.cred.id])
        found = self.enhanced.get_presentation(pres.id)
        assert found is not None
        assert found.id == pres.id

    def test_list_presentations(self):
        self.enhanced.create_presentation(self.holder_doc.id, [self.cred.id])
        pres_list = self.enhanced.list_presentations(self.holder_doc.id)
        assert len(pres_list) >= 1

    def test_list_presentations_filter(self):
        other_doc, _ = self.id_service.create_did("Other2", f"other2_pres_{self.__class__.__name__}@test.com")
        self.enhanced.create_presentation(self.holder_doc.id, [self.cred.id])
        other_list = self.enhanced.list_presentations(other_doc.id)
        assert len(other_list) == 0


class TestSDKInfo:
    def test_sdk_info(self):
        service = get_identity_enhanced_service()
        info = service.get_developer_sdk_info()
        assert info["version"] == "1.0.0"
        assert info["did_method"] == "did:verdis"
        assert "kyc" in info["credential_types"]
        assert "create_did" in info["endpoints"]
        assert "example" in info

    def test_sdk_info_has_all_endpoints(self):
        service = get_identity_enhanced_service()
        info = service.get_developer_sdk_info()
        endpoints = info["endpoints"]
        assert "create_did" in endpoints
        assert "resolve_did" in endpoints
        assert "issue_credential" in endpoints
        assert "verify_credential" in endpoints
        assert "create_presentation" in endpoints
        assert "verify_presentation" in endpoints


class TestEnhancedIdentityAPI:
    def test_get_schema(self, client, test_user):
        resp = client.get("/api/v1/identity-enhanced/schema/kyc", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "country" in resp.json()["required_fields"]

    def test_list_schemas(self, client, test_user):
        resp = client.get("/api/v1/identity-enhanced/schemas", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 6

    def test_validate_claims(self, client, test_user):
        resp = client.post("/api/v1/identity-enhanced/validate", json={
            "credential_type": "kyc", "claims": {"country": "Spain", "verified": True},
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_claims_invalid(self, client, test_user):
        resp = client.post("/api/v1/identity-enhanced/validate", json={
            "credential_type": "kyc", "claims": {"country": "Spain"},
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    def test_resolve_did(self, client, test_user):
        create = client.post("/api/v1/identity/did/create", json={
            "name": "Resolve", "email": "resolve_api@test.com",
        }, headers=test_user["headers"])
        did = create.json()["did_document"]["id"]
        resp = client.get(f"/api/v1/identity-enhanced/resolve/{did}", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["resolved"] is True

    def test_create_presentation(self, client, test_user):
        issuer = client.post("/api/v1/identity/did/create", json={
            "name": "I", "email": "pres_i@test.com", "role": "admin",
        }, headers=test_user["headers"])
        holder = client.post("/api/v1/identity/did/create", json={
            "name": "H", "email": "pres_h@test.com",
        }, headers=test_user["headers"])
        cred = client.post("/api/v1/identity/credential/issue", json={
            "issuer_did": issuer.json()["did_document"]["id"],
            "subject_did": holder.json()["did_document"]["id"],
            "credential_type": "kyc",
            "claims": {"country": "Spain", "verified": True},
        }, headers=test_user["headers"])
        resp = client.post("/api/v1/identity-enhanced/presentation/create", json={
            "holder_did": holder.json()["did_document"]["id"],
            "credential_ids": [cred.json()["id"]],
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "VerifiablePresentation" in resp.json()["type"]

    def test_verify_presentation(self, client, test_user):
        issuer = client.post("/api/v1/identity/did/create", json={
            "name": "I2", "email": "vp_i@test.com", "role": "admin",
        }, headers=test_user["headers"])
        holder = client.post("/api/v1/identity/did/create", json={
            "name": "H2", "email": "vp_h@test.com",
        }, headers=test_user["headers"])
        cred = client.post("/api/v1/identity/credential/issue", json={
            "issuer_did": issuer.json()["did_document"]["id"],
            "subject_did": holder.json()["did_document"]["id"],
            "credential_type": "developer",
            "claims": {"level": "senior"},
        }, headers=test_user["headers"])
        pres = client.post("/api/v1/identity-enhanced/presentation/create", json={
            "holder_did": holder.json()["did_document"]["id"],
            "credential_ids": [cred.json()["id"]],
        }, headers=test_user["headers"])
        pres_id = pres.json()["id"]
        resp = client.get(f"/api/v1/identity-enhanced/presentation/{pres_id}/verify", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_sdk_info(self, client):
        resp = client.get("/api/v1/identity-enhanced/sdk-info")
        assert resp.status_code == 200
        assert resp.json()["did_method"] == "did:verdis"

    def test_singleton(self):
        assert get_identity_enhanced_service() is get_identity_enhanced_service()
