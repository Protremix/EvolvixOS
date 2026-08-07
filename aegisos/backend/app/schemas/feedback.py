"""Pydantic schemas for Agent Feedback Loop."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=100)
    task_type: str = Field(..., min_length=1, max_length=100)
    task_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    correction: Optional[str] = None
    original_result: Optional[Dict[str, Any]] = None


class FeedbackResponse(BaseModel):
    id: UUID
    agent_name: str
    task_type: str
    task_id: Optional[str] = None
    user_id: Optional[UUID] = None
    rating: int
    correction: Optional[str] = None
    original_result: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeedbackList(BaseModel):
    items: List[FeedbackResponse]
    total: int


class ImprovementSummary(BaseModel):
    """Agent improvement summary based on accumulated feedback."""
    agent_name: str
    average_rating: float
    total_feedback: int
    common_corrections: List[str]
    rating_distribution: Dict[int, int]
