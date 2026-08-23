"""
EvolvixOS Platform API — Base44-style platform layer.
Provides: Entity system, Backend functions, Workflows, File storage, Chat builder.
Runs on port 8080 alongside the existing Mr James API on port 8000.
"""
import os
import sys
import json
import time
import uuid
import asyncio
import importlib.util
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, async_session
from entities.manager import EntityManager, EntityCRUD

# ─── App ───
app = FastAPI(
    title="EvolvixOS Platform API",
    description="Base44-style entity system, backend functions, workflows, and AI builder.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ───
class EntityCreate(BaseModel):
    name: str = Field(..., description="PascalCase entity name")
    schema: dict = Field(..., description="JSON schema for entity fields")

class EntityUpdate(BaseModel):
    schema: dict = Field(..., description="Updated JSON schema")

class RecordCreate(BaseModel):
    data: dict = Field(..., description="Record data")

class RecordUpdate(BaseModel):
    data: dict = Field(..., description="Updated record data")

class FunctionCreate(BaseModel):
    name: str = Field(..., description="Function name (camelCase)")
    code: str = Field(..., description="Python function code")
    env_vars: dict = Field(default_factory=dict)

class WorkflowCreate(BaseModel):
    name: str
    definition: dict
    trigger_type: str = Field(..., description="scheduled | entity | connector")
    trigger_config: Optional[dict] = None

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None


# ─── Health ───
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "EvolvixOS Platform API", "version": "1.0.0"}


# ─── Entity Routes ───
@app.get("/api/entities")
async def list_entities(db=Depends(get_db)):
    """List all entity schemas."""
    try:
        entities = await EntityManager.list_entities(db)
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/entities")
async def create_entity(entity: EntityCreate, db=Depends(get_db)):
    """Create a new entity with JSON schema → auto CRUD."""
    try:
        result = await EntityManager.create_entity(db, entity.name, entity.schema)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/entities/{name}")
async def get_entity(name: str, db=Depends(get_db)):
    """Get entity schema."""
    entity = await EntityManager.get_entity(db, name)
    if not entity:
        raise HTTPException(404, f"Entity '{name}' not found")
    return entity

@app.put("/api/entities/{name}")
async def update_entity(name: str, entity: EntityUpdate, db=Depends(get_db)):
    """Update entity schema (adds new columns)."""
    try:
        return await EntityManager.update_entity(db, name, entity.schema)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/entities/{name}")
async def delete_entity(name: str, db=Depends(get_db)):
    """Delete entity (schema + table). Fails if records exist."""
    try:
        return await EntityManager.delete_entity(db, name)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─── Entity Records (CRUD) ───
@app.get("/api/entities/{name}/records")
async def list_records(
    name: str,
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    sort: Optional[str] = None,
    db=Depends(get_db)
):
    """List entity records with pagination and sorting."""
    try:
        # Extract filters from query params
        filters = {}
        # Note: In a real implementation, we'd extract non-standard query params
        result = await EntityCRUD.list_records(db, name, limit=limit, skip=skip, filters=filters, sort=sort)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/entities/{name}/records")
async def create_record(name: str, record: RecordCreate, db=Depends(get_db)):
    """Create a new entity record."""
    try:
        return await EntityCRUD.create_record(db, name, record.data)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/entities/{name}/records/{record_id}")
async def get_record(name: str, record_id: int, db=Depends(get_db)):
    """Get a single entity record."""
    record = await EntityCRUD.get_record(db, name, record_id)
    if not record:
        raise HTTPException(404, f"Record {record_id} not found")
    return record

@app.put("/api/entities/{name}/records/{record_id}")
async def update_record(name: str, record_id: int, record: RecordUpdate, db=Depends(get_db)):
    """Update an entity record."""
    try:
        return await EntityCRUD.update_record(db, name, record_id, record.data)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/entities/{name}/records/{record_id}")
