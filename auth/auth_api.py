#!/usr/bin/env python3
"""
EvolvixOS Auth API — User registration, OTP verification, JWT sessions.
Runs on port 5020. Uses SQLite for user storage.
OTP is sent via Telegram bot (already running).
"""

import json
import os
import re
import secrets
import sqlite3
import time
import hashlib
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

# ─── Config ───
DB_PATH = "/opt/evolvixos/auth/users.db"
AUTH_DIR = "/opt/evolvixos/auth"
os.makedirs(AUTH_DIR, exist_ok=True)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8663115714:AAHJ399PFcRc4ugNOvTew4_ucky8LFAzpt0")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# JWT-like token (simplified HMAC signing)
JWT_SECRET = secrets.token_hex(32)
JWT_FILE = os.path.join(AUTH_DIR, ".jwt_secret")
if os.path.exists(JWT_FILE):
    with open(JWT_FILE) as f:
        JWT_SECRET = f.read().strip()
else:
    with open(JWT_FILE, "w") as f:
        f.write(JWT_SECRET)

# ─── Database Setup ───
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            telegram_chat_id TEXT,
            telegram_username TEXT,
            created_date TEXT DEFAULT (datetime('now')),
            verified INTEGER DEFAULT 0,
            otp_code TEXT,
            otp_expires TEXT,
            session_token TEXT,
            session_expires TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_date TEXT DEFAULT (datetime('now')),
            expires TEXT NOT NULL,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─── Helpers ───
