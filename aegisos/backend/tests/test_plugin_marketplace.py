"""Tests for Plugin Marketplace — Phase 39."""

import pytest
from app.services.plugin_marketplace import (
    PluginMarketplaceService, get_plugin_marketplace_service, PluginStatus, PluginCategory,
)


class TestSubmission:
    def test_submit_plugin(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("My Plugin", "Test desc", "0xauthor", "1.0.0", "utility")
        assert p.id.startswith("plg-")
        assert p.status == "submitted"
        assert p.slug == "my-plugin"

    def test_submit_duplicate_name(self):
        service = PluginMarketplaceService()
        p1 = service.submit_plugin("Test Plugin", "Desc", "0x1", "1.0.0", "utility")
        p2 = service.submit_plugin("Test Plugin", "Desc", "0x2", "1.0.0", "utility")
        assert p1.slug != p2.slug

    def test_get_plugin(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Get Me", "Desc", "0x1", "1.0.0", "utility")
        found = service.get_plugin(p.id)
        assert found is not None

    def test_get_by_slug(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Slug Test", "Desc", "0x1", "1.0.0", "utility")
        found = service.get_plugin_by_slug(p.slug)
        assert found is not None

    def test_list_plugins(self):
        service = PluginMarketplaceService()
        all_p = service.list_plugins()
        assert len(all_p) >= 8  # Default plugins

    def test_list_by_category(self):
        service = PluginMarketplaceService()
        monitoring = service.list_plugins(category="monitoring")
        assert all(p.category == "monitoring" for p in monitoring)

    def test_list_by_status(self):
        service = PluginMarketplaceService()
        approved = service.list_plugins(status="approved")
        assert all(p.status == "approved" for p in approved)

    def test_list_by_author(self):
        service = PluginMarketplaceService()
        verdis = service.list_plugins(author="Verdis Team")
        assert all(p.author == "Verdis Team" for p in verdis)

    def test_search(self):
        service = PluginMarketplaceService()
        results = service.list_plugins(search="carbon")
        assert any("carbon" in p.name.lower() or "carbon" in p.description.lower() for p in results)

    def test_sort_by_rating(self):
        service = PluginMarketplaceService()
        by_rating = service.list_plugins(sort_by="rating")
        ratings = [p.rating for p in by_rating]
        assert ratings == sorted(ratings, reverse=True)


class TestApproval:
    def test_approve_plugin(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Approve Me", "Desc", "0x1", "1.0.0", "utility")
        approved = service.approve_plugin(p.id)
        assert approved.status == "approved"
        assert approved.approved_at != ""

    def test_reject_plugin(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Reject Me", "Desc", "0x1", "1.0.0", "utility")
        rejected = service.reject_plugin(p.id, "Security issues")
        assert rejected.status == "rejected"
        assert rejected.rejection_reason == "Security issues"

    def test_suspend_plugin(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Suspend Me", "Desc", "0x1", "1.0.0", "utility")
        service.approve_plugin(p.id)
        suspended = service.suspend_plugin(p.id)
        assert suspended.status == "suspended"

    def test_deprecate_plugin(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        deprecated = service.deprecate_plugin(p.id)
        assert deprecated.status == "deprecated"

    def test_approve_already_approved(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Test", "Desc", "0x1", "1.0.0", "utility")
        service.approve_plugin(p.id)
        result = service.approve_plugin(p.id)
        assert result is None

    def test_update_plugin(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Update Me", "Desc", "0x1", "1.0.0", "utility")
        updated = service.update_plugin(p.id, description="New desc", version="1.1.0")
        assert updated.description == "New desc"
        assert updated.version == "1.1.0"


class TestInstallation:
    def test_install_plugin(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        installed = service.install_plugin(p.id, "0xuser1")
        assert "0xuser1" in installed.installs

    def test_install_non_approved(self):
        service = PluginMarketplaceService()
        p = service.submit_plugin("Pending", "Desc", "0x1", "1.0.0", "utility")
        result = service.install_plugin(p.id, "0xuser")
        assert result is None

    def test_double_install(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        service.install_plugin(p.id, "0xuser")
        before = p.downloads
        service.install_plugin(p.id, "0xuser")
        assert p.downloads == before  # No duplicate

    def test_uninstall(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        service.install_plugin(p.id, "0xuser")
        assert service.uninstall_plugin(p.id, "0xuser") is True
        assert "0xuser" not in p.installs

    def test_get_installed(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        service.install_plugin(p.id, "0xuser")
        installed = service.get_installed_plugins("0xuser")
        assert any(i.id == p.id for i in installed)


class TestReviews:
    def test_add_review(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        r = service.add_review(p.id, "0xreviewer", 5, "Great plugin!")
        assert r.rating == 5
        assert p.rating_count >= 1

    def test_double_review(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        service.add_review(p.id, "0xrev", 5, "Great")
        result = service.add_review(p.id, "0xrev", 3, "Changed mind")
        assert result is None

    def test_invalid_rating(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        assert service.add_review(p.id, "0xrev", 6, "Too high") is None
        assert service.add_review(p.id, "0xrev", 0, "Too low") is None

    def test_review_updates_rating(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        service.add_review(p.id, "0x1", 4, "Good")
        service.add_review(p.id, "0x2", 5, "Great")
        assert p.rating == 4.5

    def test_mark_helpful(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        r = service.add_review(p.id, "0xrev", 5, "Good")
        assert service.mark_review_helpful(r.id) is True
        assert r.helpful == 1

    def test_get_reviews(self):
        service = PluginMarketplaceService()
        p = service.list_plugins(status="approved")[0]
        service.add_review(p.id, "0x1", 5, "A")
        service.add_review(p.id, "0x2", 4, "B")
        reviews = service.get_reviews(p.id)
        assert len(reviews) >= 2


class TestDevelopers:
    def test_register_developer(self):
        service = PluginMarketplaceService()
        dev = service.register_developer("0xnew", "New Dev", bio="Developer")
        assert dev.name == "New Dev"
        assert dev.bio == "Developer"

    def test_verify_developer(self):
        service = PluginMarketplaceService()
        service.register_developer("0xdev", "Dev")
        assert service.verify_developer("0xdev") is True
        assert service.get_developer("0xdev").verified is True

    def test_list_developers(self):
        service = PluginMarketplaceService()
        devs = service.list_developers()
        assert len(devs) >= 1

    def test_list_verified_only(self):
        service = PluginMarketplaceService()
        service.register_developer("0xunverified", "Unverified")
        verified = service.list_developers(verified_only=True)
        assert all(d.verified for d in verified)


class TestCategories:
    def test_list_categories(self):
        service = PluginMarketplaceService()
        cats = service.list_categories()
        assert len(cats) >= 8
        assert all("count" in c for c in cats)


class TestStats:
    def test_stats(self):
        service = PluginMarketplaceService()
        stats = service.get_stats()
        assert stats["total_plugins"] >= 8
        assert stats["approved"] >= 8
        assert stats["total_downloads"] > 0

    def test_dashboard(self):
        service = PluginMarketplaceService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "featured" in dash
        assert "popular" in dash
        assert "newest" in dash
        assert "categories" in dash


class TestPluginAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/plugins/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "stats" in resp.json()

    def test_list_plugins(self, client, test_user):
        resp = client.get("/api/v1/plugins", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 8

    def test_submit(self, client, test_user):
        resp = client.post("/api/v1/plugins/", json={
            "name": "API Plugin", "description": "Test", "author": "0xapi",
            "version": "1.0.0", "category": "utility",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("plg-")

    def test_install(self, client, test_user):
        plugins = client.get("/api/v1/plugins", headers=test_user["headers"]).json()
        pid = plugins[0]["id"]
        resp = client.post(f"/api/v1/plugins/{pid}/install?user_address=0xtest", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_review(self, client, test_user):
        plugins = client.get("/api/v1/plugins", headers=test_user["headers"]).json()
        pid = plugins[0]["id"]
        resp = client.post(f"/api/v1/plugins/{pid}/reviews", json={
            "reviewer": "0xrev", "rating": 5, "comment": "Great!",
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_categories(self, client):
        resp = client.get("/api/v1/plugins/categories/list")
        assert resp.status_code == 200
        assert len(resp.json()) >= 8

    def test_singleton(self):
        assert get_plugin_marketplace_service() is get_plugin_marketplace_service()