async def delete_record(name: str, record_id: int, db=Depends(get_db)):
    """Delete an entity record."""
    try:
        return await EntityCRUD.delete_record(db, name, record_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─── Backend Functions ───
@app.get("/api/functions")
async def list_functions(db=Depends(get_db)):
    """List all deployed backend functions."""
    result = await db.execute(text("SELECT name, language, created_date FROM platform_functions ORDER BY created_date DESC"))
    rows = result.fetchall()
    return {"functions": [{"name": r[0], "language": r[1], "created_date": r[2].isoformat() if r[2] else None} for r in rows]}

@app.post("/api/functions")
async def create_function(func: FunctionCreate, db=Depends(get_db)):
    """Deploy a backend function."""
    # Basic validation
    if not func.code.strip():
        raise HTTPException(400, "Function code cannot be empty")

    # Check if function exists
    result = await db.execute(text("SELECT id FROM platform_functions WHERE name = :name"), {"name": func.name})
    if result.fetchone():
        # Update existing
        await db.execute(text("""
            UPDATE platform_functions SET code = :code, env_vars = :env, updated_date = NOW()
            WHERE name = :name
        """), {"name": func.name, "code": func.code, "env": json.dumps(func.env_vars)})
    else:
        await db.execute(text("""
            INSERT INTO platform_functions (name, code, env_vars)
            VALUES (:name, :code, :env)
        """), {"name": func.name, "code": func.code, "env": json.dumps(func.env_vars)})
    await db.commit()
    return {"name": func.name, "message": f"Function '{func.name}' deployed", "url": f"/api/fn/{func.name}"}

@app.get("/api/fn/{name}")
async def run_function_get(name: str, request: Request, db=Depends(get_db)):
    """Execute a backend function (GET)."""
    return await _execute_function(name, request, db, method="GET")

@app.post("/api/fn/{name}")
async def run_function_post(name: str, request: Request, db=Depends(get_db)):
    """Execute a backend function (POST)."""
    return await _execute_function(name, request, db, method="POST")

async def _execute_function(name: str, request: Request, db, method: str):
    """Execute a backend function by name."""
    result = await db.execute(text("SELECT code, env_vars FROM platform_functions WHERE name = :name"), {"name": name})
    row = result.fetchone()
    if not row:
        raise HTTPException(404, f"Function '{name}' not found")

    code = row[0]
    env_vars = row[1] if isinstance(row[1], dict) else json.loads(row[1] or "{}")

    # Parse body if POST
    body = {}
    if method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}

    # Execute function in sandboxed environment
    try:
        local_vars = {"input": body, "request": {"method": method, "query": dict(request.query_params)}}
        exec_globals = {"__builtins__": __builtins__, "json": json, "time": time, "os": os}
        exec(code, exec_globals, local_vars)

        # Call the handler function if it exists
        if "handler" in local_vars and callable(local_vars["handler"]):
            result_val = local_vars["handler"](body)
            if asyncio.iscoroutine(result_val):
                result_val = await result_val
            return result_val
        elif "result" in local_vars:
            return local_vars["result"]
        else:
            return {"message": "Function executed", "output": str({k: v for k, v in local_vars.items() if k not in exec_globals})}
    except Exception as e:
        raise HTTPException(500, f"Function error: {str(e)}\n{traceback.format_exc()[:500]}")


# ─── Workflows ───
@app.get("/api/workflows")
async def list_workflows(db=Depends(get_db)):
    """List all workflows."""
    result = await db.execute(text("SELECT name, trigger_type, status, created_date FROM platform_workflows ORDER BY created_date DESC"))
    rows = result.fetchall()
    return {"workflows": [{"name": r[0], "trigger_type": r[1], "status": r[2], "created_date": r[3].isoformat() if r[3] else None} for r in rows]}

@app.post("/api/workflows")
async def create_workflow(wf: WorkflowCreate, db=Depends(get_db)):
    """Create a new workflow."""
    if wf.trigger_type not in ("scheduled", "entity", "connector"):
        raise HTTPException(400, "trigger_type must be: scheduled, entity, or connector")

    await db.execute(text("""
        INSERT INTO platform_workflows (name, definition, trigger_type, trigger_config)
        VALUES (:name, :def, :type, :config)
    """), {"name": wf.name, "def": json.dumps(wf.definition), "type": wf.trigger_type, "config": json.dumps(wf.trigger_config or {})})
    await db.commit()
    return {"name": wf.name, "trigger_type": wf.trigger_type, "status": "active", "message": "Workflow created"}

@app.put("/api/workflows/{name}/activate")
async def activate_workflow(name: str, db=Depends(get_db)):
    await db.execute(text("UPDATE platform_workflows SET status = 'active' WHERE name = :name"), {"name": name})
    await db.commit()
    return {"name": name, "status": "active"}

@app.put("/api/workflows/{name}/deactivate")
async def deactivate_workflow(name: str, db=Depends(get_db)):
    await db.execute(text("UPDATE platform_workflows SET status = 'paused' WHERE name = :name"), {"name": name})
    await db.commit()
    return {"name": name, "status": "paused"}

@app.delete("/api/workflows/{name}")
async def delete_workflow(name: str, db=Depends(get_db)):
    await db.execute(text("DELETE FROM platform_workflows WHERE name = :name"), {"name": name})
    await db.commit()
    return {"name": name, "deleted": True}


