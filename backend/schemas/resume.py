import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ParsedResumeData(BaseModel):
    skills: list[str] = []
    job_titles: list[str] = []
    experience_level: Optional[str] = None  # entry|mid|senior|lead
    years_experience: Optional[float] = None
    summary: Optional[str] = None


class ResumeResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    parse_status: str
    parsed_data: Optional[ParsedResumeData]
    uploaded_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeDetailResponse(ResumeResponse):
    raw_text: str


class ExtractedResumeText(BaseModel):
    filename: str
    text: str


class CoverLetterFromResumeRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: Optional[str] = None
