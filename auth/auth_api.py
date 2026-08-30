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

# ─── Billing & Credits ───
MODEL_CREDIT_COST = {"free": 1, "cheap": 2, "standard": 5, "premium": 10, "ultra": 20}

def get_model_tier(model_id):
    model_lower = model_id.lower()
    ultra = ["gemini-3.1-pro-preview", "claude-opus"]
    premium = ["glm-5.2", "glm-5.3", "claude-sonnet-5", "gemini-3.1-pro", "kimi-k2.7", "nemotron-3-ultra"]
    standard = ["glm-5", "kimi-k2", "qwen2.5"]
    cheap = ["gpt-oss-20b", "gpt-oss-120b", "deepseek-v4-flash", "nemotron-3-super"]
    for m in ultra:
        if m in model_lower: return "ultra"
    for m in premium:
        if m in model_lower and ":free" not in model_lower: return "premium"
    for m in standard:
        if m in model_lower and ":free" not in model_lower and "5.2" not in model_lower: return "standard"
    for m in cheap:
        if m in model_lower: return "cheap"
    if ":free" in model_lower: return "free"
    return "standard"

def deduct_credits(user_id, model_id, tokens_in=0, tokens_out=0):
    tier = get_model_tier(model_id)
    cost = MODEL_CREDIT_COST.get(tier, 5)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, credits_remaining FROM subscriptions WHERE user_id = ? AND status = ?", (user_id, "active"))
        row = c.fetchone()
        if not row:
            return {"ok": False, "error": "No active subscription"}
        sub_id, remaining = row
        if remaining < cost:
            return {"ok": False, "error": "Insufficient credits", "remaining": remaining, "cost": cost}
        new_balance = remaining - cost
        c.execute("UPDATE subscriptions SET credits_remaining = ?, credits_used = credits_used + ? WHERE id = ?", (new_balance, cost, sub_id))
        c.execute("INSERT INTO credit_transactions (user_id, amount, type, description, model_used, tokens_in, tokens_out, balance_after, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, cost, "debit", "API call: " + model_id, model_id, tokens_in, tokens_out, new_balance, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    return {"ok": True, "cost": cost, "remaining": new_balance, "tier": tier}

def get_user_subscription(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT s.id, s.credits_remaining, s.credits_used, s.current_period_end, p.name, p.price_monthly, p.credits_monthly, p.max_agents, p.max_entities, p.max_functions, p.max_workflows, p.allowed_models, p.features FROM subscriptions s JOIN plans p ON s.plan_id = p.id WHERE s.user_id = ? AND s.status = ?", (user_id, "active"))
        row = c.fetchone()
        if not row: return None
        return {
            "subscription_id": row[0], "credits_remaining": row[1], "credits_used": row[2],
            "period_end": row[3], "plan_name": row[4], "price": row[5],
            "credits_monthly": row[6], "max_agents": row[7], "max_entities": row[8],
            "max_functions": row[9], "max_workflows": row[10],
            "allowed_models": json.loads(row[11]) if row[11] else [],
            "features": json.loads(row[12]) if row[12] else []
        }

def check_resource_limit(user_id, resource_type):
    limits_map = {"agent": "max_agents", "entity": "max_entities", "function": "max_functions", "workflow": "max_workflows"}
    limit_col = limits_map.get(resource_type)
    if not limit_col: return {"ok": True}
    sub = get_user_subscription(user_id)
    if not sub: return {"ok": False, "error": "No active subscription"}
    limit = sub.get(limit_col, 0)
    if limit >= 999: return {"ok": True}
    import urllib.request
    try:
        url_map = {"agent": "agents", "entity": "entities", "function": "functions", "workflow": "workflows"}
        resp = urllib.request.urlopen("http://127.0.0.1:8080/api/" + url_map.get(resource_type, ""))
        count = len(json.loads(resp.read()).get(url_map.get(resource_type, []), []))
    except: count = 0
    if count >= limit:
        return {"ok": False, "error": "Limit reached: " + str(limit) + " " + resource_type + "s on " + sub["plan_name"] + " plan. Upgrade to create more."}
    return {"ok": True, "current": count, "limit": limit}


import hmac
import hashlib
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

# Stripe product/price IDs (created via Stripe dashboard or API)
STRIPE_PRICES = {
    "Starter_monthly": None,  # price_xxx — set after creating in Stripe
    "Starter_yearly": None,
    "Pro_monthly": None,
    "Pro_yearly": None,
    "Team_monthly": None,
    "Team_yearly": None,
    "credits_1000": None,
    "credits_5000": None,
    "credits_15000": None,
    "credits_50000": None,
}

# ── Paddle Billing configuration ──────────────────────────────────────────────
PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET", "")
PADDLE_API_BASE = os.environ.get("PADDLE_API_BASE", "https://api.paddle.com")
# Paddle's documented variance tolerance is 5s. Keep NTP synced or raise this.
PADDLE_WEBHOOK_TOLERANCE = int(os.environ.get("PADDLE_WEBHOOK_TOLERANCE", "5"))

def verify_paddle_signature(raw_body, signature_header, secret=None, tolerance=None):
    """Verify a Paddle Billing webhook.

    Header format: ts=<unix>;h1=<hex hmac-sha256>
    Signed payload: b"<ts>:" + raw_body   (raw bytes — never re-serialized JSON)
    Returns (ok: bool, reason: str).
    """
    secret = PADDLE_WEBHOOK_SECRET if secret is None else secret
    tolerance = PADDLE_WEBHOOK_TOLERANCE if tolerance is None else tolerance
    if not secret:
        return False, "no_secret_configured"
    if not signature_header or raw_body is None:
        return False, "missing_signature_or_body"

    parts = {}
    for item in signature_header.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            parts[k.strip()] = v.strip()
    ts_str, h1 = parts.get("ts"), parts.get("h1")
    if not ts_str or not h1:
        return False, "malformed_header"

    try:
        ts = int(ts_str)
    except (TypeError, ValueError):
        return False, "bad_timestamp"
    if abs(time.time() - ts) > tolerance:
        return False, "timestamp_out_of_tolerance"

    expected = hmac.new(secret.encode("utf-8"),
                        ts_str.encode("utf-8") + b":" + raw_body,
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, h1):
        return False, "signature_mismatch"
    return True, "ok"

def paddle_event_to_fulfilment(event):
    """Map a verified Paddle event onto apply_payment_event kwargs, or None to ignore.

    Paddle carries checkout metadata in custom_data (Stripe's metadata equivalent).
    Expected custom_data: {user_id, type: subscription|credits, plan, cycle, credits}
    """
    event_type = event.get("event_type") or ""
    data = event.get("data", {}) or {}
    custom = data.get("custom_data") or {}
    try:
        user_id = int(custom.get("user_id") or 0)
    except (TypeError, ValueError):
        user_id = 0

    if event_type == "transaction.completed":
        kind = custom.get("type")
        if kind not in ("subscription", "credits"):
            return None
        return {"kind": kind, "user_id": user_id, "charge_id": data.get("id"),
                "plan": custom.get("plan", "Free"), "cycle": custom.get("cycle", "monthly"),
                "credits": custom.get("credits", 0), "provider": "paddle"}
    if event_type in ("subscription.canceled", "subscription.past_due"):
        return {"kind": "cancel", "user_id": user_id, "provider": "paddle"}
    return None

# ── Provider-neutral payment fulfilment ───────────────────────────────────────
# Any payment provider normalizes its webhook into these calls via an adapter.
# calls. Nothing below is provider-specific — adapters do the translating.

PAYMENT_PROVIDER = os.environ.get("PAYMENT_PROVIDER", "stripe").lower()

def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def mark_payment_paid(charge_id):
    """Flag a payment row as paid by its provider charge/session id."""
    if not charge_id:
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE payments SET status = 'paid' WHERE provider_charge_id = ?", (charge_id,))
        conn.commit()

def fulfill_subscription(user_id, plan_name, cycle="monthly"):
    """Activate or upgrade a user's subscription and reset their credit balance."""
    if not user_id:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, credits_monthly FROM plans WHERE name = ?", (plan_name,))
        plan = c.fetchone()
        if not plan:
            return False
        plan_id, credits = plan
        now = _now()
        days = 365 if cycle == "yearly" else 30
        period_end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + days * 86400))
        c.execute("SELECT id FROM subscriptions WHERE user_id = ? AND status = ?", (user_id, "active"))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE subscriptions SET plan_id = ?, billing_cycle = ?, credits_remaining = ?, "
                      "current_period_start = ?, current_period_end = ?, updated_date = ? WHERE id = ?",
                      (plan_id, cycle, credits, now, period_end, now, existing[0]))
        else:
            c.execute("INSERT INTO subscriptions (user_id, plan_id, status, billing_cycle, credits_remaining, "
                      "credits_used, current_period_start, current_period_end, created_date, updated_date) "
                      "VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)",
                      (user_id, plan_id, "active", cycle, credits, now, period_end, now, now))
        conn.commit()
    return True