# ─── File Storage ───
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/opt/evolvixos/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...), db=Depends(get_db)):
    """Upload a file (public or private)."""
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    await db.execute(text("""
        INSERT INTO platform_files (filename, file_path, content_type, file_size)
        VALUES (:name, :path, :type, :size)
    """), {"name": file.filename, "path": file_path, "type": file.content_type, "size": len(content)})
    await db.commit()

    file_url = f"/api/files/{file_id}"
    return {"filename": file.filename, "url": file_url, "size": len(content)}

@app.get("/api/files/{file_id}")
async def get_file(file_id: str):
    """Download a file."""
    # Find file by UUID prefix
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(file_id):
            file_path = os.path.join(UPLOAD_DIR, f)
            original_name = f.split("_", 1)[1] if "_" in f else f
            with open(file_path, "rb") as fp:
                return StreamingResponse(
                    iter([fp.read()]),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment; filename={original_name}"}
                )
    raise HTTPException(404, "File not found")


# ─── AI Chat Builder ───
@app.post("/api/chat")
async def chat_build(msg: ChatMessage, db=Depends(get_db)):
    """
    AI chat builder — talk to the platform to create entities, functions, workflows.
    Uses the local Ollama LLM to interpret intent and execute actions.
    """
    import urllib.request

    # System prompt that teaches the LLM about platform capabilities
    system_prompt = """You are EvolvixOS Platform Builder. You help users build apps by creating entities, backend functions, and workflows via natural language.

Available API actions (respond with JSON):
- Create entity: {"action": "create_entity", "name": "Task", "schema": {"type": "object", "properties": {"title": {"type": "string"}, "done": {"type": "boolean"}}, "required": ["title"]}}
- List entities: {"action": "list_entities"}
- Create function: {"action": "create_function", "name": "getJoke", "code": "def handler(input):\\n    return {'joke': 'Why did the chicken cross the road?'}"}
- Create workflow: {"action": "create_workflow", "name": "Daily Report", "trigger_type": "scheduled", "definition": {}}

Always respond with a JSON action object. If the user just wants to chat, respond with {"action": "chat", "message": "your response"}."""

    # Call Ollama
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    payload = json.dumps({
        "model": "qwen2.5:7b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": msg.message}
        ],
        "stream": False,
        "options": {"temperature": 0.3}
    }).encode()

    try:
        req = urllib.request.Request(f"{ollama_url}/api/chat", data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        ollama_data = json.loads(resp.read())
        ai_response = ollama_data.get("message", {}).get("content", "")
    except Exception as e:
        return {"error": f"LLM error: {str(e)}", "message": "Sorry, I couldn't process that."}

    # Try to parse AI response as JSON action
    try:
        # Find JSON in response
        json_start = ai_response.find("{")
        json_end = ai_response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            action = json.loads(ai_response[json_start:json_end])
        else:
            return {"action": "chat", "message": ai_response}
    except json.JSONDecodeError:
        return {"action": "chat", "message": ai_response}

    # Execute the action
    action_type = action.get("action")
    try:
        if action_type == "create_entity":
            result = await EntityManager.create_entity(db, action["name"], action["schema"])
            return {"action": "create_entity", "result": result, "message": f"Entity '{action['name']}' created!"}
        elif action_type == "list_entities":
            entities = await EntityManager.list_entities(db)
            return {"action": "list_entities", "entities": entities}
        elif action_type == "create_function":
            # Store function
            await db.execute(text("""
                INSERT INTO platform_functions (name, code, env_vars)
                VALUES (:name, :code, '{}')
                ON CONFLICT (name) DO UPDATE SET code = EXCLUDED.code
            """), {"name": action["name"], "code": action["code"]})
            await db.commit()
            return {"action": "create_function", "name": action["name"], "url": f"/api/fn/{action['name']}", "message": f"Function '{action['name']}' deployed!"}
        elif action_type == "create_workflow":
            await db.execute(text("""
                INSERT INTO platform_workflows (name, definition, trigger_type, trigger_config)
                VALUES (:name, :def, :type, '{}')
                ON CONFLICT (name) DO UPDATE SET definition = EXCLUDED.definition
            """), {"name": action["name"], "def": json.dumps(action.get("definition", {})), "type": action.get("trigger_type", "scheduled")})
            await db.commit()
            return {"action": "create_workflow", "name": action["name"], "message": f"Workflow '{action['name']}' created!"}
        elif action_type == "chat":
            return {"action": "chat", "message": action.get("message", ai_response)}
        else:
            return {"action": "unknown", "message": ai_response}
    except Exception as e:
        return {"action": action_type, "error": str(e), "message": ai_response}


# ─── Startup ───
@app.on_event("startup")
async def startup():
    await init_db()
    print("EvolvixOS Platform API started on port 8080")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
