from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _none_to_str(v: object) -> object:
    return "" if v is None else v


class ContactSection(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""

    @field_validator("name", "email", "phone", "location", "linkedin", "github", "website", mode="before")
    @classmethod
    def empty_string_fields(cls, v: object) -> object:
        return _none_to_str(v)


class ExperienceEntry(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []

    @field_validator("title", "company", "location", "start_date", "end_date", mode="before")
    @classmethod
    def empty_string_fields(cls, v: object) -> object:
        return _none_to_str(v)

    @field_validator("bullets", mode="before")
    @classmethod
    def empty_bullet_list(cls, v: object) -> object:
        if v is None:
            return []
        if isinstance(v, list):
            return ["" if b is None else b for b in v]
        return v


class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    location: str = ""
    graduation_date: str = ""
    details: list[str] = []

    @field_validator("degree", "institution", "location", "graduation_date", mode="before")
    @classmethod
    def empty_string_fields(cls, v: object) -> object:
        return _none_to_str(v)

    @field_validator("details", mode="before")
    @classmethod
    def empty_details_list(cls, v: object) -> object:
        if v is None:
            return []
        if isinstance(v, list):
            return ["" if d is None else d for d in v]
        return v


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
