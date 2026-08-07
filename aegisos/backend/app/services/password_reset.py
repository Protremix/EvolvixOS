"""
Password Reset Service for EvolvixOS.
Uses Redis for shared state across multiple worker processes.
"""

import time
import json
import secrets
import logging
import hashlib
import hmac
from typing import Optional

import redis

logger = logging.getLogger("evolvixos")
_redis = redis.from_url("redis://redis:6379/0", decode_responses=True)

RESET_PREFIX = "pw_reset:"
LOCKOUT_PREFIX = "lockout:"
ATTEMPTS_PREFIX = "attempts:"

RESET_TTL = 3600  # 1 hour
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes


import os

_SECRET_SALT = os.environ.get("SECRET_KEY", "evolvixos-default-salt-2026")

def _hash_token(token: str) -> str:
    return hmac.new(_SECRET_SALT.encode(), token.encode(), hashlib.sha256).hexdigest()


class PasswordResetService:
    RESET_TOKEN_TTL = RESET_TTL
    MAX_LOGIN_ATTEMPTS = MAX_LOGIN_ATTEMPTS
    LOCKOUT_DURATION = LOCKOUT_DURATION

    def request_reset(self, email: str) -> dict:
        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        key = f"{RESET_PREFIX}{token_hash}"

        data = json.dumps({
            "email": email,
            "expires_at": int(time.time()) + RESET_TTL,
            "used": False,
            "created_at": int(time.time()),
        })
        _redis.setex(key, RESET_TTL + 60, data)

        logger.info(f"password_reset_requested: {email}")
        return {
            "token": token,
            "expires_in_seconds": RESET_TTL,
            "message": "Password reset token generated. Use it within 1 hour.",
        }

    def verify_token(self, token: str) -> dict:
        token_hash = _hash_token(token)
        key = f"{RESET_PREFIX}{token_hash}"
        raw = _redis.get(key)

        if not raw:
            return {"valid": False, "reason": "Token not found"}

        data = json.loads(raw)
        if data.get("used"):
            return {"valid": False, "reason": "Token already used"}
        if int(time.time()) > data.get("expires_at", 0):
            return {"valid": False, "reason": "Token expired"}

        return {"valid": True, "email": data["email"], "expires_at": data["expires_at"]}

    def invalidate_token(self, token: str):
        token_hash = _hash_token(token)
        key = f"{RESET_PREFIX}{token_hash}"
        raw = _redis.get(key)
        if raw:
            data = json.loads(raw)
            data["used"] = True
            _redis.setex(key, 60, json.dumps(data))

    def reset_password(self, token: str) -> dict:
        verification = self.verify_token(token)
        if not verification["valid"]:
            return {"success": False, "reason": verification["reason"]}

        self.invalidate_token(token)

        email = verification["email"]
        _redis.delete(f"{ATTEMPTS_PREFIX}{email}")
        _redis.delete(f"{LOCKOUT_PREFIX}{email}")
        logger.info(f"password_reset_completed: {email}")
        return {"success": True, "email": email, "message": "Password reset successful."}

    def record_login_attempt(self, email: str, success: bool) -> dict:
        if success:
            _redis.delete(f"{ATTEMPTS_PREFIX}{email}")
            _redis.delete(f"{LOCKOUT_PREFIX}{email}")
            return {"locked": False, "attempts_remaining": MAX_LOGIN_ATTEMPTS}

        now = int(time.time())

        if self.is_locked(email):
            ttl = _redis.ttl(f"{LOCKOUT_PREFIX}{email}")
            return {"locked": True, "lockout_remaining_seconds": max(ttl, 0)}

        attempts_key = f"{ATTEMPTS_PREFIX}{email}"
        attempts_raw = _redis.get(attempts_key)

        if attempts_raw:
            attempts_list = json.loads(attempts_raw)
        else:
            attempts_list = []

        attempts_list = [ts for ts in attempts_list if now - ts < LOCKOUT_DURATION]
        attempts_list.append(now)
        _redis.setex(attempts_key, LOCKOUT_DURATION, json.dumps(attempts_list))

        count = len(attempts_list)
        remaining = MAX_LOGIN_ATTEMPTS - count

        if count >= MAX_LOGIN_ATTEMPTS:
            _redis.setex(f"{LOCKOUT_PREFIX}{email}", LOCKOUT_DURATION, str(now))
            logger.warning(f"account_locked: {email} after {count} failed attempts")
            return {
                "locked": True,
                "lockout_remaining_seconds": LOCKOUT_DURATION,
                "reason": f"Account locked after {MAX_LOGIN_ATTEMPTS} failed attempts",
            }

        return {"locked": False, "attempts_remaining": remaining}

    def is_locked(self, email: str) -> bool:
        key = f"{LOCKOUT_PREFIX}{email}"
        val = _redis.get(key)
        if not val:
            return False
        if _redis.ttl(key) <= 0:
            _redis.delete(key)
            return False
        return True

    def cleanup_expired_tokens(self) -> int:
        # Redis handles expiry automatically via TTL
        count = 0
        for key in _redis.scan_iter(f"{RESET_PREFIX}*"):
            raw = _redis.get(key)
            if raw:
                data = json.loads(raw)
                if int(time.time()) > data.get("expires_at", 0):
                    _redis.delete(key)
                    count += 1
        return count


password_reset = PasswordResetService()
