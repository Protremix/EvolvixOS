#!/usr/bin/env python3
"""
EvolvixOS Auth API v8.1 — User registration, OTP verification, JWT sessions.
Runs on port 5022. Uses SQLite for user storage.
OTP is sent via Telegram bot (already running).

v8.1: Removed otp_display from API responses (security fix),
      context managers for all SQLite, WAL mode, strict OTP expiry,
      port consistency, rate limiting.
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
import sys
sys.path.insert(0, '/opt/evolvixos/auth')
from api_keys_system import init_api_keys_table, generate_api_key, validate_api_key, list_user_keys, revoke_key, get_usage_stats
from datetime import datetime, timezone, timedelta
from collections import defaultdict

DB_PATH = "/opt/evolvixos/auth/users.db"
AUTH_DIR = "/opt/evolvixos/auth"
os.makedirs(AUTH_DIR, exist_ok=True)

# Rate limiting
RATE_LIMIT = defaultdict(list)  # ip -> [timestamps]
MAX_REQUESTS = 10  # per 60 seconds per IP
OTP_MAX_ATTEMPTS = 5  # max OTP attempts before lockout

def check_rate_limit(ip):
    now = time.time()
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < 60]
    if len(RATE_LIMIT[ip]) >= MAX_REQUESTS:
        return False
    RATE_LIMIT[ip].append(now)
    # Clean old entries periodically
    if len(RATE_LIMIT) > 10000:
        for k in list(RATE_LIMIT.keys()):
            if now - RATE_LIMIT[k][-1] > 300:
                del RATE_LIMIT[k]
    return True

# Load token from environment or existing secret file
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else ""

# JWT-like token (simplified HMAC signing)
JWT_SECRET = secrets.token_hex(32)
JWT_FILE = os.path.join(AUTH_DIR, ".jwt_secret")
if os.path.exists(JWT_FILE):
    with open(JWT_FILE) as f:
        JWT_SECRET = f.read().strip()
else:
    with open(JWT_FILE, "w") as f:
        f.write(JWT_SECRET)

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    c = conn.cursor()
    # Enable WAL mode for better concurrent access
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
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
            otp_attempts INTEGER DEFAULT 0,
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

def hash_password(password):
    return hashlib.sha256(password.encode() + JWT_SECRET.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"

def generate_token():
    return secrets.token_urlsafe(48)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_otp(to_email, otp_code, display_name=""):
    """Send OTP verification code via Brevo API (HTTPS — no port 25 needed)."""
    import os
    import urllib.request

    BREVO_API_KEY = os.environ.get("BREVO_API_KEY", os.environ.get("BRAVO_API_KEY", ""))
    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
    SENDER_EMAIL = os.environ.get("SMTP_USER", "noreply@evolvixos.com")
    SENDER_NAME = "EvolvixOS"

    html = f"""<html><body style="font-family:Inter,Arial,sans-serif;background:#0a0a0f;color:#fff;padding:40px;margin:0;">
<div style="max-width:480px;margin:0 auto;background:#111113;border:1px solid #1f1f23;border-radius:16px;padding:40px;">
<h1 style="color:#fff;font-size:24px;margin:0 0 8px;">EvolvixOS</h1>
<p style="color:#888;font-size:14px;margin:0 0 24px;">AI Engineering Platform</p>
<p style="color:#ccc;font-size:16px;">Hello {display_name or 'there'},</p>
<p style="color:#ccc;font-size:16px;">Your verification code is:</p>
<div style="background:#0a0a0b;border:1px solid #333;border-radius:12px;padding:20px;text-align:center;margin:20px 0;">
<span style="font-size:32px;font-weight:700;color:#2dd4bf;letter-spacing:8px;">{otp_code}</span>
</div>
<p style="color:#888;font-size:13px;">This code expires in 10 minutes. If you didn\'t create an account, ignore this email.</p>
<p style="color:#555;font-size:12px;margin-top:32px;">— EvolvixOS Team</p>
</div></body></html>"""

    text = f"""EvolvixOS Email Verification

Hello {display_name or 'there'}!

Your verification code is: {otp_code}

This code expires in 10 minutes.

