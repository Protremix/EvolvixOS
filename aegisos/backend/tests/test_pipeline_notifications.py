"""Tests for Pipeline Notifications — Post-MVP Phase 4."""

import pytest
from app.services.pipeline_notifications import (
    Notification, NotificationManager,
)
from app.services.pipeline_events import (
    PipelineEvent, PipelineEventBus, emit_pipeline_completed,
    emit_pipeline_failed, emit_pipeline_cancelled, emit_stage_failed,
)


@pytest.fixture
def fresh_mgr():
    """Get a fresh notification manager."""
    mgr = NotificationManager(max_notifications=50)
    return mgr


class TestNotification:
    """Test the Notification dataclass."""

    def test_notification_creation(self):
        notif = Notification(
            pipeline_id="p1",
            event_type="pipeline.completed",
            title="Pipeline Completed",
            message="Pipeline p1 completed successfully",
        )
        assert notif.pipeline_id == "p1"
        assert notif.severity == "info"
        assert notif.read is False

    def test_notification_to_dict(self):
        notif = Notification(pipeline_id="p1", title="Test")
        d = notif.to_dict()
        assert "id" in d
        assert "pipeline_id" in d
        assert "created_at" in d

    def test_unique_ids(self):
        n1 = Notification()
        n2 = Notification()
        assert n1.id != n2.id


class TestNotificationManager:
    """Test the notification manager."""

    def test_add_notification(self, fresh_mgr):
        notif = Notification(pipeline_id="p1", title="Test")
        fresh_mgr._add_notification(notif)
        assert fresh_mgr.total_count == 1

    def test_max_notifications(self):
        mgr = NotificationManager(max_notifications=3)
        for i in range(10):
            mgr._add_notification(Notification(title=f"Test {i}"))
        assert mgr.total_count == 3  # capped at 3

    def test_get_notifications(self, fresh_mgr):
        for i in range(5):
            fresh_mgr._add_notification(Notification(
                pipeline_id="p1", title=f"Test {i}", severity="info"
            ))
        notifs = fresh_mgr.get_notifications()
        assert len(notifs) == 5

    def test_get_unread_only(self, fresh_mgr):
        fresh_mgr._add_notification(Notification(title="Read", read=True))
        fresh_mgr._add_notification(Notification(title="Unread"))
        unread = fresh_mgr.get_notifications(unread_only=True)
        assert len(unread) == 1
        assert unread[0]["title"] == "Unread"

    def test_mark_read(self, fresh_mgr):
        notif = Notification(title="Test")
        fresh_mgr._add_notification(notif)
        assert fresh_mgr.unread_count == 1
        
        success = fresh_mgr.mark_read(notif.id)
        assert success is True
        assert fresh_mgr.unread_count == 0

    def test_mark_read_not_found(self, fresh_mgr):
        success = fresh_mgr.mark_read("nonexistent")
        assert success is False

    def test_mark_all_read(self, fresh_mgr):
        for i in range(5):
            fresh_mgr._add_notification(Notification(title=f"Test {i}"))
        count = fresh_mgr.mark_all_read()
        assert count == 5
        assert fresh_mgr.unread_count == 0

    def test_clear_notifications(self, fresh_mgr):
        fresh_mgr._add_notification(Notification(title="Test"))
        fresh_mgr.clear_notifications()
        assert fresh_mgr.total_count == 0

    def test_unread_count(self, fresh_mgr):
        fresh_mgr._add_notification(Notification(title="Read", read=True))
        fresh_mgr._add_notification(Notification(title="Unread 1"))
        fresh_mgr._add_notification(Notification(title="Unread 2"))
        assert fresh_mgr.unread_count == 2


