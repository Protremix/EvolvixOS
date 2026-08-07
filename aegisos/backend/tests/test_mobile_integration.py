"""Tests for Mobile Integration — Phase 48."""

import pytest
import time
from app.services.mobile_integration import (
    MobileIntegrationService, get_mobile_integration_service, DevicePlatform, SyncStatus, FeatureKey,
)


class TestSessions:
    def test_register_session(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet1", "dev-001")
        assert s.id.startswith("ses-")
        assert s.wallet_address == "0xwallet1"

    def test_get_session(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet2", "dev-002")
        found = service.get_session(s.id)
        assert found is not None

    def test_wallet_sessions(self):
        service = MobileIntegrationService()
        service.register_session("0xwallet3", "dev-003")
        service.register_session("0xwallet3", "dev-004")
        sessions = service.get_wallet_sessions("0xwallet3")
        assert len(sessions) >= 2

    def test_update_session(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet4", "dev-004")
        updated = service.update_session(s.id, battery_level=50, network_type="5g")
        assert updated.battery_level == 50
        assert updated.network_type == "5g"

    def test_deactivate_session(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet5", "dev-005")
        assert service.deactivate_session(s.id) is True
        assert service.get_session(s.id) is None

    def test_list_sessions(self):
        service = MobileIntegrationService()
        sessions = service.list_sessions()
        assert len(sessions) > 0

    def test_filter_by_platform(self):
        service = MobileIntegrationService()
        service.register_session("0xwallet6", "dev-006", platform="ios")
        ios = service.list_sessions(platform="ios")
        assert all(s.platform == "ios" for s in ios)


class TestFeatures:
    def test_list_features(self):
        service = MobileIntegrationService()
        features = service.list_features()
        assert len(features) >= 12

    def test_get_feature(self):
        service = MobileIntegrationService()
        f = service.get_feature("staking")
        assert f is not None
        assert f.name == "Staking"

    def test_version_compatibility(self):
        service = MobileIntegrationService()
        # Older version should have fewer features
        old = service.list_features(app_version="2.4.0")
        current = service.list_features(app_version="2.5.3")
        assert len(old) < len(current)

    def test_toggle_feature(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet7", "dev-007")
        # Disable staking
        updated = service.toggle_feature(s.id, "staking", False)
        assert "staking" not in updated.features_enabled
        # Re-enable
        updated = service.toggle_feature(s.id, "staking", True)
        assert "staking" in updated.features_enabled


class TestQuickActions:
    def test_list_quick_actions(self):
        service = MobileIntegrationService()
        actions = service.list_quick_actions()
        assert len(actions) >= 8


class TestSync:
    def test_sync_feature(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet8", "dev-008")
        record = service.sync_feature(s.id, "staking", 2048)
        assert record.status == "synced"
        assert record.data_size == 2048

    def test_sync_history(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet9", "dev-009")
        service.sync_feature(s.id, "wallet", 1024)
        service.sync_feature(s.id, "staking", 2048)
        history = service.get_sync_history(session_id=s.id)
        assert len(history) >= 2

    def test_filter_sync_by_feature(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet10", "dev-010")
        service.sync_feature(s.id, "wallet", 1024)
        service.sync_feature(s.id, "staking", 2048)
        wallet_syncs = service.get_sync_history(session_id=s.id, feature="wallet")
        assert all(r.feature == "wallet" for r in wallet_syncs)


class TestNotifications:
    def test_send_notification(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet11", "dev-011")
        n = service.send_notification(s.id, "Test", "Body text")
        assert n.id.startswith("ntf-")
        assert n.title == "Test"

    def test_get_notifications(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet12", "dev-012")
        service.send_notification(s.id, "N1", "B1")
        service.send_notification(s.id, "N2", "B2")
        notifs = service.get_notifications(s.id)
        assert len(notifs) >= 2

    def test_unread_only(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet13", "dev-013")
        service.send_notification(s.id, "N1", "B1")
        notifs = service.get_notifications(s.id, unread_only=True)
        assert all(not n.read for n in notifs)

    def test_mark_read(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet14", "dev-014")
        n = service.send_notification(s.id, "Test", "Body")
        assert service.mark_read(s.id, n.id) is True
        notifs = service.get_notifications(s.id, unread_only=True)
        assert all(notif.id != n.id for notif in notifs)

    def test_mark_all_read(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet15", "dev-015")
        service.send_notification(s.id, "N1", "B1")
        service.send_notification(s.id, "N2", "B2")
        count = service.mark_all_read(s.id)
        assert count >= 2

    def test_broadcast_notification(self):
        service = MobileIntegrationService()
        service.register_session("0xbroadcast", "dev-016")
        service.register_session("0xbroadcast", "dev-017")
        results = service.broadcast_notification("0xbroadcast", "Broadcast", "To all devices")
        assert len(results) >= 2


class TestDashboard:
    def test_mobile_dashboard(self):
        service = MobileIntegrationService()
        s = service.register_session("0xwallet16", "dev-018")
        dash = service.get_mobile_dashboard(s.id)
        assert "session" in dash
        assert "features" in dash
        assert "quick_actions" in dash

    def test_app_config(self):
        service = MobileIntegrationService()
        config = service.get_app_config("2.5.3")
        assert "features" in config
        assert "quick_actions" in config
        assert "network" in config
        assert "settings" in config

    def test_stats(self):
        service = MobileIntegrationService()
        stats = service.get_stats()
        assert stats["total_sessions"] > 0
        assert stats["total_features"] >= 12

    def test_dashboard(self):
        service = MobileIntegrationService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "recent_sessions" in dash
        assert "features" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = MobileIntegrationService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestMobileAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/mobile/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_register_session(self, client, test_user):
        resp = client.post("/api/v1/mobile/sessions", json={
            "wallet_address": "0xapiwallet", "device_id": "dev-api",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("ses-")

    def test_list_sessions(self, client, test_user):
        resp = client.get("/api/v1/mobile/sessions", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_features(self, client, test_user):
        resp = client.get("/api/v1/mobile/features", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 12

    def test_quick_actions(self, client, test_user):
        resp = client.get("/api/v1/mobile/quick-actions", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_app_config(self, client, test_user):
        resp = client.get("/api/v1/mobile/app-config", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/mobile/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_mobile_integration_service() is get_mobile_integration_service()
