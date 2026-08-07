"""
Feedback service for continuous learning and agent improvement.
"""

from typing import Optional
from collections import Counter

from sqlalchemy.orm import Session

from app.models.feedback import AgentFeedback
from app.schemas.feedback import FeedbackCreate, ImprovementSummary

import html
import re

def sanitize_feedback_text(text: str, max_length: int = 500) -> str:
    """Sanitize feedback text to prevent prompt injection and XSS."""
    if not text:
        return ""
    # HTML escape to prevent XSS
    text = html.escape(text)
    # Remove potential prompt injection markers
    text = re.sub(r'---\s*(End|Previous|Feedback).*?---', '', text, flags=re.IGNORECASE)
    # Limit length
    text = text[:max_length]
    return text.strip()


class FeedbackService:
    """Service for managing agent feedback and improvements."""

    def __init__(self, db: Session):
        self.db = db

    def create_feedback(self, user_id: str, feedback: FeedbackCreate) -> AgentFeedback:
        """Create new feedback for an agent result."""
        db_feedback = AgentFeedback(
            agent_name=feedback.agent_name,
            task_type=feedback.task_type,
            task_id=feedback.task_id,
            user_id=user_id,
            rating=feedback.rating,
            correction=sanitize_feedback_text(feedback.correction) if feedback.correction else None,
        )
        self.db.add(db_feedback)
        self.db.commit()
        self.db.refresh(db_feedback)
        return db_feedback

    def get_feedback_by_agent(self, agent_name: str, limit: int = 50) -> list[AgentFeedback]:
        """Get all feedback for a specific agent."""
        return (
            self.db.query(AgentFeedback)
            .filter(AgentFeedback.agent_name == agent_name)
            .order_by(AgentFeedback.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_feedback_by_task_type(self, task_type: str, limit: int = 50) -> list[AgentFeedback]:
        """Get all feedback for a specific task type."""
        return (
            self.db.query(AgentFeedback)
            .filter(AgentFeedback.task_type == task_type)
            .order_by(AgentFeedback.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_agent_improvements(self, agent_name: str) -> ImprovementSummary:
        """Get improvement summary for an agent."""
        feedbacks = (
            self.db.query(AgentFeedback)
            .filter(AgentFeedback.agent_name == agent_name)
            .all()
        )

        if not feedbacks:
            return ImprovementSummary(
                agent_name=agent_name,
                average_rating=0.0,
                total_feedback=0,
                common_corrections=[],
                rating_distribution={},
            )

        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
        corrections = [f.correction for f in feedbacks if f.correction]
        common = Counter(corrections).most_common(5)
        rating_dist = Counter(f.rating for f in feedbacks)

        return ImprovementSummary(
            agent_name=agent_name,
            average_rating=round(avg_rating, 2),
            total_feedback=len(feedbacks),
            common_corrections=[c for c, _ in common],
            rating_distribution={k: v for k, v in rating_dist.items()},
        )

    def enrich_agent_context(self, agent_name: str, task_type: str) -> str:
        """
        Generate a context string from past feedback to inject into agent prompts.

        This enables continuous learning — agents see their past mistakes and corrections.
        """
        feedbacks = (
            self.db.query(AgentFeedback)
            .filter(
                AgentFeedback.agent_name == agent_name,
                AgentFeedback.task_type == task_type,
            )
            .order_by(AgentFeedback.created_at.desc())
            .limit(5)
            .all()
        )

        if not feedbacks:
            return ""

        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
        corrections = [f.correction for f in feedbacks if f.correction]

        lines = [
            f"--- Previous Feedback for {agent_name} on {task_type} ---",
            f"Average rating: {avg_rating:.1f}/5 from {len(feedbacks)} reviews.",
        ]

        if corrections:
            lines.append("Past corrections to avoid:")
            for i, c in enumerate(corrections[:3], 1):
                lines.append(f"  {i}. {sanitize_feedback_text(c, 200)}")

        lines.append("--- End Feedback ---")

        return "\n".join(lines)
