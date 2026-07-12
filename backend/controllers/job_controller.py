import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from models.user import User
from repositories.job_repository import JobRepository
from repositories.resume_repository import ResumeRepository
from repositories.saved_search_repository import SavedSearchRepository
from schemas.analytics import SearchAnalytics
from schemas.job import JobSearchResultResponse
from services import analytics_service, resume_match_service


class JobController:
    def __init__(self, session: AsyncSession):
        self._repo = JobRepository(session)
        self._search_repo = SavedSearchRepository(session)
        self._resume_repo = ResumeRepository(session)

    async def get_results(
        self,
        user: User,
        search_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        only_new: bool = False,
        posted_within_days: int | None = None,
        resume_id: uuid.UUID | None = None,
    ) -> tuple[list[JobSearchResultResponse], int]:
        search = await self._search_repo.get_by_id(search_id, user_id=user.id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))

        # Query param wins if given; otherwise fall back to the search's saved default.
        effective_posted_within_days = posted_within_days
        if effective_posted_within_days is None:
            effective_posted_within_days = search.posted_within_days

        results, total = await self._repo.get_results_for_search(
            search_id=search_id,
            page=page,
            page_size=page_size,
            only_new=only_new,
            posted_within_days=effective_posted_within_days,
        )

        responses = [JobSearchResultResponse.model_validate(r) for r in results]

        # Optional personalized match: score this page's jobs against a chosen resume.
        if resume_id is not None:
            resume = await self._resume_repo.get_by_id(resume_id, user_id=user.id)
            if resume:
                resume_skills = (resume.parsed_data or {}).get("skills", [])
                match_by_job = resume_match_service.match_jobs(
                    resume_text=resume.raw_text,
                    resume_skills=resume_skills,
                    jobs=[r.job for r in results],
                )
                for resp in responses:
                    resp.match = match_by_job.get(str(resp.job.id))

        return responses, total

    async def get_analytics(
        self,
        user: User,
        search_id: uuid.UUID,
        posted_within_days: int | None = None,
    ) -> SearchAnalytics:
        search = await self._search_repo.get_by_id(search_id, user_id=user.id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        effective_posted_within_days = posted_within_days
        if effective_posted_within_days is None:
            effective_posted_within_days = search.posted_within_days
        jobs = await self._repo.get_all_jobs_for_search(
            search_id,
            posted_within_days=effective_posted_within_days,
        )
        return analytics_service.compute_analytics(jobs)
