import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.search_run import SearchRun


class SearchRunRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, search_id: uuid.UUID) -> SearchRun:
        run = SearchRun(search_id=search_id, status="running")
        self._session.add(run)
        await self._session.flush()
        return run

    async def update_stage(self, run_id: uuid.UUID, stage_index: int) -> None:
        # Commits immediately (not just flush): the whole point is that a separate
        # connection polling for progress sees this the moment it happens, rather
        # than only once the caller's outer transaction eventually commits.
        await self._session.execute(
            update(SearchRun).where(SearchRun.id == run_id).values(current_stage_index=stage_index)
        )
        await self._session.commit()

    async def complete(
        self,
        run_id: uuid.UUID,
        jobs_fetched: int,
        jobs_matched: int,
        new_jobs: int,
        source_stats: dict | None = None,
    ) -> None:
        await self._session.execute(
            update(SearchRun)
            .where(SearchRun.id == run_id)
            .values(
                status="completed",
                finished_at=datetime.now(timezone.utc),
                jobs_fetched=jobs_fetched,
                jobs_matched=jobs_matched,
                new_jobs=new_jobs,
                source_stats=source_stats,
            )
        )
        await self._session.commit()

    async def fail(self, run_id: uuid.UUID, error_detail: str, source_stats: dict | None = None) -> None:
        await self._session.execute(
            update(SearchRun)
            .where(SearchRun.id == run_id)
            .values(
                status="failed",
                finished_at=datetime.now(timezone.utc),
                error_detail=error_detail[:2000],
                source_stats=source_stats,
            )
        )
        await self._session.commit()

    async def get_latest(self, search_id: uuid.UUID) -> SearchRun | None:
        result = await self._session.execute(
            select(SearchRun)
            .where(SearchRun.search_id == search_id, SearchRun.status == "completed")
            .order_by(SearchRun.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_any(self, search_id: uuid.UUID) -> SearchRun | None:
        """Latest run regardless of status — used for live progress polling."""
        result = await self._session.execute(
            select(SearchRun)
            .where(SearchRun.search_id == search_id)
            .order_by(SearchRun.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
