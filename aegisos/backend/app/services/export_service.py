"""
Export/Import Service — Post-MVP Phase 8

Exports EvolvixOS data in JSON or CSV format:
- Pipeline runs (with stages)
- Analytics summary
- Knowledge base entries
- Activity log entries
- Agent configurations
- Full system snapshot
"""

from typing import Optional
from datetime import datetime
from io import StringIO
import json
import csv
from app.core.logging import get_logger

logger = get_logger("service.export_service")


class ExportService:

    def export_pipelines(self, format: str = "json") -> str:
        """Export all pipeline runs."""
        from app.api.v1.feature_pipeline import _pipeline_runs
        runs = list(_pipeline_runs.values())

        data = []
        for run in runs:
            item = {
                "id": run.id,
                "title": getattr(run, "title", ""),
                "status": run.status,
                "created_at": getattr(run, "created_at", ""),
                "total_duration_ms": getattr(run, "total_duration_ms", 0),
                "stages": [],
            }
            for stage in run.stages:
                item["stages"].append({
                    "stage": stage.stage,
                    "agent": stage.agent,
                    "status": stage.status,
                    "duration_ms": getattr(stage, "duration_ms", 0),
                    "retry_count": getattr(stage, "retry_count", 0),
                    "error": stage.error,
                })
            data.append(item)

        if format == "csv":
            return self._to_csv(data, ["id", "title", "status", "created_at", "total_duration_ms", "stages_count"])
        return json.dumps(data, indent=2, default=str)

    def export_analytics(self, format: str = "json") -> str:
        """Export analytics summary."""
        from app.services.pipeline_analytics import get_analytics_service
        svc = get_analytics_service()
        data = svc.get_full_analytics()
        if format == "csv":
            return self._analytics_to_csv(data)
        return json.dumps(data, indent=2, default=str)

    def export_knowledge_base(self, format: str = "json") -> str:
        """Export all knowledge base entries."""
        from app.services.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        entries = kb.list_entries(limit=1000)
        data = [e.to_dict() for e in entries]

        if format == "csv":
            return self._to_csv(data, ["id", "category", "title", "content", "source", "confidence", "tags", "created_at"])
        return json.dumps(data, indent=2, default=str)

    def export_activity_log(self, format: str = "json", limit: int = 1000) -> str:
        """Export activity log entries."""
        from app.services.activity_log import get_activity_log
        log = get_activity_log()
        entries = log.list(limit=limit)
        data = [e.to_dict() for e in entries]

        if format == "csv":
            return self._to_csv(data, ["id", "timestamp", "user_id", "user_email", "action", "entity_type", "entity_id", "entity_name", "severity"])
        return json.dumps(data, indent=2, default=str)

    def export_agent_configs(self, format: str = "json") -> str:
        """Export all agent configurations."""
        from app.services.agent_config import get_agent_config_manager, DEFAULT_AGENT_CONFIGS
        mgr = get_agent_config_manager()

        data = []
        for agent_name in DEFAULT_AGENT_CONFIGS:
            config = mgr.get_effective_config(agent_name)
            data.append(config.to_dict())

        if format == "csv":
            return self._to_csv(data, ["agent_name", "model", "temperature", "max_retries", "timeout_seconds", "enabled", "system_prompt_prefix"])
        return json.dumps(data, indent=2, default=str)

    def export_full_snapshot(self) -> str:
        """Export a complete system snapshot as JSON."""
        from app.services.dashboard import get_dashboard_service
        dashboard = get_dashboard_service()
        snapshot = {
            "exported_at": datetime.utcnow().isoformat(),
            "system": dashboard.get_overview(),
            "data": {
                "pipelines": json.loads(self.export_pipelines()),
                "knowledge_base": json.loads(self.export_knowledge_base()),
                "agent_configs": json.loads(self.export_agent_configs()),
            },
        }
        logger.info("full_snapshot_exported")
        return json.dumps(snapshot, indent=2, default=str)

    def _to_csv(self, data: list, columns: list) -> str:
        """Convert list of dicts to CSV string."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for item in data:
            row = []
            for col in columns:
                val = item.get(col, "")
                if isinstance(val, (list, dict)):
                    val = json.dumps(val, default=str)
                row.append(val)
            writer.writerow(row)
        return output.getvalue()

    def _analytics_to_csv(self, data: dict) -> str:
        """Flatten analytics to CSV."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        for key, val in data.items():
            if isinstance(val, (int, float, str)):
                writer.writerow([key, val])
            elif isinstance(val, list):
                writer.writerow([key, f"{len(val)} items"])
            elif isinstance(val, dict):
                for k, v in val.items():
                    writer.writerow([f"{key}.{k}", v])
        return output.getvalue()


# Singleton
_export: Optional[ExportService] = None


def get_export_service() -> ExportService:
    global _export
    if _export is None:
        _export = ExportService()
    return _export
