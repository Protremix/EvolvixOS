"""
Multi-Project Manager — Phase 20

Manages multiple projects within EvolvixOS, each with its own:
- Project type adapter (blockchain, web, mobile, etc.)
- Health monitoring configuration
- Agent configuration overrides
- Pipeline templates
- Learning context (agent feedback is per-project)

Integrates with:
- ProjectAdapter for project-type-specific behavior
- VerdisAgentEnhancer for Verdis context injection
- AgentLearningLoop for per-project learning feedback
- RealtimeMonitor for project health events
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.multi_project")


@dataclass
class ManagedProject:
    """A project managed by EvolvixOS."""
    id: str = field(default_factory=lambda: f"proj-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    name: str = ""
    type: str = ""  # blockchain, web_backend, frontend, mobile, infrastructure, ai_ml, generic
    status: str = "active"  # active, paused, archived
    description: str = ""
    repository: str = ""  # GitHub repo URL
    domain: str = ""  # production domain if deployed
    health_endpoint: str = ""  # health check URL
    config: dict = field(default_factory=dict)  # project-type-specific config
    agent_overrides: dict = field(default_factory=dict)  # per-project agent config
    pipeline_template: str = ""  # default pipeline template for this project
    tags: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_health_check: Optional[str] = None
    health_status: str = "unknown"  # healthy, degraded, down, unknown

    def to_dict(self) -> dict:
        return asdict(self)


class MultiProjectManager:
    """
    Manages multiple projects within EvolvixOS.
    Each project can have different types, configs, and agent behavior.
    """

    def __init__(self, max_projects: int = 100):
        self._projects: dict[str, ManagedProject] = {}
        self._max_projects = max_projects
        self._lock = threading.Lock()

    def register_project(self, name: str, project_type: str, **kwargs) -> ManagedProject:
        """Register a new project."""
        with self._lock:
            # Check if project with same name exists
            for p in self._projects.values():
                if p.name.lower() == name.lower():
                    raise ValueError(f"Project '{name}' already registered")

            project = ManagedProject(
                name=name, type=project_type,
                description=kwargs.get("description", ""),
                repository=kwargs.get("repository", ""),
                domain=kwargs.get("domain", ""),
                health_endpoint=kwargs.get("health_endpoint", ""),
                config=kwargs.get("config", {}),
                agent_overrides=kwargs.get("agent_overrides", {}),
                pipeline_template=kwargs.get("pipeline_template", ""),
                tags=kwargs.get("tags", []),
            )
            self._projects[project.id] = project

        logger.info("project_registered", id=project.id, name=name, type=project_type)
        return project

    def get_project(self, project_id: str) -> Optional[ManagedProject]:
        """Get a project by ID."""
        return self._projects.get(project_id)

    def get_project_by_name(self, name: str) -> Optional[ManagedProject]:
        """Get a project by name."""
        for p in self._projects.values():
            if p.name.lower() == name.lower():
                return p
        return None

    def list_projects(self, project_type: str = None, status: str = None) -> list[ManagedProject]:
        """List projects, optionally filtered."""
        projects = list(self._projects.values())
        if project_type:
            projects = [p for p in projects if p.type == project_type]
        if status:
            projects = [p for p in projects if p.status == status]
        return sorted(projects, key=lambda p: p.created_at, reverse=True)

    def update_project(self, project_id: str, **kwargs) -> Optional[ManagedProject]:
        """Update a project."""
        project = self._projects.get(project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.utcnow().isoformat()
        return project

    def archive_project(self, project_id: str) -> bool:
        """Archive a project."""
        project = self._projects.get(project_id)
        if not project:
            return False
        project.status = "archived"
        project.updated_at = datetime.utcnow().isoformat()
        return True

    def pause_project(self, project_id: str) -> bool:
        """Pause a project (stop monitoring)."""
        project = self._projects.get(project_id)
        if not project:
            return False
        project.status = "paused"
        project.updated_at = datetime.utcnow().isoformat()
        return True

    def resume_project(self, project_id: str) -> bool:
        """Resume a paused project."""
        project = self._projects.get(project_id)
        if not project:
            return False
        project.status = "active"
        project.updated_at = datetime.utcnow().isoformat()
        return True

    def get_agent_config(self, project_id: str, agent_name: str) -> dict:
        """Get agent configuration for a specific project + agent."""
        project = self._projects.get(project_id)
        if not project:
            return {}
        return project.agent_overrides.get(agent_name, {})

    def get_learning_context(self, project_id: str) -> dict:
        """Get learning context for a project (for agent feedback injection)."""
        project = self._projects.get(project_id)
        if not project:
            return {}
        return {
            "project_name": project.name,
            "project_type": project.type,
            "project_config": project.config,
            "health_status": project.health_status,
        }

    def update_health_status(self, project_id: str, status: str) -> bool:
        """Update a project's health status."""
        project = self._projects.get(project_id)
        if not project:
            return False
        project.health_status = status
        project.last_health_check = datetime.utcnow().isoformat()
        return True

    def get_stats(self) -> dict:
        """Get multi-project statistics."""
        projects = list(self._projects.values())
        type_counts = defaultdict(int)
        status_counts = defaultdict(int)
        for p in projects:
            type_counts[p.type] += 1
            status_counts[p.status] += 1

        return {
            "total_projects": len(projects),
            "active": status_counts.get("active", 0),
            "paused": status_counts.get("paused", 0),
            "archived": status_counts.get("archived", 0),
            "by_type": dict(type_counts),
            "by_status": dict(status_counts),
        }

    def register_verdis(self) -> ManagedProject:
        """Register the Verdis blockchain as a managed project."""
        existing = self.get_project_by_name("Verdis")
        if existing:
            return existing

        return self.register_project(
            name="Verdis",
            project_type="blockchain",
            description="Verdis blockchain — DPoS + BABE/GRANDPA, carbon-negative, native AMM DEX",
            repository="https://github.com/verdischain/Verdis",
            domain="verdischain.com",
            health_endpoint="https://verdischain.com/rpc",
            config={
                "consensus": "DPoS + BABE/GRANDPA",
                "total_supply": "100B VRS",
                "pallets": 13,
                "validators": 14,
                "spec_version": 11,
                "eco_features": ["CarbonCredits", "GreenValidator", "Reforestation"],
            },
            pipeline_template="blockchain_audit",
            tags=["blockchain", "substrate", "eco", "production"],
        )


# Singleton
_manager: Optional[MultiProjectManager] = None


def get_multi_project_manager() -> MultiProjectManager:
    global _manager
    if _manager is None:
        _manager = MultiProjectManager()
        _manager.register_verdis()
    return _manager
