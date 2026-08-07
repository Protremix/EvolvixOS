"""
Pipeline Notifications — Post-MVP Phase 4

Sends notifications when pipeline events occur:
- Pipeline completed (success)
- Pipeline failed
- Pipeline cancelled
- Stage failed (with retry info)

Notification channels:
- In-app (stored in memory for frontend polling)
- Webhook (configurable URL, POST with event data)
- Email (optional, via SMTP if configured)

This is a pluggable notification system — channels can be added
without modifying the event bus.
"""

import json
import urllib.request
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict

from app.core.logging import get_logger
from app.services.pipeline_events import PipelineEvent, get_event_bus

logger = get_logger("service.pipeline_notifications")


@dataclass
class Notification:
    """A notification record."""
    id: str = field(default_factory=lambda: f"notif-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    pipeline_id: str = ""
    event_type: str = ""
    title: str = ""
    message: str = ""
    severity: str = "info"  # info, success, warning, error
    read: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class NotificationManager:
    """
    Manages pipeline notifications.
    
    Subscribes to the pipeline event bus and generates
    user-facing notifications from pipeline events.
    """

    def __init__(self, max_notifications: int = 500):
        self._notifications: list[Notification] = []
        self._max = max_notifications
        self._webhook_url: Optional[str] = None
        self._webhook_listeners: list[Callable] = []
        self._subscribed = False

    def configure_webhook(self, url: str):
        """Configure a webhook URL for external notifications."""
        self._webhook_url = url
        logger.info("webhook_configured", url=url)

    def subscribe_to_events(self):
        """Subscribe to the pipeline event bus."""
        if self._subscribed:
            return
        bus = get_event_bus()
        bus.subscribe(self._on_event)
        self._subscribed = True
        logger.info("notification_manager_subscribed")

    def _on_event(self, event: PipelineEvent):
        """Handle a pipeline event and generate notifications."""
        notif = self._event_to_notification(event)
        if notif:
            self._add_notification(notif)
            self._fire_webhook(notif)

    def _event_to_notification(self, event: PipelineEvent) -> Optional[Notification]:
        """Convert a pipeline event to a user notification."""
        if event.event_type == "pipeline.completed":
            return Notification(
                pipeline_id=event.pipeline_id,
                event_type=event.event_type,
                title="Pipeline Completed",
                message=event.message,
                severity="success",
                data=event.data,
            )
        elif event.event_type == "pipeline.failed":
            return Notification(
                pipeline_id=event.pipeline_id,
                event_type=event.event_type,
                title="Pipeline Failed",
                message=event.message,
                severity="error",
                data=event.data,
            )
        elif event.event_type == "pipeline.cancelled":
            return Notification(
                pipeline_id=event.pipeline_id,
                event_type=event.event_type,
                title="Pipeline Cancelled",
                message=event.message,
                severity="warning",
                data=event.data,
            )
        elif event.event_type == "pipeline.stage_failed":
            will_retry = event.data.get("will_retry", False)
            if not will_retry:
                return Notification(
                    pipeline_id=event.pipeline_id,
                    event_type=event.event_type,
                    title=f"Stage Failed: {event.stage}",
                    message=event.message,
                    severity="error",
                    data=event.data,
                )
        return None

    def _add_notification(self, notif: Notification):
        """Add a notification, respecting max size."""
        self._notifications.append(notif)
        if len(self._notifications) > self._max:
            self._notifications = self._notifications[-self._max:]

    def _fire_webhook(self, notif: Notification):
        """Fire webhook if configured."""
        if not self._webhook_url:
            return
        try:
            payload = json.dumps(notif.to_dict()).encode("utf-8")
            req = urllib.request.Request(
                self._webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
            logger.info("webhook_fired", notif_id=notif.id)
        except Exception as e:
            logger.warning("webhook_failed", error=str(e))

    def get_notifications(self, unread_only: bool = False,
                          limit: int = 50) -> list[dict]:
        """Get notifications, optionally filtered to unread."""
        notifs = self._notifications
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        return [n.to_dict() for n in notifs[-limit:]]

    def mark_read(self, notif_id: str) -> bool:
        """Mark a notification as read."""
        for n in self._notifications:
            if n.id == notif_id:
                n.read = True
                return True
        return False

    def mark_all_read(self) -> int:
        """Mark all notifications as read. Returns count marked."""
        count = 0
        for n in self._notifications:
            if not n.read:
                n.read = True
                count += 1
        return count

    def clear_notifications(self):
        """Clear all notifications."""
        self._notifications = []

    @property
    def unread_count(self) -> int:
        return sum(1 for n in self._notifications if not n.read)

    @property
    def total_count(self) -> int:
        return len(self._notifications)


# Singleton
_notif_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get the singleton notification manager."""
    global _notif_manager
    if _notif_manager is None:
        _notif_manager = NotificationManager()
        _notif_manager.subscribe_to_events()
    return _notif_manager
