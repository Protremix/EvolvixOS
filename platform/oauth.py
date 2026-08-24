"""OAuth Connectors Manager — self-service OAuth flow management."""
import json
import urllib.parse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

SUPPORTED_PROVIDERS = {
    "google": {
        "name": "Google",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "default_scopes": ["openid", "email", "profile"],
        "available_scopes": [
            "openid", "email", "profile",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    },
    "github": {
        "name": "GitHub",
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "default_scopes": ["read:user", "repo"],
        "available_scopes": ["read:user", "repo", "write:org", "gist", "notifications"],
    },
    "slack": {
        "name": "Slack",
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "default_scopes": ["chat:write", "channels:read"],
        "available_scopes": ["chat:write", "channels:read", "channels:history", "files:write", "users:read"],
    },
    "discord": {
        "name": "Discord",
        "auth_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "default_scopes": ["identify", "guilds"],
        "available_scopes": ["identify", "guilds", "bot", "messages.read"],
    },
}

class OAuthManager:
    @staticmethod
    def list_providers():
        return [
            {"id": k, "name": v["name"], "default_scopes": v["default_scopes"],
             "available_scopes": v["available_scopes"]}
            for k, v in SUPPORTED_PROVIDERS.items()
        ]

    @staticmethod
    async def list_connectors(db: AsyncSession, user_id: str = None):
        query = "SELECT id, provider, name, config, status, scopes, created_date FROM platform_connectors"
        params = {}
        if user_id:
            query += " WHERE created_by = :uid"
            params["uid"] = user_id
        query += " ORDER BY created_date DESC"
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        connectors = []
        for row in rows:
            config = row[3] if isinstance(row[3], dict) else json.loads(row[3] or '{}')
            # Mask client_secret
            if "client_secret" in config:
                config["client_secret"] = config["client_secret"][:4] + "***"
            scopes = row[5] if isinstance(row[5], list) else json.loads(row[5] or '[]')
            connectors.append({
                "id": row[0], "provider": row[1], "name": row[2],
                "config": config, "status": row[4],
                "scopes": scopes, "created_date": str(row[6]),
            })
        return connectors

    @staticmethod
    async def create_connector(db: AsyncSession, provider: str, name: str, client_id: str, client_secret: str, scopes: list = None, created_by: str = None):
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        p = SUPPORTED_PROVIDERS[provider]
        scopes = scopes or p["default_scopes"]
        result = await db.execute(text("""
            INSERT INTO platform_connectors (provider, name, config, status, scopes, created_by)
            VALUES (:p, :n, :c, 'disconnected', :s, :u)
            RETURNING id
        """), {
            "p": provider, "n": name,
            "c": json.dumps({"client_id": client_id, "client_secret": client_secret}),
            "s": scopes, "u": created_by
        })
        connector_id = result.fetchone()[0]
        await db.commit()
        return {"id": connector_id, "provider": provider, "name": name, "status": "disconnected", "scopes": scopes}

    @staticmethod
    async def get_auth_url(db: AsyncSession, connector_id: int, redirect_uri: str):
        result = await db.execute(text("SELECT provider, config FROM platform_connectors WHERE id = :id"), {"id": connector_id})
        row = result.fetchone()
        if not row:
            raise ValueError("Connector not found")
        provider = row[0]
        config = row[1] if isinstance(row[1], dict) else json.loads(row[1] or '{}')
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError("Unsupported provider")
        p = SUPPORTED_PROVIDERS[provider]
        params = {
            "client_id": config.get("client_id", ""),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(p["default_scopes"]),
        }
        return {"auth_url": p["auth_url"] + "?" + urllib.parse.urlencode(params), "provider": provider}

    @staticmethod
    async def delete_connector(db: AsyncSession, connector_id: int, user_id: str = None):
        result = await db.execute(text("SELECT created_by FROM platform_connectors WHERE id = :id"), {"id": connector_id})
        row = result.fetchone()
        if not row:
            raise ValueError("Connector not found")
        if user_id and row[0] and str(row[0]) != str(user_id):
            raise ValueError("Not authorized")
        await db.execute(text("DELETE FROM platform_connectors WHERE id = :id"), {"id": connector_id})
        await db.commit()
        return {"deleted": True}
