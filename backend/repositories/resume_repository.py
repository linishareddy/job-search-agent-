import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, filename: str, content_type: str, file_size: int, raw_text: str) -> Resume:
        resume = Resume(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            raw_text=raw_text,
            parse_status="pending",
        )
        self._session.add(resume)
        await self._session.flush()
        return resume

    async def get_all(self, page: int = 1, page_size: int = 100) -> tuple[list[Resume], int]:
        total = (await self._session.execute(select(func.count(Resume.id)))).scalar_one()
        result = await self._session.execute(
            select(Resume)
            .order_by(Resume.uploaded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def get_by_id(self, resume_id: uuid.UUID) -> Resume | None:
        result = await self._session.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        return result.scalar_one_or_none()

    async def update_parsed_data(self, resume_id: uuid.UUID, parsed_data: dict, status: str) -> None:
        resume = await self.get_by_id(resume_id)
        if not resume:
            return
        resume.parsed_data = parsed_data
        resume.parse_status = status
        await self._session.flush()

    async def delete(self, resume_id: uuid.UUID) -> bool:
        resume = await self.get_by_id(resume_id)
        if not resume:
            return False
        await self._session.delete(resume)
        await self._session.flush()
        return True