def hash_password(password):
    return hashlib.sha256(password.encode() + JWT_SECRET.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"

def generate_token():
    return secrets.token_urlsafe(48)

def send_telegram_otp(chat_id, otp_code, display_name=""):
    """Send OTP via Telegram bot."""
    try:
        msg = f"🔐 EvolvixOS Verification Code\n\nHello {display_name}!\n\nYour verification code is:\n\n**{otp_code}**\n\nThis code expires in 10 minutes.\n\n— EvolvixOS"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(
            f"{TELEGRAM_API}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram OTP send error: {e}")
        return False

def get_telegram_chat_id(username):
    """Look up Telegram chat_id by username from the bot's database."""
    try:
        bot_db = "/opt/evolvixos-platform-git/messaging/telegram_bot.db"
        if not os.path.exists(bot_db):
            # Try finding linked users in the bot's storage
            return None
        conn = sqlite3.connect(bot_db)
        c = conn.cursor()
        # Try common table structures
        try:
            c.execute("SELECT chat_id FROM linked_users WHERE username = ?", (username.lstrip('@').lower(),))
            row = c.fetchone()
            conn.close()
            return row[0] if row else None
        except:
            conn.close()
            return None
    except:
        return None

def is_authorized(handler):
    """Check if request has valid Bearer token. Returns user_id or None."""
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        # Also check cookie
        cookies = handler.headers.get("Cookie", "")
        token_match = re.search(r'evolvix_token=([^;]+)', cookies)
        if token_match:
            token = token_match.group(1)
        else:
            return None
    else:
        token = auth_header[7:]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT user_id FROM user_sessions 
        WHERE token = ? AND expires > datetime('now')
    """, (token,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, display_name, telegram_username, verified FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "display_name": row[2], "telegram_username": row[3], "verified": bool(row[4])}
    return None

# ─── API Handler ───
class AuthHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/auth/health":
            self._send_json(200, {"status": "online", "service": "EvolvixOS Auth"})
            return

        if self.path == "/auth/me":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            user = get_user_by_id(user_id)
            if not user:
                self._send_json(401, {"error": "User not found"})
                return
            self._send_json(200, {"user": user})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        body = self._read_body()
        path = self.path.rstrip("/")

        # ─── Register ───
        if path == "/auth/register":
            email = body.get("email", "").lower().strip()
            password = body.get("password", "")
            display_name = body.get("display_name", "")
            telegram_username = body.get("telegram_username", "").lstrip("@").lower()

            if not email or not password:
                self._send_json(400, {"error": "Email and password required"})
                return
            if len(password) < 6:
                self._send_json(400, {"error": "Password must be at least 6 characters"})
                return
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                self._send_json(400, {"error": "Invalid email format"})
                return

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Check if already exists
            c.execute("SELECT id, verified FROM users WHERE email = ?", (email,))
            existing = c.fetchone()
            if existing and existing[1]:
                self._send_json(409, {"error": "Email already registered. Please login."})
                conn.close()
                return

            # Create or update
            otp = generate_otp()
            otp_expires = datetime.now(timezone.utc).isoformat()
            import datetime as dt
            otp_expires = (datetime.utcnow().replace(tzinfo=None) + dt.timedelta(minutes=10)).isoformat()

            if existing and not existing[1]:
                # Update existing unverified user
                c.execute("""
                    UPDATE users SET password_hash=?, display_name=?, telegram_username=?, otp_code=?, otp_expires=?
                    WHERE email=?
                """, (hash_password(password), display_name, telegram_username, otp, otp_expires, email))
                user_id = existing[0]
            else:
                c.execute("""
                    INSERT INTO users (email, password_hash, display_name, telegram_username, otp_code, otp_expires)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (email, hash_password(password), display_name, telegram_username, otp, otp_expires))
                user_id = c.lastrowid

            conn.commit()

            # Try to send OTP via Telegram
            otp_sent_via_telegram = False
            otp_display = None

            if telegram_username:
                chat_id = get_telegram_chat_id(telegram_username)
                if chat_id:
                    otp_sent_via_telegram = send_telegram_otp(chat_id, otp, display_name or email)

            if not otp_sent_via_telegram:
                # No Telegram linked — return OTP for display (demo mode)
                otp_display = otp

            conn.close()

            self._send_json(200, {
                "ok": True,
                "user_id": user_id,
                "otp_sent_via_telegram": otp_sent_via_telegram,
                "otp_display": otp_display,  # Only set if Telegram delivery failed
                "message": "OTP generated. Check Telegram or the displayed code."
            })
            return

        # ─── Verify OTP ───
        if path == "/auth/verify":
            email = body.get("email", "").lower().strip()
            otp = body.get("otp", "").strip()

            if not email or not otp:
                self._send_json(400, {"error": "Email and OTP required"})
                return

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, otp_code, otp_expires, display_name FROM users WHERE email = ?", (email,))
            row = c.fetchone()
            if not row:
                self._send_json(404, {"error": "User not found. Please register first."})
                conn.close()
                return

            user_id, stored_otp, otp_expires_str, display_name = row

            # Check OTP
            if stored_otp != otp:
                self._send_json(400, {"error": "Invalid OTP code"})
                conn.close()
                return

            # Check expiry
            try:
                expires = datetime.fromisoformat(otp_expires_str)
                if datetime.utcnow() > expires:
                    self._send_json(400, {"error": "OTP expired. Please register again."})
                    conn.close()
                    return
            except:
                pass  # If we can't parse, allow it

            # Mark verified, create session
            token = generate_token()
            import datetime as dt
            expires = (datetime.utcnow() + dt.timedelta(days=30)).isoformat()

            c.execute("UPDATE users SET verified=1, otp_code=NULL, otp_expires=NULL WHERE id=?", (user_id,))
            c.execute("""
                INSERT INTO user_sessions (user_id, token, expires)
                VALUES (?, ?, ?)
            """, (user_id, token, expires))
            conn.commit()
            conn.close()

            self._send_json(200, {
                "ok": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "display_name": display_name or email.split("@")[0]
                },
                "message": "Account verified! Redirecting to Studio..."
            })
            return

        # ─── Login (for returning verified users) ───
        if path == "/auth/login":
            email = body.get("email", "").lower().strip()
            password = body.get("password", "")

            if not email or not password:
                self._send_json(400, {"error": "Email and password required"})
                return

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, password_hash, verified, display_name FROM users WHERE email = ?", (email,))
            row = c.fetchone()
            if not row:
                self._send_json(404, {"error": "No account found. Please register first."})
                conn.close()
                return

            user_id, pw_hash, verified, display_name = row
            if not verify_password(password, pw_hash):
                self._send_json(401, {"error": "Invalid password"})
                conn.close()
                return

            if not verified:
                self._send_json(403, {"error": "Account not verified. Please register again to get a new OTP."})
                conn.close()
                return

            # Create session
            token = generate_token()
            import datetime as dt
            expires = (datetime.utcnow() + dt.timedelta(days=30)).isoformat()
            c.execute("""
                INSERT INTO user_sessions (user_id, token, expires)
                VALUES (?, ?, ?)
            """, (user_id, token, expires))
            conn.commit()
            conn.close()

            self._send_json(200, {
                "ok": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "display_name": display_name or email.split("@")[0]
                }
            })
            return

        # ─── Logout ───
        if path == "/auth/logout":
            user_id = is_authorized(self)
            if user_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                # Delete current session
                auth_header = self.headers.get("Authorization", "")
                token = auth_header[7:] if auth_header.startswith("Bearer ") else None
                if token:
                    c.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
                conn.commit()
                conn.close()
            self._send_json(200, {"ok": True, "message": "Logged out"})
            return

        # ─── Resend OTP ───
        if path == "/auth/resend-otp":
            email = body.get("email", "").lower().strip()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, telegram_username, display_name FROM users WHERE email = ?", (email,))
            row = c.fetchone()
            if not row:
                self._send_json(404, {"error": "User not found"})
                conn.close()
                return

            user_id, tg_username, display_name = row
            otp = generate_otp()
            import datetime as dt
            otp_expires = (datetime.utcnow() + dt.timedelta(minutes=10)).isoformat()
            c.execute("UPDATE users SET otp_code=?, otp_expires=? WHERE id=?", (otp, otp_expires, user_id))
            conn.commit()

            otp_sent_via_telegram = False
            otp_display = None
            if tg_username:
                chat_id = get_telegram_chat_id(tg_username)
                if chat_id:
                    otp_sent_via_telegram = send_telegram_otp(chat_id, otp, display_name or email)
            if not otp_sent_via_telegram:
                otp_display = otp

            conn.close()
            self._send_json(200, {
                "ok": True,
                "otp_sent_via_telegram": otp_sent_via_telegram,
                "otp_display": otp_display
            })
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        print(f"[Auth] {args[0]}")


if __name__ == "__main__":
    port = 5022
    print(f"EvolvixOS Auth API starting on port 5021")
    server = ThreadingHTTPServer(("0.0.0.0", port), AuthHandler)
    server.serve_forever()
