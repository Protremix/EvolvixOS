"""Tests for Notification Center — Phase 40."""

import pytest
import time
from app.services.notifications import (
    NotificationService, get_notification_service,
    NotificationType, NotificationSeverity,
)


class TestCreate:
    def test_create_notification(self):
        service = NotificationService()
        n = service.create_notification("0xuser", "system", "info", "Test", "Hello")
        assert n.id.startswith("notif-")
        assert n.read is False
        assert n.user_address == "0xuser"

    def test_create_with_action(self):
        service = NotificationService()
        n = service.create_notification("0xuser", "transaction", "info", "Tx", "Confirmed",
                                         action_url="/tx/123", action_label="View")
        assert n.action_url == "/tx/123"
        assert n.action_label == "View"

    def test_create_with_expiry(self):
        service = NotificationService()
        n = service.create_notification("0xuser", "system", "info", "Temp", "Expires", expires_hours=24)
        assert n.expires != ""

    def test_create_disabled_user(self):
        service = NotificationService()
        service.update_preferences("0xdisabled", enabled=False)
        n = service.create_notification("0xdisabled", "system", "info", "Test", "Hello")
        assert n is None

    def test_create_filtered_type(self):
        service = NotificationService()
        service.update_preferences("0xuser", type_filters={"governance": False})
        n = service.create_notification("0xuser", "governance", "info", "Gov", "Vote!")
        assert n is None

    def test_create_filtered_severity(self):
        service = NotificationService()
        service.update_preferences("0xuser", min_severity="warning")
        n = service.create_notification("0xuser", "system", "info", "Low", "Info")
        assert n is None  # info is below warning
        n2 = service.create_notification("0xuser", "system", "warning", "Mid", "Warning")
        assert n2 is not None


class TestList:
    def test_list_notifications(self):
        service = NotificationService()
        service.create_notification("0xuser", "system", "info", "A", "msg")
        service.create_notification("0xuser", "system", "info", "B", "msg")
        notifs = service.list_notifications("0xuser")
        assert len(notifs) >= 2

    def test_list_unread_only(self):
        service = NotificationService()
        n1 = service.create_notification("0xuser", "system", "info", "A", "msg")
        n2 = service.create_notification("0xuser", "system", "info", "B", "msg")
        service.mark_read(n1.id)
        unread = service.list_notifications("0xuser", unread_only=True)
        assert all(not n.read for n in unread)

    def test_list_by_type(self):
        service = NotificationService()
        service.create_notification("0xuser", "system", "info", "A", "msg")
        service.create_notification("0xuser", "governance", "info", "B", "msg")
        system = service.list_notifications("0xuser", type="system")
        assert all(n.type == "system" for n in system)

    def test_list_by_severity(self):
        service = NotificationService()
        service.create_notification("0xuser", "system", "info", "A", "msg")
        service.create_notification("0xuser", "system", "critical", "B", "msg")
        critical = service.list_notifications("0xuser", severity="critical")
        assert all(n.severity == "critical" for n in critical)

    def test_unread_count(self):
        service = NotificationService()
        service.create_notification("0xuser", "system", "info", "A", "msg")
        service.create_notification("0xuser", "system", "info", "B", "msg")
        assert service.get_unread_count("0xuser") >= 2


class TestActions:
    def test_mark_read(self):
        service = NotificationService()
        n = service.create_notification("0xuser", "system", "info", "Test", "msg")
        assert service.mark_read(n.id) is True
        assert n.read is True
        assert n.read_at != ""

    def test_mark_all_read(self):
        service = NotificationService()
        service.create_notification("0xuser", "system", "info", "A", "msg")
        service.create_notification("0xuser", "system", "info", "B", "msg")
        count = service.mark_all_read("0xuser")
        assert count >= 2

    def test_delete_notification(self):
        service = NotificationService()
        n = service.create_notification("0xuser", "system", "info", "Test", "msg")
        assert service.delete_notification(n.id) is True
        assert service.get_notification(n.id) is None

    def test_clear_read(self):
        service = NotificationService()
        n1 = service.create_notification("0xuser", "system", "info", "A", "msg")
        n2 = service.create_notification("0xuser", "system", "info", "B", "msg")
        service.mark_read(n1.id)
        service.mark_read(n2.id)
        cleared = service.clear_read("0xuser")
        assert cleared >= 2


