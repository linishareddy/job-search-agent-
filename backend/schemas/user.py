import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str]
    is_active: bool
    email_enabled: bool
    auto_apply_enabled: bool
    auto_apply_min_score: float
    auto_apply_resume_id: Optional[uuid.UUID]
    auto_apply_max_per_run: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPreferencesUpdate(BaseModel):
    name: Optional[str] = None
    email_enabled: Optional[bool] = None
    auto_apply_enabled: Optional[bool] = None
    auto_apply_min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    auto_apply_resume_id: Optional[uuid.UUID] = None
    auto_apply_max_per_run: Optional[int] = Field(default=None, ge=1, le=50)
