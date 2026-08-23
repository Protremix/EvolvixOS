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

from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, async_session
from entities.manager import EntityManager
from entities.crud import EntityCRUD as EnhancedCRUD
from auth.middleware import optional_auth, require_auth, require_admin, get_user_from_token
from workflows.engine import WorkflowEngine
from agents.manager import AgentManager

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
    system_prompt: str = Field(..., description="System prompt for the agent")
    model: str = Field("qwen2.5:7b", description="Ollama model")
    temperature: float = Field(0.7, description="Temperature 0-1")
    tools: list = Field(default_factory=list, description="Available tools")

class AgentUpdate(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[list] = None
    status: Optional[str] = None

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
        result = await EnhancedCRUD.list_records(db, name, limit=limit, skip=skip, filters=filters, sort=sort)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/entities/{name}/records")
async def create_record(name: str, record: RecordCreate, db=Depends(get_db)):
    """Create a new entity record."""
    try:
        return await EnhancedCRUD.create_record(db, name, record.data)
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
async def update_record(name: str, record_id: int, record: RecordUpdate, db=Depends(get_db)):
    """Update an entity record."""
    try:
        return await EnhancedCRUD.update_record(db, name, record_id, record.data)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/entities/{name}/records/{record_id}")
async def delete_record(name: str, record_id: int, db=Depends(get_db)):
    """Delete an entity record."""
    try:
        return await EnhancedCRUD.delete_record(db, name, record_id)
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
        result = await EnhancedCRUD.list_records(db, name, limit=limit, skip=skip, filters=filters, sort=sort)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Agents ───
@app.get("/api/agents")
async def list_agents(db=Depends(get_db)):
    """List all AI agents."""
    agents = await AgentManager.list_agents(db)
    return {"agents": agents}

@app.post("/api/agents")
async def create_agent(agent: AgentCreate, db=Depends(get_db)):
    """Create a new AI agent with custom system prompt."""
    try:
        return await AgentManager.create_agent(db, agent.name, agent.system_prompt,
            agent.model, agent.temperature, agent.tools)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/agents/{name}")
async def get_agent(name: str, db=Depends(get_db)):
    """Get agent details including system prompt and memory."""
    agent = await AgentManager.get_agent(db, name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    return agent

@app.put("/api/agents/{name}")
async def update_agent(name: str, updates: AgentUpdate, db=Depends(get_db)):
    """Update agent configuration."""
    try:
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        return await AgentManager.update_agent(db, name, update_data)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete("/api/agents/{name}")
async def delete_agent(name: str, db=Depends(get_db)):
    """Delete an agent."""
    try:
        return await AgentManager.delete_agent(db, name)
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.post("/api/agents/{name}/invoke")
async def invoke_agent(name: str, msg: AgentInvoke, db=Depends(get_db)):
    """Invoke an agent — send a message and get a response."""
    try:
        return await AgentManager.invoke_agent(db, name, msg.message, msg.context)
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
@app.post("/api/chat")
async def chat_build(msg: ChatMessage, db=Depends(get_db)):
    """
    AI chat builder — talk to the platform to create entities, functions, workflows.
    Uses the local Ollama LLM to interpret intent and execute actions.
    """
    import urllib.request

    # Get existing entities so the LLM knows what's already built
    existing_entities = await EntityManager.list_entities(db)
    existing_names = [e["name"] for e in existing_entities] if existing_entities else []
    existing_summary = ", ".join(existing_names) if existing_names else "none yet"

    # System prompt that teaches the LLM about platform capabilities
    system_prompt = f"""You are EvolvixOS Platform Builder. You help users build apps by creating entities, backend functions, and workflows via natural language.

CURRENT STATE — Entities already in the project: {existing_summary}

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

Always respond with a JSON action object. If the user just wants to chat, respond with {{"action": "chat", "message": "your response"}}."""

    # ─── LLM Chain: OpenRouter (smart routing) → GLM direct → Ollama local ───
    ai_response = None

    # "auto" = smart routing — pick best model for the task
    selected_model = msg.model or "auto"
    if selected_model == "auto":
        msg_lower = msg.message.lower()
        if any(w in msg_lower for w in ["build", "create", "make", "add", "entity", "crm", "app", "store", "shop", "dashboard", "blog", "inventory", "task", "project", "social"]):
            selected_model = "z-ai/glm-5"
        elif any(w in msg_lower for w in ["code", "function", "api", "deploy", "python", "script", "backend", "endpoint"]):
            selected_model = "openai/gpt-oss-120b"
        elif any(w in msg_lower for w in ["analyze", "reason", "think", "complex", "architect", "design", "plan", "strategy"]):
            selected_model = "z-ai/glm-5.2"
        elif any(w in msg_lower for w in ["hello", "hi", "hey", "help", "what", "how", "why", "thanks", "thank"]):
            selected_model = "openai/gpt-oss-20b"
        elif len(msg.message) > 500:
            selected_model = "z-ai/glm-5"
        else:
            selected_model = "openai/gpt-oss-20b"

    # Try OpenRouter (unified gateway, 422+ models)
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if or_key:
        fallback_chain = list(dict.fromkeys([selected_model, "z-ai/glm-5", "openai/gpt-oss-20b", "z-ai/glm-5.2:free"]))
        for try_model in fallback_chain:
            try:
                or_payload = json.dumps({
                    "model": try_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": msg.message}
                    ],
                    "stream": False,
                    "temperature": 0.3,
                    "max_tokens": 2000
                }).encode()
                or_req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=or_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {or_key}",
                        "HTTP-Referer": "https://evolvixos.com",
                        "X-Title": "EvolvixOS"
                    }
                )
                or_resp = urllib.request.urlopen(or_req, timeout=60)
                or_data = json.loads(or_resp.read())
                or_resp.close()
                or_msg = or_data.get("choices", [{}])[0].get("message", {})
                ai_response = or_msg.get("content") or or_msg.get("reasoning", "") or ""
                if ai_response and len(ai_response) > 5:
                    break
                ai_response = None
            except Exception as or_err:
                print(f"OpenRouter {try_model} failed: {or_err}")
                continue

    # Fallback: GLM direct (Z.ai)
    zai_key = os.environ.get("ZAI_API_KEY", "")
    if ai_response is None and zai_key:
        try:
            glm_payload = json.dumps({
                "model": "glm-4.5-flash",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": msg.message}
                ],
                "stream": False,
                "temperature": 0.3,
                "max_tokens": 2000
            }).encode()
            glm_req = urllib.request.Request(
                "https://api.z.ai/api/paas/v4/chat/completions",
                data=glm_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {zai_key}",
                    "Accept-Language": "en-US,en"
                }
            )
            glm_resp = urllib.request.urlopen(glm_req, timeout=60)
            glm_data = json.loads(glm_resp.read())
            ai_response = glm_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            glm_resp.close()
        except Exception as glm_err:
            print(f"GLM failed: {glm_err}")

    # Last resort: Ollama local
    if ai_response is None:
        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        ollama_payload = json.dumps({
            "model": "qwen2.5:7b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg.message}
            ],
            "stream": False,
            "options": {"temperature": 0.3}
        }).encode()
        try:
            ollama_req = urllib.request.Request(f"{ollama_url}/api/chat", data=ollama_payload, headers={"Content-Type": "application/json"})
            ollama_resp = urllib.request.urlopen(ollama_req, timeout=30)
            ollama_data = json.loads(ollama_resp.read())
            ai_response = ollama_data.get("message", {}).get("content", "")
            ollama_resp.close()
        except Exception as ollama_err:
            return {"error": f"All LLM providers failed: {ollama_err}", "message": "Sorry, I couldn't process that."}

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
