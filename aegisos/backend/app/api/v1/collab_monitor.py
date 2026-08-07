"""API for Agent Collaboration + Real-Time Monitoring — Phase 18."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.agent_collaboration import (
    get_collaboration_service, COLLAB_PATTERNS,
)
from app.services.realtime_monitor import get_realtime_monitor

router = APIRouter(prefix="/collab-monitor", tags=["collab-monitor"])


class CreateSessionRequest(BaseModel):
    name: str
    pattern: str
    project: str = ""
    description: str = ""
    custom_steps: list = None


class UpdateStepRequest(BaseModel):
    status: str
    output_data: dict = {}
    score: Optional[float] = None
    verdict: Optional[str] = None
    findings: list = []
    recommendations: list = []


class EmitEventRequest(BaseModel):
    type: str
    source: str
    message: str
    data: dict = {}
    severity: str = "info"


# === Collaboration Endpoints ===

@router.get("/patterns")
async def list_patterns(current_user: User = Depends(get_current_active_user)):
    return get_collaboration_service().list_patterns()


@router.get("/patterns/{key}")
async def get_pattern(key: str, current_user: User = Depends(get_current_active_user)):
    pat = get_collaboration_service().get_pattern(key)
    return pat or {"error": "not found"}


@router.post("/sessions")
async def create_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_active_user),
):
    session = get_collaboration_service().create_session(
        name=req.name, pattern=req.pattern,
        project=req.project, description=req.description,
        custom_steps=req.custom_steps,
    )
    # Emit real-time event
    get_realtime_monitor().emit(
        "collaboration_started", "collaboration",
        f"Session '{req.name}' created with pattern '{req.pattern}'",
        {"session_id": session.id}, "success",
    )
    return session.to_dict()


@router.get("/sessions")
async def list_sessions(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    return [s.to_dict() for s in get_collaboration_service().list_sessions(status, limit)]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    s = get_collaboration_service().get_session(session_id)
    return s.to_dict() if s else {"error": "not found"}


@router.put("/sessions/{session_id}/steps/{step_id}")
async def update_step(
    session_id: str,
    step_id: str,
    req: UpdateStepRequest,
    current_user: User = Depends(get_current_active_user),
):
    success = get_collaboration_service().update_step(
        session_id, step_id, req.status,
        req.output_data, req.score, req.verdict,
        req.findings, req.recommendations,
    )
    if success:
        # Emit real-time event
        severity = "success" if req.status == "completed" else "error" if req.status == "failed" else "info"
        get_realtime_monitor().emit(
            f"step_{req.status}", "collaboration",
            f"Step {step_id} {req.status}",
            {"session_id": session_id, "score": req.score, "verdict": req.verdict},
            severity,
        )
        return {"status": "updated"}
    return {"error": "not found"}


@router.get("/sessions/{session_id}/steps/{step_id}/context")
async def get_step_context(
    session_id: str,
    step_id: str,
    current_user: User = Depends(get_current_active_user),
):
    return get_collaboration_service().get_step_context(session_id, step_id)


@router.post("/sessions/{session_id}/simulate")
async def simulate_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    result = get_collaboration_service().simulate_session(session_id)
    if "error" not in result:
        get_realtime_monitor().emit(
            "collaboration_completed", "collaboration",
            f"Session {session_id} simulation completed",
            result, "success",
        )
    return result


@router.post("/sessions/{session_id}/execute")
async def execute_session_real(
    session_id: str,
    use_verdis_context: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """Execute a collaboration session with REAL LLM calls."""
    result = get_collaboration_service().execute_session_real(session_id, use_verdis_context)
    return result


@router.get("/stats")
async def collab_stats(current_user: User = Depends(get_current_active_user)):
    return get_collaboration_service().get_stats()


# === Real-Time Monitoring Endpoints ===

@router.get("/events")
async def get_events(
    limit: int = 100,
    type: Optional[str] = None,
    source: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    return get_realtime_monitor().get_events(limit, type, source, severity)


@router.post("/events")
async def emit_event(
    req: EmitEventRequest,
    current_user: User = Depends(get_current_active_user),
):
    event = get_realtime_monitor().emit(
        req.type, req.source, req.message, req.data, req.severity,
    )
    return event.to_dict()


@router.get("/events/feed")
async def get_live_feed(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    return get_realtime_monitor().get_live_feed(limit)


@router.get("/events/types")
async def get_event_types(current_user: User = Depends(get_current_active_user)):
    return get_realtime_monitor().get_event_types()


@router.get("/metrics")
async def get_metrics(
    name: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    return get_realtime_monitor().get_metrics(name, limit)


@router.post("/metrics")
async def record_metric(
    name: str,
    value: float,
    unit: str = "",
    current_user: User = Depends(get_current_active_user),
):
    get_realtime_monitor().record_metric(name, value, unit)
    return {"status": "recorded"}


@router.get("/system-stats")
async def get_system_stats(current_user: User = Depends(get_current_active_user)):
    return get_realtime_monitor().get_system_stats()
