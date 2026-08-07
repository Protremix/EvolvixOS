"""
Secret Manager — Phase 50 Security Fix

Wraps secret access to prevent secrets from being logged or exposed.
In production, this would connect to HashiCorp Vault, AWS Secrets Manager, etc.
"""

import os
import hashlib
import hmac
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("core.secret_manager")


class SecretManager:
    """Secure secret access wrapper."""

    # Keys that should never be logged
    SENSITIVE_KEYS = {"API_KEY", "SECRET_KEY", "PRIVATE_KEY", "PASSWORD",
                      "TOKEN", "OPENAI_API_KEY", "OPENAI_API_KEY_2",
                      "DATABASE_URL", "JWT_SECRET"}

    def __init__(self):
        self._cache: dict = {}
        self._access_log: list = []

    def get(self, key: str, default: str = "") -> str:
        """Get a secret value. Never logs the value."""
        value = os.environ.get(key, default)
        self._cache[key] = True  # Mark as accessed (don't cache value)
        self._access_log.append({
            "key": key,
            "found": bool(value),
            "masked": self._mask_key(key),
        })
        return value

    def _mask_key(self, key: str) -> str:
        if key in self.SENSITIVE_KEYS:
            return f"***{key[-4:]}"
        return key

    def is_set(self, key: str) -> bool:
        return bool(os.environ.get(key))

    def list_keys(self) -> list[str]:
        """List all environment variable names (not values)."""
        return [k for k in os.environ if not k.startswith("_")]

    def get_access_log(self) -> list[dict]:
        return self._access_log[-50:]  # Last 50 accesses

    def verify_no_secrets_in_response(self, data: dict) -> bool:
        """Check if any secret values appear in a response dict."""
        for key in self.SENSITIVE_KEYS:
            value = os.environ.get(key, "")
            if value and len(value) > 10:
                serialized = str(data)
                if value in serialized:
                    logger.warning("secret_leak_detected", key=key)
                    return False
        return True

    def get_config(self) -> dict:
        return {
            "sensitive_keys": list(self.SENSITIVE_KEYS),
            "total_env_keys": len(self.list_keys()),
            "access_count": len(self._access_log),
            "message": "Secrets are read from environment, never logged, never cached",
        }


_manager: Optional[SecretManager] = None

def get_secret_manager() -> SecretManager:
    global _manager
    if _manager is None:
        _manager = SecretManager()
    return _manager
