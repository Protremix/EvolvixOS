"""API for Community Engagement — Phase 53."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.community import get_community_service

router = APIRouter(prefix="/community", tags=["community"])


class SubmitFeedbackRequest(BaseModel):
    type: str
    severity: str = "medium"
    title: str
    description: str
    category: str = "general"
    page: str = ""
    user_email: str = ""
    user_address: str = ""
    rating: int = 0
    tags: list = []


class CreateFeatureRequest(BaseModel):
    title: str
    description: str
    category: str = "general"
    priority: str = "medium"
    estimated_effort: str = ""
    target_phase: str = ""
    requested_by: str = ""
    tags: list = []


class VoteRequest(BaseModel):
    voter: str = ""


class RegisterMemberRequest(BaseModel):
    address: str
    email: str = ""
    username: str = ""


class RegisterEventRequest(BaseModel):
    address: str


class CreateEventRequest(BaseModel):
    name: str
    type: str
    description: str
    start_time: str = ""
    end_time: str = ""
    max_participants: int = 0
    reward_points: int = 100


class AddCommentRequest(BaseModel):
    author: str
    comment: str


class UpdateStatusRequest(BaseModel):
    status: str
    priority: str = ""
    resolution: str = ""


class UpdateUsabilityRequest(BaseModel):
    visits: int = 0
    avg_duration: float = 0.0
    bounce_rate: float = 0.0
    error_rate: float = 0.0
    satisfaction: float = 0.0


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_community_service().get_dashboard()

# === Feedback ===

@router.get("/feedback")
async def list_feedback(type: Optional[str] = None, status: Optional[str] = None,
                         severity: Optional[str] = None, limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [f.to_dict() for f in get_community_service().list_feedback(type, status, severity, limit)]

@router.get("/feedback/stats")
async def feedback_stats(current_user: User = Depends(get_current_active_user)):
    return get_community_service().get_feedback_stats()

@router.post("/feedback")
async def submit_feedback(req: SubmitFeedbackRequest, current_user: User = Depends(get_current_active_user)):
    return get_community_service().submit_feedback(
        req.type, req.severity, req.title, req.description,
        category=req.category, page=req.page, user_email=req.user_email,
        user_address=req.user_address, rating=req.rating, tags=req.tags,
    ).to_dict()

@router.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str, current_user: User = Depends(get_current_active_user)):
    f = get_community_service().get_feedback(feedback_id)
    return f.to_dict() if f else {"error": "Feedback not found"}

@router.patch("/feedback/{feedback_id}/status")
async def update_feedback_status(feedback_id: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    f = get_community_service().update_feedback_status(feedback_id, req.status, req.resolution)
    return f.to_dict() if f else {"error": "Feedback not found"}

@router.post("/feedback/{feedback_id}/vote")
async def vote_feedback(feedback_id: str, current_user: User = Depends(get_current_active_user)):
    f = get_community_service().vote_feedback(feedback_id)
    return f.to_dict() if f else {"error": "Feedback not found"}

# === Feature Requests ===

@router.get("/features")
async def list_features(status: Optional[str] = None, category: Optional[str] = None,
                         limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_community_service().list_feature_requests(status, category, limit)]

@router.post("/features")
async def create_feature(req: CreateFeatureRequest, current_user: User = Depends(get_current_active_user)):
    return get_community_service().create_feature_request(
        req.title, req.description, category=req.category,
        priority=req.priority, estimated_effort=req.estimated_effort,
        target_phase=req.target_phase, requested_by=req.requested_by,
        tags=req.tags,
    ).to_dict()

@router.get("/features/{req_id}")
async def get_feature(req_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_community_service().get_feature_request(req_id)
    return r.to_dict() if r else {"error": "Feature request not found"}

@router.post("/features/{req_id}/vote")
async def vote_feature(req_id: str, req: VoteRequest, current_user: User = Depends(get_current_active_user)):
    r = get_community_service().vote_feature_request(req_id, req.voter)
    return r.to_dict() if r else {"error": "Feature request not found"}

@router.patch("/features/{req_id}/status")
async def update_feature_status(req_id: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    r = get_community_service().update_feature_status(req_id, req.status, req.priority)
    return r.to_dict() if r else {"error": "Feature request not found"}

@router.post("/features/{req_id}/comments")
async def add_comment(req_id: str, req: AddCommentRequest, current_user: User = Depends(get_current_active_user)):
    r = get_community_service().add_comment(req_id, req.author, req.comment)
    return r.to_dict() if r else {"error": "Feature request not found"}

# === Members ===

@router.get("/members")
async def list_members(limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [m.to_dict() for m in get_community_service().list_members(limit)]

@router.get("/members/{address}")
async def get_member(address: str, current_user: User = Depends(get_current_active_user)):
    m = get_community_service().get_member(address)
    return m.to_dict() if m else {"error": "Member not found"}

@router.post("/members")
async def register_member(req: RegisterMemberRequest, current_user: User = Depends(get_current_active_user)):
    return get_community_service().register_member(req.address, req.email, req.username).to_dict()

@router.post("/members/{address}/badge/{badge_type}")
async def award_badge(address: str, badge_type: str, current_user: User = Depends(get_current_active_user)):
    m = get_community_service().award_badge(address, badge_type)
    return m.to_dict() if m else {"error": "Member not found"}

@router.get("/leaderboard")
async def leaderboard(limit: int = 20, current_user: User = Depends(get_current_active_user)):
    return [m.to_dict() for m in get_community_service().get_leaderboard(limit)]

# === Events ===

@router.get("/events")
async def list_events(status: Optional[str] = None, type: Optional[str] = None,
                       limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [e.to_dict() for e in get_community_service().list_events(status, type, limit)]

@router.post("/events")
async def create_event(req: CreateEventRequest, current_user: User = Depends(get_current_active_user)):
    return get_community_service().create_event(
        req.name, req.type, req.description,
        start_time=req.start_time, end_time=req.end_time,
        max_participants=req.max_participants, reward_points=req.reward_points,
    ).to_dict()

@router.get("/events/{event_id}")
async def get_event(event_id: str, current_user: User = Depends(get_current_active_user)):
    e = get_community_service().get_event(event_id)
    return e.to_dict() if e else {"error": "Event not found"}

@router.post("/events/{event_id}/register")
async def register_for_event(event_id: str, req: RegisterEventRequest, current_user: User = Depends(get_current_active_user)):
    e = get_community_service().register_for_event(event_id, req.address)
    return e.to_dict() if e else {"error": "Event not found or full"}

@router.patch("/events/{event_id}/status")
async def update_event_status(event_id: str, req: UpdateStatusRequest, current_user: User = Depends(get_current_active_user)):
    e = get_community_service().update_event_status(event_id, req.status)
    return e.to_dict() if e else {"error": "Event not found"}

# === Badges ===

@router.get("/badges")
async def list_badges(current_user: User = Depends(get_current_active_user)):
    return [b.to_dict() for b in get_community_service().list_badges()]

@router.get("/badges/{badge_id}")
async def get_badge(badge_id: str, current_user: User = Depends(get_current_active_user)):
    b = get_community_service().get_badge(badge_id)
    return b.to_dict() if b else {"error": "Badge not found"}

# === Usability ===

@router.get("/usability")
async def list_usability(current_user: User = Depends(get_current_active_user)):
    return [u.to_dict() for u in get_community_service().list_usability()]

@router.get("/usability/{page}")
async def get_usability(page: str, current_user: User = Depends(get_current_active_user)):
    u = get_community_service().get_usability(page)
    return u.to_dict() if u else {"error": "Page not tracked"}

@router.patch("/usability/{page}")
async def update_usability(page: str, req: UpdateUsabilityRequest, current_user: User = Depends(get_current_active_user)):
    return get_community_service().update_usability(
        page, visits=req.visits, avg_duration=req.avg_duration,
        bounce_rate=req.bounce_rate, error_rate=req.error_rate,
        satisfaction=req.satisfaction,
    ).to_dict()

@router.get("/usability/summary")
async def usability_summary(current_user: User = Depends(get_current_active_user)):
    return get_community_service().get_usability_summary()
