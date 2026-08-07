"""Tests for Webhooks + System Settings + Rate Limiter — Post-MVP Phase 9."""

import pytest
from app.services.webhook_subscriptions import (
    WebhookSubscriptionManager, get_webhook_manager, SUBSCRIBABLE_EVENTS,
    WebhookSubscription, WebhookDelivery,
)
from app.services.system_settings import (
    SystemSettingsManager, get_settings_manager, DEFAULT_SETTINGS,
)
from app.middleware.enhanced_rate_limit import EnhancedRateLimiter, get_rate_limiter


class TestWebhookSubscriptions:
    def test_create_subscription(self):
        mgr = WebhookSubscriptionManager()
        sub = mgr.create_subscription("https://example.com/hook", ["pipeline.completed"])
        assert sub.id is not None
        assert sub.url == "https://example.com/hook"
        assert "pipeline.completed" in sub.event_types
        assert sub.active is True

    def test_invalid_url(self):
        mgr = WebhookSubscriptionManager()
        with pytest.raises(ValueError, match="URL must start"):
            mgr.create_subscription("ftp://bad.url", ["pipeline.completed"])

    def test_invalid_event_type(self):
        mgr = WebhookSubscriptionManager()
        with pytest.raises(ValueError, match="Invalid event types"):
            mgr.create_subscription("https://example.com", ["invalid.event"])

    def test_get_subscription(self):
        mgr = WebhookSubscriptionManager()
        sub = mgr.create_subscription("https://example.com", ["pipeline.started"])
        retrieved = mgr.get_subscription(sub.id)
        assert retrieved is not None
        assert retrieved.url == "https://example.com"

    def test_get_nonexistent(self):
        mgr = WebhookSubscriptionManager()
        assert mgr.get_subscription("nonexistent") is None

    def test_list_subscriptions(self):
        mgr = WebhookSubscriptionManager()
        mgr.create_subscription("https://a.com", ["pipeline.completed"])
        mgr.create_subscription("https://b.com", ["pipeline.failed"])
        subs = mgr.list_subscriptions()
        assert len(subs) == 2

    def test_list_active_only(self):
        mgr = WebhookSubscriptionManager()
        sub = mgr.create_subscription("https://a.com", ["pipeline.completed"])
        mgr.deactivate(sub.id)
        active = mgr.list_subscriptions(active_only=True)
        assert len(active) == 0

    def test_update_subscription(self):
        mgr = WebhookSubscriptionManager()
        sub = mgr.create_subscription("https://a.com", ["pipeline.completed"], description="old")
        updated = mgr.update_subscription(sub.id, description="new", url="https://b.com")
        assert updated.description == "new"
        assert updated.url == "https://b.com"

    def test_update_nonexistent(self):
        mgr = WebhookSubscriptionManager()
        assert mgr.update_subscription("nonexistent", description="x") is None

    def test_delete_subscription(self):
        mgr = WebhookSubscriptionManager()
        sub = mgr.create_subscription("https://a.com", ["pipeline.completed"])
        assert mgr.delete_subscription(sub.id) is True
        assert mgr.get_subscription(sub.id) is None

    def test_delete_nonexistent(self):
        mgr = WebhookSubscriptionManager()
        assert mgr.delete_subscription("nonexistent") is False

    def test_activate_deactivate(self):
        mgr = WebhookSubscriptionManager()
        sub = mgr.create_subscription("https://a.com", ["pipeline.completed"])
        assert mgr.deactivate(sub.id) is True
        assert sub.active is False
        assert mgr.activate(sub.id) is True
        assert sub.active is True

    def test_deactivate_nonexistent(self):
        mgr = WebhookSubscriptionManager()
        assert mgr.deactivate("nonexistent") is False

    def test_get_deliveries_empty(self):
        mgr = WebhookSubscriptionManager()
        deliveries = mgr.get_deliveries()
        assert len(deliveries) == 0

    def test_get_stats(self):
        mgr = WebhookSubscriptionManager()
        mgr.create_subscription("https://a.com", ["pipeline.completed"])
        stats = mgr.get_stats()
        assert stats["total_subscriptions"] == 1
        assert stats["active_subscriptions"] == 1
        assert "pipeline.completed" in stats["subscribable_events"]

    def test_subscribable_events_complete(self):
        assert len(SUBSCRIBABLE_EVENTS) >= 15
        assert "pipeline.completed" in SUBSCRIBABLE_EVENTS
        assert "stage.failed" in SUBSCRIBABLE_EVENTS
        assert "system.alert" in SUBSCRIBABLE_EVENTS

    def test_delivery_to_dict(self):
        d = WebhookDelivery(subscription_id="x", event_type="test", payload={"a": 1})
        d_dict = d.to_dict()
        assert d_dict["subscription_id"] == "x"
        assert d_dict["event_type"] == "test"

    def test_subscription_to_dict(self):
        s = WebhookSubscription(url="https://a.com", event_types=["pipeline.completed"])
        s_dict = s.to_dict()
        assert s_dict["url"] == "https://a.com"
        assert s_dict["active"] is True