def fulfill_credits(user_id, credits_amount, provider=None):
    """Add purchased credits to a user's active subscription."""
    credits_amount = int(credits_amount or 0)
    if not (user_id and credits_amount):
        return False
    provider = provider or PAYMENT_PROVIDER
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, credits_remaining FROM subscriptions WHERE user_id = ? AND status = ?", (user_id, "active"))
        row = c.fetchone()
        if not row:
            return False
        c.execute("UPDATE subscriptions SET credits_remaining = ? WHERE id = ?", (row[1] + credits_amount, row[0]))
        c.execute("INSERT INTO credit_transactions (user_id, amount, type, description, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (user_id, credits_amount, "credit",
                   "Purchased " + str(credits_amount) + " credits via " + str(provider).title(), _now()))
        conn.commit()
    return True

def downgrade_to_free(user_id):
    """Drop a user back to the Free plan (subscription cancelled/expired)."""
    if not user_id:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        free = c.execute("SELECT id FROM plans WHERE name = 'Free'").fetchone()
        if not free:
            return False
        c.execute("UPDATE subscriptions SET plan_id = ?, credits_remaining = 100, updated_date = ? "
                  "WHERE user_id = ? AND status = ?", (free[0], _now(), user_id, "active"))
        conn.commit()
    return True

