from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=150, description="Unique username")
    email: EmailStr = Field(..., description="Unique email address")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")
    is_active: bool = Field(default=True, description="Account active status")


class UserCreate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=150)
    full_name: Optional[str] = Field(default=None, max_length=200, description="Display name, used to derive username if not given")
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    role: Optional[UserRole] = Field(default=UserRole.VIEWER)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[UUID] = None
    role: Optional[str] = None
