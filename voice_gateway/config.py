"""
Configuration module for EvolvixOS Voice Gateway.

Reads configuration settings from config/config.yaml under the 'voice_gateway' section,
supporting environment variable overrides and sensible default values.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class VoiceGatewayConfig:
    """Voice Gateway configuration manager."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "enabled": True,
        "auth_enabled": False,
        "api_key": None,
        "max_upload_mb": 10,
        "rate_limit": 30,  # Max requests per minute per IP
        "session_timeout_min": 30,
        "default_language": "en",
        "wake_word": "hey evolvix",
        "tts_voice": "af",
        "languages": {
            "en": {
                "tts_voice": "af",
                "wake_word": "hey evolvix"
            },
            "ru": {
                "tts_voice": "af",
                "wake_word": "эй эволвикс"
            }
        }
    }

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration from YAML file and environment variables."""
        self.config_path = config_path
        self._raw_config = self._load_yaml_config()
        self._gateway_config = self._merge_defaults()

    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file if it exists."""
        if not os.path.exists(self.config_path):
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    if "config" in data and isinstance(data["config"], dict):
                        return data["config"].get("voice_gateway", {})
                    return data.get("voice_gateway", {})
        except Exception:
            pass
        return {}

    def _merge_defaults(self) -> Dict[str, Any]:
        """Merge file configuration with default configuration."""
        merged = self.DEFAULT_CONFIG.copy()
        for key, val in self._raw_config.items():
            if isinstance(val, dict) and key in merged and isinstance(merged[key], dict):
                merged_sub = merged[key].copy()
                merged_sub.update(val)
                merged[key] = merged_sub
            else:
                merged[key] = val
        return merged

    @property
    def enabled(self) -> bool:
        """Check if voice gateway is enabled."""
        val = os.getenv("EVOLVIX_VOICE_ENABLED")
        if val is not None:
            return val.lower() in ("true", "1", "yes")
        return bool(self._gateway_config.get("enabled", True))

    @property
    def auth_enabled(self) -> bool:
        """Check if authentication is enabled for the voice gateway."""
        val = os.getenv("EVOLVIX_VOICE_AUTH_ENABLED")
        if val is not None:
            return val.lower() in ("true", "1", "yes")
        return bool(self._gateway_config.get("auth_enabled", False))

    @property
    def max_upload_mb(self) -> int:
        """Maximum allowed upload file size in megabytes."""
        val = os.getenv("EVOLVIX_VOICE_MAX_UPLOAD_MB")
        if val is not None:
            try:
                return int(val)
            except ValueError:
                pass
        return int(self._gateway_config.get("max_upload_mb", 10))

    @property
    def max_upload_bytes(self) -> int:
        """Maximum allowed upload file size in bytes."""
        return self.max_upload_mb * 1024 * 1024

    @property
    def rate_limit(self) -> int:
        """Maximum allowed requests per minute per IP."""
        val = os.getenv("EVOLVIX_VOICE_RATE_LIMIT")
        if val is not None:
            try:
                return int(val)
            except ValueError:
                pass
        return int(self._gateway_config.get("rate_limit", 30))

    @property
    def session_timeout_min(self) -> int:
        """Session inactivity expiration timeout in minutes."""
        val = os.getenv("EVOLVIX_VOICE_SESSION_TIMEOUT_MIN")
        if val is not None:
            try:
                return int(val)
            except ValueError:
                pass
        return int(self._gateway_config.get("session_timeout_min", 30))

    @property
    def default_language(self) -> str:
        """Default language code for speech recognition and synthesis."""
        return os.getenv("EVOLVIX_VOICE_DEFAULT_LANGUAGE") or str(
            self._gateway_config.get("default_language", "en")
        )

    @property
    def wake_word(self) -> str:
        """Configured wake word for voice activation."""
        return os.getenv("EVOLVIX_VOICE_WAKE_WORD") or str(
            self._gateway_config.get("wake_word", "hey evolvix")
        )

    @property
    def default_tts_voice(self) -> str:
        """Default TTS voice ID."""
        return os.getenv("EVOLVIX_VOICE_TTS_VOICE") or str(
            self._gateway_config.get("tts_voice", "af")
        )

    def get_api_key(self) -> Optional[str]:
        """Retrieve configured API key from environment variable or YAML config."""
        env_key = os.getenv("EVOLVIX_VOICE_API_KEY")
        if env_key:
            return env_key
        key = self._gateway_config.get("api_key")
        return str(key) if key else None

    def get_voice_for_language(self, language: Optional[str] = None) -> str:
        """
        Get the configured TTS voice ID for a specific language code.
        
        Falls back to default TTS voice if no language-specific override is found.
        """
        lang = (language or self.default_language).lower().strip()
        languages = self._gateway_config.get("languages", {})
        if isinstance(languages, dict) and lang in languages:
            lang_cfg = languages[lang]
            if isinstance(lang_cfg, dict) and "tts_voice" in lang_cfg:
                return str(lang_cfg["tts_voice"])
        return self.default_tts_voice
