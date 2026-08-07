"""Tests for Documentation & Deployment Manifests — Phase 51."""

import pytest
from app.services.deployment_docs import (
    DeploymentDocsService, get_deployment_docs_service, DocCategory, DocStatus, ManifestType,
)


class TestDocs:
    def test_list_docs(self):
        service = DeploymentDocsService()
        docs = service.list_docs()
        assert len(docs) > 0

    def test_filter_by_category(self):
        service = DeploymentDocsService()
        arch = service.list_docs(category="architecture")
        assert all(d.category == "architecture" for d in arch)

    def test_get_doc(self):
        service = DeploymentDocsService()
        docs = service.list_docs(limit=1)
        doc = service.get_doc(docs[0].id)
        assert doc is not None

    def test_search_docs(self):
        service = DeploymentDocsService()
        results = service.search_docs("blockchain")
        assert len(results) > 0

    def test_search_docs_no_results(self):
        service = DeploymentDocsService()
        results = service.search_docs("nonexistent_zzz")
        assert len(results) == 0

    def test_create_doc(self):
        service = DeploymentDocsService()
        doc = service.create_doc("Test", "general", "Test desc", "Test content")
        assert doc.id.startswith("doc-")
        assert doc.title == "Test"

    def test_update_doc(self):
        service = DeploymentDocsService()
        doc = service.create_doc("Test Update", "general", "desc", "content")
        updated = service.update_doc(doc.id, title="Updated Title")
        assert updated.title == "Updated Title"

    def test_delete_doc(self):
        service = DeploymentDocsService()
        doc = service.create_doc("Delete Me", "general", "desc", "content")
        assert service.delete_doc(doc.id) is True
        assert service.get_doc(doc.id) is None


class TestManifests:
    def test_list_manifests(self):
        service = DeploymentDocsService()
        manifests = service.list_manifests()
        assert len(manifests) >= 7

    def test_filter_by_type(self):
        service = DeploymentDocsService()
        docker = service.list_manifests(type="docker-compose")
        assert all(m.type == "docker-compose" for m in docker)

    def test_get_manifest(self):
        service = DeploymentDocsService()
        manifests = service.list_manifests(limit=1)
        m = service.get_manifest(manifests[0].id)
        assert m is not None

    def test_get_by_filename(self):
        service = DeploymentDocsService()
        m = service.get_manifest_by_filename("docker-compose.prod.yml")
        assert m is not None
        assert m.name == "Docker Compose Production"

    def test_create_manifest(self):
        service = DeploymentDocsService()
        m = service.create_manifest("Test", "dockerfile", "test", "Dockerfile.test", "FROM scratch")
        assert m.id.startswith("man-")


class TestFAQs:
    def test_list_faqs(self):
        service = DeploymentDocsService()
        faqs = service.list_faqs()
        assert len(faqs) >= 10

    def test_filter_by_category(self):
        service = DeploymentDocsService()
        general = service.list_faqs(category="general")
        assert all(f.category == "general" for f in general)

    def test_search_faqs(self):
        service = DeploymentDocsService()
        results = service.search_faqs("stake")
        assert len(results) > 0

    def test_create_faq(self):
        service = DeploymentDocsService()
        f = service.create_faq("Test Q?", "Test A.", "test")
        assert f.id.startswith("faq-")

    def test_mark_helpful(self):
        service = DeploymentDocsService()
        faqs = service.list_faqs(limit=1)
        before = faqs[0].helpful_count
        marked = service.mark_faq_helpful(faqs[0].id)
        assert marked.helpful_count == before + 1


class TestRunbooks:
    def test_list_runbooks(self):
        service = DeploymentDocsService()
        runbooks = service.list_runbooks()
        assert len(runbooks) >= 5

    def test_filter_by_severity(self):
        service = DeploymentDocsService()
        critical = service.list_runbooks(severity="critical")
        assert all(r.severity == "critical" for r in critical)

    def test_get_runbook(self):
        service = DeploymentDocsService()
        runbooks = service.list_runbooks(limit=1)
        r = service.get_runbook(runbooks[0].id)
        assert r is not None

    def test_create_runbook(self):
        service = DeploymentDocsService()
        r = service.create_runbook("Test RB", "Test scenario", ["step1", "step2"])
        assert r.id.startswith("rb-")


class TestDashboard:
    def test_dashboard(self):
        service = DeploymentDocsService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert dash["stats"]["total_docs"] > 0
        assert dash["stats"]["total_manifests"] > 0
        assert dash["stats"]["total_faqs"] > 0
        assert dash["stats"]["total_runbooks"] > 0


class TestDocsAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/docs/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_docs(self, client, test_user):
        resp = client.get("/api/v1/docs/", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_search_docs(self, client, test_user):
        resp = client.get("/api/v1/docs/search?q=blockchain", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_manifests(self, client, test_user):
        resp = client.get("/api/v1/docs/manifests", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_faqs(self, client, test_user):
        resp = client.get("/api/v1/docs/faqs", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_search_faqs(self, client, test_user):
        resp = client.get("/api/v1/docs/faqs/search?q=stake", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_runbooks(self, client, test_user):
        resp = client.get("/api/v1/docs/runbooks", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_deployment_docs_service() is get_deployment_docs_service()