class TestEventToNotification:
    """Test converting pipeline events to notifications."""

    def test_pipeline_completed_creates_notification(self, fresh_mgr):
        event = PipelineEvent(
            event_type="pipeline.completed",
            pipeline_id="p1",
            message="Pipeline completed: 10/10 stages",
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is not None
        assert notif.severity == "success"
        assert notif.title == "Pipeline Completed"

    def test_pipeline_failed_creates_notification(self, fresh_mgr):
        event = PipelineEvent(
            event_type="pipeline.failed",
            pipeline_id="p1",
            stage="security_review",
            message="Pipeline failed at security_review",
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is not None
        assert notif.severity == "error"
        assert notif.title == "Pipeline Failed"

    def test_pipeline_cancelled_creates_notification(self, fresh_mgr):
        event = PipelineEvent(
            event_type="pipeline.cancelled",
            pipeline_id="p1",
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is not None
        assert notif.severity == "warning"

    def test_stage_failed_no_retry_creates_notification(self, fresh_mgr):
        event = PipelineEvent(
            event_type="pipeline.stage_failed",
            pipeline_id="p1",
            stage="implementation",
            data={"will_retry": False},
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is not None
        assert notif.severity == "error"

    def test_stage_failed_with_retry_no_notification(self, fresh_mgr):
        """Stage failures that will retry should NOT create a notification."""
        event = PipelineEvent(
            event_type="pipeline.stage_failed",
            pipeline_id="p1",
            stage="implementation",
            data={"will_retry": True},
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is None

    def test_stage_passed_no_notification(self, fresh_mgr):
        """Stage passing should NOT create a notification (too noisy)."""
        event = PipelineEvent(
            event_type="pipeline.stage_passed",
            pipeline_id="p1",
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is None

    def test_stage_started_no_notification(self, fresh_mgr):
        event = PipelineEvent(
            event_type="pipeline.stage_started",
            pipeline_id="p1",
        )
        notif = fresh_mgr._event_to_notification(event)
        assert notif is None


class TestNotificationIntegration:
    """Test notification manager integration with event bus."""

    def test_subscribe_to_events(self):
        """Test that subscribing to events generates notifications."""
        import app.services.pipeline_events as pe
        import app.services.pipeline_notifications as pn
        
        # Create fresh instances
        old_bus = pe._event_bus
        old_mgr = pn._notif_manager
        pe._event_bus = PipelineEventBus()
        pn._notif_manager = NotificationManager()
        pn._notif_manager.subscribe_to_events()
        
        try:
            # Emit a pipeline completed event
            pe._event_bus.emit(PipelineEvent(
                event_type="pipeline.completed",
                pipeline_id="test-integration",
                message="Pipeline completed",
            ))
            
            assert pn._notif_manager.total_count == 1
            assert pn._notif_manager.unread_count == 1
        finally:
            pe._event_bus = old_bus
            pn._notif_manager = old_mgr

    def test_multiple_events_generate_notifications(self):
        """Test that multiple events generate multiple notifications."""
        import app.services.pipeline_events as pe
        import app.services.pipeline_notifications as pn
        
        old_bus = pe._event_bus
        old_mgr = pn._notif_manager
        pe._event_bus = PipelineEventBus()
        pn._notif_manager = NotificationManager()
        pn._notif_manager.subscribe_to_events()
        
        try:
            pe._event_bus.emit(PipelineEvent(
                event_type="pipeline.completed",
                pipeline_id="p1",
            ))
            pe._event_bus.emit(PipelineEvent(
                event_type="pipeline.failed",
                pipeline_id="p2",
            ))
            pe._event_bus.emit(PipelineEvent(
                event_type="pipeline.cancelled",
                pipeline_id="p3",
            ))
            
            assert pn._notif_manager.total_count == 3
        finally:
            pe._event_bus = old_bus
            pn._notif_manager = old_mgr


class TestNotificationAPI:
    """Test the notification API endpoints."""

    def test_get_notifications_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/notifications/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)  # New API returns list directly

    def test_get_unread_count_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/notifications/unread/count", headers=headers)
        assert resp.status_code == 200
        assert "count" in resp.json()  # New API uses "count" instead of "unread_count"

    def test_mark_all_read_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/notifications/read-all", headers=headers)
        assert resp.status_code == 200

    def test_clear_notifications_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.delete("/api/v1/notifications/clear/all?user_address=0xverdis", headers=headers)
        assert resp.status_code == 200

    def test_get_unread_only_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/notifications/?unread_only=true", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # All returned notifications should be unread
        for n in data:  # New API returns a list
            assert n["read"] is False
