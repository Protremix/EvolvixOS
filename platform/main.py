"""
EvolvixOS Platform API — Base44-style platform layer.
Provides: Entity system, Backend functions, Workflows, File storage, Chat builder.
Runs on port 8080 alongside the existing Mr James API on port 8000.
"""
# Load environment from .env file
import os as _os
from pathlib import Path as _Path
_env_file = _Path(_os.path.dirname(__file__)).parent / '.env'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _, _v = _line.partition('=')
            _os.environ.setdefault(_k.strip(), _v.strip())


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

from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, async_session
from entities.manager import EntityManager
from entities.crud import EntityCRUD as EnhancedCRUD
from auth.middleware import optional_auth, require_auth, require_admin, get_user_from_token
from routing_bridge import unified_chat
import sqlite3 as sqlite3_billing

AUTH_DB_PATH = "/opt/evolvixos/auth/users.db"

def deduct_user_credits(user_id, model_id, tokens_in=0, tokens_out=0):
    """Deduct credits from user subscription based on model tier."""
    if not user_id:
        return {"ok": True, "cost": 0}  # No user = free (internal calls)
    # Model tier costs
    model_lower = (model_id or "").lower()
    if ":free" in model_lower:
        cost = 1
    elif any(m in model_lower for m in ["gpt-oss-20b", "gpt-oss-120b", "deepseek-v4-flash", "nemotron-3-super", "gemma-4-31b"]):
        cost = 2
    elif any(m in model_lower for m in ["gemini-3.1-pro-preview", "claude-opus", "gemini-3.7-flash"]):
        cost = 20
    elif any(m in model_lower for m in ["glm-5.2", "glm-5.3", "claude-sonnet-5", "gemini-3.1-pro", "kimi-k2.7", "nemotron-3-ultra", "qwen3.8"]):
        cost = 10
    elif any(m in model_lower for m in ["glm-5", "kimi-k2", "qwen2.5", "step-3.7"]):
        cost = 5
    else:
        cost = 3
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute("SELECT id, credits_remaining FROM subscriptions WHERE user_id = ? AND status = ?", (int(user_id), "active"))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"ok": True, "cost": 0}  # No subscription = free for now
        sub_id, remaining = row
        if remaining < cost:
            conn.close()
            return {"ok": False, "error": "Insufficient credits. Upgrade your plan or buy more credits.", "remaining": remaining, "cost": cost}
        new_balance = remaining - cost
        c.execute("UPDATE subscriptions SET credits_remaining = ?, credits_used = credits_used + ? WHERE id = ?", (new_balance, cost, sub_id))
        c.execute("INSERT INTO credit_transactions (user_id, amount, type, description, model_used, tokens_in, tokens_out, balance_after, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (int(user_id), cost, "debit", "API call: " + (model_id or "auto"), model_id or "auto", tokens_in, tokens_out, new_balance, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return {"ok": True, "cost": cost, "remaining": new_balance}
    except Exception as e:
        return {"ok": True, "cost": 0}  # Don't block API on billing errors

def get_user_plan_limits(user_id):
    """Get user plan limits for resource gating."""
    if not user_id:
        return None
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute("SELECT s.credits_remaining, p.name, p.max_agents, p.max_entities, p.max_functions, p.max_workflows FROM subscriptions s JOIN plans p ON s.plan_id = p.id WHERE s.user_id = ? AND s.status = ?", (int(user_id), "active"))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {"credits": row[0], "plan": row[1], "max_agents": row[2], "max_entities": row[3], "max_functions": row[4], "max_workflows": row[5]}
    except:
        return None
from workflows.engine import WorkflowEngine
from agents.manager import AgentManager
from plugins.registry import PluginRegistry

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

class AgentCreate(BaseModel):
    name: str = Field(..., description="Agent name")
    system_prompt: str = Field(..., description="System prompt — defines agent personality and behavior")
    model: str = Field("auto", description="AI model (auto, openai/gpt-oss-120b, z-ai/glm-5, qwen2.5:7b, etc.)")
    temperature: float = Field(0.7, description="Temperature 0-1 (lower=precise, higher=creative)")
    tools: list = Field(default_factory=list, description="Available tools")
    max_tokens: int = Field(4096, description="Max response tokens")
    top_p: float = Field(0.9, description="Top-p nucleus sampling")
    memory_enabled: bool = Field(True, description="Whether agent persists memory across sessions")
    stream: bool = Field(False, description="Stream responses")

class AgentUpdate(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[list] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    memory_enabled: Optional[bool] = None
    status: Optional[str] = None
    stream: Optional[bool] = None
    automation_model: Optional[str] = None
    cross_app_access: Optional[bool] = None
    avatar: Optional[str] = None
    identity_doc: Optional[str] = None
    share_enabled: Optional[bool] = None
    collaborators: Optional[list] = None
    channel_config: Optional[dict] = None
    allow_update_data: Optional[bool] = None
    allow_delete_data: Optional[bool] = None
    auto_detect_secrets: Optional[bool] = None
    agent_secrets: Optional[dict] = None
    api_key: Optional[str] = None

class AgentInvoke(BaseModel):
    message: str = Field(..., description="Message to the agent")
    context: Optional[dict] = None

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None
    model: Optional[str] = None  # OpenRouter model ID, e.g. "z-ai/glm-5"


# ─── Health ───
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "EvolvixOS Platform API", "version": "1.0.0"}


# ─── Entity Routes ───
@app.get("/api/entities")
async def list_entities(db=Depends(get_db), request: Request = None):
    """List all entity schemas — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        entities = await EntityManager.list_entities(db)
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/entities")
async def create_entity(entity: EntityCreate, db=Depends(get_db), request: Request = None):
    """Create a new entity — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        result = await EntityManager.create_entity(db, entity.name, entity.schema, created_by=user.get("user_id") if user else None)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/entities/{name}")
async def get_entity(name: str, db=Depends(get_db), request: Request = None):
    """Get entity schema — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    entity = await EntityManager.get_entity(db, name)
    if not entity:
        raise HTTPException(404, f"Entity '{name}' not found")
    return entity

@app.put("/api/entities/{name}")
async def update_entity(name: str, entity: EntityUpdate, db=Depends(get_db), request: Request = None):
    """Update entity schema — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        return await EntityManager.update_entity(db, name, entity.schema)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/entities/{name}")
async def delete_entity(name: str, db=Depends(get_db), request: Request = None):
    """Delete entity — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
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
    request: Request = None,
    db=Depends(get_db)
):
    """List entity records with pagination and sorting."""
    try:
        # Extract filters from query params
        filters = {}
        # Note: In a real implementation, we'd extract non-standard query params
        user = get_user_from_token(request) if request else None
        user_id = user.get("user_id") if user else None
        result = await EnhancedCRUD.list_records(db, name, limit=limit, skip=skip, filters=filters, sort=sort, user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/entities/{name}/records")
async def create_record(name: str, record: RecordCreate, request: Request, db=Depends(get_db)):
    """Create a new entity record."""
    try:
        user = get_user_from_token(request) if request else None
        created_by = user.get("user_id") if user else None
        return await EnhancedCRUD.create_record(db, name, record.data, created_by=created_by)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/entities/{name}/records/{record_id}")
async def get_record(name: str, record_id: int, db=Depends(get_db)):
    """Get a single entity record."""
    record = await EnhancedCRUD.get_record(db, name, record_id)
    if not record:
        raise HTTPException(404, f"Record {record_id} not found")
    return record

@app.put("/api/entities/{name}/records/{record_id}")
async def update_record(name: str, record_id: int, record: RecordUpdate, request: Request, db=Depends(get_db)):
    """Update an entity record."""
    try:
        user = get_user_from_token(request) if request else None
        user_id = user.get("user_id") if user else None
        return await EnhancedCRUD.update_record(db, name, record_id, record.data, user_id=user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/entities/{name}/records/{record_id}")
async def delete_record(name: str, record_id: int, request: Request, db=Depends(get_db)):
    """Delete an entity record."""
    try:
        user = get_user_from_token(request) if request else None
        user_id = user.get("user_id") if user else None
        return await EnhancedCRUD.delete_record(db, name, record_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─── Backend Functions ───
@app.get("/api/functions")
async def list_functions(db=Depends(get_db), request: Request = None):
    """List all deployed functions — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
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
    # ─── Credit deduction for function calls ───
    user = get_user_from_token(request)
    user_id = user.get("user_id") if user else None
    if user_id:
        credit_check = deduct_user_credits(user_id, "function-call", 0, 0)
        if not credit_check.get("ok"):
            raise HTTPException(402, credit_check.get("error", "Insufficient credits"))
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
async def list_workflows(db=Depends(get_db), request: Request = None):
    """List all workflows — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
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



# ─── Workflow Execution ───
@app.post("/api/workflows/{name}/execute")
async def execute_workflow(name: str, db=Depends(get_db)):
    """Manually execute a workflow."""
    result = await WorkflowEngine.execute_workflow(db, name)
    return result

@app.get("/api/workflows/{name}/logs")
async def workflow_logs(name: str, limit: int = 10, db=Depends(get_db)):
    """Get workflow execution logs."""
    result = await db.execute(text(
        "SELECT id, results, executed_at FROM platform_workflow_logs WHERE workflow_name = :name ORDER BY executed_at DESC LIMIT :limit"
    ), {"name": name, "limit": limit})
    rows = result.fetchall()
    return {"logs": [{"id": r[0], "results": r[1] if isinstance(r[1], dict) else json.loads(r[1] or "{}"), "executed_at": r[2].isoformat() if r[2] else None} for r in rows]}


# ─── Entity Aggregation ───
class AggregationPipeline(BaseModel):
    pipeline: list = Field(..., description="MongoDB-style aggregation pipeline")

@app.post("/api/entities/{name}/aggregate")
async def aggregate_entity(name: str, agg: AggregationPipeline, db=Depends(get_db)):
    """Run aggregation pipeline on entity (group by, count, sum, avg)."""
    try:
        result = await EnhancedCRUD.aggregate(db, name, agg.pipeline)
        return {"result": result}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Enhanced filter endpoint ───
@app.post("/api/entities/{name}/filter")
async def filter_records(name: str, filter_req: dict, db=Depends(get_db)):
    """Filter entity records with operators. POST body: {"filters": {"priority": {"operator": "gte", "value": 3}}, "limit": 50, "skip": 0, "sort": "-created_date"}"""
    try:
        filters = filter_req.get("filters", {})
        limit = filter_req.get("limit", 50)
        skip = filter_req.get("skip", 0)
        sort = filter_req.get("sort")
        user = get_user_from_token(request) if request else None
        user_id = user.get("user_id") if user else None
        result = await EnhancedCRUD.list_records(db, name, limit=limit, skip=skip, filters=filters, sort=sort, user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Agents ───
@app.get("/api/agents")
async def list_agents(db=Depends(get_db), request: Request = None):
    """List all AI agents — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    agents = await AgentManager.list_agents(db)
    return {"agents": agents}

@app.post("/api/agents")
async def create_agent(agent: AgentCreate, db=Depends(get_db), request: Request = None):
    """Create a new AI agent with custom system prompt."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    created_by = user.get("user_id", "platform")
    try:
        return await AgentManager.create_agent(db, agent.name, agent.system_prompt,
            agent.model, agent.temperature, agent.tools, created_by,
            agent.max_tokens, agent.top_p, agent.memory_enabled, agent.stream)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/agents/{name}")
async def get_agent(name: str, db=Depends(get_db), request: Request = None):
    """Get agent details — requires auth, masks secrets."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    agent = await AgentManager.get_agent(db, name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    # Mask api_key for everyone, secrets for non-owners
    if agent.get("api_key"):
        agent["api_key"] = agent["api_key"][:8] + "..."
    if agent.get("created_by") != user.get("user_id") and user.get("role") != "admin":
        agent["agent_secrets"] = {k: "***" for k in (agent.get("agent_secrets") or {})}
    return agent

@app.put("/api/agents/{name}")
async def update_agent(name: str, updates: AgentUpdate, db=Depends(get_db), request: Request = None):
    """Update agent — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    agent = await AgentManager.get_agent(db, name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    if agent.get("created_by") != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(403, "You can only modify agents you own")
    try:
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        return await AgentManager.update_agent(db, name, update_data)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/agents/{name}")
async def delete_agent(name: str, db=Depends(get_db), request: Request = None):
    """Delete agent — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    agent = await AgentManager.get_agent(db, name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    if agent.get("created_by") != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(403, "You can only delete agents you own")
    try:
        return await AgentManager.delete_agent(db, name)
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.post("/api/agents/{name}/invoke")
async def invoke_agent(name: str, msg: AgentInvoke, request: Request, db=Depends(get_db)):
    """Invoke an agent — send a message and get a response."""
    # ─── Credit deduction ───
    user = get_user_from_token(request)
    user_id = user.get("user_id") if user else None
    if user_id:
        # Get agent model for credit cost
        agent = await AgentManager.get_agent(db, name)
        agent_model = agent.get("model", "auto") if agent else "auto"
        credit_check = deduct_user_credits(user_id, agent_model)
        if not credit_check.get("ok"):
            raise HTTPException(402, credit_check.get("error", "Insufficient credits"))
    try:
        result = await AgentManager.invoke_agent(db, name, msg.message, msg.context)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/agents/{name}/clear-memory")
async def clear_agent_memory(name: str, db=Depends(get_db)):
    """Clear agent conversation memory."""
    return await AgentManager.clear_memory(db, name)


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
# ─── Plugins ───
@app.get("/api/plugins")
async def list_plugins():
    """List all available plugins."""
    return {"plugins": PluginRegistry.list_plugins()}

@app.get("/api/plugins/{plugin_id}")
async def get_plugin_info(plugin_id: str):
    """Get details of a specific plugin."""
    plugin = PluginRegistry.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return {"id": plugin_id, "name": plugin["name"], "description": plugin["description"],
            "category": plugin["category"], "icon": plugin["icon"], "params": plugin["params"]}

@app.post("/api/plugins/{plugin_id}/execute")
async def exec_plugin(plugin_id: str, params: dict = Body(...), db=Depends(get_db), request: Request = None):
    """Execute a plugin — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    result = await PluginRegistry.execute_plugin(plugin_id, params, db)
    return result

# ─── Chat / AI Builder ───
@app.post("/api/chat")
async def chat_build(msg: ChatMessage, request: Request, db=Depends(get_db)):
    """
    AI chat builder — talk to the platform to create entities, functions, workflows.
    Uses the local Ollama LLM to interpret intent and execute actions.
    """
    import urllib.request

    # ─── Credit deduction ───
    user = get_user_from_token(request)
    user_id = user.get("user_id") if user else None
    if user_id:
        # Determine model that will be used for credit cost
        pre_model = msg.model or "auto"
        if pre_model == "auto":
            msg_lower = msg.message.lower()
            if any(w in msg_lower for w in ["build", "create", "make", "entity", "app", "store", "shop", "dashboard", "blog", "task", "project", "note", "feedback", "contact", "order"]):
                pre_model = "qwen/qwen3.8-27b"        # 80.7% tool accuracy
            elif any(w in msg_lower for w in ["code", "function", "api", "deploy", "python", "script", "backend", "endpoint"]):
                pre_model = "deepseek/deepseek-v4-flash-0731"  # 76.3%, bash.010/task
            elif any(w in msg_lower for w in ["analyze", "reason", "think", "complex", "architect", "design", "plan", "strategy"]):
                pre_model = "google/gemini-3.7-flash"  # 80.6%, bash.077/task
            else:
                pre_model = "google/gemma-4-31b"       # 76.5%, bash.016/task
        credit_check = deduct_user_credits(user_id, pre_model)
        if not credit_check.get("ok"):
            raise HTTPException(402, credit_check.get("error", "Insufficient credits"))

    # Get existing entities so the LLM knows what's already built
    existing_entities = await EntityManager.list_entities(db)
    existing_names = [e["name"] for e in existing_entities] if existing_entities else []
    existing_summary = ", ".join(existing_names) if existing_names else "none yet"

    # Load persistent memory to give the builder context
    memory_text = ""
    try:
        mem_result = await db.execute(text(
            "SELECT content FROM entity_platformmemory ORDER BY created_date DESC LIMIT 20"
        ))
        mem_rows = mem_result.fetchall()
        if mem_rows:
            memory_items = [r[0] for r in mem_rows if r[0]]
            if memory_items:
                memory_text = "\n\nUSER MEMORY — Things to remember about this user and project:\n" + "\n".join(f"- {m}" for m in memory_items)
    except Exception:
        pass

    # System prompt that teaches the LLM about platform capabilities
    system_prompt = f"""You are EvolvixOS Platform Builder. You help users build apps by creating entities, backend functions, and workflows via natural language.

CURRENT STATE — Entities already in the project: {existing_summary}{memory_text}

Available API actions (respond with JSON):
- Create entity: {{"action": "create_entity", "name": "Task", "schema": {{"type": "object", "properties": {{"title": {{"type": "string"}}, "done": {{"type": "boolean"}}}}, "required": ["title"]}}}}
- List entities: {{"action": "list_entities"}}
- Create function: {{"action": "create_function", "name": "getJoke", "code": "def handler(input):\n    return {{'joke': 'Why did the chicken cross the road?'}}"}}
- Create workflow: {{"action": "create_workflow", "name": "Daily Report", "trigger_type": "scheduled", "definition": {{}}}}

CRITICAL RULES:
1. Be proactive, not interrogative. When the user gives a vague request, CREATE something immediately.
2. CHECK the "CURRENT STATE" list above. If a suitable entity already exists, do NOT create a duplicate. Instead respond with {{"action": "chat", "message": "You already have a 'Post' entity for that — want me to add more fields or create a different entity?"}}.
3. If the user asks for something related but different from existing entities, create a NEW entity with a distinct name. For example, if "Page" exists and the user wants a delivery app, create "Order" (not another "Page").
4. Only ask a clarifying question if the request is truly ambiguous with no sensible default.

Proactive defaults (always use action "create_entity"):
- "website" or "landing page" -> "Page": {{title, slug, content, published}}
- "blog" -> "Post": {{title, slug, content, author, published}}
- "store" or "shop" or "ecommerce" -> "Product": {{name, description, price, stock, image_url}}
- "delivery" or "delivery business" -> "Order": {{order_id, customer_name, customer_email, items, status, delivery_address, estimated_delivery_time, completed}}
- "CRM" -> "Contact": {{name, email, phone, company, status}}
- "portfolio" -> "Project": {{title, description, image_url, link, category}}
- "booking" or "reservations" -> "Booking": {{name, email, date, time, status}}
- "fitness" or "workout tracker" -> "Workout": {{title, date, duration, calories_burned, type, notes}}
- "task manager" or "todo" -> "Task": {{title, status, priority, due_date}}

You also have access to PLUGINS for external operations:
- web_search: Search the internet for current info
- web_fetch: Fetch and parse any URL
- email_send: Send emails via Brevo
- http_request: Call external APIs
- code_exec: Run Python code
- github: GitHub repo operations
- crypto: Get crypto prices
- weather: Get weather
- image_gen: Generate images
- translate: Translate text
When a user asks for something requiring external data, respond with: {{"action": "plugin", "plugin": "web_search", "params": {{"query": "search term"}}}}

Always respond with a JSON action object. If the user just wants to chat, respond with {{"action": "chat", "message": "your response"}}."""

    # ─── Unified LLM routing via V10 ModelRouter (respects privacy mode) ───
    llm_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": msg.message}
    ]
    llm_result = await unified_chat(llm_messages, model=msg.model or "auto", temperature=0.3, max_tokens=2000, prefer_cloud=True)
    ai_response = llm_result.get("content", "")
    used_model = llm_result.get("model", "auto")
    used_provider = llm_result.get("provider", "auto")
    privacy_mode = llm_result.get("privacy_mode", "HYBRID")

    # Extract and save memories from the conversation
    try:
        user_msg_lower = msg.message.lower()
        # Detect preferences, decisions, instructions
        memory_triggers = ["prefer", "always", "never", "use ", "don't ", "remember", "should", "want", "need", "like", "default"]
        is_question = "?" in msg.message or msg.message.strip().lower().startswith(("what", "how", "why", "where", "when", "who", "can you", "do you"))
        should_save = any(t in user_msg_lower for t in memory_triggers) and len(msg.message) > 10 and not is_question
        if should_save:
            mem_data = json.dumps({
                "content": msg.message[:200],
                "category": "preference",
                "scope": "builder",
                "confidence": "inferred",
                "source": "chat",
                "timestamp": datetime.now().isoformat()
            })
            # Use asyncpg directly to avoid transaction issues
            try:
                import asyncpg
                conn = await asyncpg.connect(
                    host="127.0.0.1", port=5432,
                    database="evolvixos", user="evolvixos", password="evolvixos"
                )
                await conn.execute(
                    "INSERT INTO entity_platformmemory (content, category, scope, confidence, source, timestamp, created_date, updated_date) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())",
                    msg.message[:200], "preference", "builder", "inferred", "chat", datetime.now().isoformat()
                )
                await conn.close()
                print(f"Memory saved: {msg.message[:40]}")
            except Exception as sync_err:
                print(f"Memory save failed: {sync_err}")
    except Exception as mem_err:
        print(f"Memory save failed: {mem_err}")

    # Try to parse AI response as JSON action
    try:
        # Handle plugin action
        if '"action": "plugin"' in ai_response or '"action":"plugin"' in ai_response:
            json_start = ai_response.find("{")
            if json_start >= 0:
                json_str = ai_response[json_start:]
                brace_count = 0
                end_idx = 0
                for i, c in enumerate(json_str):
                    if c == "{": brace_count += 1
                    elif c == "}": brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
                plugin_action = json.loads(json_str[:end_idx])
                if plugin_action.get("action") == "plugin":
                    plugin_id = plugin_action.get("plugin", "")
                    plugin_params = plugin_action.get("params", {})
                    plugin_result = await PluginRegistry.execute_plugin(plugin_id, plugin_params, db)
                    return {
                        "message": f"Plugin '{plugin_id}' executed. Result: {json.dumps(plugin_result.get('result', plugin_result), indent=2)[:1000]}",
                        "action": "plugin",
                        "plugin": plugin_id,
                        "result": plugin_result,
                    }
        
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
            entity_name = action["name"]
            # Check existence first for a friendly response instead of raising
            existing = await EntityManager.get_entity(db, entity_name)
            if existing:
                return {
                    "action": "create_entity",
                    "already_existed": True,
                    "message": f"You already have a '{entity_name}' entity set up — no need to create it again. Want me to add fields to it, or build something else?"
                }
            result = await EntityManager.create_entity(db, entity_name, action["schema"])
            fields = ", ".join(action["schema"].get("properties", {}).keys())
            return {"action": "create_entity", "result": result, "message": f"Created the '{entity_name}' entity with fields: {fields}. You can start adding records to it now."}
        elif action_type == "list_entities":
            entities = await EntityManager.list_entities(db)
            return {"action": "list_entities", "entities": entities}
        elif action_type == "create_function":
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
            return {"action": "chat", "message": action.get("message", "How can I help you build today?")}
        else:
            return {"action": "unknown", "message": "Got that — but I'm not sure what to build yet. Could you tell me a bit more?"}
    except ValueError as e:
        # Known/expected validation errors — show the message cleanly, never raw JSON
        return {"action": action_type, "error": str(e), "message": str(e)}
    except Exception as e:
        return {"action": action_type, "error": str(e), "message": "Something went wrong on my end while doing that — mind trying again?"}


# ─── Startup ───
@app.on_event("startup")
async def startup():
    await init_db()
    print("EvolvixOS Platform API started on port 8080")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
