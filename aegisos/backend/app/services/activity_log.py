from __future__ import annotations

"""
Activity Log / Audit Trail — Post-MVP Phase 7

Tracks all user actions for compliance and debugging:
- User activity (login, project creation, pipeline execution, config changes)
- System events (agent failures, pipeline state changes)
- Searchable by user, action type, entity, date range
- Retention policy support (max entries, age-based cleanup)
"""

from typing import Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger("service.activity_log")

# Known action types
ACTION_TYPES = {
    "user.login", "user.logout", "user.register",
    "project.created", "project.updated", "project.deleted",
    "task.created", "task.updated", "task.completed", "task.assigned",
    "pipeline.created", "pipeline.started", "pipeline.completed", "pipeline.failed",
    "pipeline.cancelled", "pipeline.template_applied",
    "config.updated", "config.global_override",
    "agent.enabled", "agent.disabled",
    "schedule.created", "schedule.updated", "schedule.deleted",
    "knowledge.created", "knowledge.updated", "knowledge.deleted",
    "github.connected", "github.webhook_received",
}


@dataclass
class ActivityEntry:
    """A single activity log entry."""
    id: str = field(default_factory=lambda: f"act-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str = ""
    entity_type: str = ""  # project, task, pipeline, config, agent, schedule, knowledge, user
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    details: dict = field(default_factory=dict)
    ip_address: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: str = "info"  # info, warning, error

    def to_dict(self) -> dict:
        return asdict(self)


class ActivityLog:
    """
    Activity log with search, filtering, and retention.

    Stores entries in-memory (production would use a database).
    """

    def __init__(self, max_entries: int = 10000):
        self._entries: list[ActivityEntry] = []
        self._max_entries = max_entries
        self._entry_index: dict[str, ActivityEntry] = {}

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        entity_type: str = "",
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        severity: str = "info",
    ) -> ActivityEntry:
        """Log an activity entry."""
        entry = ActivityEntry(
            user_id=user_id,
            user_email=user_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details or {},
            ip_address=ip_address,
            severity=severity,
        )
        self._entries.append(entry)
        self._entry_index[entry.id] = entry

        # Enforce max entries (ring buffer)
        if len(self._entries) > self._max_entries:
            removed = self._entries.pop(0)
            self._entry_index.pop(removed.id, None)

        logger.debug("activity_logged", action=action, entity=entity_type, user=user_id)
        return entry

    def get(self, entry_id: str) -> Optional[ActivityEntry]:
        """Get a specific entry."""
        return self._entry_index.get(entry_id)

    def list(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ActivityEntry]:
        """List entries with filters."""
        entries = list(reversed(self._entries))  # newest first

        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if action:
            entries = [e for e in entries if e.action == action]
        if entity_type:
            entries = [e for e in entries if e.entity_type == entity_type]
        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]
        if severity:
            entries = [e for e in entries if e.severity == severity]
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        if until:
            entries = [e for e in entries if e.timestamp <= until]

        return entries[offset:offset + limit]

    def search(self, query: str, limit: int = 20) -> list[ActivityEntry]:
        """Search activity log by text (action, entity_name, user_email, details)."""
        query_lower = query.lower()
        results = []

        for entry in reversed(self._entries):
            searchable = f"{entry.action} {entry.entity_name or ''} {entry.user_email or ''} {entry.entity_type}"
            if query_lower in searchable.lower():
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def get_stats(self) -> dict:
        """Get activity log statistics."""
        action_counts = defaultdict(int)
        entity_counts = defaultdict(int)
        severity_counts = defaultdict(int)

        for entry in self._entries:
            action_counts[entry.action] += 1
            entity_counts[entry.entity_type] += 1
            severity_counts[entry.severity] += 1

        return {
            "total_entries": len(self._entries),
            "actions": dict(action_counts),
            "entities": dict(entity_counts),
            "severities": dict(severity_counts),
        }

    def get_user_activity(self, user_id: str, limit: int = 20) -> list[ActivityEntry]:
        """Get recent activity for a specific user."""
        return self.list(user_id=user_id, limit=limit)

    def get_recent_errors(self, limit: int = 10) -> list[ActivityEntry]:
        """Get recent error-level entries."""
        return self.list(severity="error", limit=limit)

    def cleanup_old(self, max_age_days: int = 90) -> int:
        """Remove entries older than max_age_days. Returns count removed."""
        cutoff = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat()
        original_count = len(self._entries)
        self._entries = [e for e in self._entries if e.timestamp >= cutoff]
        removed = original_count - len(self._entries)

        # Rebuild index
        self._entry_index = {e.id: e for e in self._entries}

        if removed:
            logger.info("activity_log_cleaned", removed=removed, remaining=len(self._entries))
        return removed


# Singleton
_log: Optional[ActivityLog] = None


def get_activity_log() -> ActivityLog:
    global _log
    if _log is None:
        _log = ActivityLog()
    return _log


def log_activity(
    action: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    **kwargs,
) -> ActivityEntry:
    """Convenience function to log an activity."""
    return get_activity_log().log(
        action=action,
        user_id=user_id,
        user_email=user_email,
        **kwargs,
    )
