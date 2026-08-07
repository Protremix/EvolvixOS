"""
Notification Center — Phase 40

Real-time notifications across the Verdis/EvolvixOS ecosystem
with event-driven triggers, user preferences, and WebSocket streaming.
"""

import secrets
import time
import threading
import asyncio
from typing import Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import json
from app.core.logging import get_logger

logger = get_logger("service.notifications")


class NotificationType(str, Enum):
    TRANSACTION = "transaction"
    GOVERNANCE = "governance"
    SECURITY = "security"
    SYSTEM = "system"
    BRIDGE = "bridge"
    VALIDATOR = "validator"
    TOKENOMICS = "tokenomics"
    DEPLOYMENT = "deployment"
    AGENT = "agent"
    PLUGIN = "plugin"


class NotificationSeverity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Notification:
    id: str
    user_address: str
    type: str
    severity: str
    title: str
    message: str
    read: bool = False
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    read_at: str = ""
    action_url: str = ""
    action_label: str = ""
    metadata: dict = field(default_factory=dict)
    expires: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NotificationPreference:
    user_address: str
    enabled: bool = True
    channels: dict = field(default_factory=lambda: {
        "in_app": True,
        "email": False,
        "webhook": False,
    })
    type_filters: dict = field(default_factory=lambda: {
        "transaction": True,
        "governance": True,
        "security": True,
        "system": True,
        "bridge": True,
        "validator": True,
        "tokenomics": True,
        "deployment": True,
        "agent": True,
        "plugin": True,
    })
    min_severity: str = "info"  # Minimum severity to receive

    def to_dict(self) -> dict:
        return asdict(self)


