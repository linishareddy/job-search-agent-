import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume_tailoring import ResumeTailoring


class ResumeTailoringRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, resume_id: uuid.UUID, job_id: uuid.UUID) -> ResumeTailoring | None:
        result = await self._session.execute(
            select(ResumeTailoring).where(
                ResumeTailoring.resume_id == resume_id, ResumeTailoring.job_id == job_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        job_id: uuid.UUID,
        match_score: float,
        suggestions: dict,
        tailored_text: str,
    ) -> ResumeTailoring:
        stmt = (
            insert(ResumeTailoring)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                resume_id=resume_id,
                job_id=job_id,
                match_score=match_score,
                suggestions=suggestions,
                tailored_text=tailored_text,
            )
            .on_conflict_do_update(
                constraint="uq_resume_job_tailoring",
                set_={
                    "match_score": match_score,
                    "suggestions": suggestions,
                    "tailored_text": tailored_text,
                },
            )
            .returning(ResumeTailoring)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()
