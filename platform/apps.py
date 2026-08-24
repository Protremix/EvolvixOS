"""Apps Manager — Create, publish, share apps with generated pages."""
import json
import uuid
import re
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class AppsManager:
    @staticmethod
    def slugify(name: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
        return slug or 'app'

    @staticmethod
    async def create_app(db: AsyncSession, name: str, description: str = "", created_by: str = None, pages: list = None):
        slug = AppsManager.slugify(name)
        existing = await db.execute(text("SELECT slug FROM platform_apps WHERE slug = :s"), {"s": slug})
        if existing.fetchone():
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
        share_token = uuid.uuid4().hex if created_by else None
        result = await db.execute(text("""
            INSERT INTO platform_apps (name, description, slug, share_token, created_by, theme, settings)
            VALUES (:name, :desc, :slug, :token, :uid, '{}', '{}')
            RETURNING id
        """), {"name": name, "desc": description, "slug": slug, "token": share_token, "uid": created_by})
        app_id = result.fetchone()[0]
        if pages:
            for i, page in enumerate(pages):
                await db.execute(text("""
                    INSERT INTO platform_pages (app_id, name, slug, layout, page_type, is_home, sort_order, created_by)
                    VALUES (:aid, :name, :slug, :layout, :ptype, :home, :order, :uid)
                """), {
                    "aid": app_id, "name": page.get("name", "Page"),
                    "slug": AppsManager.slugify(page.get("name", "page")),
                    "layout": json.dumps(page.get("layout", [])),
                    "ptype": page.get("type", "custom"),
                    "home": i == 0, "order": i, "uid": created_by
                })
        await db.commit()
        await AppsManager._log_activity(db, "create", "app", name, f"App '{name}' created", created_by)
        return {"id": app_id, "name": name, "slug": slug, "share_token": share_token}

    @staticmethod
    async def list_apps(db: AsyncSession, user_id: str = None):
        query = "SELECT * FROM platform_apps"
        params = {}
        if user_id:
            query += ' WHERE created_by = :uid'
            params["uid"] = user_id
        query += " ORDER BY created_date DESC"
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        return [AppsManager._row_to_dict(r) for r in rows]

    @staticmethod
    async def get_app(db: AsyncSession, app_id: int, user_id: str = None):
        result = await db.execute(text("SELECT * FROM platform_apps WHERE id = :id"), {"id": app_id})
        row = result.fetchone()
        return AppsManager._row_to_dict(row) if row else None

    @staticmethod
    async def get_app_by_slug(db: AsyncSession, slug: str):
        result = await db.execute(text("SELECT * FROM platform_apps WHERE slug = :s"), {"s": slug})
        row = result.fetchone()
        return AppsManager._row_to_dict(row) if row else None

    @staticmethod
    async def update_app(db: AsyncSession, app_id: int, updates: dict, user_id: str = None):
        sets = []
        params = {"id": app_id}
        for k, v in updates.items():
            if k in ("name", "description", "status", "is_public", "theme", "settings"):
                params[k] = json.dumps(v) if isinstance(v, dict) else v
                sets.append(f"{k} = :{k}")
        sets.append("updated_date = NOW()")
        if sets:
            await db.execute(text(f"UPDATE platform_apps SET {', '.join(sets)} WHERE id = :id"), params)
            await db.commit()
        await AppsManager._log_activity(db, "update", "app", str(app_id), "App updated", user_id)
        return await AppsManager.get_app(db, app_id)

    @staticmethod
    async def delete_app(db: AsyncSession, app_id: int, user_id: str = None):
        app = await AppsManager.get_app(db, app_id)
        if app:
            await AppsManager._save_version(db, "app", str(app_id), app["name"], app, "App deleted", user_id)
        await db.execute(text("DELETE FROM platform_apps WHERE id = :id"), {"id": app_id})
        await db.commit()

    @staticmethod
    async def publish_app(db: AsyncSession, app_id: int, user_id: str = None):
        await db.execute(text("UPDATE platform_apps SET status = 'published', is_public = TRUE, updated_date = NOW(), version = version + 1 WHERE id = :id"), {"id": app_id})
        await db.commit()
        app = await AppsManager.get_app(db, app_id)
        if app:
            await AppsManager._log_activity(db, "publish", "app", app["name"], f"App '{app['name']}' published (v{app['version']})", user_id)
            await AppsManager._save_version(db, "app", str(app_id), app["name"], app, f"Published v{app['version']}", user_id)
        return app

    @staticmethod
    async def get_pages(db: AsyncSession, app_id: int):
        result = await db.execute(text("SELECT * FROM platform_pages WHERE app_id = :aid ORDER BY sort_order"), {"aid": app_id})
        rows = result.fetchall()
        pages = []
        for row in rows:
            # Columns: id(0), app_id(1), name(2), slug(3), layout(4), page_type(5), is_home(6), sort_order(7), created_date(8), updated_date(9), created_by(10)
            layout_raw = row[4]
            if isinstance(layout_raw, str):
                layout = json.loads(layout_raw) if layout_raw else []
            elif isinstance(layout_raw, list):
                layout = layout_raw
            else:
                layout = []
            pages.append({
                "id": row[0], "app_id": row[1], "name": row[2], "slug": row[3],
                "layout": layout, "page_type": row[5], "is_home": row[6],
                "sort_order": row[7], "created_date": str(row[8]), "updated_date": str(row[9])
            })
        return pages

    @staticmethod
    async def create_page(db: AsyncSession, app_id: int, name: str, layout: list = None, page_type: str = "custom", is_home: bool = False, created_by: str = None):
        slug = AppsManager.slugify(name)
        await db.execute(text("""
            INSERT INTO platform_pages (app_id, name, slug, layout, page_type, is_home, sort_order, created_by)
            VALUES (:aid, :name, :slug, :layout, :ptype, :home, 0, :uid)
            RETURNING id
        """), {"aid": app_id, "name": name, "slug": slug, "layout": json.dumps(layout or []), "ptype": page_type, "home": is_home, "uid": created_by})
        await db.commit()
        result = await db.execute(text("SELECT MAX(id) FROM platform_pages WHERE app_id = :aid"), {"aid": app_id})
        page_id = result.fetchone()[0]
        return {"id": page_id, "name": name, "slug": slug, "layout": layout or []}

    @staticmethod
    async def update_page(db: AsyncSession, page_id: int, updates: dict, user_id: str = None):
        sets = []
        params = {"id": page_id}
        for k, v in updates.items():
            if k in ("name", "layout", "page_type", "is_home", "sort_order"):
                params[k] = json.dumps(v) if isinstance(v, (list, dict)) else v
                sets.append(f"{k} = :{k}")
        sets.append("updated_date = NOW()")
        if sets:
            await db.execute(text(f"UPDATE platform_pages SET {', '.join(sets)} WHERE id = :id"), params)
            await db.commit()
        return {"id": page_id, "updated": True}

    @staticmethod
    async def delete_page(db: AsyncSession, page_id: int):
        await db.execute(text("DELETE FROM platform_pages WHERE id = :id"), {"id": page_id})
        await db.commit()

    @staticmethod
    async def _log_activity(db: AsyncSession, action, entity_type, entity_name, description, user_id):
        await db.execute(text("""
            INSERT INTO platform_activity (action, entity_type, entity_name, description, created_by)
            VALUES (:a, :t, :n, :d, :u)
        """), {"a": action, "t": entity_type, "n": entity_name, "d": description, "u": user_id})
        await db.commit()

    @staticmethod
    async def _save_version(db: AsyncSession, entity_type, entity_id, entity_name, snapshot, description, user_id):
        result = await db.execute(text("""
            SELECT COALESCE(MAX(version_number), 0) + 1 FROM platform_versions
            WHERE entity_type = :t AND entity_id = :id
        """), {"t": entity_type, "id": entity_id})
        version_num = result.fetchone()[0]
        await db.execute(text("""
            INSERT INTO platform_versions (entity_type, entity_id, entity_name, snapshot, change_description, version_number, created_by)
            VALUES (:t, :id, :n, :s, :d, :v, :u)
        """), {"t": entity_type, "id": entity_id, "n": entity_name, "s": json.dumps(snapshot, default=str), "d": description, "v": version_num, "u": user_id})
        await db.commit()

    @staticmethod
    async def get_versions(db: AsyncSession, entity_type: str = None, entity_id: str = None, limit: int = 20):
        query = "SELECT * FROM platform_versions"
        params = {"limit": limit}
        conditions = []
        if entity_type:
            conditions.append("entity_type = :t")
            params["t"] = entity_type
        if entity_id:
            conditions.append("entity_id = :id")
            params["id"] = entity_id
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY version_number DESC LIMIT :limit"
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        versions = []
        for row in rows:
            snap = row[4] if isinstance(row[4], dict) else json.loads(row[4] or '{}')
            versions.append({
                "id": row[0], "entity_type": row[1], "entity_id": row[2],
                "entity_name": row[3], "snapshot": snap,
                "change_description": row[5], "version_number": row[6],
                "created_date": str(row[7]), "created_by": row[8]
            })
        return versions

    @staticmethod
    async def get_activity(db: AsyncSession, limit: int = 20, user_id: str = None):
        query = "SELECT * FROM platform_activity"
        params = {"limit": limit}
        if user_id:
            query += " WHERE created_by = :uid"
            params["uid"] = user_id
        query += " ORDER BY created_date DESC LIMIT :limit"
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        activities = []
        for row in rows:
            activities.append({
                "id": row[0], "action": row[1], "entity_type": row[2],
                "entity_name": row[3], "description": row[4],
                "created_date": str(row[6]), "created_by": row[7]
            })
        return activities

    @staticmethod
    def _row_to_dict(row):
        if not row:
            return None
        return {
            "id": row[0], "name": row[1], "description": row[2],
            "slug": row[3], "status": row[4], "is_public": row[5],
            "share_token": row[6],
            "theme": row[7] if isinstance(row[7], dict) else json.loads(row[7] or '{}'),
            "settings": row[8] if isinstance(row[8], dict) else json.loads(row[8] or '{}'),
            "version": row[9], "created_date": str(row[10]), "updated_date": str(row[11]),
            "created_by": row[12]
        }
