"""
Feedback model — stores user feedback and corrections for AI agent executions.
"""

import uuid
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import String, Text, DateTime, Integer, JSON, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.user import User


class AgentFeedback(Base):
    """SQLAlchemy model for storing feedback on AI agent performance."""
    __tablename__ = "agent_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_agent_feedback_agent_task", "agent_name", "task_type"),
    )
