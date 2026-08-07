"""Organization schemas for EvolvixOS API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Schema for organization API responses."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    owner_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member responses."""
    user_id: str
    role: str
    joined_at: datetime

    model_config = {'from_attributes': True}


class AddMemberRequest(BaseModel):
    """Schema for adding a member to an organization."""
    user_id: str
    role: str = Field("member", pattern="^(admin|member|viewer)$")
