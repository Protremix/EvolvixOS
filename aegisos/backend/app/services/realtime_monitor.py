"""
Real-Time Monitoring Service — Phase 18

Provides live monitoring of agent activities, system health,
and collaboration sessions with WebSocket streaming support.
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import deque
import threading
import time
from app.core.logging import get_logger

logger = get_logger("service.realtime_monitor")


@dataclass
class LiveEvent:
    """A real-time event for the monitoring dashboard."""
    id: str = field(default_factory=lambda: f"evt-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    type: str = ""  # agent_started, agent_completed, agent_failed, step_started, step_completed, health_check, alert, collaboration_started, collaboration_completed
    source: str = ""  # agent name, system, collaboration
    message: str = ""
    data: dict = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, success

    def to_dict(self) -> dict:
        return asdict(self)


class RealtimeMonitor:
    """
    Real-time monitoring for agent activities and system events.
    Maintains a ring buffer of events and supports WebSocket streaming.
    """

    def __init__(self, max_events: int = 2000, max_metrics: int = 500):
        self._events: deque = deque(maxlen=max_events)
        self._metrics: deque = deque(maxlen=max_metrics)
        self._subscribers: list = []  # WebSocket connections
        self._lock = threading.Lock()
        self._system_stats = {
            "agents_active": 0,
            "agents_idle": 11,
            "tasks_running": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "collaborations_active": 0,
            "collaborations_completed": 0,
            "avg_response_ms": 0.0,
            "total_tokens_used": 0,
        }

    def emit(self, event_type: str, source: str, message: str,
             data: dict = None, severity: str = "info") -> LiveEvent:
        """Emit a real-time event."""
        event = LiveEvent(
            type=event_type, source=source, message=message,
            data=data or {}, severity=severity,
        )
        with self._lock:
            self._events.append(event)

            # Update stats
            if event_type == "agent_started":
                self._system_stats["tasks_running"] += 1
            elif event_type == "agent_completed":
                self._system_stats["tasks_running"] -= 1
                self._system_stats["tasks_completed"] += 1
            elif event_type == "agent_failed":
                self._system_stats["tasks_running"] -= 1
                self._system_stats["tasks_failed"] += 1
            elif event_type == "collaboration_started":
                self._system_stats["collaborations_active"] += 1
            elif event_type == "collaboration_completed":
                self._system_stats["collaborations_active"] -= 1
                self._system_stats["collaborations_completed"] += 1

            # Notify subscribers
            for sub in self._subscribers:
                try:
                    sub(event.type, event.to_dict())
                except Exception:
                    pass

        return event

    def get_events(self, limit: int = 100, event_type: str = None,
                   source: str = None, severity: str = None) -> list[dict]:
        """Get recent events, optionally filtered."""
        events = list(self._events)
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]
        if severity:
            events = [e for e in events if e.severity == severity]
        return [e.to_dict() for e in reversed(events)][:limit]

    def record_metric(self, name: str, value: float, unit: str = ""):
        """Record a time-series metric."""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": name, "value": value, "unit": unit,
        }
        with self._lock:
            self._metrics.append(metric)

    def get_metrics(self, name: str = None, limit: int = 100) -> list[dict]:
        """Get recent metrics, optionally filtered by name."""
        metrics = list(self._metrics)
        if name:
            metrics = [m for m in metrics if m["name"] == name]
        return list(reversed(metrics))[:limit]

    def get_system_stats(self) -> dict:
        """Get current system statistics."""
        with self._lock:
            stats = self._system_stats.copy()
        stats["events_buffered"] = len(self._events)
        stats["metrics_buffered"] = len(self._metrics)
        stats["timestamp"] = datetime.utcnow().isoformat()
        return stats

    def get_live_feed(self, limit: int = 20) -> dict:
        """Get a complete live feed snapshot."""
        with self._lock:
            events = list(reversed(self._events))[:limit]
            stats = self._system_stats.copy()
        return {
            "events": [e.to_dict() for e in events],
            "stats": stats,
            "event_count": len(self._events),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def add_subscriber(self, callback):
        """Add a subscriber for real-time event notifications."""
        self._subscribers.append(callback)

    def remove_subscriber(self, callback):
        """Remove a subscriber."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def get_event_types(self) -> list[str]:
        """Get all known event types."""
        return [
            "agent_started", "agent_completed", "agent_failed",
            "step_started", "step_completed", "step_failed",
            "collaboration_started", "collaboration_completed",
            "health_check", "alert_raised", "alert_resolved",
            "benchmark_started", "benchmark_completed",
            "pipeline_started", "pipeline_completed", "pipeline_failed",
        ]

    def clear_events(self):
        """Clear all events (for testing)."""
        with self._lock:
            self._events.clear()


# Singleton
_monitor: Optional[RealtimeMonitor] = None


def get_realtime_monitor() -> RealtimeMonitor:
    global _monitor
    if _monitor is None:
        _monitor = RealtimeMonitor()
    return _monitor
