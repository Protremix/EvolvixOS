"""
Agent Configuration Service — Post-MVP Phase 7

Manages per-project agent configurations:
- Override agent behavior per project (temperature, model, max_retries)
- Custom system prompt prefixes per project
- Enable/disable specific agents per project
- Global defaults with project-level overrides
- Config validation
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger("service.agent_config")

# Default configuration for all agents
DEFAULT_AGENT_CONFIGS = {
    "cto_agent": {
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_retries": 2,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "architect_agent": {
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_retries": 2,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "security_agent": {
        "model": "gpt-4o",
        "temperature": 0.1,
        "max_retries": 3,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "qa_agent": {
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_retries": 2,
        "timeout_seconds": 90,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "planner_agent": {
        "model": "gpt-4o",
        "temperature": 0.4,
        "max_retries": 2,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "reviewer_agent": {
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_retries": 2,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "documentation_agent": {
        "model": "gpt-4o",
        "temperature": 0.4,
        "max_retries": 1,
        "timeout_seconds": 90,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "memory_agent": {
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_retries": 1,
        "timeout_seconds": 60,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "test_generator_agent": {
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_retries": 2,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "ci_healer_agent": {
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_retries": 3,
        "timeout_seconds": 120,
        "system_prompt_prefix": "",
        "enabled": True,
    },
    "code_analyzer_agent": {
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_retries": 2,
        "timeout_seconds": 90,
        "system_prompt_prefix": "",
        "enabled": True,
    },
}

VALID_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"}


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    agent_name: str
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_retries: int = 2
    timeout_seconds: int = 120
    system_prompt_prefix: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectAgentConfig:
    """Per-project agent configuration with overrides."""
    project_id: str
    configs: dict[str, AgentConfig] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "configs": {k: v.to_dict() for k, v in self.configs.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def validate_config(config: AgentConfig) -> list[str]:
    """Validate an agent config. Returns list of error messages."""
    errors = []
    if config.agent_name not in DEFAULT_AGENT_CONFIGS:
        errors.append(f"Unknown agent: {config.agent_name}")
    if config.model not in VALID_MODELS:
        errors.append(f"Invalid model: {config.model}. Valid: {VALID_MODELS}")
    if not 0.0 <= config.temperature <= 2.0:
        errors.append(f"Temperature must be 0.0-2.0, got {config.temperature}")
    if config.max_retries < 0 or config.max_retries > 10:
        errors.append(f"max_retries must be 0-10, got {config.max_retries}")
    if config.timeout_seconds < 10 or config.timeout_seconds > 600:
        errors.append(f"timeout_seconds must be 10-600, got {config.timeout_seconds}")
    return errors


class AgentConfigManager:
    """Manages agent configurations globally and per-project."""

    def __init__(self):
        self._project_configs: dict[str, ProjectAgentConfig] = {}
        self._global_overrides: dict[str, AgentConfig] = {}

    def get_default_config(self, agent_name: str) -> AgentConfig:
        """Get the default configuration for an agent."""
        defaults = DEFAULT_AGENT_CONFIGS.get(agent_name, {})
        return AgentConfig(
            agent_name=agent_name,
            model=defaults.get("model", "gpt-4o"),
            temperature=defaults.get("temperature", 0.3),
            max_retries=defaults.get("max_retries", 2),
            timeout_seconds=defaults.get("timeout_seconds", 120),
            system_prompt_prefix=defaults.get("system_prompt_prefix", ""),
            enabled=defaults.get("enabled", True),
        )

    def get_effective_config(self, agent_name: str, project_id: Optional[str] = None) -> AgentConfig:
        """
        Get the effective config for an agent in a project context.
        Priority: project override > global override > default.
        """
        # Start with default
        config = self.get_default_config(agent_name)

        # Apply global override
        if agent_name in self._global_overrides:
            override = self._global_overrides[agent_name]
            config.model = override.model
            config.temperature = override.temperature
            config.max_retries = override.max_retries
            config.timeout_seconds = override.timeout_seconds
            config.system_prompt_prefix = override.system_prompt_prefix
            config.enabled = override.enabled

        # Apply project override
        if project_id and project_id in self._project_configs:
            project_config = self._project_configs[project_id]
            if agent_name in project_config.configs:
                override = project_config.configs[agent_name]
                config.model = override.model
                config.temperature = override.temperature
                config.max_retries = override.max_retries
                config.timeout_seconds = override.timeout_seconds
                config.system_prompt_prefix = override.system_prompt_prefix
                config.enabled = override.enabled

        return config

    def set_project_config(self, project_id: str, agent_name: str, config: AgentConfig) -> AgentConfig:
        """Set agent configuration for a specific project."""
        errors = validate_config(config)
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        if project_id not in self._project_configs:
            self._project_configs[project_id] = ProjectAgentConfig(project_id=project_id)

        self._project_configs[project_id].configs[agent_name] = config
        self._project_configs[project_id].updated_at = datetime.utcnow().isoformat()
        logger.info("project_config_set", project_id=project_id, agent=agent_name)
        return config

    def get_project_config(self, project_id: str) -> Optional[ProjectAgentConfig]:
        """Get all agent configs for a project."""
        return self._project_configs.get(project_id)

    def delete_project_config(self, project_id: str, agent_name: str) -> bool:
        """Delete a project-specific agent config (reverts to global/default)."""
        if project_id in self._project_configs:
            configs = self._project_configs[project_id].configs
            if agent_name in configs:
                del configs[agent_name]
                self._project_configs[project_id].updated_at = datetime.utcnow().isoformat()
                return True
        return False

    def set_global_override(self, agent_name: str, config: AgentConfig) -> AgentConfig:
        """Set a global override for an agent."""
        errors = validate_config(config)
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        self._global_overrides[agent_name] = config
        logger.info("global_config_set", agent=agent_name)
        return config

    def get_global_override(self, agent_name: str) -> Optional[AgentConfig]:
        """Get the global override for an agent."""
        return self._global_overrides.get(agent_name)

    def delete_global_override(self, agent_name: str) -> bool:
        """Delete a global override (reverts to defaults)."""
        if agent_name in self._global_overrides:
            del self._global_overrides[agent_name]
            return True
        return False

    def list_all_agents(self) -> list[dict]:
        """List all known agents with their default configs."""
        return [
            {"agent_name": name, **defaults}
            for name, defaults in DEFAULT_AGENT_CONFIGS.items()
        ]

    def list_enabled_agents(self, project_id: Optional[str] = None) -> list[str]:
        """List agents that are enabled for a project (or globally)."""
        enabled = []
        for agent_name in DEFAULT_AGENT_CONFIGS:
            config = self.get_effective_config(agent_name, project_id)
            if config.enabled:
                enabled.append(agent_name)
        return enabled

    def reset_project_configs(self, project_id: str) -> bool:
        """Delete all project-specific agent configs."""
        if project_id in self._project_configs:
            del self._project_configs[project_id]
            return True
        return False


# Singleton
_manager: Optional[AgentConfigManager] = None


def get_agent_config_manager() -> AgentConfigManager:
    global _manager
    if _manager is None:
        _manager = AgentConfigManager()
    return _manager
