"""Organization model for EvolvixOS."""

import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Table
from app.models.types import GUID
from sqlalchemy.orm import relationship

from app.models.base import Base


# Association table for organization members
org_members = Table(
    "org_members",
    Base.metadata,
    Column("id", GUID, primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("org_id", GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(20), nullable=False, default="member"),  # admin, member, viewer
    Column("joined_at", DateTime, default=lambda: datetime.now(UTC)),
)


class Organization(Base):
    """Organization entity for grouping users and projects."""
    __tablename__ = "organizations"

    id = Column(GUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("User", secondary=org_members, backref="organizations")
