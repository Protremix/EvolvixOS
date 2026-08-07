"""API for Agent Simulation + Verdis Enhancement — Phase 17."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.agent_simulation import (
    get_simulation_service, SimulationScenario,
)
from app.services.verdis_agent_enhancer import (
    get_verdis_enhancer, AgentActivity, VERDIS_TASK_TYPES,
)

router = APIRouter(prefix="/agent-enhancement", tags=["agent-enhancement"])


class CreateScenarioRequest(BaseModel):
    name: str
    description: str = ""
    agent_name: str
    task_type: str
    mock_input: dict = {}
    mock_output: dict = {}
    mock_score: float = 8.0
    mock_verdict: str = "GO"
    mock_findings: list = []
    mock_recommendations: list = []
    tags: list = []


class RecordActivityRequest(BaseModel):
    agent_name: str
    task_type: str
    status: str = "completed"
    project: str = ""
    input_summary: str = ""
    output_summary: str = ""
    score: Optional[float] = None
    verdict: Optional[str] = None
    findings_count: int = 0
    recommendations_count: int = 0
    tokens_used: int = 0
    latency_ms: float = 0.0
    is_simulation: bool = False


# === Simulation Endpoints ===

@router.get("/simulations")
async def list_scenarios(
    agent_name: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List simulation scenarios."""
    return [s.to_dict() for s in get_simulation_service().list_scenarios(agent_name, tag)]


@router.get("/simulations/stats")
async def get_simulation_stats(current_user: User = Depends(get_current_active_user)):
    """Get simulation statistics."""
    return get_simulation_service().get_stats()


@router.get("/simulations/history")
async def get_simulation_history(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get simulation execution history."""
    return get_simulation_service().get_history(limit)


@router.post("/simulations/run-agent")
async def run_agent_simulation(
    agent_name: str,
    task_type: str,
    data: dict = {},
    current_user: User = Depends(get_current_active_user),
):
    """Run a simulated agent task."""
    return get_simulation_service().run_agent_simulation(agent_name, task_type, data)


@router.post("/simulations")
async def create_scenario(
    req: CreateScenarioRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a custom simulation scenario."""
    scenario = SimulationScenario(
        name=req.name, description=req.description,
        agent_name=req.agent_name, task_type=req.task_type,
        mock_input=req.mock_input, mock_output=req.mock_output,
        mock_score=req.mock_score, mock_verdict=req.mock_verdict,
        mock_findings=req.mock_findings, mock_recommendations=req.mock_recommendations,
        tags=req.tags,
    )
    return get_simulation_service().create_scenario(scenario).to_dict()


@router.get("/simulations/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific scenario."""
    s = get_simulation_service().get_scenario(scenario_id)
    return s.to_dict() if s else {"error": "not found"}


@router.post("/simulations/{scenario_id}/run")
async def run_simulation(
    scenario_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Run a simulation scenario."""
    return get_simulation_service().run_simulation(scenario_id)


# === Verdis Enhancement Endpoints ===

@router.get("/verdis-context")
async def get_verdis_context(current_user: User = Depends(get_current_active_user)):
    """Get Verdis agent context."""
    return get_verdis_enhancer().get_context().to_dict()


@router.get("/verdis-context/prompt")
async def get_verdis_context_prompt(current_user: User = Depends(get_current_active_user)):
    """Get Verdis context as prompt string."""
    return {"prompt": get_verdis_enhancer().get_context_prompt()}


@router.put("/verdis-context")
async def update_verdis_context(
    data: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Update Verdis context."""
    get_verdis_enhancer().update_context(**data)
    return {"status": "updated"}


@router.get("/verdis-task-types")
async def get_verdis_task_types(current_user: User = Depends(get_current_active_user)):
    """Get Verdis-specific task types."""
    return VERDIS_TASK_TYPES


@router.post("/enhancement/{enabled}")
async def toggle_enhancement(
    enabled: bool,
    current_user: User = Depends(get_current_active_user),
):
    """Enable or disable Verdis context injection."""
    if enabled:
        get_verdis_enhancer().enable()
    else:
        get_verdis_enhancer().disable()
    return {"enhancement_enabled": enabled}


# === Agent Activity Endpoints ===

@router.get("/activities")
async def get_activities(
    agent_name: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get agent activities."""
    return [a.to_dict() for a in get_verdis_enhancer().get_activities(agent_name, limit)]


@router.post("/activities")
async def record_activity(
    req: RecordActivityRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Record an agent activity."""
    activity = AgentActivity(
        agent_name=req.agent_name, task_type=req.task_type,
        status=req.status, project=req.project,
        input_summary=req.input_summary, output_summary=req.output_summary,
        score=req.score, verdict=req.verdict,
        findings_count=req.findings_count, recommendations_count=req.recommendations_count,
        tokens_used=req.tokens_used, latency_ms=req.latency_ms,
        is_simulation=req.is_simulation,
    )
    get_verdis_enhancer().record_activity(activity)
    return {"status": "recorded", "id": activity.id}


@router.get("/activities/stats")
async def get_agent_stats(current_user: User = Depends(get_current_active_user)):
    """Get per-agent statistics."""
    return get_verdis_enhancer().get_agent_stats()


@router.get("/overview")
async def get_enhancement_overview(current_user: User = Depends(get_current_active_user)):
    """Get overview of all agent enhancement data."""
    return get_verdis_enhancer().get_overview()
