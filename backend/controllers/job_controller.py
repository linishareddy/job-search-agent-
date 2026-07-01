import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.job_repository import JobRepository
from schemas.job import JobSearchResultResponse


class JobController:
    def __init__(self, session: AsyncSession):
        self._repo = JobRepository(session)

    async def get_results(
        self,
        search_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        only_new: bool = False,
    ) -> tuple[list[JobSearchResultResponse], int]:
        results, total = await self._repo.get_results_for_search(
            search_id=search_id,
            page=page,
            page_size=page_size,
            only_new=only_new,
        )
        return [JobSearchResultResponse.model_validate(r) for r in results], total
