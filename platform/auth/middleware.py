"""JWT authentication middleware for platform API."""
import os
import json
import hashlib
import time
import sqlite3
from fastapi import Request, HTTPException

JWT_SECRET = os.environ.get("JWT_SECRET", "evolvixos-platform-secret-2026")
AUTH_DB = "/opt/evolvixos/auth/users.db"

def get_user_from_token(request: Request) -> dict | None:
    """Extract user info from JWT token in Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    try:
        # Simple JWT decode (header.payload.signature)
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        # Decode payload
        import base64
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_bytes)
        
        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None
        
        return {"user_id": payload.get("sub"), "email": payload.get("email"), "role": payload.get("role", "user")}
    except Exception:
        return None

def require_auth(request: Request) -> dict:
    """Require authentication — returns user info or raises 401."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, "Authentication required. Provide Bearer token.")
    return user

def optional_auth(request: Request) -> dict | None:
    """Optional authentication — returns user info or None."""
    return get_user_from_token(request)

def require_admin(request: Request) -> dict:
    """Require admin role."""
    user = require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required.")
    return user
