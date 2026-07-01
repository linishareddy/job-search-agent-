import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AtsCompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    source: str = Field(..., pattern="^(greenhouse|lever|ashby)$")


class AtsCompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    source: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
