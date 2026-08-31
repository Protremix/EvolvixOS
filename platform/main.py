"""
EvolvixOS Platform API — Self-Hosted platform layer.
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
from awesome_routes import router as awesome_router
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, async_session
from entities.manager import EntityManager
from entities.crud import EntityCRUD as EnhancedCRUD
from templates import get_template_list, get_template, instantiate_template
from auth.middleware import optional_auth, require_auth, require_admin, get_user_from_token
JWT_SECRET = os.environ.get('JWT_SECRET', 'evolvixos-platform-secret-2026')
from routing_bridge import unified_chat
import sqlite3 as sqlite3_billing


# --- Self-Hosted upgrades (Aug 31 2026) ---
from sandbox_executor import SandboxedExecutor
from cncf_workflow_engine import CNCFWorkflowEngine, JQExpression
from signed_urls import SignedURLManager, FileStorageManager
from websocket_manager import ws_manager, DeclarativeRLS
from fastapi import WebSocket, WebSocketDisconnect

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
    description="Self-Hosted entity system, backend functions, workflows, and AI builder.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.include_router(awesome_router)

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
    app_id: Optional[int] = Field(None, description="App ID to scope entity to")

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

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "EvolvixOS Platform API", "version": "1.0.0"}


# ─── Entity Routes ───


@app.delete("/api/functions/{name}")
async def delete_function(name: str, request: Request = None, db=Depends(get_db)):
    """Delete a deployed function — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        # Delete from DB (asyncpg)
        result = await db.execute(text("DELETE FROM platform_functions WHERE name = :name"), {"name": name})
        await db.commit()
        if "DELETE 0" in str(result):
            raise ValueError(f"Function '{name}' not found")
        # Also delete from filesystem if exists
        import os
        fn_path = f"/opt/evolvixos/platform/functions/{name}.py"
        if os.path.exists(fn_path):
            os.remove(fn_path)
        return {"ok": True, "deleted": name}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/entities")
async def list_entities(db=Depends(get_db), request: Request = None, app_id: int = None):
    """List all entity schemas — optionally scoped to an app. Requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        entities = await EntityManager.list_entities(db, app_id=app_id)
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/entities")
async def create_entity(entity: EntityCreate, db=Depends(get_db), request: Request = None):
    """Create a new entity — requires auth. Optionally scoped to an app."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        result = await EntityManager.create_entity(db, entity.name, entity.schema, created_by=user.get("user_id") if user else None, app_id=entity.app_id)
        return result
    except ValueError as e:
        await db.rollback()
        raise HTTPException(400, str(e))
    except Exception as e:
        await db.rollback()
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
    """Delete entity and all its records — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    # Cascade delete records first
    await db.execute(text(f"DELETE FROM entity_{name.lower()}"))
    await db.commit()
    try:
        return await EntityManager.delete_entity(db, name)
    except ValueError as e:
        raise HTTPException(400, str(e))

# ─── Entity Relations ───
@app.get("/api/entities/{name}/relations")
async def get_entity_relations(name: str, db=Depends(get_db), request: Request = None):
    """Get all relation fields for an entity."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        relations = await EntityManager.get_relations(db, name)
        return {"relations": relations}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/entities/{name}/records/{record_id}/expanded")
async def get_record_expanded(name: str, record_id: int, db=Depends(get_db), request: Request = None):
    """Get a record with all relation fields expanded."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        record = await EntityManager.fetch_with_relations(db, name, record_id)
        if not record:
            raise HTTPException(404, f"Record {record_id} not found in {name}")
        return record
    except Exception as e:
        raise HTTPException(500, str(e))



# ─── Entity Records (CRUD) ───
@app.get("/api/entities/{name}/records")
async def list_records(
    name: str,
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    sort: Optional[str] = None,
    expand: bool = Query(False, description="Expand relation fields with related data"),
    request: Request = None,
    db=Depends(get_db)
):
    """List entity records with pagination, sorting, and optional relation expansion."""
    try:
        # Parse query params into filters (exclude built-in params)
        built_in = {"limit", "skip", "sort", "expand"}
        filters = {}
        if request and request.query_params:
            for key, value in request.query_params.items():
                if key not in built_in:
                    filters[key] = value
        user = get_user_from_token(request) if request else None
        user_id = user.get("user_id") if user else None
        result = await EnhancedCRUD.list_records(db, name, limit=limit, skip=skip, filters=filters, sort=sort, user_id=user_id)
        if expand:
            # Expand relations for each record
            entity = await EntityManager.get_entity(db, name)
            if entity:
                expanded = []
                for record in result.get("records", []):
                    for fn, fd in entity["schema"].get("properties", {}).items():
                        if fd.get("type") == "relation" and record.get(fn):
                            target = fd["relation"]["target"]
                            display = fd.get("relation", {}).get("display", "name")
                            try:
                                rel_res = await db.execute(text(f'SELECT * FROM entity_{target.lower()} WHERE id = :id'), {"id": record[fn]})
                                rel_row = rel_res.fetchone()
                                if rel_row:
                                    rel_cols = rel_res.keys() if hasattr(rel_res, 'keys') else [d[0] for d in rel_res.cursor.description]
                                    rel_rec = {rel_cols[j]: (rel_row[j].isoformat() if isinstance(rel_row[j], datetime) else rel_row[j]) for j in range(len(rel_cols))}
                                    record[f"_rel_{fn}"] = rel_rec
                                    record[f"_rel_{fn}_label"] = rel_rec.get(display, f"#{record[fn]}")
                            except Exception:
                                pass
                    expanded.append(record)
                result["records"] = expanded
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

    # Execute function using sandboxed executor (Self-Hosted isolation)
    try:
        result = await SandboxedExecutor.execute(
            code=code,
            input_data=body,
            user_id=user_id,
            env_vars=env_vars,
            timeout=30,
            use_docker=False
        )
        if result.get("status") == "error":
            raise HTTPException(500, f"Function error: {result.get('error', 'Unknown error')}")
        if result.get("status") == "blocked":
            raise HTTPException(403, result.get("error", "Function blocked by security policy"))
        return result.get("result", result)
    except HTTPException:
        raise
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
    """List all AI agents — requires auth. User-isolated."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agents = await AgentManager.list_agents(db, user_id=user_id)
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
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    # Mask api_key for everyone, secrets for non-owners
    if agent.get("api_key"):
        agent["api_key"] = agent["api_key"][:8] + "..."
    user_id_str = str(user.get("user_id", user.get("id", "")))
    agent_creator = str(agent.get("created_by", ""))
    if user_id_str != agent_creator and user_id_str != "1" and user.get("role") != "admin":
        agent["agent_secrets"] = {k: "***" for k in (agent.get("agent_secrets") or {})}
    return agent

@app.put("/api/agents/{name}")
async def update_agent(name: str, updates: AgentUpdate, db=Depends(get_db), request: Request = None):
    """Update agent — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    user_id_str = str(user.get("user_id", user.get("id", "")))
    agent_creator = str(agent.get("created_by", ""))
    if user_id_str != agent_creator and user_id_str != "1" and user.get("role") != "admin":
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
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    user_id_str = str(user.get("user_id", user.get("id", "")))
    agent_creator = str(agent.get("created_by", ""))
    if user_id_str != agent_creator and user_id_str != "1" and user.get("role") != "admin":
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
        user_id = str(user.get("user_id", 0)) if user else None
        agent = await AgentManager.get_agent(db, name, user_id=user_id)
        agent_model = agent.get("model", "auto") if agent else "auto"
        credit_check = deduct_user_credits(int(user_id) if user_id else 0, agent_model)
        if not credit_check.get("ok"):
            raise HTTPException(402, credit_check.get("error", "Insufficient credits"))
    # Load chat history to give the agent conversation context
    chat_context = msg.context or {}
    try:
        hist_result = await db.execute(
            text("SELECT role, content FROM builder_chat_history WHERE user_id = :uid ORDER BY created_date DESC LIMIT 20"),
            {"uid": int(user_id) if user_id else 0}
        )
        hist_rows = list(reversed(hist_result.fetchall()))
        if hist_rows:
            chat_lines = []
            for hr in hist_rows:
                role = "User" if hr[0] == "user" else "Builder"
                chat_lines.append(f"{role}: {hr[1][:300]}")
            chat_context["system_context"] = "PREVIOUS CONVERSATION (most recent last):\n" + "\n".join(chat_lines)
    except Exception as hist_err:
        print(f"Chat history load for agent context failed: {hist_err}")

    try:
        result = await AgentManager.invoke_agent(db, name, msg.message, chat_context)

        # Save user message to chat history
        try:
            await db.execute(text(
                "INSERT INTO builder_chat_history (user_id, role, content, agent_name) VALUES (:uid, 'user', :msg, :agent)"
            ), {"uid": int(user_id) if user_id else 0, "msg": msg.message, "agent": name})
            await db.commit()
        except Exception as save_err:
            print(f"Chat history save (user) failed: {save_err}")

        # Save AI response to chat history
        try:
            ai_content = result.get("response", "")
            await db.execute(text(
                "INSERT INTO builder_chat_history (user_id, role, content, agent_name, tool_action, tool_result) VALUES (:uid, 'assistant', :msg, :agent, :action, :tresult)"
            ), {
                "uid": int(user_id) if user_id else 0,
                "msg": ai_content[:2000],
                "agent": name,
                "action": result.get("tool_action"),
                "tresult": json.dumps(result.get("tool_result")) if result.get("tool_result") else None
            })
            await db.commit()
        except Exception as save_err2:
            print(f"Chat history save (assistant) failed: {save_err2}")

        # Auto-generate app after entity creation
        if result.get("tool_action") == "create_entity" and result.get("tool_result") and not result["tool_result"].get("already_existed"):
            try:
                import sys as _sys
                _sys.path.insert(0, "/opt/evolvixos/platform")
                from app_generator import deploy_app
                
                all_ents = await EntityManager.list_entities(db)
                ents_with_schemas = []
                for e in (all_ents or []):
                    if e.get("name") not in ["ApiKey", "UsageLog", "Agent", "Wallet", "Transaction", "Block"]:
                        ents_with_schemas.append({"name": e["name"], "schema": e.get("schema", {})})
                
                if ents_with_schemas:
                    entity_name = result["tool_result"].get("name", "My App")
                    app_name = entity_name + " App"
                    gen_result = deploy_app(app_name, ents_with_schemas)
                    result["tool_action"] = "generate_app"
                    result["tool_result"] = {
                        "name": app_name,
                        "url": gen_result["url"],
                        "app_name": app_name,
                        "entities": [e["name"] for e in ents_with_schemas]
                    }
                    result["response"] = "Created the '" + entity_name + "' entity and generated your live app! You can see it in the preview panel on the right. Your app is live at https://evolvixos.com" + gen_result["url"]

                    # Save the app generation message too
                    try:
                        await db.execute(text(
                            "INSERT INTO builder_chat_history (user_id, role, content, agent_name, tool_action, tool_result) VALUES (:uid, 'assistant', :msg, :agent, :action, :tresult)"
                        ), {
                            "uid": int(user_id) if user_id else 0,
                            "msg": result["response"][:2000],
                            "agent": name,
                            "action": "generate_app",
                            "tresult": json.dumps(result["tool_result"])
                        })
                        await db.commit()
                    except Exception:
                        pass
            except Exception as gen_err:
                print(f"Auto-generate app failed: {gen_err}")

        return result
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/agents/{name}/clear-memory")
async def clear_agent_memory(name: str, db=Depends(get_db)):
    """Clear agent conversation memory."""
    return await AgentManager.clear_memory(db, name)


# ─── Long-Term Memory ───

class LongMemoryCreate(BaseModel):
    content: str = Field(..., description="The memory content to persist")
    category: str = Field("general", description="Category for grouping memories")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    importance: int = Field(5, description="Importance 1-10")

@app.get("/api/agents/{name}/long-memory")
async def list_long_memory(name: str, db=Depends(get_db), request: Request = None, category: str = None, limit: int = 50):
    """List long-term memories for an agent — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")

    query = "SELECT id, agent_name, category, content, metadata, importance, created_date, updated_date FROM agent_long_memory WHERE agent_name = :name"
    params = {"name": name}
    if category:
        query += " AND category = :cat"
        params["cat"] = category
    query += " ORDER BY importance DESC, created_date DESC LIMIT :lim"
    params["lim"] = min(limit, 200)

    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return {"memories": [
        {
            "id": r[0], "agent": r[1], "category": r[2],
            "content": r[3], "metadata": r[4] if isinstance(r[4], dict) else json.loads(r[4] or "{}"),
            "importance": r[5], "created_date": r[6].isoformat() if r[6] else None,
            "updated_date": r[7].isoformat() if r[7] else None
        } for r in rows
    ]}

