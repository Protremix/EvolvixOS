"""API for Agent Learning Loop — Phase 19."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.agent_learning import (
    get_learning_loop, AgentExecution,
)

router = APIRouter(prefix="/agent-learning", tags=["agent-learning"])


class RecordExecutionRequest(BaseModel):
    agent_name: str
    task_type: str
    status: str = "completed"
    score: Optional[float] = None
    verdict: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0
    findings_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    recommendations_count: int = 0
    input_summary: str = ""
    output_summary: str = ""
    session_id: Optional[str] = None
    project: str = ""


@router.post("/executions")
async def record_execution(
    req: RecordExecutionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Record an agent execution for learning analysis."""
    execution = AgentExecution(
        agent_name=req.agent_name, task_type=req.task_type,
        status=req.status, score=req.score, verdict=req.verdict,
        tokens_used=req.tokens_used, latency_ms=req.latency_ms,
        findings_count=req.findings_count, critical_findings=req.critical_findings,
        high_findings=req.high_findings, recommendations_count=req.recommendations_count,
        input_summary=req.input_summary, output_summary=req.output_summary,
        session_id=req.session_id, project=req.project,
    )
    get_learning_loop().record_execution(execution)
    return {"status": "recorded", "id": execution.id}


@router.get("/executions")
async def get_executions(
    agent_name: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get execution history."""
    loop = get_learning_loop()
    with loop._lock:
        execs = list(reversed(loop._executions))[:limit]
    if agent_name:
        execs = [e for e in execs if e.agent_name == agent_name]
    return [e.to_dict() for e in execs]


@router.post("/analyze")
async def analyze(current_user: User = Depends(get_current_active_user)):
    """Run learning analysis and generate insights."""
    insights = get_learning_loop().analyze()
    return [i.to_dict() for i in insights]


@router.get("/insights")
async def get_insights(
    agent_name: Optional[str] = None,
    insight_type: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get learning insights."""
    return [i.to_dict() for i in get_learning_loop().get_insights(agent_name, insight_type, limit)]


@router.get("/prompt-optimizations")
async def get_prompt_optimizations(
    agent_name: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    """Get prompt optimization suggestions."""
    return [o.to_dict() for o in get_learning_loop().get_prompt_optimizations(agent_name, limit)]


@router.get("/performance")
async def get_all_performance(current_user: User = Depends(get_current_active_user)):
    """Get performance metrics for all agents."""
    return get_learning_loop().get_all_performance()


@router.get("/performance/{agent_name}")
async def get_agent_performance(
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get performance metrics for a specific agent."""
    return get_learning_loop().get_agent_performance(agent_name)


@router.get("/feedback/{agent_name}")
async def get_feedback(
    agent_name: str,
    task_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get learning feedback to inject into an agent's next execution."""
    return get_learning_loop().get_feedback_for_agent(agent_name, task_type)


@router.get("/summary")
async def get_learning_summary(current_user: User = Depends(get_current_active_user)):
    """Get a summary of the learning system state."""
    return get_learning_loop().get_learning_summary()
