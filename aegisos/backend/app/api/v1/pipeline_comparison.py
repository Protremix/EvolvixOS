"""API for Pipeline Comparison — Post-MVP Phase 7."""

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.pipeline_comparison import compare_pipeline_runs

router = APIRouter(prefix="/pipeline-comparison", tags=["pipeline-comparison"])


@router.get("/{run_a_id}/{run_b_id}")
async def compare_runs(
    run_a_id: str,
    run_b_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Compare two pipeline runs side by side."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    run_a = _pipeline_runs.get(run_a_id)
    run_b = _pipeline_runs.get(run_b_id)
    if not run_a:
        raise HTTPException(status_code=404, detail=f"Pipeline {run_a_id} not found")
    if not run_b:
        raise HTTPException(status_code=404, detail=f"Pipeline {run_b_id} not found")
    comparison = compare_pipeline_runs(run_a, run_b)
    return comparison.to_dict()
