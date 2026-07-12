import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from schemas.job import JobResponse

_STATUSES = "^(saved|ready_to_apply|applied|interviewing|offer|rejected)$"


class JobApplicationCreate(BaseModel):
    job_id: uuid.UUID
    status: str = Field(default="saved", pattern=_STATUSES)


class JobApplicationUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern=_STATUSES)
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: uuid.UUID
    job: JobResponse
    status: str
    notes: Optional[str]
    applied_at: Optional[datetime]
    auto_prepared: bool
    match_score: Optional[float]
    cover_letter: Optional[str]
    tailored_resume: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
