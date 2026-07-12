import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TailoringSuggestion(BaseModel):
    section: str
    current: str = ""
    suggested: str
    reason: str = ""


class ResumeTailoringResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    job_id: uuid.UUID
    match_score: float
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    suggestions: list[TailoringSuggestion] = []
    summary_rewrite: Optional[str] = None
    gaps: list[str] = []
    tailored_resume: str
    created_at: datetime
