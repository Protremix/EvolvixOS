"""API for Developer Feedback System — Phase 24."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.feedback_system import get_feedback_system

router = APIRouter(prefix="/feedback", tags=["feedback"])


class SubmitFeedbackRequest(BaseModel):
    category: str
    rating: int
    title: str
    description: str = ""
    page: str = ""

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be 1-5")
        return v


class RespondRequest(BaseModel):
    response: str
    status: str = "resolved"


@router.post("")
async def submit_feedback(
    req: SubmitFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Submit developer feedback."""
    fb = get_feedback_system().submit(
        category=req.category, rating=req.rating, title=req.title,
        description=req.description, user=current_user.email, page=req.page,
    )
    return fb.to_dict()


@router.get("")
async def list_feedback(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """List feedback."""
    return [f.to_dict() for f in get_feedback_system().list_feedback(category, status, limit)]


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get feedback statistics."""
    return get_feedback_system().get_stats()


@router.get("/{feedback_id}")
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific feedback item."""
    fb = get_feedback_system().get(feedback_id)
    return fb.to_dict() if fb else {"error": "not found"}


@router.post("/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: str,
    req: RespondRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Respond to feedback (admin)."""
    success = get_feedback_system().respond(feedback_id, req.response, req.status)
    return {"responded": success}


@router.post("/{feedback_id}/acknowledge")
async def acknowledge_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Acknowledge feedback."""
    success = get_feedback_system().acknowledge(feedback_id)
    return {"acknowledged": success}


@router.post("/{feedback_id}/dismiss")
async def dismiss_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Dismiss feedback."""
    success = get_feedback_system().dismiss(feedback_id)
    return {"dismissed": success}


