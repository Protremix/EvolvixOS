"""
Deployment Dashboard Service — Phase 30

Manages deployment lifecycle, tracks GitHub Actions deployments,
provides deployment history and environment status.
"""

import time
import threading
import json
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
from app.core.logging import get_logger

logger = get_logger("service.deployment")


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"


class DeploymentTarget(str, Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    MAINNET = "mainnet"


class DeploymentComponent(str, Enum):
    BLOCKCHAIN = "blockchain"
    EVOLVIXOS_BACKEND = "evolvixos_backend"
    EVOLVIXOS_FRONTEND = "evolvixos_frontend"
    EXPLORER = "explorer"
    WALLET_ANDROID = "wallet_android"
    WALLET_WEB = "wallet_web"
    BRIDGE = "bridge"
    SDK = "sdk"
    DOCS = "docs"


@dataclass
class Deployment:
    id: str
    component: str
    target: str
    status: str
    version: str
    commit_sha: str
    commit_message: str
    branch: str
    triggered_by: str
    started_at: str
    completed_at: str = ""
    duration_seconds: float = 0
    logs: list[dict] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    rollback_available: bool = False
    previous_version: str = ""
    environment_vars: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Environment:
    name: str
    target: str
    url: str
    status: str  # healthy, degraded, offline
    components: dict  # component -> status
    last_deploy: str = ""
    version: str = ""
    uptime_percent: float = 100.0

    def to_dict(self) -> dict:
        return asdict(self)


class DeploymentService:
    """Manages deployments and environment tracking."""

    def __init__(self, max_history: int = 500):
        self._deployments: dict[str, Deployment] = {}
        self._history: deque = deque(maxlen=max_history)
        self._environments: dict[str, Environment] = {
            "staging": Environment(
                name="Staging",
                target="staging",
                url="https://staging.verdischain.com",
                status="offline",
                components={c.value: "not_deployed" for c in DeploymentComponent},
            ),
            "production": Environment(
                name="Production",
                target="production",
                url="https://verdischain.com",
                status="degraded",
                components={
                    "blockchain": "deployed",
                    "evolvixos_backend": "not_deployed",
                    "evolvixos_frontend": "not_deployed",
                    "explorer": "deployed",
                    "wallet_android": "deployed",
                    "wallet_web": "deployed",
                    "bridge": "not_deployed",
                    "sdk": "deployed",
                    "docs": "deployed",
                },
                last_deploy="2026-08-05T08:00:00",
                version="v11.0.0",
            ),
            "mainnet": Environment(
                name="Mainnet",
                target="mainnet",
                url="https://verdischain.com/rpc",
                status="healthy",
                components={"blockchain": "deployed"},
                last_deploy="2026-08-05T08:00:00",
                version="v11.0.0",
            ),
        }
        self._lock = threading.Lock()
        self._counter = 0

    def _gen_id(self) -> str:
        self._counter += 1
        return f"dep-{int(time.time())}-{self._counter:04d}"

    def create_deployment(
        self,
        component: str,
        target: str,
        version: str,
        commit_sha: str,
        commit_message: str,
        branch: str,
        triggered_by: str,
        previous_version: str = "",
    ) -> Deployment:
        """Create a new deployment record."""
        with self._lock:
            dep_id = self._gen_id()
            deployment = Deployment(
                id=dep_id,
                component=component,
                target=target,
                status=DeploymentStatus.PENDING.value,
                version=version,
                commit_sha=commit_sha,
                commit_message=commit_message,
                branch=branch,
                triggered_by=triggered_by,
                started_at=datetime.utcnow().isoformat(),
                previous_version=previous_version,
                rollback_available=bool(previous_version),
            )
            self._deployments[dep_id] = deployment
            self._history.append(deployment)
            logger.info("deployment_created", dep_id=dep_id, component=component, target=target)
            return deployment

    def update_deployment(
        self,
        dep_id: str,
        status: str = None,
        logs: list[dict] = None,
        artifacts: list[dict] = None,
        environment_vars: dict = None,
    ) -> Optional[Deployment]:
        """Update a deployment."""
        dep = self._deployments.get(dep_id)
        if not dep:
            return None
        if status:
            dep.status = status
            if status in (DeploymentStatus.SUCCESS.value, DeploymentStatus.FAILED.value, DeploymentStatus.CANCELLED.value):
                dep.completed_at = datetime.utcnow().isoformat()
                try:
                    start = datetime.fromisoformat(dep.started_at)
                    dep.duration_seconds = max(0.1, (datetime.utcnow() - start).total_seconds())
                except Exception:
                    dep.duration_seconds = 0.1
        if logs:
            dep.logs.extend(logs)
        if artifacts:
            dep.artifacts.extend(artifacts)
        if environment_vars:
            dep.environment_vars.update(environment_vars)
        return dep

    def add_log(self, dep_id: str, level: str, message: str) -> bool:
        """Add a log entry to a deployment."""
        dep = self._deployments.get(dep_id)
        if not dep:
            return False
        dep.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        })
        return True

    def get_deployment(self, dep_id: str) -> Optional[Deployment]:
        """Get a deployment by ID."""
        return self._deployments.get(dep_id)

    def list_deployments(
        self,
        component: str = None,
        target: str = None,
        status: str = None,
        limit: int = 50,
    ) -> list[Deployment]:
        """List deployments with optional filters."""
        deps = list(self._history)
        if component:
            deps = [d for d in deps if d.component == component]
        if target:
            deps = [d for d in deps if d.target == target]
        if status:
            deps = [d for d in deps if d.status == status]
        return deps[:limit]

    def rollback_deployment(self, dep_id: str) -> Optional[Deployment]:
        """Mark a deployment as rolled back and create rollback record."""
        dep = self._deployments.get(dep_id)
        if not dep or not dep.rollback_available:
            return None
        dep.status = DeploymentStatus.ROLLBACK.value
        dep.completed_at = datetime.utcnow().isoformat()
        rollback = self.create_deployment(
            component=dep.component,
            target=dep.target,
            version=dep.previous_version,
            commit_sha="rollback",
            commit_message=f"Rollback to {dep.previous_version}",
            branch=dep.branch,
            triggered_by=dep.triggered_by,
        )
        rollback.status = DeploymentStatus.IN_PROGRESS.value
        return rollback

    def get_environment(self, target: str) -> Optional[Environment]:
        """Get environment status."""
        return self._environments.get(target)

    def list_environments(self) -> list[Environment]:
        """List all environments."""
        return list(self._environments.values())

    def update_environment(self, target: str, status: str = None, version: str = None, component_status: dict = None) -> Optional[Environment]:
        """Update environment status."""
        env = self._environments.get(target)
        if not env:
            return None
        if status:
            env.status = status
        if version:
            env.version = version
        if component_status:
            env.components.update(component_status)
        return env

    def get_deployment_stats(self) -> dict:
        """Get deployment statistics."""
        deps = list(self._history)
        by_status = {}
        by_component = {}
        by_target = {}
        for d in deps:
            by_status[d.status] = by_status.get(d.status, 0) + 1
            by_component[d.component] = by_component.get(d.component, 0) + 1
            by_target[d.target] = by_target.get(d.target, 0) + 1

        success_rate = 0
        if deps:
            completed = [d for d in deps if d.status in (DeploymentStatus.SUCCESS.value, DeploymentStatus.FAILED.value)]
            if completed:
                successes = sum(1 for d in completed if d.status == DeploymentStatus.SUCCESS.value)
                success_rate = round(successes / len(completed) * 100, 1)

        avg_duration = 0
        completed_with_time = [d for d in deps if d.duration_seconds > 0]
        if completed_with_time:
            avg_duration = round(sum(d.duration_seconds for d in completed_with_time) / len(completed_with_time), 1)

        return {
            "total_deployments": len(deps),
            "by_status": by_status,
            "by_component": by_component,
            "by_target": by_target,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
        }

    def get_github_actions_workflows(self) -> list[dict]:
        """Return GitHub Actions deployment workflows."""
        return [
            {
                "name": "Deploy Verdis Blockchain",
                "file": "deploy-blockchain.yml",
                "trigger": "workflow_dispatch",
                "targets": ["staging", "mainnet"],
                "component": "blockchain",
                "description": "Deploy Verdis node to staging or mainnet via SSH",
            },
            {
                "name": "Deploy EvolvixOS Backend",
                "file": "deploy-backend.yml",
                "trigger": "workflow_dispatch",
                "targets": ["staging", "production"],
                "component": "evolvixos_backend",
                "description": "Deploy EvolvixOS FastAPI backend",
            },
            {
                "name": "Deploy EvolvixOS Frontend",
                "file": "deploy-frontend.yml",
                "trigger": "workflow_dispatch",
                "targets": ["staging", "production"],
                "component": "evolvixos_frontend",
                "description": "Deploy EvolvixOS React frontend",
            },
            {
                "name": "Deploy Verdiscan Explorer",
                "file": "deploy-explorer.yml",
                "trigger": "workflow_dispatch",
                "targets": ["production"],
                "component": "explorer",
                "description": "Deploy Verdiscan block explorer",
            },
            {
                "name": "Deploy Bridge Service",
                "file": "deploy-bridge.yml",
                "trigger": "workflow_dispatch",
                "targets": ["staging", "production"],
                "component": "bridge",
                "description": "Deploy cross-chain bridge relayer",
            },
        ]


_service: Optional[DeploymentService] = None

def get_deployment_service() -> DeploymentService:
    global _service
    if _service is None:
        _service = DeploymentService()
    return _service