class NotificationService:
    """Notification center with event-driven triggers and WebSocket streaming."""

    def __init__(self, max_history: int = 10000):
        self._notifications: dict[str, Notification] = {}
        self._user_notifications: dict[str, list[str]] = defaultdict(list)  # user -> [notification_ids]
        self._preferences: dict[str, NotificationPreference] = {}
        self._webhook_subscribers: list[Callable] = []
        self._lock = threading.Lock()
        self._max_history = max_history
        self._ws_clients: dict[str, list] = {}  # user_address -> [websocket queues]
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_default_preferences()

    def _init_default_preferences(self):
        """All users get all notifications by default."""
        pass  # Preferences are created on first access

    # === Create ===

    def create_notification(
        self, user_address: str, type: str, severity: str,
        title: str, message: str, action_url: str = "",
        action_label: str = "", metadata: dict = None,
        expires_hours: int = 0,
    ) -> Optional[Notification]:
        """Create a notification for a user."""
        # Check preferences
        prefs = self._get_or_create_prefs(user_address)
        if not prefs.enabled:
            return None
        if not prefs.type_filters.get(type, True):
            return None

        # Check severity threshold
        severity_order = ["info", "success", "warning", "error", "critical"]
        if severity_order.index(severity) < severity_order.index(prefs.min_severity):
            return None

        notif_id = f"notif-{secrets.token_hex(8)}"
        expires = ""
        if expires_hours > 0:
            expires = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()

        notif = Notification(
            id=notif_id, user_address=user_address, type=type,
            severity=severity, title=title, message=message,
            action_url=action_url, action_label=action_label,
            metadata=metadata or {}, expires=expires,
        )

        with self._lock:
            self._notifications[notif_id] = notif
            self._user_notifications[user_address].append(notif_id)

            # Trim history
            if len(self._notifications) > self._max_history:
                oldest = list(self._notifications.keys())[:100]
                for oid in oldest:
                    self._notifications.pop(oid, None)

        # Notify webhook subscribers
        for callback in self._webhook_subscribers:
            try:
                callback(notif.to_dict())
            except Exception as e:
                logger.error("webhook_callback_error", error=str(e))

        logger.info("notification_created", id=notif_id, user=user_address, type=type, severity=severity)
        return notif

    def broadcast_notification(
        self, type: str, severity: str, title: str, message: str,
        action_url: str = "", action_label: str = "", metadata: dict = None,
    ) -> list[Notification]:
        """Broadcast to all users with matching preferences."""
        users = set(self._user_notifications.keys())
        # Also include users with preferences
        users.update(self._preferences.keys())
        if not users:
            # No users yet, create for a default set
            users = {"0xverdis"}

        results = []
        for user in users:
            notif = self.create_notification(
                user, type, severity, title, message,
                action_url, action_label, metadata,
            )
            if notif:
                results.append(notif)
        return results

    # === Read ===

    def get_notification(self, notif_id: str) -> Optional[Notification]:
        return self._notifications.get(notif_id)

    def list_notifications(
        self, user_address: str, unread_only: bool = False,
        type: str = None, severity: str = None, limit: int = 50,
    ) -> list[Notification]:
        """List notifications for a user."""
        ids = self._user_notifications.get(user_address, [])
        notifs = [self._notifications[nid] for nid in ids if nid in self._notifications]

        if unread_only:
            notifs = [n for n in notifs if not n.read]
        if type:
            notifs = [n for n in notifs if n.type == type]
        if severity:
            notifs = [n for n in notifs if n.severity == severity]

        notifs.sort(key=lambda n: n.created, reverse=True)
        return notifs[:limit]

    def get_unread_count(self, user_address: str) -> int:
        return len([n for n in self.list_notifications(user_address, unread_only=True)])

    def get_stats(self, user_address: str = None) -> dict:
        if user_address:
            notifs = self.list_notifications(user_address, limit=10000)
        else:
            notifs = list(self._notifications.values())

        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        unread = 0

        for n in notifs:
            by_type[n.type] += 1
            by_severity[n.severity] += 1
            if not n.read:
                unread += 1

        return {
            "total": len(notifs),
            "unread": unread,
            "read": len(notifs) - unread,
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
        }

    # === Actions ===

    def mark_read(self, notif_id: str) -> bool:
        notif = self._notifications.get(notif_id)
        if not notif:
            return False
        notif.read = True
        notif.read_at = datetime.utcnow().isoformat()
        return True

    def mark_all_read(self, user_address: str) -> int:
        """Mark all notifications as read for a user."""
        count = 0
        for nid in self._user_notifications.get(user_address, []):
            notif = self._notifications.get(nid)
            if notif and not notif.read:
                notif.read = True
                notif.read_at = datetime.utcnow().isoformat()
                count += 1
        return count

    def delete_notification(self, notif_id: str) -> bool:
        notif = self._notifications.pop(notif_id, None)
        if notif:
            if notif.user_address in self._user_notifications:
                try:
                    self._user_notifications[notif.user_address].remove(notif_id)
                except ValueError:
                    pass
            return True
        return False

    def clear_all(self, user_address: str) -> int:
        """Clear all notifications for a user."""
        ids = self._user_notifications.get(user_address, [])
        count = 0
        for nid in ids:
            if nid in self._notifications:
                del self._notifications[nid]
                count += 1
        self._user_notifications[user_address] = []
        return count

    def clear_read(self, user_address: str) -> int:
        """Clear all read notifications for a user."""
        ids = self._user_notifications.get(user_address, [])
        to_remove = [nid for nid in ids if nid in self._notifications and self._notifications[nid].read]
        for nid in to_remove:
            del self._notifications[nid]
            ids.remove(nid)
        return len(to_remove)

    # === Preferences ===

    def _get_or_create_prefs(self, user_address: str) -> NotificationPreference:
        if user_address not in self._preferences:
            self._preferences[user_address] = NotificationPreference(user_address=user_address)
        return self._preferences[user_address]

    def get_preferences(self, user_address: str) -> NotificationPreference:
        return self._get_or_create_prefs(user_address)

    def update_preferences(self, user_address: str, **kwargs) -> NotificationPreference:
        prefs = self._get_or_create_prefs(user_address)
        if "enabled" in kwargs:
            prefs.enabled = kwargs["enabled"]
        if "channels" in kwargs:
            prefs.channels.update(kwargs["channels"])
        if "type_filters" in kwargs:
            prefs.type_filters.update(kwargs["type_filters"])
        if "min_severity" in kwargs:
            prefs.min_severity = kwargs["min_severity"]
        return prefs

    # === Webhooks ===

    def subscribe_webhook(self, callback: Callable):
        """Subscribe to notification events."""
        self._webhook_subscribers.append(callback)

    def unsubscribe_webhook(self, callback: Callable):
        if callback in self._webhook_subscribers:
            self._webhook_subscribers.remove(callback)

    # === WebSocket ===

    def register_ws_client(self, user_address: str, queue):
        """Register a WebSocket client for real-time notifications."""
        if user_address not in self._ws_clients:
            self._ws_clients[user_address] = []
        self._ws_clients[user_address].append(queue)

    def unregister_ws_client(self, user_address: str, queue):
        if user_address in self._ws_clients:
            if queue in self._ws_clients[user_address]:
                self._ws_clients[user_address].remove(queue)
            if not self._ws_clients[user_address]:
                del self._ws_clients[user_address]

    def _push_to_ws(self, user_address: str, notification: dict):
        """Push notification to WebSocket clients."""
        clients = self._ws_clients.get(user_address, [])
        for queue in clients:
            try:
                queue.put_nowait(notification)
            except Exception:
                pass

    # === Templates ===

    def get_templates(self) -> list[dict]:
        """Return notification templates for common events."""
        return [
            {"type": "transaction", "severity": "info", "title": "Transaction Confirmed", "message": "Your transaction of {amount} {token} has been confirmed in block {block}."},
            {"type": "governance", "severity": "info", "title": "New Proposal", "message": "A new governance proposal '{title}' has been created. Voting ends in {days} days."},
            {"type": "security", "severity": "warning", "title": "Security Alert", "message": "Unusual activity detected on your account. Please review."},
            {"type": "bridge", "severity": "info", "title": "Bridge Transfer Update", "message": "Your cross-chain transfer of {amount} {token} from {source} to {target} is now {status}."},
            {"type": "validator", "severity": "info", "title": "Validator Status Change", "message": "Validator {name} status changed to {status}."},
            {"type": "tokenomics", "severity": "info", "title": "Vesting Release", "message": "{amount} VRS has been released from your vesting schedule."},
            {"type": "deployment", "severity": "success", "title": "Deployment Complete", "message": "Component {component} deployed to {target} successfully."},
            {"type": "agent", "severity": "info", "title": "Agent Task Complete", "message": "Agent {agent} completed task '{task}' with score {score}/10."},
            {"type": "plugin", "severity": "info", "title": "Plugin Update", "message": "Plugin {name} has been updated to version {version}."},
            {"type": "system", "severity": "critical", "title": "System Alert", "message": "System health check failed for {component}. Immediate attention required."},
        ]

    # === Monitoring ===

    def start_monitoring(self, interval: int = 60):
        """Start background cleanup of expired notifications."""
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("notification_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                now = datetime.utcnow()
                expired = []
                for nid, notif in self._notifications.items():
                    if notif.expires and notif.expires != "":
                        try:
                            exp = datetime.fromisoformat(notif.expires.replace("Z", ""))
                            if now > exp:
                                expired.append(nid)
                        except Exception:
                            pass
                for nid in expired:
                    self.delete_notification(nid)
                if expired:
                    logger.info("expired_notifications_cleaned", count=len(expired))
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Dashboard ===

    def get_dashboard(self, user_address: str = "0xverdis") -> dict:
        stats = self.get_stats(user_address)
        recent = [n.to_dict() for n in self.list_notifications(user_address, limit=20)]
        unread = self.get_unread_count(user_address)
        return {
            "stats": stats,
            "unread_count": unread,
            "recent": recent,
            "monitoring": self._monitoring,
            "preferences": self._get_or_create_prefs(user_address).to_dict(),
            "templates": len(self.get_templates()),
        }


_service: Optional[NotificationService] = None

def get_notification_service() -> NotificationService:
    global _service
    if _service is None:
        _service = NotificationService()
    return _service