class TestWebhookAPI:
    def test_list_events_api(self, client, test_user):
        resp = client.get("/api/v1/webhooks/events", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_webhook_api(self, client, test_user):
        resp = client.post("/api/v1/webhooks/", json={
            "url": "https://example.com/hook",
            "event_types": ["pipeline.completed"],
            "description": "Test webhook",
        }, headers=test_user["headers"])
        assert resp.status_code == 201
        assert resp.json()["url"] == "https://example.com/hook"

    def test_create_invalid_event_api(self, client, test_user):
        resp = client.post("/api/v1/webhooks/", json={
            "url": "https://example.com",
            "event_types": ["invalid.event"],
        }, headers=test_user["headers"])
        assert resp.status_code == 422

    def test_list_subscriptions_api(self, client, test_user):
        client.post("/api/v1/webhooks/", json={
            "url": "https://a.com", "event_types": ["pipeline.completed"],
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/webhooks/", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_subscription_api(self, client, test_user):
        create = client.post("/api/v1/webhooks/", json={
            "url": "https://a.com", "event_types": ["pipeline.completed"],
        }, headers=test_user["headers"])
        sub_id = create.json()["id"]
        resp = client.get(f"/api/v1/webhooks/{sub_id}", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_update_subscription_api(self, client, test_user):
        create = client.post("/api/v1/webhooks/", json={
            "url": "https://a.com", "event_types": ["pipeline.completed"],
        }, headers=test_user["headers"])
        sub_id = create.json()["id"]
        resp = client.patch(f"/api/v1/webhooks/{sub_id}", json={"description": "Updated"}, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated"

    def test_delete_subscription_api(self, client, test_user):
        create = client.post("/api/v1/webhooks/", json={
            "url": "https://a.com", "event_types": ["pipeline.completed"],
        }, headers=test_user["headers"])
        sub_id = create.json()["id"]
        resp = client.delete(f"/api/v1/webhooks/{sub_id}", headers=test_user["headers"])
        assert resp.status_code == 204

    def test_deactivate_activate_api(self, client, test_user):
        create = client.post("/api/v1/webhooks/", json={
            "url": "https://a.com", "event_types": ["pipeline.completed"],
        }, headers=test_user["headers"])
        sub_id = create.json()["id"]
        resp = client.post(f"/api/v1/webhooks/{sub_id}/deactivate", headers=test_user["headers"])
        assert resp.status_code == 200
        resp = client.post(f"/api/v1/webhooks/{sub_id}/activate", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_stats_api(self, client, test_user):
        resp = client.get("/api/v1/webhooks/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_subscriptions" in resp.json()

    def test_recent_deliveries_api(self, client, test_user):
        resp = client.get("/api/v1/webhooks/deliveries/recent", headers=test_user["headers"])
        assert resp.status_code == 200


class TestSystemSettings:
    def test_get_default_value(self):
        mgr = SystemSettingsManager()
        assert mgr.get("ai.default_model") == "gpt-4o"
        assert mgr.get("api.rate_limit.per_minute") == 100

    def test_set_override(self):
        mgr = SystemSettingsManager()
        mgr.set("api.rate_limit.per_minute", 200)
        assert mgr.get("api.rate_limit.per_minute") == 200

    def test_reset_override(self):
        mgr = SystemSettingsManager()
        mgr.set("api.rate_limit.per_minute", 200)
        assert mgr.reset("api.rate_limit.per_minute") is True
        assert mgr.get("api.rate_limit.per_minute") == 100

    def test_reset_nonexistent_override(self):
        mgr = SystemSettingsManager()
        assert mgr.reset("ai.default_model") is False

    def test_unknown_setting(self):
        mgr = SystemSettingsManager()
        with pytest.raises(ValueError, match="Unknown setting"):
            mgr.set("nonexistent.setting", True)

    def test_type_validation_bool(self):
        mgr = SystemSettingsManager()
        with pytest.raises(ValueError, match="expects bool"):
            mgr.set("feature.pipelines.enabled", "not_a_bool")

    def test_type_validation_int(self):
        mgr = SystemSettingsManager()
        with pytest.raises(ValueError, match="expects int"):
            mgr.set("api.rate_limit.per_minute", "not_an_int")

    def test_type_validation_float(self):
        mgr = SystemSettingsManager()
        with pytest.raises(ValueError, match="expects float"):
            mgr.set("ai.default_temperature", "not_a_float")

    def test_list_all(self):
        mgr = SystemSettingsManager()
        settings = mgr.list_all()
        assert len(settings) >= 30
        for s in settings:
            assert "key" in s
            assert "value" in s
            assert "default" in s
            assert "type" in s
            assert "category" in s
            assert "overridden" in s

    def test_list_by_category(self):
        mgr = SystemSettingsManager()
        ai_settings = mgr.list_by_category("ai")
        assert all(s["category"] == "ai" for s in ai_settings)
        assert len(ai_settings) >= 4

    def test_get_categories(self):
        mgr = SystemSettingsManager()
        cats = mgr.get_categories()
        assert "features" in cats
        assert "api" in cats
        assert "ai" in cats

    def test_export_import(self):
        mgr1 = SystemSettingsManager()
        mgr1.set("api.rate_limit.per_minute", 500)
        exported = mgr1.export_settings()
        assert exported["api.rate_limit.per_minute"] == 500

        mgr2 = SystemSettingsManager()
        count = mgr2.import_settings({"api.rate_limit.per_minute": 500})
        assert count == 1
        assert mgr2.get("api.rate_limit.per_minute") == 500

    def test_reset_all(self):
        mgr = SystemSettingsManager()
        mgr.set("api.rate_limit.per_minute", 999)
        mgr.set("ai.default_model", "gpt-4o-mini")
        mgr.reset_all()
        assert mgr.get("api.rate_limit.per_minute") == 100
        assert mgr.get("ai.default_model") == "gpt-4o"

    def test_default_settings_count(self):
        assert len(DEFAULT_SETTINGS) >= 30


class TestSystemSettingsAPI:
    def test_list_settings_api(self, client, test_user):
        resp = client.get("/api/v1/system-settings/", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 30

    def test_list_by_category_api(self, client, test_user):
        resp = client.get("/api/v1/system-settings/?category=ai", headers=test_user["headers"])
        assert resp.status_code == 200
        assert all(s["category"] == "ai" for s in resp.json())

    def test_get_categories_api(self, client, test_user):
        resp = client.get("/api/v1/system-settings/categories", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "features" in resp.json()

    def test_get_setting_api(self, client, test_user):
        resp = client.get("/api/v1/system-settings/ai.default_model", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["value"] == "gpt-4o"

    def test_set_setting_api(self, client, test_user):
        resp = client.put("/api/v1/system-settings/", json={
            "key": "api.rate_limit.per_minute", "value": 200,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["value"] == 200

    def test_reset_setting_api(self, client, test_user):
        client.put("/api/v1/system-settings/", json={
            "key": "api.rate_limit.per_minute", "value": 200,
        }, headers=test_user["headers"])
        resp = client.delete("/api/v1/system-settings/api.rate_limit.per_minute", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["value"] == 100

    def test_export_settings_api(self, client, test_user):
        resp = client.get("/api/v1/system-settings/export/all", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "ai.default_model" in resp.json()

    def test_import_settings_api(self, client, test_user):
        resp = client.post("/api/v1/system-settings/import", json={
            "api.rate_limit.per_minute": 300,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["imported"] == 1


class TestRateLimiter:
    def test_check_allowed(self):
        limiter = EnhancedRateLimiter()
        allowed, headers = limiter.check("test_key", 10, 60)
        assert allowed is True
        assert "X-RateLimit-Remaining" in headers

    def test_check_exceeds_limit(self):
        limiter = EnhancedRateLimiter()
        for _ in range(5):
            limiter.check("test_key", 5, 60)
        allowed, _ = limiter.check("test_key", 5, 60)
        assert allowed is False

    def test_rate_limit_headers(self):
        limiter = EnhancedRateLimiter()
        _, headers = limiter.check("k", 100, 60)
        assert headers["X-RateLimit-Limit"] == "100"
        assert int(headers["X-RateLimit-Remaining"]) == 99

    def test_disabled_limiter(self):
        limiter = EnhancedRateLimiter()
        limiter.set_enabled(False)
        allowed, headers = limiter.check("k", 1, 60)
        assert allowed is True
        assert headers == {}

    def test_get_stats(self):
        limiter = EnhancedRateLimiter()
        limiter.check("k1", 100, 60)
        limiter.check("k2", 100, 60)
        stats = limiter.get_stats()
        assert stats["enabled"] is True
        assert stats["tracked_keys"] == 2

    def test_cleanup_expired(self):
        limiter = EnhancedRateLimiter()
        limiter.check("k", 100, 1)  # 1 second window
        import time; time.sleep(2)
        limiter.cleanup_expired(max_age_seconds=1)
        stats = limiter.get_stats()
        assert stats["tracked_keys"] == 0


class TestRateLimiterAPI:
    def test_stats_api(self, client, test_user):
        resp = client.get("/api/v1/rate-limiter/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "enabled" in resp.json()

    def test_toggle_api(self, client, test_user):
        resp = client.post("/api/v1/rate-limiter/toggle?enabled=false", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_cleanup_api(self, client, test_user):
        resp = client.post("/api/v1/rate-limiter/cleanup", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "tracked_keys" in resp.json()
