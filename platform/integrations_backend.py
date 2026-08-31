"""
EvolvixOS Connected App Integrations — GitHub, Vercel, Supabase, Slack, Gmail.
Each service connects via OAuth or API key, stores tokens in the secrets table,
and exposes list/execute endpoints for the workstation UI.
"""
import httpx
import json
import os
import base64
import asyncio
from datetime import datetime

# ─── GitHub Integration ───
GITHUB_API = "https://api.github.com"

async def github_verify_token(token):
    """Verify a GitHub personal access token."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{GITHUB_API}/user", headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })
        if r.status_code == 200:
            u = r.json()
            return {"connected": True, "username": u.get("login"), "name": u.get("name", ""), "avatar": u.get("avatar_url", "")}
        return {"connected": False, "error": "Invalid token"}

async def github_list_repos(token):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{GITHUB_API}/user/repos?sort=updated&per_page=50",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
        if r.status_code == 200:
            return [{"id": repo["id"], "name": repo["name"], "full_name": repo["full_name"],
                     "private": repo["private"], "url": repo["html_url"], "stars": repo["stargazers_count"],
                     "language": repo.get("language", ""), "updated": repo["updated_at"]} for repo in r.json()]
        return []

async def github_create_repo(token, name, private=True, description=""):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{GITHUB_API}/user/repos", headers={
            "Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"
        }, json={"name": name, "private": private, "description": description, "auto_init": True})
        if r.status_code in [200, 201]:
            return {"created": True, "url": r.json().get("html_url"), "name": r.json().get("full_name")}
        return {"created": False, "error": r.json().get("message", "Unknown error")}

async def github_push_file(token, repo_owner, repo_name, path, content, message="Deploy from EvolvixOS"):
    """Push a single file to a GitHub repo."""
    b64_content = base64.b64encode(content.encode()).decode()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.put(f"{GITHUB_API}/repos/{repo_owner}/{repo_name}/contents/{path}",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            json={"message": message, "content": b64_content})
        return r.status_code in [200, 201]

# ─── Supabase Integration ───
async def supabase_verify(url, service_key):
    """Verify Supabase credentials."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{url}/rest/v1/", headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}"
        })
        if r.status_code == 200:
            return {"connected": True, "url": url}
        return {"connected": False, "error": f"HTTP {r.status_code}"}

async def supabase_list_tables(url, service_key):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{url}/rest/v1/?apikey={service_key}", headers={
            "apikey": service_key, "Authorization": f"Bearer {service_key}",
            "Accept": "application/json"
        })
        if r.status_code == 200:
            tables = []
            for key in r.json():
                if not key.startswith("_"):
                    tables.append({"name": key})
            return tables
        return []

# ─── Slack Integration ───
async def slack_verify_token(token):
    """Verify a Slack bot token."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post("https://slack.com/api/auth.test", headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"
        })
        if r.status_code == 200 and r.json().get("ok"):
            d = r.json()
            return {"connected": True, "team": d.get("team"), "user": d.get("user"), "bot_id": d.get("bot_id")}
        return {"connected": False, "error": "Invalid token"}

async def slack_list_channels(token):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get("https://slack.com/api/conversations.list?types=public_channel,private_channel",
            headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200 and r.json().get("ok"):
            return [{"id": c["id"], "name": c["name"], "is_private": c.get("is_private", False)} 
                    for c in r.json().get("channels", [])]
        return []

async def slack_post_message(token, channel, text):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post("https://slack.com/api/chat.postMessage", headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"
        }, json={"channel": channel, "text": text})
        return r.status_code == 200 and r.json().get("ok", False)

# ─── Gmail Integration (via OAuth or App Password) ───
async def gmail_send(to, subject, body, app_password=None, sender=None):
    """Send email via Gmail SMTP with app password."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    if not app_password or not sender:
        return {"sent": False, "error": "Gmail credentials required"}
    
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, app_password)
            server.sendmail(sender, to, msg.as_string())
        return {"sent": True, "to": to, "subject": subject}
    except Exception as e:
        return {"sent": False, "error": str(e)}
