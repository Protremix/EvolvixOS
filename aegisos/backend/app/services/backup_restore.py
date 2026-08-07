"""
Backup & Restore Service — Post-MVP Phase 10

Full system state export and import:
- Export all in-memory data as a single JSON snapshot
- Restore from a backup file
- Backup history tracking
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
from app.core.logging import get_logger

logger = get_logger("service.backup_restore")


@dataclass
class BackupRecord:
    """Metadata about a backup."""
    id: str = field(default_factory=lambda: f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    size_bytes: int = 0
    entity_counts: dict = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class BackupRestoreService:
    """Manages full system backups and restores."""

    def __init__(self, max_history: int = 100):
        self._backup_history: list[BackupRecord] = []
        self._max_history = max_history
        self._last_backup: Optional[BackupRecord] = None

    def create_backup(self, description: str = "") -> dict:
        """Create a full system backup."""
        data = {
            "version": "1.0",
            "backup_id": f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": datetime.utcnow().isoformat(),
            "description": description,
            "entities": {},
        }

        counts = {}

        # Pipelines
        try:
            from app.api.v1.feature_pipeline import _pipeline_runs
            data["entities"]["pipelines"] = [
                {"id": r.id, "title": getattr(r, "title", ""), "status": r.status}
                for r in _pipeline_runs.values()
            ]
            counts["pipelines"] = len(data["entities"]["pipelines"])
        except Exception:
            counts["pipelines"] = 0

        # Knowledge base
        try:
            from app.services.knowledge_base import get_knowledge_base
            kb = get_knowledge_base()
            data["entities"]["knowledge_entries"] = [e.to_dict() for e in kb._entries.values()]
            data["entities"]["knowledge_patterns"] = [p.to_dict() for p in kb._patterns]
            counts["knowledge_entries"] = len(data["entities"]["knowledge_entries"])
            counts["knowledge_patterns"] = len(data["entities"]["knowledge_patterns"])
        except Exception:
            counts["knowledge_entries"] = 0
            counts["knowledge_patterns"] = 0

        # Agent configs
        try:
            from app.services.agent_config import get_agent_config_manager
            mgr = get_agent_config_manager()
            data["entities"]["agent_global_overrides"] = {k: v.to_dict() for k, v in mgr._global_overrides.items()}
            data["entities"]["agent_project_configs"] = {
                pid: {k: v.to_dict() for k, v in configs.items()}
                for pid, configs in mgr._project_configs.items()
            }
            counts["agent_global_overrides"] = len(data["entities"]["agent_global_overrides"])
            counts["agent_project_configs"] = sum(len(c) for c in data["entities"]["agent_project_configs"].values())
        except Exception:
            counts["agent_global_overrides"] = 0
            counts["agent_project_configs"] = 0

        # Webhook subscriptions
        try:
            from app.services.webhook_subscriptions import get_webhook_manager
            mgr = get_webhook_manager()
            data["entities"]["webhooks"] = [s.to_dict() for s in mgr._subscriptions.values()]
            data["entities"]["webhook_deliveries"] = [d.to_dict() for d in mgr._deliveries]
            counts["webhooks"] = len(data["entities"]["webhooks"])
            counts["webhook_deliveries"] = len(data["entities"]["webhook_deliveries"])
        except Exception:
            counts["webhooks"] = 0
            counts["webhook_deliveries"] = 0

        # System settings
        try:
            from app.services.system_settings import get_settings_manager
            mgr = get_settings_manager()
            data["entities"]["system_settings"] = mgr.export_settings()
            counts["system_settings"] = len(data["entities"]["system_settings"])
        except Exception:
            counts["system_settings"] = 0

        # Pipeline templates
        try:
            from app.services.pipeline_templates import list_templates
            templates = list_templates()
            data["entities"]["pipeline_templates"] = [t.model_dump() for t in templates]
            counts["pipeline_templates"] = len(data["entities"]["pipeline_templates"])
        except Exception:
            counts["pipeline_templates"] = 0

        # Activity log
        try:
            from app.services.activity_log import get_activity_log
            log = get_activity_log()
            data["entities"]["activity_log"] = [e.to_dict() for e in log._entries]
            counts["activity_log"] = len(data["entities"]["activity_log"])
        except Exception:
            counts["activity_log"] = 0

        # Pipeline analytics
        try:
            from app.services.pipeline_analytics import get_analytics_service
            svc = get_analytics_service()
            data["entities"]["pipeline_analytics"] = [r.to_dict() for r in svc._runs]
            counts["pipeline_analytics"] = len(data["entities"]["pipeline_analytics"])
        except Exception:
            counts["pipeline_analytics"] = 0

        # Pipeline schedules
        try:
            from app.services.pipeline_scheduler import get_scheduler
            sched = get_scheduler()
            data["entities"]["pipeline_schedules"] = [s.to_dict() for s in sched._schedules.values()]
            counts["pipeline_schedules"] = len(data["entities"]["pipeline_schedules"])
        except Exception:
            counts["pipeline_schedules"] = 0

        serialized = json.dumps(data, default=str)
        record = BackupRecord(
            id=data["backup_id"],
            timestamp=data["timestamp"],
            size_bytes=len(serialized),
            entity_counts=counts,
            description=description,
        )
        self._backup_history.append(record)
        if len(self._backup_history) > self._max_history:
            self._backup_history.pop(0)
        self._last_backup = record

        logger.info("backup_created", id=record.id, size=record.size_bytes, counts=counts)
        return data

    def restore_backup(self, backup_data: dict, restore_types: Optional[list[str]] = None) -> dict:
        """Restore from a backup."""
        restored = {}
        entities = backup_data.get("entities", {})

        # Knowledge base
        if not restore_types or "knowledge" in restore_types:
            try:
                from app.services.knowledge_base import get_knowledge_base, KnowledgeEntry
                kb = get_knowledge_base()
                count = 0
                for entry_data in entities.get("knowledge_entries", []):
                    entry = KnowledgeEntry(
                        id=entry_data["id"],
                        title=entry_data["title"],
                        content=entry_data["content"],
                        category=entry_data["category"],
                        source=entry_data.get("source", ""),
                        confidence=entry_data.get("confidence", 0.5),
                        tags=entry_data.get("tags", []),
                    )
                    kb._entries[entry.id] = entry
                    count += 1
                restored["knowledge_entries"] = count
            except Exception as e:
                restored["knowledge_entries"] = f"Error: {e}"

        # System settings
        if not restore_types or "settings" in restore_types:
            try:
                from app.services.system_settings import get_settings_manager
                mgr = get_settings_manager()
                count = 0
                for key, value in entities.get("system_settings", {}).items():
                    try:
                        mgr.set(key, value)
                        count += 1
                    except (ValueError, KeyError):
                        pass
                restored["system_settings"] = count
            except Exception as e:
                restored["system_settings"] = f"Error: {e}"

        # Webhook subscriptions
        if not restore_types or "webhooks" in restore_types:
            try:
                from app.services.webhook_subscriptions import get_webhook_manager, WebhookSubscription
                mgr = get_webhook_manager()
                count = 0
                for wh_data in entities.get("webhooks", []):
                    sub = WebhookSubscription(
                        id=wh_data["id"],
                        url=wh_data["url"],
                        event_types=wh_data["event_types"],
                        secret=wh_data.get("secret", ""),
                        description=wh_data.get("description", ""),
                        active=wh_data.get("active", True),
                    )
                    mgr._subscriptions[sub.id] = sub
                    count += 1
                restored["webhooks"] = count
            except Exception as e:
                restored["webhooks"] = f"Error: {e}"

        # Agent config overrides
        if not restore_types or "agent_config" in restore_types:
            try:
                from app.services.agent_config import get_agent_config_manager, AgentConfig
                mgr = get_agent_config_manager()
                count = 0
                for agent, config_data in entities.get("agent_global_overrides", {}).items():
                    config = AgentConfig(**config_data)
                    mgr._global_overrides[agent] = config
                    count += 1
                restored["agent_global_overrides"] = count
            except Exception as e:
                restored["agent_global_overrides"] = f"Error: {e}"

        logger.info("backup_restored", restored=restored)
        return restored

    def get_backup_history(self, limit: int = 20) -> list[BackupRecord]:
        """Get backup history."""
        return list(reversed(self._backup_history[-limit:]))

    def get_last_backup(self) -> Optional[BackupRecord]:
        return self._last_backup

    def get_stats(self) -> dict:
        return {
            "total_backups": len(self._backup_history),
            "last_backup": self._last_backup.to_dict() if self._last_backup else None,
        }


# Singleton
_service: Optional[BackupRestoreService] = None


def get_backup_service() -> BackupRestoreService:
    global _service
    if _service is None:
        _service = BackupRestoreService()
    return _service
