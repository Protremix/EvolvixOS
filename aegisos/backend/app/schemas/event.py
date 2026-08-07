from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventCreate(EventBase):
    user_id: Optional[UUID] = None


class EventResponse(EventBase):
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
