"""
Enhanced Rate Limiting — Post-MVP Phase 9

Per-user, per-endpoint rate limiting with configurable limits:
- Uses system settings for limits
- Tracks usage per user and per IP
- Returns rate limit headers
"""

from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger("middleware.rate_limit")


class RateLimitEntry:
    """Tracks rate limit state for a single key."""
    def __init__(self):
        self.count = 0
        self.window_start = datetime.utcnow()

    def is_expired(self, window_seconds: int) -> bool:
        return (datetime.utcnow() - self.window_start).total_seconds() >= window_seconds

    def reset(self):
        self.count = 0
        self.window_start = datetime.utcnow()


class EnhancedRateLimiter:
    """Per-user/per-IP rate limiter with configurable limits."""

    def __init__(self):
        self._limits: dict[str, RateLimitEntry] = {}
        self._lock = threading.Lock()
        self._enabled = True

    def check(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, dict]:
        """
        Check if a request is within rate limits.
        Returns (allowed, headers_dict).
        """
        if not self._enabled:
            return True, {}

        with self._lock:
            entry = self._limits.get(key)
            if not entry or entry.is_expired(window_seconds):
                entry = RateLimitEntry()
                self._limits[key] = entry

            entry.count += 1
            allowed = entry.count <= limit

            remaining = max(0, limit - entry.count)
            reset_at = int((entry.window_start + timedelta(seconds=window_seconds)).timestamp())

            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_at),
            }

            if not allowed:
                logger.warning("rate_limit_exceeded", key=key, count=entry.count, limit=limit)

            return allowed, headers

    def get_user_key(self, request: Request) -> str:
        """Extract user key from request."""
        # Try to get user from auth
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"
        # Fall back to IP
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"

    def cleanup_expired(self, max_age_seconds: int = 3600):
        """Remove expired entries."""
        with self._lock:
            expired = [
                key for key, entry in self._limits.items()
                if entry.is_expired(max_age_seconds)
            ]
            for key in expired:
                del self._limits[key]
            if expired:
                logger.info("rate_limit_cleanup", removed=len(expired))

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                "enabled": self._enabled,
                "tracked_keys": len(self._limits),
                "active_keys": sum(
                    1 for e in self._limits.values()
                    if not e.is_expired(60)
                ),
            }

    def set_enabled(self, enabled: bool):
        self._enabled = enabled


# Singleton
_limiter: Optional[EnhancedRateLimiter] = None


def get_rate_limiter() -> EnhancedRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = EnhancedRateLimiter()
    return _limiter
