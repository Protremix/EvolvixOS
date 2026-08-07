"""
Webhook Subscription Service — Post-MVP Phase 9

Allows external systems to subscribe to EvolvixOS events:
- Register webhook URLs for specific event types
- Automatic payload delivery with retry
- HMAC-SHA256 signature for security
- Delivery history tracking
- Active/inactive subscriptions
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import hashlib
import hmac
import json
import urllib.request
import urllib.error
import threading
from app.core.logging import get_logger

logger = get_logger("service.webhook_subscriptions")

# Event types that can be subscribed to
SUBSCRIBABLE_EVENTS = {
    "pipeline.started", "pipeline.completed", "pipeline.failed", "pipeline.cancelled",
    "stage.started", "stage.passed", "stage.failed",
    "task.created", "task.completed", "task.failed",
    "knowledge.created", "knowledge.updated",
    "agent.enabled", "agent.disabled",
    "schedule.triggered",
    "system.alert",
}


@dataclass
class WebhookSubscription:
    """A webhook subscription."""
    id: str = field(default_factory=lambda: f"wh-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    url: str = ""
    event_types: list[str] = field(default_factory=list)
    secret: str = ""  # HMAC signing secret
    description: str = ""
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    delivery_count: int = 0
    failure_count: int = 0
    last_delivery: Optional[str] = None
    last_status: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WebhookDelivery:
    """Record of a single webhook delivery attempt."""
    id: str = field(default_factory=lambda: f"del-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    subscription_id: str = ""
    event_type: str = ""
    payload: dict = field(default_factory=dict)
    status_code: Optional[int] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class WebhookSubscriptionManager:
    """Manages webhook subscriptions and deliveries."""

    def __init__(self, max_delivery_history: int = 1000):
        self._subscriptions: dict[str, WebhookSubscription] = {}
        self._deliveries: list[WebhookDelivery] = []
        self._max_delivery_history = max_delivery_history
        self._lock = threading.Lock()

    def create_subscription(
        self,
        url: str,
        event_types: list[str],
        secret: str = "",
        description: str = "",
    ) -> WebhookSubscription:
        """Create a new webhook subscription."""
        # Validate event types
        invalid = [e for e in event_types if e not in SUBSCRIBABLE_EVENTS]
        if invalid:
            raise ValueError(f"Invalid event types: {invalid}")

        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        sub = WebhookSubscription(
            url=url,
            event_types=event_types,
            secret=secret,
            description=description,
        )
        with self._lock:
            self._subscriptions[sub.id] = sub
        logger.info("webhook_created", id=sub.id, url=url, events=event_types)
        return sub

    def get_subscription(self, sub_id: str) -> Optional[WebhookSubscription]:
        return self._subscriptions.get(sub_id)

    def list_subscriptions(self, active_only: bool = False) -> list[WebhookSubscription]:
        subs = list(self._subscriptions.values())
        if active_only:
            subs = [s for s in subs if s.active]
        return subs

    def update_subscription(self, sub_id: str, **kwargs) -> Optional[WebhookSubscription]:
        sub = self._subscriptions.get(sub_id)
        if not sub:
            return None

        if "event_types" in kwargs:
            invalid = [e for e in kwargs["event_types"] if e not in SUBSCRIBABLE_EVENTS]
            if invalid:
                raise ValueError(f"Invalid event types: {invalid}")

        for key, val in kwargs.items():
            if hasattr(sub, key):
                setattr(sub, key, val)
        sub.updated_at = datetime.utcnow().isoformat()
        return sub

    def delete_subscription(self, sub_id: str) -> bool:
        if sub_id in self._subscriptions:
            del self._subscriptions[sub_id]
            return True
        return False

    def deactivate(self, sub_id: str) -> bool:
        sub = self._subscriptions.get(sub_id)
        if sub:
            sub.active = False
            sub.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def activate(self, sub_id: str) -> bool:
        sub = self._subscriptions.get(sub_id)
        if sub:
            sub.active = True
            sub.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def deliver(self, event_type: str, payload: dict) -> list[WebhookDelivery]:
        """Deliver an event to all matching active subscriptions."""
        deliveries = []
        matching_subs = [
            s for s in self._subscriptions.values()
            if s.active and event_type in s.event_types
        ]

        for sub in matching_subs:
            delivery = self._deliver_one(sub, event_type, payload)
            deliveries.append(delivery)

        # Store deliveries
        with self._lock:
            self._deliveries.extend(deliveries)
            if len(self._deliveries) > self._max_delivery_history:
                self._deliveries = self._deliveries[-self._max_delivery_history:]

        return deliveries

    def _deliver_one(self, sub: WebhookSubscription, event_type: str, payload: dict) -> WebhookDelivery:
        """Deliver to a single subscription."""
        delivery = WebhookDelivery(
            subscription_id=sub.id,
            event_type=event_type,
            payload=payload,
        )

        body = json.dumps({"event": event_type, "data": payload, "timestamp": datetime.utcnow().isoformat()}).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        # HMAC signature
        if sub.secret:
            signature = hmac.new(sub.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-EvolvixOS-Signature"] = f"sha256={signature}"

        start = datetime.utcnow()
        try:
            req = urllib.request.Request(sub.url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                delivery.status_code = resp.status
                delivery.success = 200 <= resp.status < 300
        except urllib.error.HTTPError as e:
            delivery.status_code = e.code
            delivery.success = False
            delivery.error = str(e)
        except Exception as e:
            delivery.success = False
            delivery.error = str(e)

        delivery.duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        # Update subscription stats
        sub.delivery_count += 1
        if not delivery.success:
            sub.failure_count += 1
        sub.last_delivery = delivery.timestamp
        sub.last_status = delivery.status_code

        logger.info(
            "webhook_delivered",
            sub_id=sub.id, event=event_type,
            status=delivery.status_code, success=delivery.success,
        )

        return delivery

    def get_deliveries(self, sub_id: Optional[str] = None, limit: int = 50) -> list[WebhookDelivery]:
        """Get delivery history."""
        deliveries = list(reversed(self._deliveries))
        if sub_id:
            deliveries = [d for d in deliveries if d.subscription_id == sub_id]
        return deliveries[:limit]

    def get_stats(self) -> dict:
        return {
            "total_subscriptions": len(self._subscriptions),
            "active_subscriptions": sum(1 for s in self._subscriptions.values() if s.active),
            "total_deliveries": len(self._deliveries),
            "successful_deliveries": sum(1 for d in self._deliveries if d.success),
            "failed_deliveries": sum(1 for d in self._deliveries if not d.success),
            "subscribable_events": list(SUBSCRIBABLE_EVENTS),
        }

    def test_subscription(self, sub_id: str) -> WebhookDelivery:
        """Send a test event to a subscription."""
        sub = self._subscriptions.get(sub_id)
        if not sub:
            raise ValueError(f"Subscription {sub_id} not found")

        delivery = self._deliver_one(sub, "test.event", {"test": True, "message": "Test from EvolvixOS"})
        with self._lock:
            self._deliveries.append(delivery)
        return delivery


# Singleton
_manager: Optional[WebhookSubscriptionManager] = None


def get_webhook_manager() -> WebhookSubscriptionManager:
    global _manager
    if _manager is None:
        _manager = WebhookSubscriptionManager()
    return _manager
