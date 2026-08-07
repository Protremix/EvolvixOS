"""
JWT Configuration — Phase 50 Security Fix

Shorter access token expiry (1 hour) with refresh token (7 days).
Previously: 7-day access token (too long).
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

ACCESS_TOKEN_EXPIRE_HOURS = 1  # Was 168 (7 days)
REFRESH_TOKEN_EXPIRE_DAYS = 7
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_HOURS * 3600

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


def get_access_token_expiry() -> timedelta:
    return timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

def get_refresh_token_expiry() -> timedelta:
    return timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

def get_token_config() -> dict:
    return {
        "access_token_expiry_hours": ACCESS_TOKEN_EXPIRE_HOURS,
        "refresh_token_expiry_days": REFRESH_TOKEN_EXPIRE_DAYS,
        "algorithm": "HS256",
        "previous_expiry_hours": 168,
        "improvement": f"Reduced from 168h to {ACCESS_TOKEN_EXPIRE_HOURS}h with {REFRESH_TOKEN_EXPIRE_DAYS}d refresh",
    }
