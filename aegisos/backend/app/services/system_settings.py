"""
System Settings Service — Post-MVP Phase 9

Manages configurable system-wide settings:
- Feature toggles (enable/disable features)
- API configuration (rate limits, timeouts)
- AI defaults (default model, temperature)
- Notification preferences
- System behavior flags
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger("service.system_settings")

# Default system settings
DEFAULT_SETTINGS = {
    # Feature toggles
    "feature.pipelines.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable pipeline execution"},
    "feature.knowledge_base.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable knowledge base"},
    "feature.analytics.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable pipeline analytics"},
    "feature.scheduler.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable pipeline scheduler"},
    "feature.webhooks.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable webhook subscriptions"},
    "feature.github.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable GitHub integration"},
    "feature.verdis.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable Verdis blockchain integration"},
    "feature.export.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable data export"},
    "feature.activity_log.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable activity logging"},
    "feature.ast_diff.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable AST diff engine"},
    "feature.spec_compiler.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable spec-driven compiler"},
    "feature.dependency_graph.enabled": {"value": True, "type": "bool", "category": "features", "description": "Enable dependency graph tracker"},

    # API settings
    "api.rate_limit.per_minute": {"value": 100, "type": "int", "category": "api", "description": "Default API rate limit per minute"},
    "api.rate_limit.per_hour": {"value": 5000, "type": "int", "category": "api", "description": "Default API rate limit per hour"},
    "api.timeout_seconds": {"value": 30, "type": "int", "category": "api", "description": "Default API timeout"},
    "api.max_request_size_mb": {"value": 10, "type": "int", "category": "api", "description": "Max request body size in MB"},
    "api.cors_origins": {"value": "*", "type": "string", "category": "api", "description": "Allowed CORS origins"},

    # AI settings
    "ai.default_model": {"value": "gpt-4o", "type": "string", "category": "ai", "description": "Default AI model"},
    "ai.default_temperature": {"value": 0.3, "type": "float", "category": "ai", "description": "Default AI temperature"},
    "ai.max_tokens": {"value": 4000, "type": "int", "category": "ai", "description": "Default max tokens for AI calls"},
    "ai.timeout_seconds": {"value": 120, "type": "int", "category": "ai", "description": "AI call timeout"},
    "ai.retry_count": {"value": 2, "type": "int", "category": "ai", "description": "Default retry count for AI calls"},

    # Notification settings
    "notification.retention_days": {"value": 30, "type": "int", "category": "notifications", "description": "Notification retention period"},
    "notification.batch_size": {"value": 50, "type": "int", "category": "notifications", "description": "Batch size for notifications"},

    # Pipeline settings
    "pipeline.max_concurrent": {"value": 10, "type": "int", "category": "pipelines", "description": "Max concurrent pipelines"},
    "pipeline.default_timeout": {"value": 3600, "type": "int", "category": "pipelines", "description": "Default pipeline timeout (seconds)"},
    "pipeline.retry_attempts": {"value": 2, "type": "int", "category": "pipelines", "description": "Default retry attempts per stage"},
    "pipeline.event_buffer_size": {"value": 1000, "type": "int", "category": "pipelines", "description": "Pipeline event buffer size"},

    # Activity log
    "activity_log.max_entries": {"value": 10000, "type": "int", "category": "activity_log", "description": "Max activity log entries"},
    "activity_log.retention_days": {"value": 90, "type": "int", "category": "activity_log", "description": "Activity log retention period"},

    # Knowledge base
    "knowledge.max_entries": {"value": 10000, "type": "int", "category": "knowledge", "description": "Max knowledge base entries"},
    "knowledge.auto_extract_patterns": {"value": True, "type": "bool", "category": "knowledge", "description": "Auto-extract patterns from pipeline runs"},
}


class SystemSettingsManager:
    """Manages system-wide configurable settings."""

    def __init__(self):
        self._settings: dict[str, dict] = {}
        self._overrides: dict[str, any] = {}
        self._load_defaults()

    def _load_defaults(self):
        for key, config in DEFAULT_SETTINGS.items():
            self._settings[key] = config.copy()

    def get(self, key: str, default=None):
        """Get a setting value (with override if set)."""
        if key in self._overrides:
            return self._overrides[key]
        if key in self._settings:
            return self._settings[key]["value"]
        return default

    def set(self, key: str, value) -> bool:
        """Set an override for a setting."""
        if key not in self._settings:
            raise ValueError(f"Unknown setting: {key}")

        # Type validation
        expected_type = self._settings[key]["type"]
        if expected_type == "bool" and not isinstance(value, bool):
            raise ValueError(f"Setting {key} expects bool, got {type(value).__name__}")
        elif expected_type == "int" and not isinstance(value, int):
            raise ValueError(f"Setting {key} expects int, got {type(value).__name__}")
        elif expected_type == "float" and not isinstance(value, (int, float)):
            raise ValueError(f"Setting {key} expects float, got {type(value).__name__}")
        elif expected_type == "string" and not isinstance(value, str):
            raise ValueError(f"Setting {key} expects string, got {type(value).__name__}")

        self._overrides[key] = value
        logger.info("setting_overridden", key=key, value=value)
        return True

    def reset(self, key: str) -> bool:
        """Reset a setting to its default value."""
        if key in self._overrides:
            del self._overrides[key]
            return True
        return False

    def list_all(self) -> list[dict]:
        """List all settings with current values."""
        result = []
        for key, config in self._settings.items():
            result.append({
                "key": key,
                "value": self.get(key),
                "default": config["value"],
                "type": config["type"],
                "category": config["category"],
                "description": config["description"],
                "overridden": key in self._overrides,
            })
        return result

    def list_by_category(self, category: str) -> list[dict]:
        """List settings in a specific category."""
        return [s for s in self.list_all() if s["category"] == category]

    def get_categories(self) -> list[str]:
        """Get all setting categories."""
        return list(set(s["category"] for s in self._settings.values()))

    def export_settings(self) -> dict:
        """Export all settings as a dict."""
        return {key: self.get(key) for key in self._settings}

    def import_settings(self, settings: dict) -> int:
        """Import settings from a dict. Returns count of imported settings."""
        count = 0
        for key, value in settings.items():
            try:
                self.set(key, value)
                count += 1
            except (ValueError, KeyError):
                pass
        logger.info("settings_imported", count=count)
        return count

    def reset_all(self):
        """Reset all overrides."""
        self._overrides.clear()
        logger.info("all_settings_reset")


# Singleton
_manager: Optional[SystemSettingsManager] = None


def get_settings_manager() -> SystemSettingsManager:
    global _manager
    if _manager is None:
        _manager = SystemSettingsManager()
    return _manager
