"""EvolvixOS API Engine — External API directory and integration hub"""
import json, os, sqlite3
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EvolvixOS API Engine", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

REGISTRY_DB = "/opt/evolvixos/models/registry.db"
OPENCLAW_JSON = "/opt/evolvixos/models/openclaw_apis.json"
FREELLM_JSON = "/opt/evolvixos/models/freellm_registry.json"
AITOOLS_JSON = "/opt/evolvixos/models/free_ai_tools_registry.json"

@app.get("/")
async def root():
    return {"status": "online", "engine": "API Engine v2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/apis")
async def list_apis(category: str = None, q: str = None, limit: int = 50, offset: int = 0):
    try:
        with open(OPENCLAW_JSON) as f:
            reg = json.load(f)
        apis = reg.get("apis", [])
        if category and category != "all":
            apis = [a for a in apis if a.get("category","").lower() == category.lower()]
        if q:
            ql = q.lower()
            apis = [a for a in apis if ql in a.get("name","").lower() or ql in a.get("description","").lower()]
        total = len(apis)
        return {"total": total, "limit": limit, "offset": offset, "apis": apis[offset:offset+limit]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/apis/categories")
async def api_categories():
    try:
        with open(OPENCLAW_JSON) as f:
            reg = json.load(f)
        return {"total_apis": reg.get("total_apis",0), "categories": reg.get("categories",{})}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/freellm")
async def freellm():
    try:
        with open(FREELLM_JSON) as f:
            return json.load(f)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/aitools")
async def aitools():
    try:
        with open(AITOOLS_JSON) as f:
            return json.load(f)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/discovery")
async def discovery():
    try:
        conn = sqlite3.connect("/opt/evolvixos/learner/discovery.db")
        c = conn.cursor()
        tools = c.execute("SELECT name, full_name, description, category, url, stars, status FROM discovered_tools ORDER BY stars DESC LIMIT 100").fetchall()
        count = c.execute("SELECT COUNT(*) FROM discovered_tools").fetchone()[0]
        scans = c.execute("SELECT COUNT(*) FROM scan_log").fetchone()[0]
        conn.close()
        return {"total": count, "scans": scans, "tools": [{"name": t[0], "full_name": t[1], "description": t[2], "category": t[3], "url": t[4], "stars": t[5], "status": t[6]} for t in tools]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/discovery/import")
async def discovery_import(request: Request):
    """Import discovered tools as skills"""
    try:
        body = await request.json() if await request.body() else {}
        tool_name = body.get("name", "")
        conn = sqlite3.connect("/opt/evolvixos/learner/discovery.db")
        c = conn.cursor()
        if tool_name:
            tool = c.execute("SELECT name, full_name, description, category, url, stars, language, topics FROM discovered_tools WHERE name=?", (tool_name,)).fetchone()
            if not tool:
                conn.close()
                return JSONResponse({"error": f"Tool '{tool_name}' not found"}, status_code=404)
            # Create skill file
            skill_path = f"/opt/evolvixos/skills/{tool[0]}.sh"
            os.makedirs("/opt/evolvixos/skills", exist_ok=True)
            with open(skill_path, "w") as f:
                f.write(f"#!/bin/bash\n# {tool[0]} - {tool[2][:80] if tool[2] else 'Discovered tool'}\n# Category: {tool[3]}\n# URL: {tool[4]}\n# Stars: {tool[5]}\necho 'Tool: {tool[0]}'\necho 'URL: {tool[4]}'\necho 'Category: {tool[3]}'\n")
            os.chmod(skill_path, 0o755)
            c.execute("UPDATE discovered_tools SET status='imported' WHERE name=?", (tool_name,))
            conn.commit()
            conn.close()
            return {"status": "imported", "name": tool[0], "skill_path": skill_path}
        else:
            # Import all new tools
            tools = c.execute("SELECT name, full_name, description, category, url, stars, language, topics FROM discovered_tools WHERE status='new' LIMIT 50").fetchall()
            imported = 0
            os.makedirs("/opt/evolvixos/skills", exist_ok=True)
            for t in tools:
                skill_path = f"/opt/evolvixos/skills/{t[0]}.sh"
                with open(skill_path, "w") as f:
                    f.write(f"#!/bin/bash\n# {t[0]} - {t[2][:80] if t[2] else 'Discovered tool'}\n# Category: {t[3]}\n# URL: {t[4]}\necho 'Tool: {t[0]}'\necho 'URL: {t[4]}'\necho 'Category: {t[3]}'\n")
                os.chmod(skill_path, 0o755)
                c.execute("UPDATE discovered_tools SET status='imported' WHERE name=?", (t[0],))
                imported += 1
            conn.commit()
            conn.close()
            return {"status": "ok", "imported": imported, "total_available": len(tools)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
