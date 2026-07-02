import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company_name: str
    location: Optional[str]
    work_mode: Optional[str]
    employment_type: Optional[str]
    experience_level: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: str
    salary_listed: bool
    description_summary: Optional[str]
    skills: list[str]
    apply_url: str
    source: str
    source_urls: list[str]
    posted_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class JobSearchResultResponse(BaseModel):
    id: uuid.UUID
    job: JobResponse
    relevance_score: float
    bm25_score: Optional[float]
    cosine_score: Optional[float]
    match_reason: Optional[str]
    gaps: Optional[str]
    is_new: bool
    is_dismissed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
