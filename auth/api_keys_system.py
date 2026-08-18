#!/usr/bin/env python3
"""
EvolvixOS API Key System
Per-user API keys for external integration.
Users can generate keys to use EvolvixOS in their own agents and platforms.
"""
import sqlite3, secrets, json, hashlib, time
from datetime import datetime

AUTH_DB = "/opt/evolvixos/auth/users.db"

def init_api_keys_table():
    """Create the api_keys table if it doesn't exist"""
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key_id TEXT UNIQUE NOT NULL,
        key_hash TEXT NOT NULL,
        name TEXT DEFAULT 'Default',
        created_date TEXT NOT NULL,
        last_used TEXT,
        expires TEXT,
        is_active INTEGER DEFAULT 1,
        requests_count INTEGER DEFAULT 0,
        rate_limit INTEGER DEFAULT 100,
        allowed_endpoints TEXT DEFAULT 'all',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS api_usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id TEXT NOT NULL,
        endpoint TEXT,
        timestamp TEXT NOT NULL,
        response_code INTEGER,
        tokens_used INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def generate_api_key(user_id, name="Default", expires_days=None):
    """Generate a new API key for a user.
    Returns the full key (only shown once) and the key_id."""
    key_id = secrets.token_hex(8)  # 16 char identifier
    key_secret = secrets.token_hex(24)  # 48 char secret
    full_key = f"evx_{key_id}_{key_secret}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    expires = None
    if expires_days:
        from datetime import timedelta
        expires = (datetime.now() + timedelta(days=expires_days)).isoformat()
    
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO api_keys 
        (user_id, key_id, key_hash, name, created_date, expires, rate_limit)
        VALUES (?, ?, ?, ?, ?, ?, 100)""",
        (user_id, key_id, key_hash, name, datetime.now().isoformat(), expires))
    conn.commit()
    conn.close()
    
    return {
        "key": full_key,
        "key_id": key_id,
        "name": name,
        "expires": expires,
        "message": "Save this key securely. It will not be shown again."
    }

def validate_api_key(full_key):
    """Validate an API key and return the user info.
    Returns (user_info, key_id) or (None, None) if invalid."""
    if not full_key or not full_key.startswith("evx_"):
        return None, None
    
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute("""SELECT ak.id, ak.user_id, ak.key_id, ak.is_active, ak.expires,
                  u.email, u.display_name
                  FROM api_keys ak JOIN users u ON ak.user_id = u.id
                  WHERE ak.key_hash = ?""", (key_hash,))
    row = c.fetchone()
    
    if not row or row[3] != 1:  # not found or inactive
        conn.close()
        return None, None
    
    # Check expiry
    if row[4]:  # has expiry
        try:
            exp = datetime.fromisoformat(row[4])
            if datetime.now() > exp:
                conn.close()
                return None, None
        except Exception:
            pass
    
    # Update last_used and increment request count
    c.execute("""UPDATE api_keys SET last_used = ?, requests_count = requests_count + 1
                 WHERE key_hash = ?""", (datetime.now().isoformat(), key_hash))
    
    # Log usage
    c.execute("""INSERT INTO api_usage_log (key_id, timestamp)
                 VALUES (?, ?)""", (row[2], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return {"id": row[1], "email": row[5], "display_name": row[6]}, row[2]

def list_user_keys(user_id):
    """List all API keys for a user (without the actual key)."""
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute("""SELECT key_id, name, created_date, last_used, is_active,
                 requests_count, rate_limit, expires
                 FROM api_keys WHERE user_id = ? ORDER BY created_date DESC""",
              (user_id,))
    keys = []
    for row in c.fetchall():
        keys.append({
            "key_id": row[0],
            "name": row[1],
            "created": row[2],
            "last_used": row[3],
            "active": bool(row[4]),
            "requests_count": row[5],
            "rate_limit": row[6],
            "expires": row[7]
        })
    conn.close()
    return keys

def revoke_key(user_id, key_id):
    """Revoke an API key."""
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute("UPDATE api_keys SET is_active = 0 WHERE user_id = ? AND key_id = ?",
              (user_id, key_id))
    result = c.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_usage_stats(user_id, key_id=None):
    """Get usage statistics for a user's keys."""
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    if key_id:
        c.execute("""SELECT endpoint, COUNT(*), MAX(timestamp)
                     FROM api_usage_log WHERE key_id = ?
                     GROUP BY endpoint ORDER BY COUNT(*) DESC LIMIT 20""", (key_id,))
    else:
        c.execute("""SELECT ak.key_id, ak.name, COUNT(al.id), MAX(al.timestamp)
                     FROM api_keys ak LEFT JOIN api_usage_log al ON ak.key_id = al.key_id
                     WHERE ak.user_id = ? GROUP BY ak.key_id""", (user_id,))
    stats = c.fetchall()
    conn.close()
    return stats
