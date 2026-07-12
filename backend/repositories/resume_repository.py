import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, user_id: uuid.UUID, filename: str, content_type: str, file_size: int, raw_text: str
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            raw_text=raw_text,
            parse_status="pending",
        )
        self._session.add(resume)
        await self._session.flush()
        return resume

    async def get_all(self, user_id: uuid.UUID, page: int = 1, page_size: int = 100) -> tuple[list[Resume], int]:
        total = (
            await self._session.execute(select(func.count(Resume.id)).where(Resume.user_id == user_id))
        ).scalar_one()
        result = await self._session.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def get_by_id(self, resume_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Resume | None:
        """user_id is an ownership filter for routes reached with a known caller; internal
        follow-up lookups right after a create/update in the same request omit it."""
        stmt = select(Resume).where(Resume.id == resume_id)
        if user_id is not None:
            stmt = stmt.where(Resume.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_parsed_data(self, resume_id: uuid.UUID, parsed_data: dict, status: str) -> None:
        resume = await self.get_by_id(resume_id)
        if not resume:
            return
        resume.parsed_data = parsed_data
        resume.parse_status = status
        await self._session.flush()

    async def delete(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        resume = await self.get_by_id(resume_id, user_id=user_id)
        if not resume:
            return False
        await self._session.delete(resume)
        await self._session.flush()
        return True
