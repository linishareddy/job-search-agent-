import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CompanySlug(BaseModel):
    name: str
    slug: str
    source: str  # greenhouse|lever|ashby


class SavedSearchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    job_title: str = Field(..., min_length=1, max_length=256)
    field_domain: str = Field(..., min_length=1)
    location: Optional[str] = None
    work_mode: Optional[str] = None          # remote|hybrid|onsite|any
    experience_level: Optional[str] = None   # entry|mid|senior|lead|any
    employment_type: Optional[str] = None    # full_time|part_time|contract|any
    salary_min: Optional[int] = Field(None, gt=0)
    salary_max: Optional[int] = Field(None, gt=0)
    company_slugs: list[CompanySlug] = Field(default_factory=list)
    poll_interval_minutes: int = Field(default=60, ge=30, le=1440)


class SavedSearchCreate(SavedSearchBase):
    pass


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    job_title: Optional[str] = Field(None, min_length=1, max_length=256)
    field_domain: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = Field(None, gt=0)
    salary_max: Optional[int] = Field(None, gt=0)
    company_slugs: Optional[list[CompanySlug]] = None
    poll_interval_minutes: Optional[int] = Field(None, ge=30, le=1440)
    is_active: Optional[bool] = None


class SavedSearchResponse(SavedSearchBase):
    id: uuid.UUID
    is_active: bool
    last_run_at: Optional[datetime]
    field_expansion_cache: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