def apply_payment_event(kind, user_id, charge_id=None, plan=None, cycle="monthly",
                        credits=0, provider=None):
    """Single entry point every provider adapter calls after verifying a webhook."""
    mark_payment_paid(charge_id)
    if kind == "subscription":
        return fulfill_subscription(user_id, plan or "Free", cycle)
    if kind == "credits":
        return fulfill_credits(user_id, credits, provider)
    if kind == "cancel":
        return downgrade_to_free(user_id)
    return False

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
    SENDER_EMAIL = os.environ.get("SMTP_USER", "info@protremix.com")
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
        if self.path == "/auth/usage":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT count(*) FROM api_usage_log WHERE key_id IN (SELECT key_id FROM api_keys WHERE user_id = ?)", (user_id,))
                api_calls = c.fetchone()[0]
                c.execute("SELECT count(*) FROM api_keys WHERE user_id = ? AND is_active = 1", (user_id,))
                api_keys_count = c.fetchone()[0]
                c.execute("SELECT count(*) FROM user_sessions WHERE user_id = ?", (user_id,))
                sessions_count = c.fetchone()[0]
                c.execute("SELECT created_date FROM users WHERE id = ?", (user_id,))
                row = c.fetchone()
                created_date = row[0] if row else ""
            import urllib.request
            entity_count = 0
            agent_count = 0
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:8080/api/entities")
                entity_count = len(json.loads(resp.read()).get("entities", []))
            except: pass
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:8080/api/agents")
                agent_count = len(json.loads(resp.read()).get("agents", []))
            except: pass
            self._send_json(200, {
                "api_calls": api_calls, "api_keys": api_keys_count,
                "active_sessions": sessions_count, "entities": entity_count,
                "agents": agent_count, "member_since": created_date,
                "plan": "Community", "plan_limits": {"entities": "Unlimited", "agents": "Unlimited", "api_calls": "Unlimited"}
            })
            return
        if self.path == "/auth/sessions":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, token, created_date, expires, ip_address FROM user_sessions WHERE user_id = ? ORDER BY created_date DESC", (user_id,))
                sessions = [{"id": r[0], "created": r[2], "expires": r[3], "ip": r[4] or "unknown"} for r in c.fetchall()]
            self._send_json(200, {"sessions": sessions})
            return
        if self.path == "/auth/plans":
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, name, price_monthly, price_yearly, credits_monthly, max_agents, max_entities, max_functions, max_workflows, allowed_models, features, sort_order FROM plans WHERE is_active = 1 ORDER BY sort_order")
                plans = []
                for r in c.fetchall():
                    plans.append({"id": r[0], "name": r[1], "price_monthly": r[2], "price_yearly": r[3], "credits_monthly": r[4], "max_agents": r[5], "max_entities": r[6], "max_functions": r[7], "max_workflows": r[8], "allowed_models": json.loads(r[9]) if r[9] else [], "features": json.loads(r[10]) if r[10] else [], "sort_order": r[11]})
            self._send_json(200, {"plans": plans})
            return
        if self.path == "/auth/subscription":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            sub = get_user_subscription(user_id)
            if not sub:
                self._send_json(404, {"error": "No subscription"})
                return
            self._send_json(200, sub)
            return
        if self.path == "/auth/credits":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            sub = get_user_subscription(user_id)
            if not sub:
                self._send_json(404, {"error": "No subscription"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT amount, type, description, model_used, timestamp FROM credit_transactions WHERE user_id = ? ORDER BY id DESC LIMIT 20", (user_id,))
                history = [{"amount": r[0], "type": r[1], "description": r[2], "model": r[3], "time": r[4]} for r in c.fetchall()]
            self._send_json(200, {"remaining": sub["credits_remaining"], "used": sub["credits_used"], "monthly_total": sub["credits_monthly"], "plan": sub["plan_name"], "history": history})
            return
        if self.path == "/auth/billing-history":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, amount, currency, plan_name, billing_cycle, status, created_date, invoice_url FROM payments WHERE user_id = ? ORDER BY id DESC", (user_id,))
                payments = [{"id": r[0], "amount": r[1], "currency": r[2], "plan": r[3], "cycle": r[4], "status": r[5], "date": r[6], "invoice": r[7]} for r in c.fetchall()]
            self._send_json(200, {"payments": payments})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        # Stripe webhook — needs raw body for signature verification
        if self.path == "/auth/stripe-webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            sig = self.headers.get("Stripe-Signature", "")
            try:
                event = stripe.Webhook.construct_event(raw_body, sig, STRIPE_WEBHOOK_SECRET)
            except ValueError:
                self._send_json(400, {"error": "Invalid payload"})
                return
            except stripe.error.SignatureVerificationError:
                self._send_json(400, {"error": "Invalid signature"})
                return

            # Normalize the Stripe event, then hand off to the neutral layer.
            event_type = event["type"]
            data = event["data"]["object"]
            metadata = data.get("metadata", {}) or {}
            try:
                user_id = int(metadata.get("user_id") or data.get("client_reference_id") or 0)
            except (TypeError, ValueError):
                user_id = 0

            if event_type == "checkout.session.completed":
                kind = metadata.get("type")
                apply_payment_event(
                    kind if kind in ("subscription", "credits") else "none",
                    user_id,
                    charge_id=data.get("id"),
                    plan=metadata.get("plan", "Free"),
                    cycle=metadata.get("cycle", "monthly"),
                    credits=metadata.get("credits", 0),
                    provider="stripe",
                )
            elif event_type == "customer.subscription.deleted":
                apply_payment_event("cancel", user_id, provider="stripe")

            self._send_json(200, {"received": True})
            return

        # Paddle Billing webhook — raw body required for HMAC verification
        if self.path == "/auth/paddle-webhook":
            raw_body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            ok, reason = verify_paddle_signature(raw_body, self.headers.get("Paddle-Signature", ""))
            if not ok:
                print("[paddle] rejected webhook: " + reason)
                self._send_json(400, {"error": "Invalid signature", "reason": reason})
                return
            try:
                event = json.loads(raw_body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._send_json(400, {"error": "Invalid payload"})
                return

            mapped = paddle_event_to_fulfilment(event)
            if mapped:
                try:
                    apply_payment_event(**mapped)
                except Exception as exc:
                    # 500 so Paddle retries rather than dropping a paid order
                    print("[paddle] fulfilment failed: " + repr(exc))
                    self._send_json(500, {"error": "Fulfilment failed"})
                    return
            self._send_json(200, {"received": True})
            return

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
        if path == "/auth/forgot-password":
            email = body.get("email", "").lower().strip()
            if not email:
                self._send_json(400, {"error": "Email required"})
                return
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, display_name FROM users WHERE email=?", (email,))
            row = c.fetchone()
            if not row:
                # Don't reveal if email exists or not
                self._send_json(200, {"ok": True, "message": "If the email exists, a reset code has been sent."})
                return
            
            user_id, display_name = row
            otp_code = generate_otp()
            otp_expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            
            c.execute("UPDATE users SET otp_code=?, otp_expires=?, otp_attempts=0 WHERE id=?",
                       (otp_code, otp_expires, user_id))
            conn.commit()
            conn.close()
            
            # Send reset code via Brevo
            try:
                import urllib.request
                BREVO_API_KEY = os.environ.get("BREVO_API_KEY", os.environ.get("BRAVO_API_KEY", ""))
                SENDER_EMAIL = os.environ.get("SMTP_USER", "support@evolvixos.com")
                SENDER_NAME = "EvolvixOS Support"
                
                html_content = f"""<html><body style='font-family:Inter,Arial,sans-serif;background:#0a0a0f;color:#fff;padding:40px;'><div style='max-width:480px;margin:0 auto;background:#111113;border:1px solid #1f1f23;border-radius:16px;padding:40px;'><h1 style='color:#8b5cf6;margin-bottom:8px;'>Password Reset</h1><p style='color:#ccc;font-size:16px;margin-bottom:24px;'>Hello {display_name or "there"},</p><p style='color:#ccc;font-size:15px;margin-bottom:20px;'>You requested a password reset for your EvolvixOS account. Use the code below to reset your password:</p><div style='background:#0a0a0f;border:1px solid #1f1f23;border-radius:12px;padding:24px;text-align:center;margin:24px 0;'><span style='font-size:32px;font-weight:700;color:#8b5cf6;letter-spacing:8px;'>{otp_code}</span></div><p style='color:#888;font-size:13px;'>This code expires in 10 minutes. If you didn't request this, you can safely ignore this email.</p></div></body></html>"""
                
                payload = json.dumps({
                    "sender": {"email": SENDER_EMAIL, "name": SENDER_NAME},
                    "to": [{"email": email}],
                    "subject": f"EvolvixOS Password Reset Code: {otp_code}",
                    "htmlContent": html_content,
                    "textContent": f"Your EvolvixOS password reset code is: {otp_code}\n\nThis code expires in 10 minutes."
                }).encode()
                
                req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=payload, headers={
                    "Content-Type": "application/json",
                    "api-key": BREVO_API_KEY
                })
                urllib.request.urlopen(req, timeout=15)
                print(f"Password reset OTP sent to {email}")
            except Exception as e:
                print(f"Failed to send reset email: {e}")
            
            self._send_json(200, {"ok": True, "message": "If the email exists, a reset code has been sent."})
            return

        if path == "/auth/reset-password":
            email = body.get("email", "").lower().strip()
            otp = body.get("otp", "").strip()
            new_password = body.get("new_password", "").strip()
            
            if not email or not otp or not new_password:
                self._send_json(400, {"error": "Email, reset code, and new password are required"})
                return
            
            if len(new_password) < 8:
                self._send_json(400, {"error": "Password must be at least 8 characters"})
                return
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, otp_code, otp_expires, otp_attempts FROM users WHERE email=?", (email,))
            row = c.fetchone()
            if not row:
                self._send_json(400, {"error": "Invalid email or reset code"})
                return
            
            user_id, stored_otp, otp_expires, otp_attempts = row
            
            # Check OTP expiry
            if not otp_expires:
                self._send_json(400, {"error": "No reset code found. Please request a new one."})
                return
            
            expires_dt = datetime.fromisoformat(otp_expires)
            if datetime.utcnow() > expires_dt:
                self._send_json(400, {"error": "Reset code expired. Please request a new one."})
                return
            
            # Check attempts
            if otp_attempts >= 5:
                self._send_json(400, {"error": "Too many attempts. Please request a new reset code."})
                return
            
            # Verify OTP
            if otp != stored_otp:
                c.execute("UPDATE users SET otp_attempts=otp_attempts+1 WHERE id=?", (user_id,))
                conn.commit()
                remaining = 5 - (otp_attempts + 1)
                self._send_json(400, {"error": f"Invalid reset code. {remaining} attempt(s) left."})
                return
            
            # Update password
            new_hash = hash_password(new_password)
            c.execute("UPDATE users SET password_hash=?, otp_code=NULL, otp_expires=NULL, otp_attempts=0 WHERE id=?",
                       (new_hash, user_id))
            conn.commit()
            conn.close()
            
            self._send_json(200, {"ok": True, "message": "Password reset successfully! You can now login with your new password."})
            return

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
        if path == "/auth/update-profile":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                if "display_name" in body:
                    c.execute("UPDATE users SET display_name = ? WHERE id = ?", (body["display_name"], user_id))
                if "telegram_username" in body:
                    c.execute("UPDATE users SET telegram_username = ? WHERE id = ?", (body["telegram_username"].lstrip("@"), user_id))
                conn.commit()
            self._send_json(200, {"message": "Profile updated"})
            return
        if path == "/auth/change-password":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            if not body.get("current_password") or not body.get("new_password"):
                self._send_json(400, {"error": "Missing passwords"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
                row = c.fetchone()
                if not row or not verify_password(body["current_password"], row[0]):
                    self._send_json(400, {"error": "Current password incorrect"})
                    return
                new_hash = hash_password(body["new_password"])
                c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                conn.commit()
            self._send_json(200, {"message": "Password changed"})
            return
        if path == "/auth/revoke-session":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM user_sessions WHERE id = ? AND user_id = ?", (body.get("session_id"), user_id))
                conn.commit()
            self._send_json(200, {"message": "Session revoked"})
            return
        if path == "/auth/subscribe":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            plan_name = body.get("plan", "Free")
            billing_cycle = body.get("cycle", "monthly")
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, credits_monthly, price_monthly, price_yearly FROM plans WHERE name = ? AND is_active = 1", (plan_name,))
                plan = c.fetchone()
                if not plan:
                    self._send_json(404, {"error": "Plan not found"})
                    return
                plan_id, credits, price_m, price_y = plan
                price = price_y if billing_cycle == "yearly" else price_m
                c.execute("SELECT id FROM subscriptions WHERE user_id = ? AND status = ?", (user_id, "active"))
                existing = c.fetchone()
                now = time.strftime("%Y-%m-%d %H:%M:%S")
                days = 365 if billing_cycle == "yearly" else 30
                period_end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + days * 86400))
                if existing:
                    c.execute("UPDATE subscriptions SET plan_id = ?, billing_cycle = ?, credits_remaining = ?, current_period_start = ?, current_period_end = ?, updated_date = ? WHERE id = ?", (plan_id, billing_cycle, credits, now, period_end, now, existing[0]))
                else:
                    c.execute("INSERT INTO subscriptions (user_id, plan_id, status, billing_cycle, credits_remaining, credits_used, current_period_start, current_period_end, created_date, updated_date) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)", (user_id, plan_id, "active", billing_cycle, credits, now, period_end, now, now))
                if price > 0:
                    c.execute("INSERT INTO payments (user_id, amount, currency, plan_name, billing_cycle, status, provider, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, price, "USD", plan_name, billing_cycle, "pending", "stripe", now))
                conn.commit()
            self._send_json(200, {"message": "Subscribed to " + plan_name, "plan": plan_name, "price": price, "credits": credits})
            return
        if path == "/auth/buy-credits":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            amount = body.get("credits", 1000)
            pack_price = body.get("price", 5)
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, credits_remaining FROM subscriptions WHERE user_id = ? AND status = ?", (user_id, "active"))
                row = c.fetchone()
                if not row:
                    self._send_json(404, {"error": "No subscription"})
                    return
                sub_id, current = row
                new_balance = current + amount
                c.execute("UPDATE subscriptions SET credits_remaining = ? WHERE id = ?", (new_balance, sub_id))
                c.execute("INSERT INTO credit_transactions (user_id, amount, type, description, timestamp) VALUES (?, ?, ?, ?, ?)", (user_id, amount, "credit", "Purchased credits", time.strftime("%Y-%m-%d %H:%M:%S")))
                c.execute("INSERT INTO payments (user_id, amount, currency, plan_name, billing_cycle, status, provider, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, pack_price, "USD", "Credit Pack", "one-time", "pending", "stripe", time.strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
            self._send_json(200, {"message": "Added " + str(amount) + " credits", "new_balance": new_balance})
            return
        if path == "/auth/stripe-checkout":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            item_type = body.get("type", "subscription")
            plan_name = body.get("plan", "")
            cycle = body.get("cycle", "monthly")
            credits_amount = body.get("credits", 0)
            price_cents = body.get("price_cents", 0)
            try:
                # Get user email for Stripe customer
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute("SELECT email, display_name FROM users WHERE id = ?", (user_id,))
                    row = c.fetchone()
                    if not row:
                        self._send_json(400, {"error": "User not found"})
                        return
                    user_email, display_name = row

                if item_type == "subscription":
                    # Create Stripe Checkout Session for subscription
                    product_name = plan_name + " Plan - " + cycle.capitalize()
                    description = "EvolvixOS " + plan_name + " plan (" + cycle + ")"
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        customer_email=user_email,
                        line_items=[{
                            "price_data": {
                                "currency": "usd",
                                "product_data": {"name": product_name, "description": description},
                                "unit_amount": price_cents,
                                "recurring": {"interval": "year" if cycle == "yearly" else "month"}
                            },
                            "quantity": 1
                        }],
                        mode="subscription",
                        success_url="https://evolvixos.com/platform/?payment=success&plan=" + plan_name,
                        cancel_url="https://evolvixos.com/platform/?payment=cancelled",
                        metadata={"user_id": str(user_id), "plan": plan_name, "cycle": cycle, "type": "subscription"},
                        client_reference_id=str(user_id)
                    )
                else:
                    # One-time credit purchase
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        customer_email=user_email,
                        line_items=[{
                            "price_data": {
                                "currency": "usd",
                                "product_data": {"name": str(credits_amount) + " Credits", "description": "EvolvixOS Credit Pack"},
                                "unit_amount": price_cents
                            },
                            "quantity": 1
                        }],
                        mode="payment",
                        success_url="https://evolvixos.com/platform/?payment=success&credits=" + str(credits_amount),
                        cancel_url="https://evolvixos.com/platform/?payment=cancelled",
                        metadata={"user_id": str(user_id), "credits": str(credits_amount), "type": "credits"},
                        client_reference_id=str(user_id)
                    )
                # Record pending payment
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO payments (user_id, amount, currency, plan_name, billing_cycle, status, provider, provider_charge_id, created_date) VALUES (?, ?, 'USD', ?, ?, 'pending', 'stripe', ?, ?)",
                        (user_id, price_cents / 100, plan_name or "Credit Pack", cycle if item_type == "subscription" else "one-time", session.id, time.strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                self._send_json(200, {"checkout_url": session.url, "session_id": session.id})
            except stripe.error.StripeError as e:
                self._send_json(400, {"error": str(e)})
                return
            except Exception as e:
                self._send_json(500, {"error": "Payment setup failed: " + str(e)})
                return


        if path == "/auth/paddle-portal":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute("SELECT email, paddle_customer_id FROM users WHERE id = ?", (user_id,))
                    row = c.fetchone()
                    if not row or not row[1]:
                        self._send_json(400, {"error": "No Paddle subscription found"})
                        return
                    email, paddle_customer_id = row

                # Create customer portal session via Paddle API
                paddle_api = PADDLE_API_BASE.rstrip('/')
                req = urllib.request.Request(
                    f"{paddle_api}/customer-portal-sessions",
                    data=json.dumps({"customer_id": paddle_customer_id}).encode(),
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {PADDLE_API_KEY}",
                        "Content-Type": "application/json",
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    session = json.loads(r.read().decode())

                portal_url = session.get("data", {}).get("url", "")
                self._send_json(200, {"portal_url": portal_url})
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                self._send_json(400, {"error": f"Paddle API error: {err_body[:300]}"})
                return
            except Exception as e:
                self._send_json(500, {"error": "Portal session failed: " + str(e)})
                return

        if path == "/auth/paddle-checkout":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            item_type = body.get("type", "subscription")
            plan_name = body.get("plan", "")
            cycle = body.get("cycle", "monthly")
            credits_amount = body.get("credits", 0)
            try:
                # Load paddle price IDs
                prices_path = os.path.join(os.path.dirname(__file__), '..', 'paddle_prices.json')
                with open(prices_path) as f:
                    paddle_prices = json.load(f)

                # Get user email
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute("SELECT email, display_name FROM users WHERE id = ?", (user_id,))
                    row = c.fetchone()
                    if not row:
                        self._send_json(400, {"error": "User not found"})
                        return
                    user_email, display_name = row

                price_id = None
                if item_type == "subscription":
                    key = f"{plan_name}_{cycle}"
                    price_id = paddle_prices.get("subscriptions", {}).get(key)
                else:
                    key = f"credits_{credits_amount}"
                    price_id = paddle_prices.get("credits", {}).get(key)

                if not price_id:
                    self._send_json(400, {"error": f"No Paddle price found for {item_type} {plan_name} {cycle}"})
                    return

                # Create Paddle transaction/checkout
                paddle_api = PADDLE_API_BASE.rstrip('/')
                checkout_body = {
                    "items": [{"price_id": price_id, "quantity": 1}],
                    "customer": {"email": user_email},
                    "custom_data": {"user_id": str(user_id), "type": item_type},
                    "success_url": f"https://evolvixos.com/platform/?payment=success&plan={plan_name}",
                }
                if item_type == "subscription":
                    checkout_body["custom_data"]["plan"] = plan_name
                    checkout_body["custom_data"]["cycle"] = cycle

                req = urllib.request.Request(
                    f"{paddle_api}/transactions",
                    data=json.dumps(checkout_body).encode(),
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {PADDLE_API_KEY}",
                        "Content-Type": "application/json",
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    txn = json.loads(r.read().decode())

                checkout_url = txn.get("data", {}).get("checkout", {}).get("url", "")
                txn_id = txn.get("data", {}).get("id", "")

                # Record pending payment
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO payments (user_id, amount, currency, plan_name, billing_cycle, status, provider, provider_charge_id, created_date) VALUES (?, ?, 'EUR', ?, ?, 'pending', 'paddle', ?, ?)",
                        (user_id, 0, plan_name or "Credit Pack", cycle if item_type == "subscription" else "one-time", txn_id, time.strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()

                self._send_json(200, {"checkout_url": checkout_url, "transaction_id": txn_id})
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                self._send_json(400, {"error": f"Paddle API error: {err_body[:300]}"})
                return
            except Exception as e:
                self._send_json(500, {"error": "Paddle checkout failed: " + str(e)})
                return

        if path == "/auth/stripe-portal":
            user_id = is_authorized(self)
            if not user_id:
                self._send_json(401, {"error": "Not authenticated"})
                return
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
                    row = c.fetchone()
                    if not row:
                        self._send_json(400, {"error": "User not found"})
                        return
                    user_email = row[0]
                # Find or create customer
                customers = stripe.Customer.list(email=user_email, limit=1)
                if customers.data:
                    customer_id = customers.data[0].id
                    session = stripe.billing_portal.Session.create(
                        customer=customer_id,
                        return_url="https://evolvixos.com/platform/?view=billing"
                    )
                    self._send_json(200, {"portal_url": session.url})
                else:
                    self._send_json(404, {"error": "No Stripe customer found. Subscribe first."})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                return
        if path == "/auth/stripe-create-products":
            # One-time setup: create Stripe products and prices
            admin_id = is_authorized(self)
            if not admin_id:
                self._send_json(401, {"error": "Admin only"})
                return
            created = {}
            products = {
                "Starter": {"monthly": 900, "yearly": 8600},
                "Pro": {"monthly": 2900, "yearly": 27800},
                "Team": {"monthly": 9900, "yearly": 95000}
            }
            credit_packs = {
                "credits_1000": {"name": "1,000 Credits", "price": 500},
                "credits_5000": {"name": "5,000 Credits", "price": 2000},
                "credits_15000": {"name": "15,000 Credits", "price": 5000},
                "credits_50000": {"name": "50,000 Credits", "price": 15000}
            }
            try:
                for plan, cycles in products.items():
                    p = stripe.Product.create(name="EvolvixOS " + plan + " Plan", description="EvolvixOS " + plan + " subscription")
                    for cycle, cents in cycles.items():
                        interval = "year" if cycle == "yearly" else "month"
                        price = stripe.Price.create(product=p.id, unit_amount=cents, currency="usd", recurring={"interval": interval})
                        key = plan + "_" + cycle
                        created[key] = price.id
                for key, info in credit_packs.items():
                    p = stripe.Product.create(name=info["name"], description="EvolvixOS Credit Pack")
                    price = stripe.Price.create(product=p.id, unit_amount=info["price"], currency="usd")
                    created[key] = price.id
                self._send_json(200, {"created": created, "message": "Products created. Save these price IDs to STRIPE_PRICES in auth_api.py"})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                return
        self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        print(f"[Auth] {args[0]}")


# Initialize API keys table
init_api_keys_table()

if __name__ == "__main__":
    port = 5022
    print(f"EvolvixOS Auth API v8.1 starting on port {port}")
    import socket
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", port), AuthHandler)
    server.serve_forever()
