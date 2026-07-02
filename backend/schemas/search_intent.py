"""Schemas for the free-text ('type one sentence') search creation flow."""
from typing import Optional

from pydantic import BaseModel, Field

from schemas.saved_search import CompanySlug, SavedSearchUpdate


class ParseSearchTextRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000)


class ParsedSearchIntent(BaseModel):
    job_title: str
    field_domain: str
    name: str
    location: Optional[str] = None
    work_mode: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    company_slugs: list[CompanySlug] = Field(default_factory=list)
    confidence: float
    ambiguities: list[str] = Field(default_factory=list)
    raw_text: str


class CreateSearchFromTextRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000)
    overrides: Optional[SavedSearchUpdate] = None
    run_immediately: bool = True
