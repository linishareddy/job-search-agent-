"""Internal schema for raw job data fetched from any source, before enrichment."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class JobRaw(BaseModel):
    external_id: Optional[str] = None
    source: str
    title: str
    company_name: str
    location: Optional[str] = None
    work_mode: Optional[str] = None        # remote|hybrid|onsite|unknown
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_text: Optional[str] = None      # raw salary string before parsing
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: Optional[str] = None
    apply_url: str
    posted_at: Optional[datetime] = None