class TestPreferences:
    def test_get_default_preferences(self):
        service = NotificationService()
        prefs = service.get_preferences("0xnew")
        assert prefs.enabled is True
        assert prefs.channels["in_app"] is True

    def test_update_preferences(self):
        service = NotificationService()
        prefs = service.update_preferences("0xuser", enabled=False, min_severity="error")
        assert prefs.enabled is False
        assert prefs.min_severity == "error"

    def test_update_type_filters(self):
        service = NotificationService()
        prefs = service.update_preferences("0xuser", type_filters={"bridge": False, "plugin": False})
        assert prefs.type_filters["bridge"] is False
        assert prefs.type_filters["plugin"] is False

    def test_update_channels(self):
        service = NotificationService()
        prefs = service.update_preferences("0xuser", channels={"email": True, "webhook": True})
        assert prefs.channels["email"] is True
        assert prefs.channels["webhook"] is True


class TestBroadcast:
    def test_broadcast(self):
        service = NotificationService()
        # Create some users first
        service.create_notification("0xa", "system", "info", "Init", "Setup")
        service.create_notification("0xb", "system", "info", "Init", "Setup")
        results = service.broadcast_notification("system", "info", "Broadcast", "Hello all")
        assert len(results) >= 1


class TestStats:
    def test_stats(self):
        service = NotificationService()
        service.create_notification("0xuser", "system", "info", "A", "msg")
        service.create_notification("0xuser", "security", "warning", "B", "msg")
        stats = service.get_stats("0xuser")
        assert stats["total"] >= 2
        assert "by_type" in stats
        assert "by_severity" in stats

    def test_dashboard(self):
        service = NotificationService()
        service.create_notification("0xverdis", "system", "info", "A", "msg")
        dash = service.get_dashboard("0xverdis")
        assert "stats" in dash
        assert "unread_count" in dash
        assert "recent" in dash
        assert "preferences" in dash


class TestTemplates:
    def test_get_templates(self):
        service = NotificationService()
        templates = service.get_templates()
        assert len(templates) >= 10
        assert all("type" in t and "title" in t and "message" in t for t in templates)


class TestMonitoring:
    def test_start_stop(self):
        service = NotificationService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestWebhook:
    def test_webhook_subscribe(self):
        service = NotificationService()
        received = []
        service.subscribe_webhook(lambda n: received.append(n))
        service.create_notification("0xuser", "system", "info", "Test", "Webhook")
        assert len(received) >= 1


class TestNotificationAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/notifications/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "stats" in resp.json()

    def test_create(self, client, test_user):
        resp = client.post("/api/v1/notifications/", json={
            "user_address": "0xapi", "type": "system", "severity": "info",
            "title": "API Test", "message": "Hello from API",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("notif-")

    def test_list(self, client, test_user):
        client.post("/api/v1/notifications/", json={
            "user_address": "0xapi", "type": "system", "severity": "info",
            "title": "Test", "message": "msg",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/notifications/?user_address=0xapi", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_mark_read(self, client, test_user):
        create = client.post("/api/v1/notifications/", json={
            "user_address": "0xapi", "type": "system", "severity": "info",
            "title": "Read", "message": "msg",
        }, headers=test_user["headers"])
        nid = create.json()["id"]
        resp = client.post(f"/api/v1/notifications/{nid}/read", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["read"] is True

    def test_unread_count(self, client, test_user):
        client.post("/api/v1/notifications/", json={
            "user_address": "0xcount", "type": "system", "severity": "info",
            "title": "Count", "message": "msg",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/notifications/unread/count?user_address=0xcount", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_preferences(self, client, test_user):
        resp = client.get("/api/v1/notifications/preferences/0xpref", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_templates(self, client):
        resp = client.get("/api/v1/notifications/templates/list")
        assert resp.status_code == 200
        assert len(resp.json()) >= 10

    def test_types(self, client):
        resp = client.get("/api/v1/notifications/types/list")
        assert resp.status_code == 200
        assert len(resp.json()) >= 10

    def test_singleton(self):
        assert get_notification_service() is get_notification_service()
