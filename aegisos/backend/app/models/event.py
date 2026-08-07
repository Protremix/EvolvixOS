import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.types import GUID, JSONType

if TYPE_CHECKING:
    from app.models.user import User


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONType(),
        nullable=False,
        default=dict,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="events")