— EvolvixOS Team"""

    payload = json.dumps({
        "sender": {"email": SENDER_EMAIL, "name": SENDER_NAME},
        "to": [{"email": to_email}],
        "subject": f"Your EvolvixOS Verification Code: {otp_code}",
        "htmlContent": html,
        "textContent": text
    }).encode()

    try:
        req = urllib.request.Request(BREVO_API_URL, data=payload, headers={
            "Content-Type": "application/json",
            "api-key": BREVO_API_KEY
        })
        resp = urllib.request.urlopen(req, timeout=15)
        if resp.status in (200, 201):
            print(f"Email OTP sent to {to_email} via Brevo API")
            return True
        else:
            print(f"Brevo API returned {resp.status}")
            return False
    except Exception as e:
        print(f"Email OTP send error (Brevo API): {e}")
        # Fallback to local postfix
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"EvolvixOS <noreply@evolvixos.com>"
            msg["To"] = to_email
            msg["Subject"] = f"Your EvolvixOS Verification Code: {otp_code}"
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP("127.0.0.1", 25, timeout=10) as server:
                server.sendmail("noreply@evolvixos.com", to_email, msg.as_string())
            print(f"Email OTP sent to {to_email} via local postfix (fallback)")
            return True
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            return False


def send_telegram_otp(chat_id, otp_code, display_name=""):
    if not TELEGRAM_TOKEN:
        return False
    try:
        msg = f"🔐 EvolvixOS Verification Code\n\nHello {display_name}!\n\nYour verification code is:\n\n**{otp_code}**\n\nThis code expires in 10 minutes.\n\n— EvolvixOS"
        payload = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(f"{TELEGRAM_API}/sendMessage", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram OTP send error: {e}")
        return False

def get_telegram_chat_id(username):
    try:
        bot_db = "/opt/evolvixos-platform-git/messaging/telegram_bot.db"
        if not os.path.exists(bot_db):
            return None
        with sqlite3.connect(bot_db, timeout=5) as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT chat_id FROM linked_users WHERE username = ?", (username.lstrip('@').lower(),))
                row = c.fetchone()
                return row[0] if row else None
            except Exception:
                return None
    except Exception:
        return None

def is_authorized(handler):
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        cookies = handler.headers.get("Cookie", "")
        token_match = re.search(r'evolvix_token=([^;]+)', cookies)
        if token_match:
            token = token_match.group(1)
        else:
            return None
    else:
        token = auth_header[7:]
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM user_sessions WHERE token = ? AND expires > datetime('now')", (token,))
        row = c.fetchone()
    return row[0] if row else None

def get_user_by_id(user_id):
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        c = conn.cursor()
        c.execute("SELECT id, email, display_name, telegram_username, verified FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
    if row:
        return {"id": row[0], "email": row[1], "display_name": row[2], "telegram_username": row[3], "verified": bool(row[4])}
    return None

class AuthHandler(BaseHTTPRequestHandler):
    def _get_ip(self):
        return self.headers.get("X-Real-IP", self.client_address[0] if self.client_address else "unknown")

    def _send_json(self, code, data, set_cookie_token=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Access-Control-Allow-Credentials", "true")
        if set_cookie_token:
            self.send_header("Set-Cookie", "evolvix_token=" + set_cookie_token + "; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=2592000")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 1048576:  # 1MB max
            return {}
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/auth/health":
            self._send_json(200, {"status": "online", "service": "EvolvixOS Auth v9.1"})
            return
        if self.path == "/auth/me":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            user = get_user_by_id(user_id)
            if not user:
                self._send_json(401, {"error": "Invalid credentials"})
                return
            self._send_json(200, {"user": user})
            return
        # ─── API Keys (GET) ───
        if self.path == "/auth/api-keys":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            keys = list_user_keys(user_id)
            self._send_json(200, {"keys": keys})
            return
        if self.path.startswith("/auth/api-keys/usage"):
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            stats = get_usage_stats(user_id)
            self._send_json(200, {"usage": stats})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        ip = self._get_ip()
        if not check_rate_limit(ip):
            self._send_json(429, {"error": "Too many requests. Please wait a minute."})
            return

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

            otp = generate_otp()
            otp_expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

            try:
                with sqlite3.connect(DB_PATH, timeout=10) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, verified FROM users WHERE email = ?", (email,))
                    existing = c.fetchone()
                    if existing and existing[1]:
                        self._send_json(409, {"error": "Email already registered. Please login."})
                        return

                    if existing and not existing[1]:
                        c.execute("UPDATE users SET password_hash=?, display_name=?, telegram_username=?, otp_code=?, otp_expires=?, otp_attempts=0 WHERE email=?",
                                  (hash_password(password), display_name, telegram_username, otp, otp_expires, email))
                        user_id = existing[0]
                    else:
                        c.execute("INSERT INTO users (email, password_hash, display_name, telegram_username, otp_code, otp_expires) VALUES (?, ?, ?, ?, ?, ?)",
                                  (email, hash_password(password), display_name, telegram_username, otp, otp_expires))
                        user_id = c.lastrowid
                    conn.commit()
            except sqlite3.Error as e:
                self._send_json(500, {"error": "Database error"})
                return

            # Send OTP via email (always) and Telegram (if linked)
            otp_sent_via_email = send_email_otp(email, otp, display_name or email.split("@")[0])

            otp_sent_via_telegram = False
            if telegram_username:
                chat_id = get_telegram_chat_id(telegram_username)
                if chat_id:
                    otp_sent_via_telegram = send_telegram_otp(chat_id, otp, display_name or email)

            self._send_json(200, {
                "ok": True,
                "user_id": user_id,
                "otp_sent_via_email": otp_sent_via_email,
                "otp_sent_via_telegram": otp_sent_via_telegram,
                "message": "Verification code sent to your email." if otp_sent_via_email else ("OTP generated. Check your Telegram." if otp_sent_via_telegram else "OTP generated but email delivery failed. Contact admin.")
            })
            return

        # ─── Verify OTP ───
        if path == "/auth/verify":
            email = body.get("email", "").lower().strip()
            otp = body.get("otp", "").strip()

            if not email or not otp:
                self._send_json(400, {"error": "Email and OTP required"})
                return

            try:
                with sqlite3.connect(DB_PATH, timeout=10) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, otp_code, otp_expires, display_name FROM users WHERE email = ?", (email,))
                    row = c.fetchone()
                    if not row:
                        self._send_json(404, {"error": "Invalid credentials"})
                        return

                    user_id, stored_otp, otp_expires_str, display_name = row

                    attempts_row = c.execute("SELECT otp_attempts FROM users WHERE id = ?", (user_id,)).fetchone()
                    current_attempts = attempts_row[0] if attempts_row else 0
                    if current_attempts >= OTP_MAX_ATTEMPTS:
                        self._send_json(429, {"error": "Too many failed attempts. Register again."})
                        return
                    if not stored_otp or not secrets.compare_digest(str(stored_otp), str(otp)):
                        c.execute("UPDATE users SET otp_attempts = otp_attempts + 1 WHERE id = ?", (user_id,))
                        conn.commit()
                        remaining = OTP_MAX_ATTEMPTS - current_attempts - 1
                        if remaining <= 0:
                            self._send_json(429, {"error": "Account locked. Register again for a new code."})
                        else:
                            self._send_json(400, {"error": "Invalid OTP. " + str(remaining) + " attempt(s) left."})
                        return

                    # FIX: Strict OTP expiry — reject on parse failure instead of allowing
                    try:
                        expires = datetime.fromisoformat(otp_expires_str)
                        if datetime.utcnow() > expires:
                            self._send_json(400, {"error": "OTP expired. Please register again to get a new code."})
                            return
                    except (ValueError, TypeError):
                        self._send_json(400, {"error": "OTP record is corrupted. Please register again."})
                        return

                    token = generate_token()
                    expires_dt = (datetime.utcnow() + timedelta(days=30)).isoformat()

                    c.execute("UPDATE users SET verified=1, otp_code=NULL, otp_expires=NULL, otp_attempts=0 WHERE id=?", (user_id,))
                    c.execute("INSERT INTO user_sessions (user_id, token, expires, ip_address) VALUES (?, ?, ?, ?)",
                              (user_id, token, expires_dt, self._get_ip()))
                    conn.commit()
            except sqlite3.Error as e:
                self._send_json(500, {"error": "Database error"})
                return

            self._send_json(200, {
                "ok": True,
                "token": token,
                "user": {"id": user_id, "email": email, "display_name": display_name or email.split("@")[0]},
                "message": "Account verified! Redirecting to Studio..."
            }, set_cookie_token=token)
            return

        # ─── Login ───
        if path == "/auth/login":
            email = body.get("email", "").lower().strip()
            password = body.get("password", "")

            if not email or not password:
                self._send_json(400, {"error": "Email and password required"})
                return

            try:
                with sqlite3.connect(DB_PATH, timeout=10) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, password_hash, verified, display_name FROM users WHERE email = ?", (email,))
                    row = c.fetchone()
                    if not row:
                        self._send_json(404, {"error": "Invalid credentials"})
                        return

                    user_id, pw_hash, verified, display_name = row
                    if not verify_password(password, pw_hash):
                        self._send_json(401, {"error": "Invalid credentials"})
                        return

                    if not verified:
                        self._send_json(403, {"error": "Account not verified. Please register again to get a new OTP."})
                        return

                    token = generate_token()
                    expires_dt = (datetime.utcnow() + timedelta(days=30)).isoformat()
                    c.execute("INSERT INTO user_sessions (user_id, token, expires, ip_address) VALUES (?, ?, ?, ?)",
                              (user_id, token, expires_dt, self._get_ip()))
                    conn.commit()
            except sqlite3.Error:
                self._send_json(500, {"error": "Database error"})
                return

            self._send_json(200, {
                "ok": True,
                "token": token,
                "user": {"id": user_id, "email": email, "display_name": display_name or email.split("@")[0]}
            }, set_cookie_token=token)
            return

        # ─── Logout ───
        if path == "/auth/logout":
            user_id = is_authorized(self)
            if user_id:
                auth_header = self.headers.get("Authorization", "")
                token = auth_header[7:] if auth_header.startswith("Bearer ") else None
                if token:
                    with sqlite3.connect(DB_PATH, timeout=5) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
                        conn.commit()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Set-Cookie", "evolvix_token=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0"); self.end_headers(); self.wfile.write(json.dumps({"ok": True, "message": "Logged out"}).encode())
            return

        # ─── Resend OTP ───
        if path == "/auth/resend-otp":
            email = body.get("email", "").lower().strip()
            try:
                with sqlite3.connect(DB_PATH, timeout=10) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, telegram_username, display_name FROM users WHERE email = ?", (email,))
                    row = c.fetchone()
                    if not row:
                        self._send_json(404, {"error": "Invalid credentials"})
                        return

                    user_id, tg_username, display_name = row
                    otp = generate_otp()
                    otp_expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
                    c.execute("UPDATE users SET otp_code=?, otp_expires=?, otp_attempts=0 WHERE id=?", (otp, otp_expires, user_id))
                    conn.commit()
            except sqlite3.Error:
                self._send_json(500, {"error": "Database error"})
                return

            otp_sent = False
            if tg_username:
                chat_id = get_telegram_chat_id(tg_username)
                if chat_id:
                    otp_sent = send_telegram_otp(chat_id, otp, display_name or email)

            # FIX: Never return OTP in API response
            self._send_json(200, {
                "ok": True,
                "otp_sent_via_telegram": otp_sent,
                "message": "New OTP sent to your Telegram." if otp_sent else "OTP regenerated. Contact admin to get your code."
            })
            return

        # ─── API Keys (POST) ───
        if path == "/auth/api-keys/generate":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            name = body.get("name", "Default")
            expires_days = body.get("expires_days")
            result = generate_api_key(user_id, name, expires_days)
            self._send_json(201, result)
            return
        if path == "/auth/api-keys/revoke":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            key_id = body.get("key_id", "")
            if revoke_key(user_id, key_id):
                self._send_json(200, {"ok": True, "message": "Key revoked"})
            else:
                self._send_json(404, {"error": "Key not found"})
            return
        self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        print(f"[Auth] {args[0]}")


# Initialize API keys table
init_api_keys_table()

if __name__ == "__main__":
    port = 5022
    print(f"EvolvixOS Auth API v8.1 starting on port {port}")
    server = ThreadingHTTPServer(("127.0.0.1", port), AuthHandler)
    server.serve_forever()