@app.post("/api/agents/{name}/long-memory")
async def create_long_memory(name: str, mem: LongMemoryCreate, db=Depends(get_db), request: Request = None):
    """Save a long-term memory for an agent — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")

    result = await db.execute(text(
        "INSERT INTO agent_long_memory (agent_name, category, content, metadata, importance, created_by) "
        "VALUES (:name, :cat, :content, :meta, :imp, :uid) RETURNING id, created_date"
    ), {
        "name": name, "cat": mem.category, "content": mem.content,
        "meta": json.dumps(mem.metadata or {}), "imp": mem.importance, "uid": user_id
    })
    row = result.fetchone()
    await db.commit()
    return {"id": row[0], "created_date": row[1].isoformat() if row[1] else None, "status": "saved"}

@app.put("/api/agents/{name}/long-memory/{mem_id}")
async def update_long_memory(name: str, mem_id: int, mem: LongMemoryCreate, db=Depends(get_db), request: Request = None):
    """Update a long-term memory — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")

    result = await db.execute(text(
        "UPDATE agent_long_memory SET content = :content, category = :cat, "
        "metadata = :meta, importance = :imp, updated_date = NOW() "
        "WHERE id = :mid AND agent_name = :name RETURNING id"
    ), {
        "mid": mem_id, "name": name, "content": mem.content,
        "cat": mem.category, "meta": json.dumps(mem.metadata or {}), "imp": mem.importance
    })
    if not result.fetchone():
        raise HTTPException(404, "Memory not found")
    await db.commit()
    return {"id": mem_id, "status": "updated"}

@app.delete("/api/agents/{name}/long-memory/{mem_id}")
async def delete_long_memory(name: str, mem_id: int, db=Depends(get_db), request: Request = None):
    """Delete a long-term memory — requires auth + ownership."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")

    result = await db.execute(text(
        "DELETE FROM agent_long_memory WHERE id = :mid AND agent_name = :name RETURNING id"
    ), {"mid": mem_id, "name": name})
    if not result.fetchone():
        raise HTTPException(404, "Memory not found")
    await db.commit()
    return {"id": mem_id, "status": "deleted"}


# ─── External Agent API (for integration with other platforms) ───

class ExternalChatRequest(BaseModel):
    message: str = Field(..., description="Message to send to the agent")
    context: Optional[str] = Field(None, description="Additional context")
    save_memory: bool = Field(True, description="Whether to save this interaction to long-term memory")

@app.post("/api/v1/agents/{name}/chat")
async def external_agent_chat(name: str, req: ExternalChatRequest, db=Depends(get_db), request: Request = None):
    """
    External API endpoint for agents — authenticates via agent API key.
    Allows other platforms to call EvolvixOS agents programmatically.

    Authentication: Bearer <agent_api_key> in Authorization header.
    """
    auth_header = request.headers.get("Authorization", "") if request else ""
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token. Use the agent API key.")

    api_key = auth_header[7:]

    # Find agent by name and verify API key
    result = await db.execute(text(
        "SELECT name, system_prompt, model, memory_enabled, api_key, created_by FROM platform_agents WHERE name = :name AND api_key = :key AND status = 'active'"
    ), {"name": name, "key": api_key})
    row = result.fetchone()
    if not row:
        raise HTTPException(401, "Invalid agent name or API key")

    agent_name = row[0]
    agent_model = row[2]
    memory_enabled = row[3]
    owner_id = row[5]

    # Deduct credits from the agent owner
    if owner_id and owner_id != "platform":
        credit_check = deduct_user_credits(int(owner_id), agent_model or "auto")
        if not credit_check.get("ok"):
            raise HTTPException(402, "Agent owner has insufficient credits")

    # Invoke the agent
    try:
        result = await AgentManager.invoke_agent(db, name, req.message, req.context)
    except ValueError as e:
        raise HTTPException(400, str(e))

    response_text = result.get("response", "")

    # Save to long-term memory if requested
    if req.save_memory and memory_enabled:
        await db.execute(text(
            "INSERT INTO agent_long_memory (agent_name, category, content, metadata, importance) "
            "VALUES (:name, :cat, :content, :meta, :imp)"
        ), {
            "name": name,
            "cat": "conversation",
            "content": "Q: " + req.message + "\nA: " + response_text,
            "meta": json.dumps({"source": "external_api", "model": agent_model}),
            "imp": 5
        })
        await db.commit()

    return {
        "agent": agent_name,
        "response": response_text,
        "model": agent_model,
        "memory_saved": req.save_memory and memory_enabled,
        "credits": {"owner": owner_id, "model": agent_model},
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/agents/{name}/memory")
async def external_agent_memory(name: str, db=Depends(get_db), request: Request = None, category: str = None, limit: int = 50):
    """
    External API — retrieve agent long-term memories via API key.
    """
    auth_header = request.headers.get("Authorization", "") if request else ""
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token. Use the agent API key.")

    api_key = auth_header[7:]
    result = await db.execute(text(
        "SELECT name FROM platform_agents WHERE name = :name AND api_key = :key AND status = 'active'"
    ), {"name": name, "key": api_key})
    if not result.fetchone():
        raise HTTPException(401, "Invalid agent name or API key")

    query = "SELECT id, category, content, metadata, importance, created_date FROM agent_long_memory WHERE agent_name = :name"
    params = {"name": name}
    if category:
        query += " AND category = :cat"
        params["cat"] = category
    query += " ORDER BY importance DESC, created_date DESC LIMIT :lim"
    params["lim"] = min(limit, 200)

    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return {
        "agent": name,
        "memories": [
            {
                "id": r[0], "category": r[1], "content": r[2],
                "metadata": r[3] if isinstance(r[3], dict) else json.loads(r[3] or "{}"),
                "importance": r[4], "created_date": r[5].isoformat() if r[5] else None
            } for r in rows
        ]
    }


@app.post("/api/v1/agents/{name}/memory")
async def external_agent_save_memory(name: str, mem: LongMemoryCreate, db=Depends(get_db), request: Request = None):
    """Save a long-term memory via external API — uses agent API key."""
    auth = request.headers.get("Authorization", "") if request else ""
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "API key required")
    api_key = auth[7:]
    result = await db.execute(text("SELECT name FROM platform_agents WHERE name = :name AND api_key = :key"), {"name": name, "key": api_key})
    row = result.fetchone()
    if not row:
        raise HTTPException(401, "Invalid agent or API key")
    try:
        mem_row = await db.execute(text(
            "INSERT INTO agent_long_memory (agent_name, content, category, metadata, importance, created_date) VALUES (:name, :content, :category, :meta, :imp, NOW()) RETURNING id"
        ), {"name": name, "content": mem.content, "category": mem.category, "meta": json.dumps(mem.metadata) if mem.metadata else None, "imp": mem.importance})
        await db.commit()
        mem_id = mem_row.fetchone()[0]
        return {"ok": True, "id": mem_id, "agent": name}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/v1/agents/{name}/info")
async def external_agent_info(name: str, db=Depends(get_db), request: Request = None):
    """External API — get agent info (model, tools, memory_enabled) via API key."""
    auth_header = request.headers.get("Authorization", "") if request else ""
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token. Use the agent API key.")

    api_key = auth_header[7:]
    result = await db.execute(text(
        "SELECT name, model, tools, memory_enabled, status, created_date FROM platform_agents WHERE name = :name AND api_key = :key"
    ), {"name": name, "key": api_key})
    row = result.fetchone()
    if not row:
        raise HTTPException(401, "Invalid agent name or API key")

    return {
        "name": row[0],
        "model": row[1],
        "tools": row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]"),
        "memory_enabled": row[3],
        "status": row[4],
        "created_date": row[5].isoformat() if row[5] else None
    }



# ─── File Storage ───
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/opt/evolvixos/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...), db=Depends(get_db), request: Request = None):
    """Upload a file (public or private) with Self-Hosted CDN + signed URL support."""
    user = get_user_from_token(request) if request else None
    user_id = user.get("user_id") if user else None
    is_private = request.query_params.get("private", "false").lower() == "true" if request else False

    content_bytes = await file.read()
    result = await FileStorageManager.upload(db, file.filename, content_bytes, file.content_type, is_private, user_id)

    if is_private:
        signed_url = SignedURLManager.generate_signed_url(result["file_id"], "", expires_in=300)
        result["signed_url"] = signed_url

    return result

@app.post("/api/files/{file_id}/signed-url")
async def create_signed_url_endpoint(file_id: str, expires_in: int = 300, db=Depends(get_db)):
    """Create a time-limited signed URL for a private file."""
    url = await SignedURLManager.create_signed_url_from_db(db, file_id, expires_in)
    if not url:
        raise HTTPException(404, "File not found")
    return {"signed_url": url, "expires_in": expires_in}

@app.get("/api/files/{file_id}")
async def get_file(file_id: str, token: str = None, db=Depends(get_db)):
    """Download a file. Private files require a signed URL token."""
    result = await FileStorageManager.download(db, file_id, token)
    if not result:
        raise HTTPException(404, "File not found")
    if "error" in result:
        raise HTTPException(result.get("status", 403), result["error"])
    with open(result["file_path"], "rb") as fp:
        return StreamingResponse(
            iter([fp.read()]),
            media_type=result.get("content_type", "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )

@app.get("/api/files/{file_id}/signed")
async def get_file_signed(file_id: str, token: str, db=Depends(get_db)):
    """Download a private file using a signed URL token."""
    return await get_file(file_id, token=token, db=db)


# --- WebSocket Real-Time (Self-Hosted) ---


# ─── Vercel Integration ───
from vercel_integration import connect_vercel, list_vercel_projects, list_vercel_deployments, deploy_to_vercel, get_vercel_deployment_status

@app.post("/api/vercel/connect")
async def api_vercel_connect(req: Request):
    """Connect a Vercel account using an access token."""
    user = require_auth(req)
    body = await req.json()
    token = body.get("token", "").strip()
    if not token:
        raise HTTPException(400, "Vercel access token required")
    result = await connect_vercel(token)
    if result["connected"]:
        # Store the token in secrets
        await secrets_store(user["user_id"], "vercel_token", token)
        return {"connected": True, "user": {"username": result["username"], "name": result["name"], "email": result["email"]}}
    raise HTTPException(401, result.get("error", "Connection failed"))

@app.get("/api/vercel/status")
async def api_vercel_status(req: Request):
    """Check if Vercel is connected."""
    user = require_auth(req)
    token = await secrets_get(user["user_id"], "vercel_token")
    if not token:
        return {"connected": False}
    result = await connect_vercel(token)
    return result

@app.get("/api/vercel/projects")
async def api_vercel_projects(req: Request):
    """List Vercel projects."""
    user = require_auth(req)
    token = await secrets_get(user["user_id"], "vercel_token")
    if not token:
        raise HTTPException(401, "Vercel not connected")
    return await list_vercel_projects(token)

@app.get("/api/vercel/deployments")
async def api_vercel_deployments(req: Request, limit: int = 10):
    """List recent Vercel deployments."""
    user = require_auth(req)
    token = await secrets_get(user["user_id"], "vercel_token")
    if not token:
        raise HTTPException(401, "Vercel not connected")
    return await list_vercel_deployments(token, limit=limit)

@app.post("/api/vercel/deploy")
async def api_vercel_deploy(req: Request):
    """Deploy an app to Vercel."""
    user = require_auth(req)
    token = await secrets_get(user["user_id"], "vercel_token")
    if not token:
        raise HTTPException(401, "Vercel not connected")
    body = await req.json()
    project_name = body.get("project_name", f"evolvixos-{int(time.time())}")
    files = body.get("files", [])
    framework = body.get("framework")
    result = await deploy_to_vercel(token, project_name, files, framework)
    return result

@app.delete("/api/vercel/disconnect")
async def api_vercel_disconnect(req: Request):
    """Disconnect Vercel."""
    user = require_auth(req)
    await secrets_delete(user["user_id"], "vercel_token")
    return {"disconnected": True}

# ─── Secret helpers (simple encrypted store) ───
async def secrets_store(user_id, key, value):
    """Store a secret in the secrets table (scope=user, scope_id=user_id, name=key)."""
    async with db.acquire() as conn:
        # Upsert: if (scope, scope_id, name) exists, update encrypted_value
        existing = await conn.fetchrow(
            "SELECT id FROM secrets WHERE scope = 'user' AND scope_id = $1 AND name = $2",
            str(user_id), key
        )
        if existing:
            await conn.execute(
                "UPDATE secrets SET encrypted_value = $1, updated_at = NOW() WHERE id = $2",
                value, existing["id"]
            )
        else:
            await conn.execute(
                "INSERT INTO secrets (scope, scope_id, name, encrypted_value, created_at, updated_at) "
                "VALUES ('user', $1, $2, $3, NOW(), NOW())",
                str(user_id), key, value
            )

async def secrets_get(user_id, key):
    """Get a secret from the secrets table."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT encrypted_value FROM secrets WHERE scope = 'user' AND scope_id = $1 AND name = $2",
            str(user_id), key
        )
        return row["encrypted_value"] if row else None

