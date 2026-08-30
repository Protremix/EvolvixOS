
"""
EvolvixOS Platform API: awesome-llm-apps integration endpoints
Add these routes to the platform API (port 8080).
"""
from fastapi import APIRouter, HTTPException
from autonomous_loop import autonomous_loop
from pydantic import BaseModel

router = APIRouter(prefix="/api/awesome", tags=["awesome-llm-apps"])

# ─── Agent Templates ───
@router.get("/templates")
async def list_templates():
    """List all 50+ agent templates from awesome-llm-apps."""
    import json, os
    catalog_path = "/opt/evolvixos/knowledge/agent_templates_catalog.json"
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            return json.load(f)
    return {"error": "Catalog not found"}

@router.get("/templates/{category}")
async def get_templates_by_category(category: str):
    """Get templates by category (starter, advanced, teams, rag, mcp, voice, skills)."""
    import json, os
    catalog_path = "/opt/evolvixos/knowledge/agent_templates_catalog.json"
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            catalog = json.load(f)
        if category in catalog:
            return catalog[category]
    raise HTTPException(404, f"Category '{category}' not found")

# ─── Multi-Agent Teams ───
class TeamCreateRequest(BaseModel):
    name: str
    description: str = ""
    members: list = []

class TeamExecuteRequest(BaseModel):
    team_name: str
    task: str
    context: str = ""

@router.get("/teams")
async def list_teams():
    from team_orchestrator import orchestrator
    return orchestrator.list_teams()

@router.post("/teams")
async def create_team(req: TeamCreateRequest):
    from team_orchestrator import orchestrator
    team = orchestrator.create_team(req.name, req.description, req.members)
    return {"ok": True, "team": team.name, "members": len(team.members)}

@router.post("/teams/execute")
async def execute_team(req: TeamExecuteRequest):
    from team_orchestrator import orchestrator
    result = await orchestrator.execute(req.team_name, req.task, req.context)
    return result

@router.get("/teams/executions")
async def list_team_executions():
    from team_orchestrator import orchestrator
    return orchestrator.list_executions()

@router.get("/teams/executions/{exec_id}")
async def get_team_execution(exec_id: str):
    from team_orchestrator import orchestrator
    data = orchestrator.get_execution(exec_id)
    if not data:
        raise HTTPException(404, "Execution not found")
    return data

@router.post("/teams/from-template/{template_name}")
async def create_team_from_template(template_name: str):
    from team_orchestrator import orchestrator
    team = orchestrator.from_template(template_name)
    if team:
        return {"ok": True, "team": team.name, "members": len(team.members)}
    raise HTTPException(404, f"Template '{template_name}' not found")

# ─── RAG Engine ───
class RAGCreateRequest(BaseModel):
    collection: str

class RAGAddRequest(BaseModel):
    collection: str
    text: str = ""
    url: str = ""
    source: str = ""

class RAGQueryRequest(BaseModel):
    collection: str
    question: str
    model: str = "auto"

@router.get("/rag/collections")
async def rag_list_collections():
    from rag_engine import rag_engine
    return {"collections": rag_engine.list_collections()}

@router.post("/rag/collections")
async def rag_create_collection(req: RAGCreateRequest):
    from rag_engine import rag_engine
    if rag_engine.create_collection(req.collection):
        return {"ok": True, "collection": req.collection}
    raise HTTPException(500, "Failed to create collection")

@router.post("/rag/add")
async def rag_add_documents(req: RAGAddRequest):
    from rag_engine import rag_engine
    docs = []
    if req.text:
        docs.append({"text": req.text, "source": req.source or "manual"})
    count = 0
    if docs:
        count = rag_engine.add_documents(req.collection, docs)
    if req.url:
        count += rag_engine.add_url(req.collection, req.url)
    return {"ok": True, "chunks_added": count}

@router.post("/rag/query")
async def rag_query(req: RAGQueryRequest):
    from rag_engine import rag_engine
    return rag_engine.query(req.collection, req.question, req.model)

@router.delete("/rag/collections/{name}")
async def rag_delete_collection(name: str):
    from rag_engine import rag_engine
    if rag_engine.delete_collection(name):
        return {"ok": True}
    raise HTTPException(404, f"Collection '{name}' not found")

# ─── Agent Skills ───
@router.get("/skills")
async def list_skills():
    from skill_registry import skill_registry
    return {"skills": skill_registry.list_skills()}

@router.get("/skills/{name}")
async def get_skill(name: str):
    from skill_registry import skill_registry
    skill = skill_registry.get_skill(name)
    if skill:
        return {"name": skill.name, "description": skill.description, "instructions": skill.instructions[:500], "scripts": skill.scripts}
    raise HTTPException(404, f"Skill '{name}' not found")

class SkillRunRequest(BaseModel):
    name: str
    args: str = ""

@router.post("/skills/run")
async def run_skill(req: SkillRunRequest):
    from skill_registry import skill_registry
    return skill_registry.run_skill(req.name, req.args)

# ─── MCP Router ───
@router.get("/mcp/agents")
async def mcp_list_agents():
    from mcp_router import mcp_router
    return {"agents": mcp_router.list_agents()}

class MCPRouterRequest(BaseModel):
    query: str

@router.post("/mcp/route")
async def mcp_route(req: MCPRouterRequest):
    from mcp_router import mcp_router
    return mcp_router.route(req.query)

# ─── Dashboard Stats ───
@router.get("/stats")
async def awesome_stats():
    """Get integration stats for the dashboard."""
    import json, os
    catalog_path = "/opt/evolvixos/knowledge/agent_templates_catalog.json"
    stats = {"templates": 0, "categories": 0}
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            catalog = json.load(f)
        stats["categories"] = len(catalog)
        stats["templates"] = sum(len(v) for v in catalog.values())
    return stats


# === AUTONOMOUS LOOP ENDPOINTS ===

class AutonomousStartRequest(BaseModel):
    goal: str
    context: str = ""
    max_rounds: int = 10

@router.post("/autonomous/start")
async def start_autonomous_task(req: AutonomousStartRequest):
    """Start a new autonomous task with plan->execute->verify->reflect loop."""
    result = await autonomous_loop.start(req.goal, req.context, req.max_rounds)
    return result

@router.get("/autonomous/tasks")
async def list_autonomous_tasks():
    """List all autonomous tasks."""
    return autonomous_loop.list_tasks()

@router.get("/autonomous/tasks/{task_id}")
async def get_autonomous_task(task_id: str):
    """Get details of a specific autonomous task."""
    task = autonomous_loop.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

