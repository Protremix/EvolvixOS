"""
Two-Factor Authentication (TOTP) Service — Phase 27

Implements RFC 6238 TOTP for EvolvixOS user accounts.
"""

import hashlib
import hmac
import struct
import time
import base64
import secrets
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
from app.core.logging import get_logger

logger = get_logger("service.2fa")

# TOTP parameters (RFC 6238)
TOTP_INTERVAL = 30  # seconds
TOTP_DIGITS = 6
TOTP_WINDOW = 1  # accept codes from ±1 interval (30s drift tolerance)


@dataclass
class TwoFactorConfig:
    """2FA configuration for a user."""
    user_id: str
    secret: str  # base32-encoded TOTP secret
    enabled: bool = False
    backup_codes: list[str] = field(default_factory=list)
    enabled_at: Optional[str] = None
    last_used: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class TwoFactorAuthService:
    """Manages TOTP-based two-factor authentication."""

    def __init__(self):
        self._configs: dict[str, TwoFactorConfig] = {}
        self._lock = threading.Lock()
        self._used_codes: dict[str, float] = {}  # code -> timestamp (replay prevention)
        self._max_replay_age = 300  # 5 minutes

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret (base32-encoded)."""
        return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")

    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """Generate one-time backup codes."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @staticmethod
    def _totp(secret: str, timestamp: int, interval: int = TOTP_INTERVAL, digits: int = TOTP_DIGITS) -> str:
        """Generate TOTP code for a given timestamp."""
        # Decode base32 secret
        key = base64.b32decode(secret, casefold=True)
        # Calculate counter
        counter = timestamp // interval
        # Pack as big-endian 8 bytes
        msg = struct.pack(">Q", counter)
        # HMAC-SHA1
        h = hmac.new(key, msg, hashlib.sha1).digest()
        # Dynamic truncation (RFC 4226)
        offset = h[-1] & 0x0F
        code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
        return str(code).zfill(digits)

    def verify_code(self, secret: str, code: str) -> bool:
        """Verify a TOTP code against a secret (for setup verification)."""
        expected = self._totp(secret, int(time.time()))
        return hmac.compare_digest(code, expected)

    def get_current_code(self, secret: str) -> str:
        """Get current TOTP code (for testing/display)."""
        return self._totp(secret, int(time.time()))

    def get_otpauth_url(self, secret: str, account: str, issuer: str = "Verdis") -> str:
        """Generate otpauth:// URL for QR code."""
        label = f"{issuer}:{account}"
        return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&digits={TOTP_DIGITS}&period={TOTP_INTERVAL}"

    def enable(self, user_id: str, secret: str, backup_codes: list[str] = None) -> TwoFactorConfig:
        """Enable 2FA for a user after secret verification."""
        with self._lock:
            if backup_codes is None:
                backup_codes = self.generate_backup_codes()
            config = TwoFactorConfig(
                user_id=user_id,
                secret=secret,
                enabled=True,
                backup_codes=backup_codes,
                enabled_at=datetime.utcnow().isoformat(),
            )
            self._configs[user_id] = config
        logger.info("2fa_enabled", user_id=user_id)
        return config

    def disable(self, user_id: str) -> bool:
        """Disable 2FA for a user."""
        with self._lock:
            if user_id in self._configs:
                del self._configs[user_id]
                return True
            return False

    def verify(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code or backup code."""
        with self._lock:
            config = self._configs.get(user_id)
            if not config or not config.enabled:
                return False

            # Check backup codes first
            if code.upper() in config.backup_codes:
                config.backup_codes.remove(code.upper())
                config.last_used = datetime.utcnow().isoformat()
                logger.info("2fa_backup_used", user_id=user_id)
                return True

            # Check TOTP code with window
            now = int(time.time())
            for offset in range(-TOTP_WINDOW, TOTP_WINDOW + 1):
                expected = self._totp(config.secret, now + offset * TOTP_INTERVAL)
                if hmac.compare_digest(code, expected):
                    # Replay prevention
                    code_key = f"{user_id}:{code}:{now // TOTP_INTERVAL}"
                    if code_key in self._used_codes:
                        logger.warning("2fa_replay_attempt", user_id=user_id)
                        return False
                    self._used_codes[code_key] = time.time()
                    self._cleanup_replay()
                    config.last_used = datetime.utcnow().isoformat()
                    return True

            return False

    def _cleanup_replay(self):
        """Clean up expired replay entries."""
        now = time.time()
        expired = [k for k, v in self._used_codes.items() if now - v > self._max_replay_age]
        for k in expired:
            del self._used_codes[k]

    def get_config(self, user_id: str) -> Optional[TwoFactorConfig]:
        return self._configs.get(user_id)

    def is_enabled(self, user_id: str) -> bool:
        config = self._configs.get(user_id)
        return config is not None and config.enabled

    def regenerate_backup_codes(self, user_id: str) -> list[str]:
        """Generate new backup codes (requires existing 2FA)."""
        config = self._configs.get(user_id)
        if not config or not config.enabled:
            return []
        config.backup_codes = self.generate_backup_codes()
        return config.backup_codes


_service: Optional[TwoFactorAuthService] = None

def get_2fa_service() -> TwoFactorAuthService:
    global _service
    if _service is None:
        _service = TwoFactorAuthService()
    return _service
