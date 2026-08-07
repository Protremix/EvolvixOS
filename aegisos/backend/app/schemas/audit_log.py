from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogBase(BaseModel):
    action: str = Field(..., min_length=1, max_length=255)
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=36)
    details: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    user_id: UUID


class AuditLogResponse(AuditLogBase):
    id: UUID
    user_id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
