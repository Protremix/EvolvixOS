"""
Feature Delivery Pipeline API — Post-MVP Phase 1

Provides endpoints for creating, tracking, and managing autonomous
feature delivery pipeline runs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.feature_pipeline import (
    FeatureRequest, FeaturePipelineRun, create_pipeline_run,
    get_pipeline_progress, get_pipeline_summary,
    PipelineStage, STAGE_DEFS, get_stage_def,
)
import uuid
from app.services.pipeline_executor import get_executor, PipelineExecutor

router = APIRouter(prefix="/feature-pipeline", tags=["feature-pipeline"])

# In-memory store (production would use DB)
_pipeline_runs: dict[str, FeaturePipelineRun] = {}


class CreatePipelineRequest(BaseModel):
    """Request to start a new feature delivery pipeline."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    project_type: str = Field("generic")
    priority: str = Field("medium")
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class PipelineRunResponse(BaseModel):
    id: str
    feature: dict
    stages: list[dict]
    status: str
    current_stage: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    total_duration_ms: int = 0
    summary: str = ""


class ProgressResponse(BaseModel):
    total: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_pct: float
    current_stage: Optional[str] = None
    status: str


class StageInfoResponse(BaseModel):
    stage: str
    name: str
    description: str
    agent: str
    max_retries: int
    order: int


def run_to_response(run: FeaturePipelineRun) -> PipelineRunResponse:
    return PipelineRunResponse(
        id=run.id,
        feature=run.feature.model_dump(),
        stages=[s.model_dump() for s in run.stages],
        status=run.status,
        current_stage=run.current_stage,
        created_at=run.created_at,
        completed_at=run.completed_at,
        total_duration_ms=run.total_duration_ms,
        summary=run.summary,
    )


@router.post("/", response_model=PipelineRunResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    request: CreatePipelineRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new feature delivery pipeline run."""
    feature = FeatureRequest(
        title=request.title,
        description=request.description,
        project_type=request.project_type,
        priority=request.priority,
        constraints=request.constraints,
        acceptance_criteria=request.acceptance_criteria,
    )
    run = create_pipeline_run(feature)
    _pipeline_runs[run.id] = run

    from app.core.logging import get_logger
    get_logger("api.feature_pipeline").info(
        "pipeline_created", pipeline_id=run.id, feature=feature.title
    )

    return run_to_response(run)


@router.get("/", response_model=list[PipelineRunResponse])
async def list_pipelines(
    current_user: User = Depends(get_current_active_user),
):
    """List all pipeline runs."""
    return [run_to_response(r) for r in _pipeline_runs.values()]


@router.get("/{pipeline_id}", response_model=PipelineRunResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific pipeline run."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run_to_response(run)


@router.get("/{pipeline_id}/progress", response_model=ProgressResponse)
async def get_progress(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get progress of a pipeline run."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return ProgressResponse(**get_pipeline_progress(run))


@router.get("/{pipeline_id}/summary")
async def get_pipeline_summary_api(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a human-readable summary of the pipeline."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return {"summary": get_pipeline_summary(run)}


@router.get("/stages/info", response_model=list[StageInfoResponse])
async def get_stages_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get information about all pipeline stages."""
    return [
        StageInfoResponse(
            stage=s["stage"].value,
            name=s["name"],
            description=s["description"],
            agent=s["agent"],
            max_retries=s["max_retries"],
            order=i,
        )
        for i, s in enumerate(STAGE_DEFS)
    ]


@router.post("/{pipeline_id}/stages/{stage}/retry", response_model=PipelineRunResponse)
async def retry_stage(
    pipeline_id: str,
    stage: str,
    current_user: User = Depends(get_current_active_user),
):
    """Retry a failed stage."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    from app.services.feature_pipeline import update_stage_result, should_retry, StageStatus
    try:
        stage_enum = PipelineStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    if not should_retry(run, stage_enum):
        raise HTTPException(status_code=400, detail="Stage cannot be retried (max retries exceeded)")

    for s in run.stages:
        if s.stage == stage:
            s.retry_count += 1
            s.status = StageStatus.PENDING
            break

    return run_to_response(run)




@router.post("/{pipeline_id}/execute", response_model=PipelineRunResponse)
async def execute_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Execute a pipeline run through all stages."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    if run.status in ("running", "completed"):
        raise HTTPException(status_code=400, detail=f"Pipeline is already {run.status}")
    
    executor = get_executor()
    run = executor.execute_pipeline(run)
    _pipeline_runs[pipeline_id] = run
    return run_to_response(run)


@router.post("/{pipeline_id}/execute/{stage}", response_model=PipelineRunResponse)
async def execute_single_stage(
    pipeline_id: str,
    stage: str,
    current_user: User = Depends(get_current_active_user),
):
    """Execute a single stage of the pipeline."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    try:
        stage_enum = PipelineStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    
    executor = get_executor()
    success = executor._execute_stage(run, stage_enum)
    _pipeline_runs[pipeline_id] = run
    return run_to_response(run)


@router.post("/{pipeline_id}/cancel", response_model=PipelineRunResponse)
async def cancel_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a running pipeline."""
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    executor = get_executor()
    cancelled = executor.cancel_run(pipeline_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Pipeline cannot be cancelled (not running)")
    _pipeline_runs[pipeline_id] = run
    return run_to_response(run)


@router.get("/active/list", response_model=list[PipelineRunResponse])
async def list_active_pipelines(
    current_user: User = Depends(get_current_active_user),
):
    """List all currently active (running) pipelines."""
    executor = get_executor()
    return [run_to_response(r) for r in executor.list_active_runs()]


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a pipeline run."""
    if pipeline_id not in _pipeline_runs:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    del _pipeline_runs[pipeline_id]


# --- Event & WebSocket endpoints ---

from app.services.pipeline_events import get_event_bus
from fastapi import WebSocket, WebSocketDisconnect


@router.get("/{pipeline_id}/events")
async def get_pipeline_events(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get all events for a specific pipeline (for replay/audit)."""
    bus = get_event_bus()
    events = bus.get_pipeline_events(pipeline_id)
    return {"pipeline_id": pipeline_id, "events": events, "count": len(events)}


@router.get("/events/recent")
async def get_recent_events(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get recent pipeline events across all pipelines."""
    bus = get_event_bus()
    events = bus.get_recent_events(limit=limit)
    return {"events": events, "count": len(events)}


@router.websocket("/ws")
async def pipeline_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time pipeline events."""
    await websocket.accept()
    bus = get_event_bus()

    # Register as an async listener
    async def on_event(event):
        try:
            await websocket.send_json(event.to_dict())
        except Exception:
            pass

    bus.subscribe_async(on_event)

    try:
        # Send recent events as initial state
        recent = bus.get_recent_events(limit=10)
        for evt in recent:
            await websocket.send_json(evt)

        # Keep connection alive, listening for client messages
        while True:
            data = await websocket.receive_text()
            # Client can request specific pipeline events
            if data.startswith("subscribe:"):
                pipeline_id = data.split(":", 1)[1]
                events = bus.get_pipeline_events(pipeline_id)
                for evt in events:
                    await websocket.send_json(evt)
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(on_event)
