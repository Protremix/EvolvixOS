"""
Auth Rate Limiting — Phase 50 Security Fix

Rate limiting specifically for authentication endpoints to prevent brute force.
Stricter than general rate limiting: 5 attempts per minute per IP, 10 per hour per address.
"""

import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("core.auth_rate_limit")


class AuthRateLimiter:
    """Rate limiter for authentication endpoints."""

    def __init__(self):
        self._ip_attempts: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._address_attempts: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._lock = threading.Lock()
        self.ip_limit_per_minute = 5
        self.address_limit_per_hour = 10
        self.lockout_duration = 900  # 15 minutes

    def can_attempt(self, ip_address: str, address: str = "") -> tuple[bool, str]:
        """Check if an auth attempt is allowed."""
        now = datetime.utcnow()
        with self._lock:
            # Check IP rate (per minute)
            ip_window = timedelta(minutes=1)
            ip_recent = [t for t in self._ip_attempts[ip_address] if now - t < ip_window]
            self._ip_attempts[ip_address] = deque(ip_recent, maxlen=100)

            if len(ip_recent) >= self.ip_limit_per_minute:
                remaining = 60 - int((now - ip_recent[0]).total_seconds())
                return False, f"Too many attempts from this IP. Try again in {remaining}s"

            # Check address rate (per hour)
            if address:
                addr_window = timedelta(hours=1)
                addr_recent = [t for t in self._address_attempts[address] if now - t < addr_window]
                self._address_attempts[address] = deque(addr_recent, maxlen=100)

                if len(addr_recent) >= self.address_limit_per_hour:
                    return False, "Too many attempts for this address. Try again later"

            return True, ""

    def record_attempt(self, ip_address: str, address: str = ""):
        """Record an auth attempt."""
        now = datetime.utcnow()
        with self._lock:
            self._ip_attempts[ip_address].append(now)
            if address:
                self._address_attempts[address].append(now)

    def is_locked(self, ip_address: str) -> bool:
        """Check if an IP is locked out."""
        now = datetime.utcnow()
        with self._lock:
            ip_recent = [t for t in self._ip_attempts[ip_address] if now - t < timedelta(seconds=self.lockout_duration)]
            return len(ip_recent) >= self.ip_limit_per_minute * 3  # 15+ attempts = lockout

    def get_stats(self) -> dict:
        return {
            "tracked_ips": len(self._ip_attempts),
            "tracked_addresses": len(self._address_attempts),
            "ip_limit_per_minute": self.ip_limit_per_minute,
            "address_limit_per_hour": self.address_limit_per_hour,
            "lockout_duration": self.lockout_duration,
        }

    def reset(self):
        with self._lock:
            self._ip_attempts.clear()
            self._address_attempts.clear()


_limiter: Optional[AuthRateLimiter] = None

def get_auth_rate_limiter() -> AuthRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = AuthRateLimiter()
    return _limiter
