import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from repositories.resume_repository import ResumeRepository
from schemas.resume import (
    CoverLetterFromResumeRequest,
    ExtractedResumeText,
    ResumeDetailResponse,
    ResumeResponse,
)
from services.groq_service import GroqService
from services.resume_parser_service import extract_text

logger = logging.getLogger(__name__)


class ResumeController:
    def __init__(self, session: AsyncSession):
        self._repo = ResumeRepository(session)
        self._groq = GroqService()

    async def upload(self, file: UploadFile) -> ResumeResponse:
        data = await file.read()
        raw_text = extract_text(file.filename or "resume", file.content_type, data)

        resume = await self._repo.create(
            filename=file.filename or "resume",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(data),
            raw_text=raw_text,
        )

        try:
            parsed = await self._groq.parse_resume(raw_text)
            await self._repo.update_parsed_data(resume.id, parsed, status="parsed")
        except Exception as e:
            logger.error(f"Resume parsing failed for {resume.id}: {e}")
            await self._repo.update_parsed_data(resume.id, {}, status="failed")

        resume = await self._repo.get_by_id(resume.id)
        return ResumeResponse.model_validate(resume)

    async def extract_text_only(self, file: UploadFile) -> ExtractedResumeText:
        """Stateless extraction for the New Search attachment flow — no DB write, no Groq call."""
        data = await file.read()
        raw_text = extract_text(file.filename or "resume", file.content_type, data)
        return ExtractedResumeText(filename=file.filename or "resume", text=raw_text)

    async def list_resumes(self, page: int = 1, page_size: int = 100) -> tuple[list[ResumeResponse], int]:
        resumes, total = await self._repo.get_all(page, page_size)
        return [ResumeResponse.model_validate(r) for r in resumes], total

    async def get_resume(self, resume_id: uuid.UUID) -> ResumeDetailResponse:
        resume = await self._repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))
        return ResumeDetailResponse.model_validate(resume)

    async def delete_resume(self, resume_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(resume_id)
        if not deleted:
            raise NotFoundError("Resume", str(resume_id))

    async def generate_cover_letter_stream(self, resume_id: uuid.UUID, data: CoverLetterFromResumeRequest):
        """Validates the resume up front (so a 404 still arrives as a normal error
        response) and returns the token generator for the route to stream — once
        streaming starts the HTTP status is already committed, so anything that can
        fail with a clean error code has to happen before this point."""
        resume = await self._repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))

        job_dict = {
            "title": data.job_title,
            "company_name": data.company_name,
            "description_summary": data.job_description,
            "skills": [],
        }
        return self._groq.generate_cover_letter_stream(job_dict, resume.raw_text)
