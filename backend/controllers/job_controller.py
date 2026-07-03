import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.job_repository import JobRepository
from repositories.saved_search_repository import SavedSearchRepository
from schemas.job import JobSearchResultResponse


class JobController:
    def __init__(self, session: AsyncSession):
        self._repo = JobRepository(session)
        self._search_repo = SavedSearchRepository(session)

    async def get_results(
        self,
        search_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        only_new: bool = False,
        posted_within_days: int | None = None,
    ) -> tuple[list[JobSearchResultResponse], int]:
        # Query param wins if given; otherwise fall back to the search's saved default.
        effective_posted_within_days = posted_within_days
        if effective_posted_within_days is None:
            search = await self._search_repo.get_by_id(search_id)
            if search:
                effective_posted_within_days = search.posted_within_days

        results, total = await self._repo.get_results_for_search(
            search_id=search_id,
            page=page,
            page_size=page_size,
            only_new=only_new,
            posted_within_days=effective_posted_within_days,
        )
        return [JobSearchResultResponse.model_validate(r) for r in results], total
