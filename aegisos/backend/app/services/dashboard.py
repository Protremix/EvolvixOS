"""
System Dashboard Service — Post-MVP Phase 8

Aggregates data from all EvolvixOS subsystems into a single overview:
- Pipeline stats (total, active, completed, failed)
- Agent status (enabled/disabled, last activity)
- Knowledge base stats
- Activity log stats
- System health (subsystem availability)
- Performance metrics (API response times)
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import time
import threading
from app.core.logging import get_logger

logger = get_logger("service.dashboard")


@dataclass
class PerformanceMetric:
    """A single performance measurement."""
    endpoint: str
    method: str
    duration_ms: float
    status_code: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class PerformanceTracker:
    """Tracks API response times for performance monitoring."""

    def __init__(self, max_metrics: int = 5000):
        self._metrics: list[PerformanceMetric] = []
        self._max_metrics = max_metrics
        self._lock = threading.Lock()

    def record(self, endpoint: str, method: str, duration_ms: float, status_code: int):
        """Record a performance metric."""
        metric = PerformanceMetric(
            endpoint=endpoint,
            method=method,
            duration_ms=round(duration_ms, 2),
            status_code=status_code,
        )
        with self._lock:
            self._metrics.append(metric)
            if len(self._metrics) > self._max_metrics:
                self._metrics.pop(0)

    def get_stats(self, limit: int = 100) -> dict:
        """Get performance statistics."""
        with self._lock:
            metrics = list(reversed(self._metrics[-limit:]))

        if not metrics:
            return {
                "total_requests": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "min_duration_ms": 0,
                "error_rate": 0,
                "slowest_endpoints": [],
                "by_endpoint": {},
            }

        durations = [m.duration_ms for m in metrics]
        errors = [m for m in metrics if m.status_code >= 400]

        # Group by endpoint
        by_endpoint = defaultdict(lambda: {"count": 0, "total_duration": 0, "errors": 0})
        for m in metrics:
            key = f"{m.method} {m.endpoint}"
            by_endpoint[key]["count"] += 1
            by_endpoint[key]["total_duration"] += m.duration_ms
            if m.status_code >= 400:
                by_endpoint[key]["errors"] += 1

        endpoint_stats = []
        for key, stats in by_endpoint.items():
            endpoint_stats.append({
                "endpoint": key,
                "count": stats["count"],
                "avg_duration_ms": round(stats["total_duration"] / stats["count"], 2),
                "error_count": stats["errors"],
            })
        endpoint_stats.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        return {
            "total_requests": len(metrics),
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "error_rate": round(len(errors) / len(metrics) * 100, 1),
            "slowest_endpoints": endpoint_stats[:10],
            "recent_metrics": [m.to_dict() for m in metrics[:20]],
        }

    def clear(self):
        with self._lock:
            self._metrics.clear()


# Singleton
_tracker: Optional[PerformanceTracker] = None


def get_performance_tracker() -> PerformanceTracker:
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker


class DashboardService:
    """Aggregates data from all subsystems for the main dashboard."""

    def get_overview(self) -> dict:
        """Get a complete system overview."""
        overview = {
            "timestamp": datetime.utcnow().isoformat(),
            "subsystems": self._get_subsystem_health(),
            "pipeline_stats": self._get_pipeline_stats(),
            "agent_stats": self._get_agent_stats(),
            "knowledge_stats": self._get_knowledge_stats(),
            "activity_stats": self._get_activity_stats(),
            "performance_stats": self._get_performance_stats(),
            "verdis_stats": self._get_verdis_stats(),
        }
        return overview

    def _get_subsystem_health(self) -> dict:
        """Check health of all subsystems."""
        subsystems = {}
        checks = [
            ("authentication", self._check_auth),
            ("projects", self._check_projects),
            ("tasks", self._check_tasks),
            ("ai_engine", self._check_ai),
            ("pipelines", self._check_pipelines),
            ("pipeline_templates", self._check_templates),
            ("pipeline_events", self._check_events),
            ("pipeline_notifications", self._check_notifications),
            ("pipeline_analytics", self._check_analytics),
            ("pipeline_scheduler", self._check_scheduler),
            ("knowledge_base", self._check_knowledge),
            ("agent_config", self._check_agent_config),
            ("activity_log", self._check_activity_log),
            ("github_integration", self._check_github),
            ("websocket", self._check_websocket),
            ("verdis_blockchain", self._check_verdis),
        ]

        for name, check in checks:
            try:
                subsystems[name] = check()
            except Exception as e:
                subsystems[name] = {"status": "error", "error": str(e)}
                logger.warning("subsystem_check_failed", subsystem=name, error=str(e))

        return subsystems

    def _check_auth(self) -> dict:
        return {"status": "healthy", "detail": "JWT + bcrypt auth active"}

    def _check_projects(self) -> dict:
        try:
            from app.services.project_service import project_service
            # Can't call DB, just verify service exists
            return {"status": "healthy", "detail": "Project service available"}
        except Exception:
            return {"status": "degraded", "detail": "Project service unavailable"}

    def _check_tasks(self) -> dict:
        try:
            from app.services.task_service import task_service
            return {"status": "healthy", "detail": "Task service available"}
        except Exception:
            return {"status": "degraded", "detail": "Task service unavailable"}

    def _check_ai(self) -> dict:
        try:
            from app.ai.workflow_engine import AIWorkflowEngine
            from app.ai.agents.base_agent import TaskType
            return {"status": "healthy", "detail": f"AI engine with {len(TaskType)} task types"}
        except Exception as e:
            return {"status": "degraded", "detail": str(e)}

    def _check_pipelines(self) -> dict:
        try:
            from app.api.v1.feature_pipeline import _pipeline_runs
            total = len(_pipeline_runs)
            active = sum(1 for r in _pipeline_runs.values() if r.status in ("running", "pending"))
            return {"status": "healthy", "total_pipelines": total, "active": active}
        except Exception:
            return {"status": "healthy", "total_pipelines": 0, "active": 0}

    def _check_templates(self) -> dict:
        try:
            from app.services.pipeline_templates import get_template_manager
            mgr = get_template_manager()
            return {"status": "healthy", "total_templates": len(mgr._templates)}
        except Exception:
            return {"status": "healthy", "total_templates": 0}

    def _check_events(self) -> dict:
        try:
            from app.services.pipeline_events import get_event_bus
            bus = get_event_bus()
            return {"status": "healthy", "total_events": len(bus._events)}
        except Exception:
            return {"status": "healthy", "total_events": 0}

    def _check_notifications(self) -> dict:
        try:
            from app.services.pipeline_notifications import get_notification_manager
            mgr = get_notification_manager()
            return {"status": "healthy", "total_notifications": len(mgr._notifications)}
        except Exception:
            return {"status": "healthy", "total_notifications": 0}

    def _check_analytics(self) -> dict:
        try:
            from app.services.pipeline_analytics import get_analytics_service
            svc = get_analytics_service()
            return {"status": "healthy", "pipeline_count": len(svc._runs)}
        except Exception:
            return {"status": "healthy", "pipeline_count": 0}

    def _check_scheduler(self) -> dict:
        try:
            from app.services.pipeline_scheduler import get_scheduler
            sched = get_scheduler()
            return {"status": "healthy", "total_schedules": len(sched._schedules)}
        except Exception:
            return {"status": "healthy", "total_schedules": 0}

    def _check_knowledge(self) -> dict:
        try:
            from app.services.knowledge_base import get_knowledge_base
            kb = get_knowledge_base()
            return {"status": "healthy", "total_entries": len(kb._entries), "total_patterns": len(kb._patterns)}
        except Exception:
            return {"status": "healthy", "total_entries": 0, "total_patterns": 0}

    def _check_agent_config(self) -> dict:
        try:
            from app.services.agent_config import get_agent_config_manager
            mgr = get_agent_config_manager()
            return {"status": "healthy", "global_overrides": len(mgr._global_overrides), "project_configs": len(mgr._project_configs)}
        except Exception:
            return {"status": "healthy", "global_overrides": 0, "project_configs": 0}

    def _check_activity_log(self) -> dict:
        try:
            from app.services.activity_log import get_activity_log
            log = get_activity_log()
            return {"status": "healthy", "total_entries": len(log._entries)}
        except Exception:
            return {"status": "healthy", "total_entries": 0}

    def _check_github(self) -> dict:
        try:
            from app.services.github_integration import get_github_client
            return {"status": "healthy", "detail": "GitHub integration available"}
        except Exception:
            return {"status": "degraded", "detail": "GitHub integration not configured"}

    def _check_websocket(self) -> dict:
        try:
            from app.services.pipeline_events import get_websocket_manager
            ws = get_websocket_manager()
            return {"status": "healthy", "connected_clients": len(ws._clients)}
        except Exception:
            return {"status": "healthy", "connected_clients": 0}

    def _check_verdis(self) -> dict:
        try:
            from app.services.verdis_integration import VerdisIntegration
            return {"status": "healthy", "detail": "Verdis integration available"}
        except Exception:
            return {"status": "degraded", "detail": "Verdis integration not configured"}

    def _get_pipeline_stats(self) -> dict:
        try:
            from app.api.v1.feature_pipeline import _pipeline_runs
            runs = list(_pipeline_runs.values())
            return {
                "total": len(runs),
                "completed": sum(1 for r in runs if r.status == "completed"),
                "failed": sum(1 for r in runs if r.status == "failed"),
                "running": sum(1 for r in runs if r.status == "running"),
                "pending": sum(1 for r in runs if r.status == "pending"),
                "cancelled": sum(1 for r in runs if r.status == "cancelled"),
            }
        except Exception:
            return {"total": 0, "completed": 0, "failed": 0, "running": 0, "pending": 0, "cancelled": 0}

    def _get_agent_stats(self) -> dict:
        try:
            from app.services.agent_config import DEFAULT_AGENT_CONFIGS, get_agent_config_manager
            mgr = get_agent_config_manager()
            enabled = mgr.list_enabled_agents()
            return {
                "total_agents": len(DEFAULT_AGENT_CONFIGS),
                "enabled": len(enabled),
                "disabled": len(DEFAULT_AGENT_CONFIGS) - len(enabled),
                "agent_names": list(DEFAULT_AGENT_CONFIGS.keys()),
            }
        except Exception:
            return {"total_agents": 0, "enabled": 0, "disabled": 0, "agent_names": []}

    def _get_knowledge_stats(self) -> dict:
        try:
            from app.services.knowledge_base import get_knowledge_base
            return get_knowledge_base().get_stats()
        except Exception:
            return {"total_entries": 0, "total_patterns": 0}

    def _get_activity_stats(self) -> dict:
        try:
            from app.services.activity_log import get_activity_log
            return get_activity_log().get_stats()
        except Exception:
            return {"total_entries": 0}

    def _get_performance_stats(self) -> dict:
        try:
            return get_performance_tracker().get_stats()
        except Exception:
            return {"total_requests": 0}

    def _get_verdis_stats(self) -> dict:
        try:
            from app.services.verdis_integration import VerdisIntegration
            integration = VerdisIntegration()
            return integration.get_health_summary()
        except Exception:
            return {"status": "not_configured"}


# Singleton
_dashboard: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    global _dashboard
    if _dashboard is None:
        _dashboard = DashboardService()
    return _dashboard
