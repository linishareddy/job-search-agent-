import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from repositories.resume_repository import ResumeRepository
from schemas.resume import ExtractedResumeText, ResumeDetailResponse, ResumeResponse
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

    async def list_resumes(self) -> list[ResumeResponse]:
        resumes = await self._repo.get_all()
        return [ResumeResponse.model_validate(r) for r in resumes]

    async def get_resume(self, resume_id: uuid.UUID) -> ResumeDetailResponse:
        resume = await self._repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError("Resume", str(resume_id))
        return ResumeDetailResponse.model_validate(resume)

    async def delete_resume(self, resume_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(resume_id)
        if not deleted:
            raise NotFoundError("Resume", str(resume_id))
