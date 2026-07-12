import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

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
    tailored_docx_available: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def set_docx_available(cls, data):
        if hasattr(data, "tailored_docx_path"):
            return {
                "id": data.id,
                "job": data.job,
                "status": data.status,
                "notes": data.notes,
                "applied_at": data.applied_at,
                "auto_prepared": data.auto_prepared,
                "match_score": data.match_score,
                "cover_letter": data.cover_letter,
                "tailored_resume": data.tailored_resume,
                "tailored_docx_available": bool(data.tailored_docx_path),
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        if isinstance(data, dict) and "tailored_docx_available" not in data:
            data = {**data, "tailored_docx_available": bool(data.get("tailored_docx_path"))}
        return data
