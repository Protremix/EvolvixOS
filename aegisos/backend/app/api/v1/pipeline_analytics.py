"""
API endpoints for Pipeline Analytics and Scheduling.
Post-MVP Phase 5.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.pipeline_analytics import get_full_analytics, compute_pipeline_summary, compute_stage_metrics, compute_agent_metrics, compute_throughput, detect_bottlenecks, get_trends
from app.services.pipeline_scheduler import (
    ScheduledPipeline, get_scheduler, PipelineScheduler,
)

router = APIRouter(prefix="/pipeline-analytics", tags=["pipeline-analytics"])
sched_router = APIRouter(prefix="/pipeline-scheduler", tags=["pipeline-scheduler"])


# --- Analytics endpoints ---

@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_active_user),
):
    """Get full analytics overview — summary, stages, agents, throughput, bottlenecks, trends."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return get_full_analytics(runs)

@router.get("/summary")
async def get_pipeline_summary(
    current_user: User = Depends(get_current_active_user),
):
    """Get pipeline summary metrics."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return compute_pipeline_summary(runs).to_dict()

@router.get("/stages")
async def get_stage_metrics(
    current_user: User = Depends(get_current_active_user),
):
    """Get per-stage performance metrics."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return [m.to_dict() for m in compute_stage_metrics(runs)]

@router.get("/agents")
async def get_agent_metrics(
    current_user: User = Depends(get_current_active_user),
):
    """Get per-agent performance metrics."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return [m.to_dict() for m in compute_agent_metrics(runs)]

@router.get("/throughput")
async def get_throughput(
    period: str = "daily",
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
):
    """Get pipeline throughput over time."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return compute_throughput(runs, period, days).to_dict()

@router.get("/bottlenecks")
async def get_bottlenecks(
    threshold: float = 1.5,
    current_user: User = Depends(get_current_active_user),
):
    """Detect pipeline stage bottlenecks."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return detect_bottlenecks(runs, threshold)

@router.get("/trends")
async def get_trends_api(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
):
    """Get trend analysis comparing recent vs previous period."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    runs = list(_pipeline_runs.values())
    return get_trends(runs, days)


# --- Scheduler endpoints ---

@sched_router.get("/", response_model=list[dict])
async def list_schedules(
    enabled_only: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    """List all scheduled pipelines."""
    scheduler = get_scheduler()
    return [s.to_dict() for s in scheduler.list_schedules(enabled_only=enabled_only)]

@sched_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    sched: ScheduledPipeline,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new scheduled pipeline."""
    scheduler = get_scheduler()
    result = scheduler.create_schedule(sched)
    return result.to_dict()

@sched_router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific scheduled pipeline."""
    sched = get_scheduler().get_schedule(schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sched.to_dict()

@sched_router.patch("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    updates: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Update a scheduled pipeline."""
    result = get_scheduler().update_schedule(schedule_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return result.to_dict()

@sched_router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a scheduled pipeline."""
    if not get_scheduler().delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

@sched_router.post("/{schedule_id}/enable")
async def enable_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Enable a scheduled pipeline."""
    sched = get_scheduler().enable_schedule(schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sched.to_dict()

@sched_router.post("/{schedule_id}/disable")
async def disable_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Disable a scheduled pipeline."""
    sched = get_scheduler().disable_schedule(schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sched.to_dict()

@sched_router.post("/check")
async def check_and_trigger(
    current_user: User = Depends(get_current_active_user),
):
    """Manually trigger a check for due schedules."""
    triggered = get_scheduler().check_and_trigger()
    return {
        "triggered_count": len(triggered),
        "triggered": [s.to_dict() for s in triggered],
    }

@sched_router.get("/upcoming/list")
async def get_upcoming(
    limit: int = 5,
    current_user: User = Depends(get_current_active_user),
):
    """Get upcoming scheduled runs."""
    return [s.to_dict() for s in get_scheduler().get_upcoming(limit)]