async def secrets_delete(user_id, key):
    """Delete a secret from the secrets table."""
    async with db.acquire() as conn:
        await conn.execute(
            "DELETE FROM secrets WHERE scope = 'user' AND scope_id = $1 AND name = $2",
            str(user_id), key
        )


# ─── Connected Apps Integrations ───

# ─── Connected Apps Integrations ───
from integrations_backend import (
    github_verify_token, github_list_repos, github_create_repo, github_push_file,
    supabase_verify, supabase_list_tables,
    slack_verify_token, slack_list_channels, slack_post_message,
    gmail_send
)
from vercel_integration import connect_vercel, list_vercel_projects, list_vercel_deployments, deploy_to_vercel

# ─── Secret helpers (SQLAlchemy) ───
async def secrets_store(user_id, key, value):
    async with async_session() as session:
        existing = await session.execute(
            text("SELECT id FROM secrets WHERE scope = 'user' AND scope_id = :uid AND name = :key"),
            {"uid": str(user_id), "key": key}
        )
        row = existing.fetchone()
        if row:
            await session.execute(
                text("UPDATE secrets SET encrypted_value = :val, updated_at = NOW() WHERE id = :id"),
                {"val": value, "id": row[0]}
            )
        else:
            await session.execute(
                text("INSERT INTO secrets (scope, scope_id, name, encrypted_value, created_at, updated_at) VALUES ('user', :uid, :key, :val, NOW(), NOW())"),
                {"uid": str(user_id), "key": key, "val": value}
            )
        await session.commit()

async def secrets_get(user_id, key):
    async with async_session() as session:
        result = await session.execute(
            text("SELECT encrypted_value FROM secrets WHERE scope = 'user' AND scope_id = :uid AND name = :key"),
            {"uid": str(user_id), "key": key}
        )
        row = result.fetchone()
        return row[0] if row else None

async def secrets_delete(user_id, key):
    async with async_session() as session:
        await session.execute(
            text("DELETE FROM secrets WHERE scope = 'user' AND scope_id = :uid AND name = :key"),
            {"uid": str(user_id), "key": key}
        )
        await session.commit()

@app.post("/api/integrations/{service}/connect")
async def api_connect_integration(service: str, req: Request):
    user = require_auth(req)
    body = await req.json()
    token = body.get("token", "").strip()
    extra = body.get("extra", {})
    if not token:
        raise HTTPException(400, "Token/key required")
    result = {"connected": False}
    if service == "vercel":
        result = await connect_vercel(token)
    elif service == "github":
        result = await github_verify_token(token)
    elif service == "supabase":
        result = await supabase_verify(extra.get("url", ""), token)
    elif service == "slack":
        result = await slack_verify_token(token)
    elif service == "gmail":
        result = {"connected": True, "email": extra.get("email", "")}
    else:
        raise HTTPException(400, f"Unknown service: {service}")
    if result.get("connected"):
        await secrets_store(user["user_id"], f"{service}_token", token)
        if service == "supabase":
            await secrets_store(user["user_id"], "supabase_url", extra.get("url", ""))
        if service == "gmail":
            await secrets_store(user["user_id"], "gmail_email", extra.get("email", ""))
    return result

@app.get("/api/integrations/{service}/status")
async def api_integration_status(service: str, req: Request):
    user = require_auth(req)
    token = await secrets_get(user["user_id"], f"{service}_token")
    if not token:
        return {"connected": False}
    if service == "vercel":
        return await connect_vercel(token)
    elif service == "github":
        return await github_verify_token(token)
    elif service == "supabase":
        url = await secrets_get(user["user_id"], "supabase_url")
        return await supabase_verify(url, token) if url else {"connected": False}
    elif service == "slack":
        return await slack_verify_token(token)
    elif service == "gmail":
        email = await secrets_get(user["user_id"], "gmail_email")
        return {"connected": True, "email": email}
    return {"connected": False}

@app.delete("/api/integrations/{service}/disconnect")
async def api_disconnect_integration(service: str, req: Request):
    user = require_auth(req)
    await secrets_delete(user["user_id"], f"{service}_token")
    if service == "supabase":
        await secrets_delete(user["user_id"], "supabase_url")
    if service == "gmail":
        await secrets_delete(user["user_id"], "gmail_email")
    return {"disconnected": True}

@app.get("/api/integrations/{service}/data")
async def api_integration_data(service: str, req: Request):
    user = require_auth(req)
    token = await secrets_get(user["user_id"], f"{service}_token")
    if not token:
        raise HTTPException(401, f"{service} not connected")
    if service == "vercel":
        return await list_vercel_projects(token)
    elif service == "github":
        return await github_list_repos(token)
    elif service == "supabase":
        url = await secrets_get(user["user_id"], "supabase_url")
        return await supabase_list_tables(url, token) if url else []
    elif service == "slack":
        return await slack_list_channels(token)
    return []

@app.post("/api/integrations/{service}/action")
async def api_integration_action(service: str, req: Request):
    user = require_auth(req)
    token = await secrets_get(user["user_id"], f"{service}_token")
    if not token:
        raise HTTPException(401, f"{service} not connected")
    body = await req.json()
    action = body.get("action")
    if service == "github":
        if action == "create_repo":
            return await github_create_repo(token, body.get("name"), body.get("private", True), body.get("description", ""))
        elif action == "push_file":
            return await github_push_file(token, body.get("owner"), body.get("repo"), body.get("path"), body.get("content"))
    elif service == "vercel":
        if action == "deploy":
            return await deploy_to_vercel(token, body.get("project_name"), body.get("files", []), body.get("framework"))
    elif service == "slack":
        if action == "post_message":
            return await slack_post_message(token, body.get("channel"), body.get("text"))
    elif service == "gmail":
        if action == "send_email":
            sender = await secrets_get(user["user_id"], "gmail_email")
            return await gmail_send(body.get("to"), body.get("subject"), body.get("body"), token, sender)
    raise HTTPException(400, f"Unknown action: {action}")

# ─── Workflow Execution ───
@app.post("/api/workflows/execute")
async def api_execute_workflow(req: Request):
    user = require_auth(req)
    body = await req.json()
    template = body.get("template", {})
    steps = template.get("steps", [])
    results = []
    for step in steps:
        step_result = {"step": step.get("name", ""), "status": "pending", "output": ""}
        step_type = step.get("type", "agent")
        try:
            if step_type == "agent":
                agent_name = step.get("agent", "Builder")
                message = step.get("prompt", "")
                from agents.manager import AgentManager
                mgr = AgentManager()
                result = await mgr.invoke_agent(agent_name, message, user)
                step_result["status"] = "completed"
                step_result["output"] = result.get("response", "")[:200] if isinstance(result, dict) else str(result)[:200]
            elif step_type == "code":
                step_result["status"] = "completed"
                step_result["output"] = "Code step acknowledged"
            elif step_type == "wait":
                import asyncio
                await asyncio.sleep(step.get("seconds", 1))
                step_result["status"] = "completed"
                step_result["output"] = f"Waited {step.get('seconds', 1)}s"
            else:
                step_result["status"] = "skipped"
                step_result["output"] = f"Unknown type: {step_type}"
        except Exception as e:
            step_result["status"] = "failed"
            step_result["output"] = str(e)[:200]
        results.append(step_result)
    return {"executed": True, "results": results, "template": template.get("name", "")}

# ─── Multi-Project Management ───
@app.get("/api/projects")
async def api_list_projects(req: Request, db = Depends(get_db)):
    user = require_auth(req)
    result = await db.execute(
        text("SELECT id, name, description, created_at FROM projects WHERE user_id = :uid ORDER BY created_at DESC"),
        {"uid": str(user["user_id"])}
    )
    rows = result.fetchall()
    return [{"id": str(r[0]), "name": r[1], "description": r[2] or "", "created_at": str(r[3])} for r in rows]

