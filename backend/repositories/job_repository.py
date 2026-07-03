import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import or_, select, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.job import Job
from models.job_search_result import JobSearchResult
from services.pipeline.enrichment_service import EnrichedJob


class JobRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_existing_fingerprints(self, fingerprints: list[str]) -> set[str]:
        """Return which fingerprints already exist in the DB."""
        result = await self._session.execute(
            select(Job.fingerprint).where(Job.fingerprint.in_(fingerprints))
        )
        return {row[0] for row in result.all()}

    async def upsert_job(self, enriched: EnrichedJob) -> Job:
        """Insert new job or update existing with richer data."""
        stmt = (
            insert(Job)
            .values(
                id=uuid.uuid4(),
                fingerprint=enriched.fingerprint,
                source=enriched.source,
                source_urls=enriched.source_urls,
                title=enriched.title,
                company_name=enriched.company_name,
                location=enriched.location,
                work_mode=enriched.work_mode,
                employment_type=enriched.employment_type,
                experience_level=enriched.experience_level,
                salary_min=enriched.salary_min,
                salary_max=enriched.salary_max,
                salary_listed=enriched.salary_listed,
                description_raw=enriched.description_raw,
                description_summary=enriched.description_summary,
                skills=enriched.skills,
                apply_url=enriched.apply_url,
                posted_at=enriched.posted_at,
                embedding=enriched.embedding,
            )
            .on_conflict_do_update(
                index_elements=["fingerprint"],
                set_={
                    "source_urls": enriched.source_urls,
                    "description_summary": enriched.description_summary,
                    "skills": enriched.skills,
                    "salary_min": enriched.salary_min,
                    "salary_max": enriched.salary_max,
                    "salary_listed": enriched.salary_listed,
                    "work_mode": enriched.work_mode,
                    "embedding": enriched.embedding,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            .returning(Job)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()

    async def upsert_search_result(
        self,
        job_id: uuid.UUID,
        search_id: uuid.UUID,
        run_id: uuid.UUID,
        relevance_score: float,
        bm25_score: float | None,
        cosine_score: float | None,
        is_new: bool,
        match_reason: str | None = None,
        gaps: str | None = None,
    ) -> None:
        stmt = (
            insert(JobSearchResult)
            .values(
                id=uuid.uuid4(),
                job_id=job_id,
                search_id=search_id,
                run_id=run_id,
                relevance_score=relevance_score,
                bm25_score=bm25_score,
                cosine_score=cosine_score,
                match_reason=match_reason,
                gaps=gaps,
                is_new=is_new,
            )
            .on_conflict_do_update(
                constraint="uq_job_search",
                set_={
                    "run_id": run_id,
                    "relevance_score": relevance_score,
                    "bm25_score": bm25_score,
                    "cosine_score": cosine_score,
                    "match_reason": match_reason,
                    "gaps": gaps,
                },
            )
        )
        await self._session.execute(stmt)

    async def get_previous_job_ids(self, search_id: uuid.UUID) -> set[uuid.UUID]:
        """Return job IDs from the last completed run for a search (for is_new detection)."""
        result = await self._session.execute(
            select(JobSearchResult.job_id).where(JobSearchResult.search_id == search_id)
        )
        return {row[0] for row in result.all()}

    async def get_results_for_search(
        self,
        search_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        only_new: bool = False,
        posted_within_days: int | None = None,
    ) -> tuple[list[JobSearchResult], int]:
        """
        posted_within_days: if set, only include jobs posted within the last N days.
        Jobs with an unknown posted_at (None) are still included — same "include and
        flag" philosophy used for missing salary, rather than silently hiding them.
        """
        def _apply_filters(stmt):
            stmt = stmt.where(
                JobSearchResult.search_id == search_id,
                JobSearchResult.is_dismissed.is_(False),
            )
            if only_new:
                stmt = stmt.where(JobSearchResult.is_new.is_(True))
            if posted_within_days is not None:
                cutoff = datetime.now(timezone.utc) - timedelta(days=posted_within_days)
                stmt = stmt.where(or_(Job.posted_at.is_(None), Job.posted_at >= cutoff))
            return stmt

        count_q = select(func.count(JobSearchResult.id))
        if posted_within_days is not None:
            count_q = count_q.join(Job, Job.id == JobSearchResult.job_id)
        count_q = _apply_filters(count_q)
        total = (await self._session.execute(count_q)).scalar_one()

        query = select(JobSearchResult).options(selectinload(JobSearchResult.job))
        if posted_within_days is not None:
            query = query.join(Job, Job.id == JobSearchResult.job_id)
        query = _apply_filters(query)
        query = query.order_by(JobSearchResult.relevance_score.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(query)
        return result.scalars().all(), total
