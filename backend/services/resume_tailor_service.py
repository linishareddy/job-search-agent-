"""Generates (and caches) a per (resume, job) tailoring result: a match score,
concrete edit suggestions, and a full tailored resume draft — the resume-tailoring
feature. Read-time/on-demand, same shape as resume_match_service but persisted
since a Groq rewrite is comparatively expensive to redo on every page view.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from models.resume_tailoring import ResumeTailoring
from models.user import User
from repositories.job_repository import JobRepository
from repositories.resume_repository import ResumeRepository
from repositories.resume_tailoring_repository import ResumeTailoringRepository
from schemas.resume_tailoring import ResumeTailoringResponse, TailoredResumeSections
from services.groq_service import GroqService
from services.resume_render_service import render_classic_docx, sections_to_plain_text
from services.resume_storage_service import save_tailored_docx


def _to_response(row: ResumeTailoring) -> ResumeTailoringResponse:
    payload = row.suggestions or {}
    tailored_sections = None
    if row.tailored_sections:
        tailored_sections = TailoredResumeSections.model_validate(row.tailored_sections)
    return ResumeTailoringResponse(
        id=row.id,
        resume_id=row.resume_id,
        job_id=row.job_id,
        match_score=row.match_score,
        matched_keywords=payload.get("matched_keywords", []),
        missing_keywords=payload.get("missing_keywords", []),
        suggestions=payload.get("suggestions", []),
        summary_rewrite=payload.get("summary_rewrite"),
        gaps=payload.get("gaps", []),
        tailored_resume=row.tailored_text,
        tailored_sections=tailored_sections,
        docx_available=bool(row.docx_path),
        template_id=row.template_id or "classic",
        created_at=row.created_at,
    )


class ResumeTailorService:
    def __init__(self, session: AsyncSession):
        self._resume_repo = ResumeRepository(session)
        self._job_repo = JobRepository(session)
        self._tailoring_repo = ResumeTailoringRepository(session)
        self._groq = GroqService()

    async def get_cached(
        self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> ResumeTailoringResponse | None:
        resume = await self._resume_repo.get_by_id(resume_id, user_id=user.id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))
        row = await self._tailoring_repo.get(resume_id, job_id)
        return _to_response(row) if row else None

    async def tailor(
        self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> ResumeTailoringResponse:
        resume = await self._resume_repo.get_by_id(resume_id, user_id=user.id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job", str(job_id))

        job_dict = {
            "title": job.title,
            "company_name": job.company_name,
            "description_summary": job.description_summary,
            "description_raw": job.description_raw,
            "skills": job.skills,
        }
        resume_sections = resume.parsed_sections or {}
        if not resume_sections:
            # Legacy resumes uploaded before structured parsing — pass raw text context
            resume_sections = {"summary": resume.raw_text[:12000], "skills": [], "experience": [], "education": [], "certifications": [], "contact": {}}

        result = await self._groq.tailor_resume(job_dict, resume_sections, resume.raw_text)

        suggestions_payload = {
            "matched_keywords": result.get("matched_keywords", []),
            "missing_keywords": result.get("missing_keywords", []),
            "suggestions": result.get("suggestions", []),
            "summary_rewrite": result.get("summary_rewrite"),
            "gaps": result.get("gaps", []),
        }
        tailored_sections = result.get("tailored_sections") or resume_sections
        tailored_text = result.get("tailored_resume") or sections_to_plain_text(tailored_sections)

        docx_bytes = render_classic_docx(tailored_sections)
        docx_path = save_tailored_docx(resume_id, job_id, docx_bytes)

        row = await self._tailoring_repo.upsert(
            user_id=user.id,
            resume_id=resume_id,
            job_id=job_id,
            match_score=float(result.get("match_score") or 0),
            suggestions=suggestions_payload,
            tailored_text=tailored_text,
            tailored_sections=tailored_sections,
            docx_path=docx_path,
            template_id="classic",
        )
        return _to_response(row)

    async def get_docx_path(
        self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> str:
        resume = await self._resume_repo.get_by_id(resume_id, user_id=user.id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))
        row = await self._tailoring_repo.get(resume_id, job_id)
        if not row or not row.docx_path:
            raise NotFoundError("ResumeTailoring", f"{resume_id}/{job_id}")
        return row.docx_path
