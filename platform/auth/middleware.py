"""JWT + session token authentication middleware for platform API."""
import os
import json
import hashlib
import time
import sqlite3
from datetime import datetime
from fastapi import Request, HTTPException

JWT_SECRET = os.environ.get("JWT_SECRET", "evolvixos-platform-secret-2026")
AUTH_DB = "/opt/evolvixos/auth/users.db"

def get_user_from_token(request: Request) -> dict | None:
    """Extract user info from JWT or session token in Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    
    # Try JWT format first (3 parts)
    parts = token.split(".")
    if len(parts) == 3:
        try:
            import base64
            payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
            payload = json.loads(payload_bytes)
            if payload.get("exp", 0) < time.time():
                return None
            return {"user_id": payload.get("sub"), "email": payload.get("email"), "role": payload.get("role", "user")}
        except Exception:
            pass
    
    # Fallback: session token lookup in SQLite
    try:
        conn = sqlite3.connect(AUTH_DB, timeout=3)
        c = conn.cursor()
        # Check user_sessions table — don't filter by expires in SQL (format mismatch)
        c.execute("SELECT user_id, expires FROM user_sessions WHERE token = ?", (token,))
        row = c.fetchone()
        if row:
            user_id, expires_str = row
            # Check expiry in Python (handles ISO format)
            try:
                expires_dt = datetime.fromisoformat(expires_str.replace("Z", ""))
                if expires_dt.timestamp() > time.time():
                    c.execute("SELECT email, display_name FROM users WHERE id = ?", (user_id,))
                    user_row = c.fetchone()
                    conn.close()
                    if user_row:
                        return {"user_id": str(user_id), "email": user_row[0], "role": "user"}
            except:
                # If we can't parse expiry, let it through
                c.execute("SELECT email, display_name FROM users WHERE id = ?", (user_id,))
                user_row = c.fetchone()
                conn.close()
                if user_row:
                    return {"user_id": str(user_id), "email": user_row[0], "role": "user"}
        
        conn.close()
    except Exception:
        pass
    
    return None

def require_auth(request: Request) -> dict:
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, "Authentication required. Provide Bearer token.")
    return user

def optional_auth(request: Request) -> dict | None:
    return get_user_from_token(request)

def require_admin(request: Request) -> dict:
    user = get_user_from_token(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(403, "Admin access required.")
    return user