@app.post("/api/projects")
async def api_create_project(req: Request, db = Depends(get_db)):
    user = require_auth(req)
    body = await req.json()
    name = body.get("name", "Untitled Project")
    description = body.get("description", "")
    result = await db.execute(
        text("INSERT INTO projects (user_id, name, description, created_at) VALUES (:uid, :name, :desc, NOW()) RETURNING id, name"),
        {"uid": str(user["user_id"]), "name": name, "desc": description}
    )
    await db.commit()
    row = result.fetchone()
    return {"id": str(row[0]), "name": row[1], "created": True}


@app.websocket("/ws/entities/{entity_name}")
async def ws_entity_subscriptions(websocket: WebSocket, entity_name: str):
    """Subscribe to entity change events in real-time."""
    connection_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, connection_id)
    ws_manager.subscribe_entity(entity_name, connection_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(connection_id)

@app.websocket("/ws/chat/{conversation_id}")
async def ws_chat_stream(websocket: WebSocket, conversation_id: str):
    """Subscribe to agent chat streaming for a conversation."""
    connection_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, connection_id)
    ws_manager.subscribe_chat(conversation_id, connection_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(connection_id)


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

# === TOOLS API ===
class BrowserCmd(BaseModel):
    action: str = "navigate"
    url: str = ""

@app.post("/api/tools/browser")
async def browser_tool(cmd: BrowserCmd, request: Request):
    user = get_user_from_token(request)
    if not user: raise HTTPException(401, "Auth required")
    import urllib.request, re as _re
    if cmd.action == "extract":
        req = urllib.request.Request(cmd.url, headers={"User-Agent": "EvolvixOS/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8", errors="replace")
        title_m = _re.search(r"<title>(.*?)</title>", html, _re.IGNORECASE | _re.DOTALL)
        title = title_m.group(1).strip() if title_m else ""
        text = _re.sub(r"<script[^>]*>.*?</script>", "", html, flags=_re.DOTALL)
        text = _re.sub(r"<style[^>]*>.*?</style>", "", text, flags=_re.DOTALL)
        text = _re.sub(r"<[^>]+>", " ", text)
        text = _re.sub(r"\s+", " ", text).strip()
        return {"status": "ok", "url": cmd.url, "title": title, "text": text[:5000]}
    req = urllib.request.Request(cmd.url, headers={"User-Agent": "EvolvixOS/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8", errors="replace")[:10000]
    return {"status": "ok", "url": cmd.url, "preview": html[:500]}

class CodeRunReq(BaseModel):
    code: str
    language: str = "python"

@app.post("/api/tools/run")
async def run_code(req: CodeRunReq, request: Request):
    import subprocess, tempfile, os
    user = get_user_from_token(request)
    if not user: raise HTTPException(401, "Auth required")
    blocked = ["rm -rf /", "shutdown", "reboot"]
    for b in blocked:
        if b in req.code: return {"error": "Blocked: " + b}
    suffix = ".sh" if req.language == "bash" else ".py"
    cmd_list = ["bash"] if req.language == "bash" else ["python3"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
        f.write(req.code); f.flush(); tmpfile = f.name
    try:
        r = subprocess.run(cmd_list + [tmpfile], capture_output=True, text=True, timeout=30,
            env={"PATH": "/usr/bin:/usr/local/bin", "HOME": "/tmp", "PYTHONPATH": "/opt/evolvixos/platform"})
        return {"stdout": r.stdout[:5000], "stderr": r.stderr[:2000], "exit_code": r.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "Timed out (30s)"}
    finally:
        os.unlink(tmpfile)

class GrepReq(BaseModel):
    pattern: str
    path: str = "/opt/evolvixos"
    include: str = "*.py"

@app.post("/api/tools/grep")
async def file_grep(req: GrepReq, request: Request):
    import subprocess
    user = get_user_from_token(request)
    if not user: raise HTTPException(401, "Auth required")
    safe = ["/opt/evolvixos", "/tmp", "/var/log/evolvixos"]
    if not any(req.path.startswith(p) for p in safe): return {"error": "Path not allowed"}
    r = subprocess.run(["grep", "-rn", "--include=" + req.include, req.pattern, req.path],
        capture_output=True, text=True, timeout=15)
    lines = r.stdout.split("\n")[:100] if r.stdout else []
    return {"matches": lines, "count": len(lines)}

class FileReq(BaseModel):
    action: str
    path: str
    content: str = ""

@app.post("/api/tools/files")
async def file_ops(req: FileReq, request: Request):
    import os
    user = get_user_from_token(request)
    if not user: raise HTTPException(401, "Auth required")
    safe = ["/opt/evolvixos", "/tmp", "/var/log/evolvixos"]
    if not any(req.path.startswith(p) for p in safe): return {"error": "Path not allowed"}
    if req.action == "read":
        with open(req.path) as f: return {"path": req.path, "content": f.read()[:10000], "size": os.path.getsize(req.path)}
    elif req.action == "write":
        os.makedirs(os.path.dirname(req.path), exist_ok=True)
        with open(req.path, "w") as f: f.write(req.content)
        return {"path": req.path, "written": True}
    elif req.action == "list":
        entries = []
        for e in os.listdir(req.path):
            full = os.path.join(req.path, e)
            entries.append({"name": e, "type": "dir" if os.path.isdir(full) else "file", "size": os.path.getsize(full) if os.path.isfile(full) else 0})
        return {"path": req.path, "entries": entries}
    elif req.action == "delete":
        if os.path.isfile(req.path): os.unlink(req.path); return {"deleted": req.path}
        return {"error": "Not a file"}
    return {"error": "Unknown action"}

class SubAgentReq(BaseModel):
    task: str
    context: str = ""

@app.post("/api/tools/subagent")
async def delegate_subagent(req: SubAgentReq, request: Request):
    user = get_user_from_token(request)
    if not user: raise HTTPException(401, "Auth required")
    sys_prompt = "You are an EvolvixOS sub-agent. Context: " + req.context + ". Task: " + req.task
    msgs = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": req.task}]
    result = await unified_chat(msgs, model="auto", temperature=0.3, max_tokens=2000, prefer_cloud=True)
    return {"result": result.get("content", ""), "model": result.get("model", "auto"), "provider": result.get("provider", "auto")}


# ─── Chat History ───
@app.get("/api/chat/history")
async def get_chat_history(request: Request, db=Depends(get_db)):
    """Load all chat history for the current user."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    user_id = int(user.get("user_id", 0))
    result = await db.execute(
        text("SELECT id, role, content, tool_action, tool_result, agent_name, created_date FROM builder_chat_history WHERE user_id = :uid ORDER BY created_date ASC"),
        {"uid": user_id}
    )
    rows = result.fetchall()
    messages = []
    for r in rows:
        msg = {"id": r[0], "role": r[1], "content": r[2], "agent": r[5] or "Builder", "time": str(r[6]) if r[6] else None}
        if r[3]:
            msg["tool_action"] = r[3]
        if r[4]:
            try:
                msg["tool_result"] = json.loads(r[4]) if isinstance(r[4], str) else r[4]
            except:
                msg["tool_result"] = {"raw": str(r[4])[:200]}
        messages.append(msg)
    return {"messages": messages}

@app.delete("/api/chat/history")
async def clear_chat_history(request: Request, db=Depends(get_db)):
    """Clear all chat history for the current user."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    user_id = int(user.get("user_id", 0))
    await db.execute(
        text("DELETE FROM builder_chat_history WHERE user_id = :uid"),
        {"uid": user_id}
    )
    await db.commit()
    return {"status": "cleared"}


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
    # Load chat history for context (last 20 messages)
    chat_history_text = ""
    try:
        history_result = await db.execute(
            text("SELECT role, content FROM builder_chat_history WHERE user_id = :uid ORDER BY created_date DESC LIMIT 20"),
            {"uid": int(user_id) if user_id else 0}
        )
        history_rows = history_result.fetchall()
        if history_rows:
            history_rows = list(reversed(history_rows))
            chat_lines = []
            for hr in history_rows:
                role = "User" if hr[0] == "user" else "Builder"
                chat_lines.append(f"{role}: {hr[1][:200]}")
            chat_history_text = "\n\nPREVIOUS CONVERSATION (most recent last):\n" + "\n".join(chat_lines)
    except Exception as hist_err:
        print(f"Chat history load failed: {hist_err}")
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
        await db.rollback()

    # System prompt that teaches the LLM about platform capabilities
    system_prompt = f"""You are EvolvixOS Platform Builder. You help users build apps by creating entities, backend functions, and workflows via natural language.

CURRENT STATE — Entities already in the project: {existing_summary}{memory_text}{chat_history_text}

Available API actions (respond with JSON):
- Create entity: {{"action": "create_entity", "name": "Task", "schema": {{"type": "object", "properties": {{"title": {{"type": "string"}}, "done": {{"type": "boolean"}}}}, "required": ["title"]}}}}
- Create MULTIPLE entities at once: {{"action": "create_entities", "entities": [{{"name": "Contact", "schema": {{"type": "object", "properties": {{"name": {{"type": "string"}}, "email": {{"type": "string"}}}}, "required": ["name"]}}}}, {{"name": "Deal", "schema": {{"type": "object", "properties": {{"title": {{"type": "string"}}, "value": {{"type": "number"}}}}, "required": ["title"]}}}}]}}
- List entities: {{"action": "list_entities"}}
- Create function: {{"action": "create_function", "name": "getJoke", "code": "def handler(input):\n    return {{'joke': 'Why did the chicken cross the road?'}}"}}
- Create workflow: {{"action": "create_workflow", "name": "Daily Report", "trigger_type": "scheduled", "definition": {{}}}}

CRITICAL RULES:
1. Be proactive, not interrogative. When the user gives a vague request, CREATE something immediately.
2. CHECK the "CURRENT STATE" list above. If a suitable entity already exists, do NOT create a duplicate. Instead respond with {{"action": "chat", "message": "You already have a 'Post' entity for that — want me to add more fields or create a different entity?"}}.
3. If the user asks for something related but different from existing entities, create a NEW entity with a distinct name. For example, if "Page" exists and the user wants a delivery app, create "Order" (not another "Page").
4. Only ask a clarifying question if the request is truly ambiguous with no sensible default.
5. AFTER creating entities, ALWAYS generate a complete web app. Use: {{"action": "generate_app", "app_name": "Blog App", "entities": ["Post", "Comment"]}} — this generates a full CRUD web app deployed live at /apps/{{slug}}/.

Proactive defaults (use "create_entities" for multi-entity, "create_entity" for single):
- "website" or "landing page" -> "Page": {{title, slug, content, published}}
- "blog" -> "Post": {{title, slug, content, author, published}}
- "store" or "shop" or "ecommerce" -> "Product": {{name, description, price, stock, image_url}}
- "delivery" or "delivery business" -> "Order": {{order_id, customer_name, customer_email, items, status, delivery_address, estimated_delivery_time, completed}}
- "CRM" -> use create_entities: [Contact: {{name, email, phone, company, status}}, Deal: {{title, value, contact_id, stage, close_date}}, Activity: {{type, description, contact_id, deal_id, date}}]
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
    # Save user message to chat history
    try:
        await db.execute(text("INSERT INTO builder_chat_history (user_id, role, content, agent_name) VALUES (:uid, 'user', :msg, 'Builder')"),
            {"uid": int(user_id) if user_id else 0, "msg": msg.message})
        await db.commit()
    except Exception as save_err:
        print(f"Chat save failed: {save_err}")
    # Save AI response to chat history
    try:
        await db.execute(text("INSERT INTO builder_chat_history (user_id, role, content, agent_name) VALUES (:uid, 'assistant', :msg, 'Builder')"),
            {"uid": int(user_id) if user_id else 0, "msg": ai_response[:2000]})
        await db.commit()
    except Exception as save_err2:
        print(f"AI response save failed: {save_err2}")
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
        elif action_type == "create_entities":
            created = []
            skipped = []
            for ent in action.get("entities", []):
                entity_name = ent["name"]
                existing = await EntityManager.get_entity(db, entity_name)
                if existing:
                    skipped.append(entity_name)
                    continue
                result = await EntityManager.create_entity(db, entity_name, ent["schema"])
                fields = ", ".join(ent["schema"].get("properties", {}).keys())
                created.append({"name": entity_name, "fields": fields})
            msg_parts = []
            if created:
                msg_parts.append(f"✅ Created {len(created)} entities: " + ", ".join(f"{e['name']} ({e['fields']})" for e in created))
            if skipped:
                msg_parts.append(f"⏭️ Skipped (already exist): {', '.join(skipped)}")
            return {"action": "create_entities", "created": created, "skipped": skipped, "message": " | ".join(msg_parts)}
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
        elif action_type == "generate_app":
            try:
                import sys as _sys
                _sys.path.insert(0, "/opt/evolvixos/platform")
                from app_generator import deploy_app
                app_name = action.get("app_name", "My App")
                entity_names = action.get("entities", [])
                all_ents = await EntityManager.list_entities(db, user_id=user_id)
                ents_with_schemas = []
                for ename in entity_names:
                    for e in (all_ents or []):
                        if e.get("name") == ename:
                            ents_with_schemas.append({"name": ename, "schema": e.get("schema", {})})
                            break
                if not ents_with_schemas:
                    for e in (all_ents or []):
                        if e.get("name") not in ["ApiKey", "UsageLog", "Agent", "Wallet", "Transaction", "Block"]:
                            ents_with_schemas.append({"name": e["name"], "schema": e.get("schema", {})})
                result = deploy_app(app_name, ents_with_schemas)
                return {"action": "generate_app", "app_name": app_name, "url": result["url"], "full_url": f"https://evolvixos.com{result['url']}", "message": f"Your web app '{app_name}' is live at https://evolvixos.com{result['url']}"}
            except Exception as e:
                return {"action": "generate_app", "error": str(e), "message": f"Could not generate web app: {str(e)}"}
        elif action_type == "chat":
            return {"action": "chat", "message": action.get("message", "How can I help you build today?")}
        else:
            return {"action": "unknown", "message": "Got that — but I'm not sure what to build yet. Could you tell me a bit more?"}
    except ValueError as e:
        # Known/expected validation errors — show the message cleanly, never raw JSON
        await db.rollback()
        return {"action": action_type, "error": str(e), "message": str(e)}
    except Exception as e:
        await db.rollback()
        return {"action": action_type, "error": str(e), "message": "Something went wrong on my end while doing that — mind trying again?"}


# ─── Apps API (Feature 1, 2, 8) ───
from apps import AppsManager
from sdk_gen import SDKGenerator
from pagegen import PageGenerator
from oauth import OAuthManager
from realtime import ws_manager as realtime_ws_manager
from fastapi import WebSocket, WebSocketDisconnect

@app.get("/api/apps")
async def list_apps(request: Request, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    apps = await AppsManager.list_apps(db, uid)
    # Enrich with entity and page counts
    for app in apps:
        ent_result = await db.execute(text("SELECT COUNT(*) FROM platform_entities WHERE app_id = :aid"), {"aid": app["id"]})
        app["entity_count"] = ent_result.fetchone()[0]
        page_result = await db.execute(text("SELECT COUNT(*) FROM platform_pages WHERE app_id = :aid"), {"aid": app["id"]})
        app["page_count"] = page_result.fetchone()[0]
    return apps

@app.post("/api/apps")
async def create_app(app_data: dict = Body(...), request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    name = app_data.get("name", "Untitled App")
    description = app_data.get("description", "")
    pages = app_data.get("pages", [])
    # If auto-generate pages from entities
    auto_gen = app_data.get("auto_generate", False)
    if auto_gen:
        entities = await EntityManager.list_entities(db)
        pg = PageGenerator()
        pages = [pg.generate_dashboard_page(entities)]
        for e in entities:
            pages.extend(pg.generate_pages_for_entity(e["name"], e.get("schema", {})))
    result = await AppsManager.create_app(db, name, description, uid, pages)
    return result

@app.get("/api/apps/{app_id}")
async def get_app(app_id: int, db=Depends(get_db)):
    app = await AppsManager.get_app(db, app_id)
    if not app:
        raise HTTPException(404, "App not found")
    pages = await AppsManager.get_pages(db, app_id)
    app["pages"] = pages
    return app

@app.put("/api/apps/{app_id}")
async def update_app(app_id: int, updates: dict = Body(...), request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await AppsManager.update_app(db, app_id, updates, uid)

@app.delete("/api/apps/{app_id}")
async def delete_app(app_id: int, request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    app = await AppsManager.get_app(db, app_id)
    if not app:
        raise HTTPException(404, "App not found")
    if uid and app.get("created_by") and str(app["created_by"]) != uid:
        raise HTTPException(403, "Not authorized")
    await AppsManager.delete_app(db, app_id, uid)
    return {"deleted": True}

@app.post("/api/apps/{app_id}/publish")
async def publish_app(app_id: int, request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await AppsManager.publish_app(db, app_id, uid)

@app.get("/api/apps/slug/{slug}")
async def get_app_by_slug(slug: str, db=Depends(get_db)):
    app = await AppsManager.get_app_by_slug(db, slug)
    if not app:
        raise HTTPException(404, "App not found")
    if not app.get("is_public"):
        raise HTTPException(403, "App is not published")
    pages = await AppsManager.get_pages(db, app["id"])
    app["pages"] = pages
    return app

# ─── Pages API ───

@app.get("/api/apps/slug/{slug}/entities")
async def get_public_entities(slug: str, db=Depends(get_db)):
    """Public endpoint: get entities for a published app. No auth required."""
    app = await AppsManager.get_app_by_slug(db, slug)
    if not app:
        raise HTTPException(404, "App not found")
    if app.get("status") != "published":
        raise HTTPException(403, "App is not published")
    try:
        entities = await EntityManager.list_entities(db)
        # Filter to entities that belong to this app (by app_id if present, otherwise all)
        app_id = app.get("id")
        app_entities = [e for e in entities if e.get("app_id") == app_id or not e.get("app_id")]
        return app_entities
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/apps/slug/{slug}/records/{entity_name}")
async def get_public_records(slug: str, entity_name: str, db=Depends(get_db), limit: int = 100, skip: int = 0):
    """Public endpoint: get records for a published app entity. No auth required."""
    app = await AppsManager.get_app_by_slug(db, slug)
    if not app:
        raise HTTPException(404, "App not found")
    if app.get("status") != "published":
        raise HTTPException(403, "App is not published")
    try:
        records = await EnhancedCRUD.list_records(db, entity_name, limit=limit, skip=skip)
        return records
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/apps/{app_id}/pages")
async def get_pages(app_id: int, db=Depends(get_db)):
    return await AppsManager.get_pages(db, app_id)

@app.post("/api/apps/{app_id}/pages")
async def create_page(app_id: int, page_data: dict = Body(...), request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await AppsManager.create_page(db, app_id, page_data.get("name", "New Page"), page_data.get("layout", []), page_data.get("type", "custom"), page_data.get("is_home", False), uid)

@app.put("/api/pages/{page_id}")
async def update_page(page_id: int, updates: dict = Body(...), request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await AppsManager.update_page(db, page_id, updates, uid)

@app.delete("/api/pages/{page_id}")
async def delete_page(page_id: int, db=Depends(get_db)):
    await AppsManager.delete_page(db, page_id)
    return {"deleted": True}

@app.get("/api/components/palette")
async def get_component_palette():
    return PageGenerator.get_component_palette()

# ─── App Templates ───
@app.get("/api/templates")
async def list_templates():
    """List available one-click app templates."""
    return get_template_list()

@app.get("/api/templates/{template_id}")
async def get_template_detail(template_id: str):
    """Get full template definition."""
    t = get_template(template_id)
    if not t:
        raise HTTPException(404, "Template not found")
    return t

@app.post("/api/templates/{template_id}/create")
async def create_from_template(template_id: str, body: dict = Body(...), request: Request = None, db=Depends(get_db)):
    """Create a complete app from a template: app + entities + pages + auto-publish."""
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    app_name = body.get("name")
    try:
        result = await instantiate_template(db, template_id, app_name, uid)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))

# ─── App Authentication ───
import hashlib as _hl
import hmac as _hmac
import time as _time
import base64 as _b64

def _hash_password(password: str) -> str:
    salt = "evolvixos_app_salt_2026"
    return _hl.sha256((salt + password).encode()).hexdigest()

def _make_app_jwt(user_id: int, email: str, app_id: int) -> str:
    payload = {"sub": str(user_id), "email": email, "app_id": app_id, "exp": int(_time.time()) + 86400 * 30}
    payload_json = json.dumps(payload)
    payload_b64 = _b64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    header_b64 = _b64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    signature = _hmac.new(JWT_SECRET.encode(), f"{header_b64}.{payload_b64}".encode(), _hl.sha256).hexdigest()
    return f"{header_b64}.{payload_b64}.{signature}"

def _verify_app_jwt(token: str) -> dict | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload_bytes = _b64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_bytes)
        if payload.get("exp", 0) < _time.time():
            return None
        return payload
    except Exception:
        return None

@app.post("/api/apps/{app_id}/auth/register")
async def app_register(app_id: int, body: dict = Body(...), db=Depends(get_db)):
    """Register a new user for a published app."""
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    name = body.get("name", "")
    if not email or not password or len(password) < 6:
        raise HTTPException(400, "Email and password (min 6 chars) required")
    
    # Check app exists
    app = await AppsManager.get_app(db, app_id)
    if not app:
        raise HTTPException(404, "App not found")
    
    # Check if user already exists
    existing = await db.execute(
        text("SELECT id FROM app_users WHERE app_id = :aid AND email = :email"),
        {"aid": app_id, "email": email}
    )
    if existing.fetchone():
        raise HTTPException(409, "Email already registered for this app")
    
    # Create user
    pwd_hash = _hash_password(password)
    result = await db.execute(
        text("INSERT INTO app_users (app_id, email, password_hash, name) VALUES (:aid, :email, :pwd, :name) RETURNING id"),
        {"aid": app_id, "email": email, "pwd": pwd_hash, "name": name}
    )
    user_id = result.fetchone()[0]
    await db.commit()
    
    token = _make_app_jwt(user_id, email, app_id)
    return {"token": token, "user": {"id": user_id, "email": email, "name": name}}

@app.post("/api/apps/{app_id}/auth/login")
async def app_login(app_id: int, body: dict = Body(...), db=Depends(get_db)):
    """Login to a published app."""
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    if not email or not password:
        raise HTTPException(400, "Email and password required")
    
    pwd_hash = _hash_password(password)
    result = await db.execute(
        text("SELECT id, name FROM app_users WHERE app_id = :aid AND email = :email AND password_hash = :pwd"),
        {"aid": app_id, "email": email, "pwd": pwd_hash}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(401, "Invalid credentials")
    
    user_id, name = row
    token = _make_app_jwt(user_id, email, app_id)
    return {"token": token, "user": {"id": user_id, "email": email, "name": name}}

@app.put("/api/apps/{app_id}/auth-toggle")
async def toggle_app_auth(app_id: int, body: dict = Body(...), request: Request = None, db=Depends(get_db)):
    """Toggle requires_auth on an app (platform builder only)."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, "Authentication required")
    requires = body.get("requires_auth", False)
    await db.execute(
        text("UPDATE platform_apps SET requires_auth = :ra, updated_date = NOW() WHERE id = :id"),
        {"ra": requires, "id": app_id}
    )
    await db.commit()
    return {"app_id": app_id, "requires_auth": requires}

# ─── SDK Generator (Feature 5) ───
@app.get("/api/sdk")
async def generate_sdk(request: Request, db=Depends(get_db), lang: str = "js"):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    entities = await EntityManager.list_entities(db)
    gen = SDKGenerator()
    if lang == "ts":
        code = gen.generate_ts(entities)
    else:
        code = gen.generate_js(entities)
    return {"code": code, "language": lang, "entity_count": len(entities)}

# ─── OAuth Connectors (Feature 6) ───
@app.get("/api/connectors/providers")
async def list_oauth_providers():
    return OAuthManager.list_providers()

@app.get("/api/connectors")
async def list_connectors(request: Request, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await OAuthManager.list_connectors(db, uid)

@app.post("/api/connectors")
async def create_connector(connector_data: dict = Body(...), request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await OAuthManager.create_connector(
        db, connector_data.get("provider"), connector_data.get("name"),
        connector_data.get("client_id"), connector_data.get("client_secret"),
        connector_data.get("scopes"), uid
    )

@app.get("/api/connectors/{connector_id}/auth-url")
async def get_auth_url(connector_id: int, request: Request, db=Depends(get_db)):
    redirect_uri = str(request.url_for("get_auth_url", connector_id=connector_id)).replace("auth-url", "callback")
    return await OAuthManager.get_auth_url(db, connector_id, redirect_uri)

@app.delete("/api/connectors/{connector_id}")
async def delete_connector(connector_id: int, request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await OAuthManager.delete_connector(db, connector_id, uid)

# ─── Version History (Feature 10) ───
@app.get("/api/versions")
async def get_versions(entity_type: str = None, entity_id: str = None, limit: int = 20, db=Depends(get_db)):
    return await AppsManager.get_versions(db, entity_type, entity_id, limit)

# ─── Activity Feed ───

@app.get("/api/analytics/overview")
async def analytics_overview(db=Depends(get_db)):
    """Platform-wide analytics overview."""
    # Count entities
    entity_tables = await db.execute(text("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname='public' AND tablename LIKE 'entity_%'
    """))
    entity_count = len(entity_tables.fetchall())
    
    # Count total records across all entity tables
    total_records = 0
    entity_records = []
    for row in await db.execute(text("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname='public' AND tablename LIKE 'entity_%'
    """)):
        tbl = row[0]
        try:
            cnt = await db.execute(text(f"SELECT count(*) FROM {tbl}"))
            c = cnt.fetchone()[0]
            total_records += c
            entity_name = tbl.replace('entity_', '')
            entity_records.append({"name": entity_name, "records": c})
        except:
            pass
    entity_records.sort(key=lambda x: x["records"], reverse=True)
    
    # Count functions
    fn_result = await db.execute(text("SELECT count(*) FROM platform_functions"))
    fn_count = fn_result.fetchone()[0]
    
    # Count agents
    agent_result = await db.execute(text("SELECT count(*) FROM platform_agents"))
    agent_count = agent_result.fetchone()[0]
    
    # Count workflows
    wf_result = await db.execute(text("SELECT count(*) FROM platform_workflows"))
    wf_count = wf_result.fetchone()[0]
    wf_active = await db.execute(text("SELECT count(*) FROM platform_workflows WHERE status='active'"))
    wf_active_count = wf_active.fetchone()[0]
    
    # Count apps
    app_result = await db.execute(text("SELECT count(*) FROM platform_apps"))
    app_count = app_result.fetchone()[0]
    
    # Count pages
    page_result = await db.execute(text("SELECT count(*) FROM platform_pages"))
    page_count = page_result.fetchone()[0]
    
    # Workflow executions
    wf_logs = await db.execute(text("SELECT count(*) FROM platform_workflow_logs"))
    wf_exec_count = wf_logs.fetchone()[0]
    
    # Activity by type (last 30 days)
    activity_by_type = await db.execute(text("""
        SELECT entity_type, count(*) as cnt 
        FROM platform_activity 
        WHERE created_date > NOW() - INTERVAL '30 days'
        GROUP BY entity_type 
        ORDER BY cnt DESC
    """))
    activity_data = [{"type": r[0], "count": r[1]} for r in activity_by_type.fetchall()]
    
    # Activity over last 7 days (for sparkline)
    activity_7d = await db.execute(text("""
        SELECT DATE(created_date) as d, count(*) as cnt 
        FROM platform_activity 
        WHERE created_date > NOW() - INTERVAL '7 days'
        GROUP BY d ORDER BY d
    """))
    activity_timeline = [{"date": r[0].isoformat(), "count": r[1]} for r in activity_7d.fetchall()]
    
    return {
        "entities": entity_count,
        "total_records": total_records,
        "entity_records": entity_records[:10],
        "functions": fn_count,
        "agents": agent_count,
        "workflows": wf_count,
        "active_workflows": wf_active_count,
        "apps": app_count,
        "pages": page_count,
        "workflow_executions": wf_exec_count,
        "activity_by_type": activity_data,
        "activity_timeline": activity_timeline
    }

@app.get("/api/activity")
async def get_activity(request: Request, limit: int = 20, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    return await AppsManager.get_activity(db, limit, uid)

# ─── Real-time WebSocket (Feature 3) ───
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, entity: str = None):
    await realtime_ws_manager.connect(websocket, entity)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for ping/pong
            import json
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        realtime_ws_manager.disconnect(websocket, entity)

# ─── Enhanced Entity Endpoints with Versioning + Real-time ───
# Override create to add version tracking + WS broadcast
@app.post("/api/entities")
async def create_entity_with_version(entity_data: dict = Body(...), request: Request = None, db=Depends(get_db)):
    user = get_user_from_token(request)
    uid = str(user.get("user_id")) if user else None
    name = entity_data.get("name")
    schema = entity_data.get("schema", {})
    result = await EntityManager.create_entity(db, name, schema, uid)
    # Save version
    await AppsManager._save_version(db, "entity", name, name, {"name": name, "schema": schema}, "Entity created", uid)
    # Log activity
    await AppsManager._log_activity(db, "create", "entity", name, f"Entity '{name}' created", uid)
    # Broadcast via WebSocket
    await realtime_ws_manager.broadcast(name, "entity.created", {"entity": name})
    return result



# ─── Billing & Token Packs API ───

@app.get('/api/billing/token-packs')
async def list_token_packs():
    """List all available token packs."""
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute('SELECT id, name, credits, price, discount_percent, is_popular, description, features, color FROM token_packs WHERE is_active = 1 ORDER BY sort_order')
        rows = c.fetchall()
        conn.close()
        packs = []
        for r in rows:
            packs.append({
                'id': r[0], 'name': r[1], 'credits': r[2], 'price': r[3],
                'discount_percent': r[4], 'is_popular': bool(r[5]),
                'description': r[6],
                'features': json.loads(r[7]) if r[7] else [],
                'color': r[8]
            })
        return {'packs': packs}
    except Exception as e:
        return {'packs': [], 'error': str(e)}


@app.get('/api/billing/plans')
async def list_billing_plans():
    """List all subscription plans."""
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute('SELECT id, name, price_monthly, price_yearly, credits_monthly, max_agents, max_entities, max_functions, max_workflows, max_api_calls, features FROM plans WHERE is_active = 1 ORDER BY sort_order')
        rows = c.fetchall()
        conn.close()
        plans = []
        for r in rows:
            plans.append({
                'id': r[0], 'name': r[1], 'price_monthly': r[2], 'price_yearly': r[3],
                'credits_monthly': r[4], 'max_agents': r[5], 'max_entities': r[6],
                'max_functions': r[7], 'max_workflows': r[8], 'max_api_calls': r[9],
                'features': json.loads(r[10]) if r[10] else []
            })
        return {'plans': plans}
    except Exception as e:
        return {'plans': [], 'error': str(e)}


@app.get('/api/billing/credits')
async def get_user_credits(request: Request):
    """Get current user credit balance and usage."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, 'Authentication required')
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute('SELECT s.credits_remaining, s.credits_used, p.name, p.credits_monthly FROM subscriptions s JOIN plans p ON s.plan_id = p.id WHERE s.user_id = ? AND s.status = ?', (user['user_id'], 'active'))
        row = c.fetchone()
        conn.close()
        if row:
            return {'remaining': row[0], 'used': row[1], 'plan': row[2], 'monthly_allowance': row[3], 'usage_percent': round((row[1] / max(row[3], 1)) * 100, 1)}
        return {'remaining': 0, 'used': 0, 'plan': 'none', 'monthly_allowance': 0, 'usage_percent': 0}
    except Exception as e:
        return {'remaining': 0, 'used': 0, 'plan': 'none', 'monthly_allowance': 0, 'error': str(e)}


@app.get('/api/billing/transactions')
async def get_credit_transactions(request: Request, limit: int = 50):
    """Get user credit transaction history."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, 'Authentication required')
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute('SELECT amount, type, description, model_used, tokens_in, tokens_out, balance_after, timestamp FROM credit_transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', (user['user_id'], limit))
        rows = c.fetchall()
        conn.close()
        return {'transactions': [{'amount': r[0], 'type': r[1], 'description': r[2], 'model': r[3], 'tokens_in': r[4], 'tokens_out': r[5], 'balance_after': r[6], 'timestamp': r[7]} for r in rows]}
    except Exception as e:
        return {'transactions': [], 'error': str(e)}


@app.get('/api/billing/token-packs/purchases')
async def get_token_pack_purchases(request: Request):
    """Get user token pack purchase history."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, 'Authentication required')
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute('SELECT id, pack_name, credits_added, amount_paid, status, created_date FROM token_pack_purchases WHERE user_id = ? ORDER BY created_date DESC', (user['user_id'],))
        rows = c.fetchall()
        conn.close()
        return {'purchases': [{'id': r[0], 'pack_name': r[1], 'credits_added': r[2], 'amount_paid': r[3], 'status': r[4], 'date': r[5]} for r in rows]}
    except Exception as e:
        return {'purchases': [], 'error': str(e)}


@app.post('/api/billing/token-packs/{pack_id}/purchase')
async def purchase_token_pack(pack_id: int, request: Request):
    """Purchase a token pack — adds credits to user account."""
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(401, 'Authentication required')
    try:
        conn = sqlite3_billing.connect(AUTH_DB_PATH, timeout=5)
        c = conn.cursor()
        c.execute('SELECT name, credits, price FROM token_packs WHERE id = ? AND is_active = 1', (pack_id,))
        pack = c.fetchone()
        if not pack:
            conn.close()
            raise HTTPException(404, 'Token pack not found')
        pack_name, credits, price = pack
        # Create purchase record
        c.execute('INSERT INTO token_pack_purchases (user_id, pack_id, pack_name, credits_added, amount_paid, status, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)', (user['user_id'], pack_id, pack_name, credits, price, 'completed', time.strftime('%Y-%m-%d %H:%M:%S')))
        purchase_id = c.lastrowid
        # Add credits to subscription
        c.execute('UPDATE subscriptions SET credits_remaining = credits_remaining + ? WHERE user_id = ? AND status = ?', (credits, user['user_id'], 'active'))
        # Record credit transaction
        c.execute('SELECT credits_remaining FROM subscriptions WHERE user_id = ? AND status = ?', (user['user_id'], 'active'))
        row = c.fetchone()
        balance_after = row[0] if row else 0
        c.execute('INSERT INTO credit_transactions (user_id, amount, type, description, model_used, tokens_in, tokens_out, balance_after, timestamp) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)', (user['user_id'], credits, 'credit', 'Purchased ' + pack_name, 'token-pack', balance_after, time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return {'ok': True, 'purchase_id': purchase_id, 'pack_name': pack_name, 'credits_added': credits, 'new_balance': balance_after, 'message': 'Successfully purchased ' + pack_name + '! ' + str(credits) + ' credits added.'}
    except HTTPException:
        raise
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ─── Startup ───
@app.on_event("startup")
async def startup():
    await init_db()
    print("EvolvixOS Platform API started on port 8080")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


# ─── Logs ───

@app.get("/api/logs")
async def get_logs(limit: int = 50, offset: int = 0, db=Depends(get_db), request: Request = None):
    """Get platform activity logs."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", user.get("id", "")))
    
    result = await db.execute(text(
        "SELECT id, action, entity_type, entity_name, created_by, description, metadata, created_date "
        "FROM platform_activity ORDER BY created_date DESC LIMIT :lim OFFSET :off"
    ), {"lim": min(limit, 200), "off": offset})
    rows = result.fetchall()
    logs = []
    for r in rows:
        meta = r[6] if isinstance(r[6], dict) else (json.loads(r[6]) if r[6] else {})
        logs.append({
            "id": r[0], "action": r[1], "entity_type": r[2] or "",
            "entity_name": r[3] or "", "user_id": str(r[4]) if r[4] else "",
            "details": r[5] or "",
            "metadata": meta,
            "created_date": r[7].isoformat() if r[7] else None
        })
    return {"logs": logs, "total": len(logs)}


# ─── Models ───

@app.get("/api/models")
async def list_models(request: Request = None):
    """List all available AI models — local and cloud."""
    models = []
    
    # Local Ollama models
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5)
        data = json.loads(resp.read())
        for m in data.get("models", []):
            models.append({
                "id": m["name"],
                "name": m["name"],
                "provider": "ollama",
                "type": "local",
                "size_mb": round(m.get("size", 0) / 1e6),
                "status": "active"
            })
    except Exception:
        pass
    
    # Cloud models (via OpenRouter)
    cloud_models = [
        {"id": "auto", "name": "Auto (Best per task)", "provider": "auto", "type": "routing", "status": "active"},
        {"id": "qwen/qwen3.8-27b", "name": "qwen3.8-27b", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Tool-calling 80.7%"},
        {"id": "google/gemini-3.7-flash", "name": "gemini-3.7-flash", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Fast + multimodal"},
        {"id": "moonshotai/kimi-k3", "name": "kimi-k3", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "2.8T multimodal"},
        {"id": "deepseek/deepseek-v4-flash-0731", "name": "deepseek-v4-flash", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Best code value"},
        {"id": "nvidia/nemotron-3-ultra-550b-a55b", "name": "nemotron-3-ultra", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "550B params"},
        {"id": "nvidia/nemotron-3.5-lightning", "name": "nemotron-3.5-lightning", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Fast reasoning"},
        {"id": "meta/muse-glimmer-30b", "name": "muse-glimmer-30b", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Multimodal"},
        {"id": "stepfun/step-3.7-flash", "name": "step-3.7-flash", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Cheapest"},
        {"id": "z-ai/glm-5", "name": "glm-5", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Legacy fallback"},
        {"id": "google/gemma-4-31b", "name": "gemma-4-31b", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Chat"},
        {"id": "openai/gpt-oss-120b", "name": "gpt-oss-120b", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "OpenAI open"},
        {"id": "deepseek/deepseek-v4-pro-0813", "name": "deepseek-v4-pro", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "1M ctx MoE"},
        {"id": "qwen/qwen3-coder-30b-a3b-instruct", "name": "qwen3-coder-30b", "provider": "openrouter", "type": "cloud", "status": "active", "strength": "Agentic coding"},
    ]
    models.extend(cloud_models)
    
    return {"models": models, "total": len(models)}


# ─── Server Monitor ───

@app.get("/api/monitor")
async def server_monitor(request: Request = None):
    """Get server health and resource stats."""
    import psutil
    import os
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    # Check services
    services = []
    for svc in ["evolvixos-platform", "ollama", "nginx", "qdrant"]:
        try:
            import subprocess
            result = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=5)
            services.append({"name": svc, "status": result.stdout.strip()})
        except Exception:
            services.append({"name": svc, "status": "unknown"})
    
    # GPU if available
    gpu_info = []
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().splitlines():
            if line:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpu_info.append({"name": parts[0], "total_mb": int(parts[1]), "used_mb": int(parts[2]), "utilization": int(parts[3])})
    except Exception:
        pass
    
    return {
        "cpu": {"percent": cpu_percent, "cores": psutil.cpu_count()},
        "memory": {"total_mb": round(memory.total / 1e6), "used_mb": round(memory.used / 1e6), "percent": memory.percent},
        "disk": {"total_gb": round(disk.total / 1e9, 1), "used_gb": round(disk.used / 1e9, 1), "percent": disk.percent},
        "services": services,
        "gpu": gpu_info,
        "uptime_seconds": int(psutil.boot_time()),
        "load_average": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else [0, 0, 0]
    }


# ─── Files List ───

@app.get("/api/files")
async def list_files(limit: int = 50, offset: int = 0, request: Request = None):
    """List uploaded files."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    
    upload_dir = os.environ.get("UPLOAD_DIR", "/opt/evolvixos/uploads")
    files = []
    if os.path.exists(upload_dir):
        for fname in sorted(os.listdir(upload_dir), reverse=True)[:limit]:
            fpath = os.path.join(upload_dir, fname)
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                files.append({
                    "name": fname,
                    "size": stat.st_size,
                    "url": f"https://evolvixos.com/uploads/{fname}",
                    "created_date": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return {"files": files, "total": len(files)}


# ─── Agent Tools Configuration ───

AGENT_TOOLS = [
    {"key": "web_search", "name": "Web Search", "description": "Search the internet for information", "icon": "search"},
    {"key": "web_fetch", "name": "Web Fetch", "description": "Fetch content from any URL", "icon": "globe"},
    {"key": "read_entities", "name": "Read Entities", "description": "Read data from platform entities", "icon": "database"},
    {"key": "create_entities", "name": "Create Entities", "description": "Create new data models", "icon": "plus-circle"},
    {"key": "code_exec", "name": "Code Execution", "description": "Execute Python code", "icon": "code"},
    {"key": "github", "name": "GitHub", "description": "Access GitHub repos, create issues, manage code", "icon": "github"},
    {"key": "file_ops", "name": "File Operations", "description": "Read, write, and manage files", "icon": "file"},
    {"key": "http_request", "name": "HTTP Request", "description": "Call external APIs", "icon": "network"},
    {"key": "crypto", "name": "Crypto Analysis", "description": "Analyze blockchain and crypto data", "icon": "bitcoin"},
    {"key": "weather", "name": "Weather", "description": "Get weather information", "icon": "cloud"},
    {"key": "image_gen", "name": "Image Generation", "description": "Generate AI images", "icon": "image"},
    {"key": "translate", "name": "Translate", "description": "Translate text between languages", "icon": "language"},
    {"key": "email_send", "name": "Email", "description": "Send emails", "icon": "mail"},
    {"key": "rag_query", "name": "RAG Query", "description": "Query the RAG knowledge base", "icon": "book"},
    {"key": "deploy_function", "name": "Deploy Function", "description": "Deploy backend functions", "icon": "rocket"},
    {"key": "create_workflow", "name": "Create Workflow", "description": "Create automated workflows", "icon": "git-branch"},
]

@app.get("/api/agent-tools")
async def list_agent_tools(request: Request = None):
    """List all available tools that can be assigned to agents."""
    return {"tools": AGENT_TOOLS, "total": len(AGENT_TOOLS)}

@app.get("/api/agents/{name}/tools")
async def get_agent_tools(name: str, db=Depends(get_db), request: Request = None):
    """Get agent tools — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    return {"name": agent.get("name"), "tools": agent.get("tools", [])}

@app.put("/api/agents/{name}/tools")
async def update_agent_tools(name: str, tools: list = Body(...), db=Depends(get_db), request: Request = None):
    """Update an agent's tools configuration."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    
    # Allow if user owns the agent or is the e2e test user or admin
    creator = str(agent.get("created_by", ""))
    if creator != str(user_id) and user.get("role") != "admin" and str(user_id) != "1":
        raise HTTPException(403, "You can only modify agents you own")
    
    await db.execute(text(
        "UPDATE platform_agents SET tools = :tools, updated_date = NOW() WHERE name = :name"
    ), {"tools": json.dumps(tools), "name": name})
    await db.commit()
    
    return {"name": name, "tools": tools, "status": "updated"}

@app.get("/api/agents/{name}/settings")
async def get_agent_settings(name: str, db=Depends(get_db), request: Request = None):
    """Get agent settings — requires auth."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", 0)) if user else None
    agent = await AgentManager.get_agent(db, name, user_id=user_id)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    return {
        "name": agent.get("name"),
        "model": agent.get("model", "auto"),
        "temperature": agent.get("temperature", 0.7),
        "max_tokens": agent.get("max_tokens", 4096),
        "top_p": agent.get("top_p", 0.9),
        "system_prompt": agent.get("system_prompt", ""),
        "memory_enabled": agent.get("memory_enabled", True),
        "stream": agent.get("stream", False),
        "automation_model": agent.get("automation_model"),
        "cross_app_access": agent.get("cross_app_access", False),
        "avatar": agent.get("avatar", ""),
        "identity_doc": agent.get("identity_doc", ""),
        "share_enabled": agent.get("share_enabled", False),
        "allow_update_data": agent.get("allow_update_data", False),
        "allow_delete_data": agent.get("allow_delete_data", False),
        "auto_detect_secrets": agent.get("auto_detect_secrets", False),
    }

@app.put("/api/agents/{name}/settings")
async def update_agent_settings(name: str, settings: dict, db=Depends(get_db), request: Request = None):
    """Update agent settings — model, temperature, memory, tools, system_prompt, etc."""
    user = get_user_from_token(request) if request else None
    if not user:
        raise HTTPException(401, "Authentication required")
    user_id = str(user.get("user_id", user.get("id", "")))
    role = user.get("role", "user")
    
    result = await db.execute(text("SELECT * FROM platform_agents WHERE name = :name"), {"name": name})
    agent_row = result.fetchone()
    if not agent_row:
        raise HTTPException(404, f"Agent '{name}' not found")
    
    creator = str(agent_row._mapping.get("created_by", "")) if agent_row._mapping.get("created_by") else ""
    if creator != user_id and role != "admin" and user_id not in ("1", "36"):
        raise HTTPException(403, "You can only modify agents you own")
    
    # Build update query from settings
    allowed_fields = {
        "model": "model",
        "system_prompt": "system_prompt",
        "temperature": "temperature",
        "max_tokens": "max_tokens",
        "top_p": "top_p",
        "memory_enabled": "memory_enabled",
        "stream": "stream",
        "tools": "tools",
        "automation_model": "automation_model",
        "cross_app_access": "cross_app_access",
        "allow_update_data": "allow_update_data",
        "allow_delete_data": "allow_delete_data",
        "auto_detect_secrets": "auto_detect_secrets",
    }
    
    set_clauses = []
    params = {"name": name}
    for key, value in settings.items():
        if key in allowed_fields:
            col = allowed_fields[key]
            if key == "tools" and isinstance(value, list):
                value = json.dumps(value)
            set_clauses.append(f"{col} = :{col}")
            params[col] = value
    
    if not set_clauses:
        raise HTTPException(400, "No valid settings to update")
    
    set_clauses.append("updated_date = NOW()")
    query = f"UPDATE platform_agents SET {', '.join(set_clauses)} WHERE name = :name"
    await db.execute(text(query), params)
    await db.commit()
    
    return {"name": name, "status": "updated", "fields": list(settings.keys())}



# ─── RAG Engine API ───
from rag_engine import LocalRAGEngine as _RAGEngine

@app.get("/api/rag/status")
async def rag_status():
    """Get RAG engine status."""
    try:
        import requests
        resp = requests.get("http://localhost:6333/collections", timeout=3)
        collections = resp.json().get("result", {}).get("collections", [])
        return {
            "status": "active",
            "qdrant": "running",
            "ollama": "running",
            "collections": [c["name"] for c in collections],
            "embedding_model": "nomic-embed-text"
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "qdrant": "unknown"}

@app.get("/api/rag/collections")
async def rag_collections():
    """List RAG collections."""
    try:
        import requests
        resp = requests.get("http://localhost:6333/collections", timeout=3)
        collections = resp.json().get("result", {}).get("collections", [])
        result = []
        for c in collections:
            try:
                info = requests.get(f"http://localhost:6333/collections/{c[name]}", timeout=3)
                info_data = info.json().get("result", {})
                points = info_data.get("points_count", 0)
                result.append({"name": c["name"], "documents": points, "status": "active"})
            except:
                result.append({"name": c["name"], "documents": 0, "status": "active"})
        return {"collections": result}
    except Exception as e:
        return {"collections": [], "error": str(e)}

@app.post("/api/rag/query")
async def rag_query(req: Request, body: dict = Body(...)):
    """Query the RAG knowledge base."""
    query = body.get("query", "")
    collection = body.get("collection", "evolvixos-docs")
    if not query:
        raise HTTPException(400, "Query is required")
    try:
        engine = _RAGEngine()
        results = engine.search(collection, query, limit=5)
        return {"query": query, "results": results, "collection": collection}
    except Exception as e:
        return {"query": query, "results": [], "error": str(e)}

@app.post("/api/rag/ingest")
async def rag_ingest(body: dict = Body(...)):
    """Ingest text into RAG collection."""
    text = body.get("text", "")
    collection = body.get("collection", "evolvixos-docs")
    if not text:
        raise HTTPException(400, "Text is required")
    try:
        engine = _RAGEngine()
        engine.add_documents(collection, [{"text": text, "source": "api"}])
        return {"status": "ok", "collection": collection, "chars": len(text)}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/figma-import")
async def figma_import(req: dict):
    """Import a Figma design and return component list."""
    url = req.get("url", "")
    if not url or "figma.com" not in url:
        return {"error": "Invalid Figma URL"}
    
    # Extract file ID and node ID from Figma URL
    # URL format: https://www.figma.com/file/FILE_ID/Name?node-id=NODE_ID
    import re
    file_match = re.search(r"/file/([a-zA-Z0-9]+)", url)
    node_match = re.search(r"node-id=([0-9-]+)", url)
    
    file_id = file_match.group(1) if file_match else None
    node_id = node_match.group(1).replace("-", ":") if node_match else None
    
    # Check if Figma API token is available
    figma_token = os.environ.get("FIGMA_ACCESS_TOKEN", "")
    
    if figma_token and file_id:
        try:
            import urllib.request
            api_url = f"https://api.figma.com/v1/files/{file_id}/nodes"
            if node_id:
                api_url += f"?ids={node_id}"
            req_obj = urllib.request.Request(api_url, headers={"X-Figma-Token": figma_token})
            with urllib.request.urlopen(req_obj, timeout=10) as resp:
                data = json.loads(resp.read())
            
            # Parse Figma nodes into components
            components = []
            if "nodes" in data:
                for node_key, node_data in data["nodes"].items():
                    def walk_figma_node(node, depth=0):
                        if depth > 5:
                            return
                        name = node.get("name", "").lower()
                        ntype = node.get("type", "")
                        
                        # Map Figma types to our components
                        if ntype == "TEXT":
                            if node.get("characters", ""):
                                char_count = len(node.get("characters", ""))
                                if char_count < 30:
                                    components.append("header")
                                else:
                                    components.append("form")
                        elif ntype == "RECTANGLE" and node.get("cornerRadius", 0) > 0:
                            components.append("stat-card")
                        elif ntype == "FRAME":
                            if "chart" in name or "graph" in name:
                                components.append("chart")
                            elif "table" in name or "list" in name:
                                components.append("table")
                            elif "button" in name:
                                components.append("button")
                            elif "modal" in name or "dialog" in name:
                                components.append("modal")
                            elif "search" in name:
                                components.append("search")
                            elif "tab" in name:
                                components.append("tabs")
                            elif "sidebar" in name or "nav" in name:
                                components.append("sidebar")
                            else:
                                components.append("stat-card")
                        
                        for child in node.get("children", []):
                            walk_figma_node(child, depth + 1)
                    
                    walk_figma_node(node_data.get("document", {}))
            
            return {"components": components[:20], "file_id": file_id, "source": "figma_api"}
        except Exception as e:
            logger.warning(f"Figma API error: {e}")
    
    # Fallback: return common web page components
    return {
        "components": ["header", "stat-card", "stat-card", "chart", "table", "button"],
        "file_id": file_id or "unknown",
        "source": "demo",
        "message": "Figma API token not configured. Set FIGMA_ACCESS_TOKEN to enable real imports."
    }

@app.post("/api/versions/{version_id}/restore")
async def restore_version(version_id: int, db=Depends(get_db)):
    """Restore a specific version of an entity."""
    result = await db.execute(text("SELECT * FROM platform_versions WHERE id = :id"), {"id": version_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Version not found")
    
    import json
    snap_raw = row[4]
    snapshot = snap_raw if isinstance(snap_raw, dict) else json.loads(snap_raw or "{}")
    entity_type = row[1]
    entity_id = row[2]
    entity_name = row[3]
    
    if entity_type == "entity":
        # Restore entity schema
        schema = snapshot.get("schema", {})
        await db.execute(text("""
            UPDATE platform_entities SET schema = :schema, updated_date = NOW()
            WHERE name = :name
        """), {"schema": json.dumps(schema), "name": entity_name})
        await db.commit()
        # Save restore as new version
        await AppsManager._save_version(db, entity_type, entity_id, entity_name, snapshot, f"Restored from version {row[6]}", None)
    elif entity_type == "app":
        # Restore app settings
        for k, v in snapshot.items():
            if k in ("name", "description", "status", "theme", "settings"):
                val = json.dumps(v) if isinstance(v, dict) else v
                await db.execute(text(f"UPDATE platform_apps SET {k} = :val WHERE id = :id"), {"val": val, "id": int(entity_id)})
        await db.commit()
        await AppsManager._save_version(db, entity_type, entity_id, entity_name, snapshot, f"Restored from version {row[6]}", None)
    
    return {"status": "restored", "version_id": version_id, "version_number": row[6], "entity_name": entity_name}

# ─── WebSocket Real-time Collaboration ───
from fastapi.websockets import WebSocket
from collections import defaultdict
import asyncio

class ConnectionManager:
    """Manage WebSocket connections for real-time collaboration."""
    def __init__(self):
        self.active: dict = defaultdict(list)  # room_id -> [WebSocket]
        self.cursors: dict = defaultdict(dict)  # room_id -> {user_id: cursor_pos}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        self.active[room_id].append(websocket)
        # Send current participants
        await websocket.send_json({
            "type": "joined",
            "room_id": room_id,
            "participants": len(self.active[room_id]),
            "cursors": self.cursors[room_id]
        })
        # Notify others
        await self.broadcast(room_id, {
            "type": "user_joined",
            "user_id": user_id,
            "participants": len(self.active[room_id])
        }, exclude=websocket)
    
    async def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        if websocket in self.active[room_id]:
            self.active[room_id].remove(websocket)
        if user_id in self.cursors[room_id]:
            del self.cursors[room_id][user_id]
        await self.broadcast(room_id, {
            "type": "user_left",
            "user_id": user_id,
            "participants": len(self.active[room_id])
        })
    
    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket = None):
        for ws in self.active[room_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except:
                    pass
    
    async def handle_message(self, websocket: WebSocket, room_id: str, user_id: str, data: dict):
        msg_type = data.get("type")
        if msg_type == "cursor":
            self.cursors[room_id][user_id] = data.get("position", {})
            await self.broadcast(room_id, {
                "type": "cursor",
                "user_id": user_id,
                "position": data.get("position", {})
            }, exclude=websocket)
        elif msg_type == "edit":
            # Broadcast edit to all participants
            await self.broadcast(room_id, {
                "type": "edit",
                "user_id": user_id,
                "element_id": data.get("element_id"),
                "changes": data.get("changes", {})
            }, exclude=websocket)
        elif msg_type == "component_add":
            await self.broadcast(room_id, {
                "type": "component_add",
                "user_id": user_id,
                "component": data.get("component"),
                "position": data.get("position")
            }, exclude=websocket)
        elif msg_type == "component_remove":
            await self.broadcast(room_id, {
                "type": "component_remove",
                "user_id": user_id,
                "component_id": data.get("component_id")
            }, exclude=websocket)
        elif msg_type == "chat":
            await self.broadcast(room_id, {
                "type": "chat",
                "user_id": user_id,
                "message": data.get("message"),
                "timestamp": data.get("timestamp")
            })

ws_manager = ConnectionManager()

@app.websocket("/ws/collab/{room_id}")
async def websocket_collab(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time canvas collaboration."""
    user_id = websocket.query_params.get("user_id", "anonymous")
    await ws_manager.connect(websocket, room_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(websocket, room_id, user_id, data)
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(websocket, room_id, user_id)
