from typing import Optional

from pydantic import BaseModel, Field


class ContactSection(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""


class ExperienceEntry(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []


class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    location: str = ""
    graduation_date: str = ""
    details: list[str] = []


class ParsedResumeSections(BaseModel):
    contact: ContactSection = Field(default_factory=ContactSection)
    summary: str = ""
    skills: list[str] = []
    experience: list[ExperienceEntry] = []
    education: list[EducationEntry] = []
    certifications: list[str] = []
    job_titles: list[str] = []
    experience_level: Optional[str] = None
    years_experience: Optional[float] = None


class TailoredResumeSections(ParsedResumeSections):
    """Same shape as parsed sections — tailoring rewrites content in-place."""
