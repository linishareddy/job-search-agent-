import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.job_application import JobApplication
from schemas.job_application import JobApplicationCreate, JobApplicationUpdate


class JobApplicationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(self, page: int = 1, page_size: int = 100) -> tuple[list[JobApplication], int]:
        total = (await self._session.execute(select(func.count(JobApplication.id)))).scalar_one()
        result = await self._session.execute(
            select(JobApplication)
            .options(selectinload(JobApplication.job))
            .order_by(JobApplication.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def get_by_id(self, application_id: uuid.UUID) -> JobApplication | None:
        result = await self._session.execute(
            select(JobApplication)
            .options(selectinload(JobApplication.job))
            .where(JobApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: uuid.UUID) -> JobApplication | None:
        result = await self._session.execute(
            select(JobApplication)
            .options(selectinload(JobApplication.job))
            .where(JobApplication.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: JobApplicationCreate) -> JobApplication:
        """Idempotent on job_id — returns the existing card if the job is already tracked."""
        existing = await self.get_by_job_id(data.job_id)
        if existing:
            return existing
        app = JobApplication(
            job_id=data.job_id,
            status=data.status,
            applied_at=datetime.now(timezone.utc) if data.status == "applied" else None,
        )
        self._session.add(app)
        await self._session.flush()
        return await self.get_by_id(app.id)

    async def update(self, application_id: uuid.UUID, data: JobApplicationUpdate) -> JobApplication | None:
        app = await self.get_by_id(application_id)
        if not app:
            return None
        if data.status is not None:
            app.status = data.status
            # Stamp applied_at the first time it moves into 'applied'.
            if data.status == "applied" and app.applied_at is None:
                app.applied_at = datetime.now(timezone.utc)
        if data.notes is not None:
            app.notes = data.notes
        await self._session.flush()
        # Re-fetch so the server-side onupdate `updated_at` is loaded via async IO,
        # not lazily during (sync) pydantic serialization.
        return await self.get_by_id(application_id)

    async def delete(self, application_id: uuid.UUID) -> bool:
        app = await self.get_by_id(application_id)
        if not app:
            return False
        await self._session.delete(app)
        await self._session.flush()
        return True

    async def count_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status)
        )
        return {row[0]: row[1] for row in result.all()}
