import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
