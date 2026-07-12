import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from models.user import User
from repositories.resume_repository import ResumeRepository
from schemas.resume import (
    CoverLetterFromResumeRequest,
    ExtractedResumeText,
    ResumeDetailResponse,
    ResumeResponse,
)
from schemas.resume_tailoring import ResumeTailoringResponse
from services.groq_service import GroqService
from services.resume_parser_service import extract_text
from services.resume_storage_service import delete_resume_files, file_kind_from_filename, save_original
from services.resume_tailor_service import ResumeTailorService

logger = logging.getLogger(__name__)


class ResumeController:
    def __init__(self, session: AsyncSession):
        self._repo = ResumeRepository(session)
        self._groq = GroqService()
        self._tailor_service = ResumeTailorService(session)

    async def upload(self, user: User, file: UploadFile) -> ResumeResponse:
        data = await file.read()
        filename = file.filename or "resume"
        content_type = file.content_type or "application/octet-stream"
        file_kind = file_kind_from_filename(filename, content_type)
        raw_text = extract_text(filename, content_type, data)

        resume = await self._repo.create(
            user_id=user.id,
            filename=filename,
            content_type=content_type,
            file_size=len(data),
            raw_text=raw_text,
            file_kind=file_kind,
        )

        storage_path = save_original(resume.id, file_kind, data)
        await self._repo.update_storage_path(resume.id, storage_path)

        try:
            parsed = await self._groq.parse_resume(raw_text)
            await self._repo.update_parsed_data(
                resume.id,
                parsed.get("parsed_data", {}),
                status="parsed",
                parsed_sections=parsed.get("parsed_sections"),
            )
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

    async def list_resumes(self, user: User, page: int = 1, page_size: int = 100) -> tuple[list[ResumeResponse], int]:
        resumes, total = await self._repo.get_all(user.id, page, page_size)
        return [ResumeResponse.model_validate(r) for r in resumes], total

    async def get_resume(self, user: User, resume_id: uuid.UUID) -> ResumeDetailResponse:
        resume = await self._repo.get_by_id(resume_id, user_id=user.id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))
        return ResumeDetailResponse.model_validate(resume)

    async def delete_resume(self, user: User, resume_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(resume_id, user_id=user.id)
        if not deleted:
            raise NotFoundError("Resume", str(resume_id))
        delete_resume_files(resume_id)

    async def generate_cover_letter_stream(self, user: User, resume_id: uuid.UUID, data: CoverLetterFromResumeRequest):
        """Validates the resume up front (so a 404 still arrives as a normal error
        response) and returns the token generator for the route to stream — once
        streaming starts the HTTP status is already committed, so anything that can
        fail with a clean error code has to happen before this point."""
        resume = await self._repo.get_by_id(resume_id, user_id=user.id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))

        job_dict = {
            "title": data.job_title,
            "company_name": data.company_name,
            "description_summary": data.job_description,
            "skills": [],
        }
        return self._groq.generate_cover_letter_stream(job_dict, resume.raw_text)

    async def get_tailoring(
        self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> ResumeTailoringResponse:
        cached = await self._tailor_service.get_cached(user, resume_id, job_id)
        if not cached:
            raise NotFoundError("ResumeTailoring", f"{resume_id}/{job_id}")
        return cached

    async def tailor_resume(
        self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> ResumeTailoringResponse:
        return await self._tailor_service.tailor(user, resume_id, job_id)

    async def download_tailored_docx(
        self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> tuple[bytes, str]:
        from services.resume_storage_service import resolve_storage_path

        rel_path = await self._tailor_service.get_docx_path(user, resume_id, job_id)
        path = resolve_storage_path(rel_path)
        if not path.exists():
            raise NotFoundError("ResumeTailoring", f"{resume_id}/{job_id}")
        return path.read_bytes(), f"tailored-resume-{job_id}.docx"
