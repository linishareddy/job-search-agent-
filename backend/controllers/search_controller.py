import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from repositories.saved_search_repository import SavedSearchRepository
from schemas.saved_search import SavedSearchCreate, SavedSearchResponse, SavedSearchUpdate
from services.pipeline.orchestrator import PipelineOrchestrator


class SearchController:
    def __init__(self, session: AsyncSession):
        self._repo = SavedSearchRepository(session)
        self._session = session

    async def list_searches(self, user_id: uuid.UUID) -> list[SavedSearchResponse]:
        searches = await self._repo.get_by_user(user_id)
        return [SavedSearchResponse.model_validate(s) for s in searches]

    async def create_search(self, data: SavedSearchCreate) -> SavedSearchResponse:
        search = await self._repo.create(data)
        return SavedSearchResponse.model_validate(search)

    async def get_search(self, search_id: uuid.UUID) -> SavedSearchResponse:
        search = await self._repo.get_by_id(search_id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        return SavedSearchResponse.model_validate(search)

    async def update_search(self, search_id: uuid.UUID, data: SavedSearchUpdate) -> SavedSearchResponse:
        search = await self._repo.update(search_id, data)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        return SavedSearchResponse.model_validate(search)

    async def delete_search(self, search_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(search_id)
        if not deleted:
            raise NotFoundError("SavedSearch", str(search_id))

    async def trigger_run(self, search_id: uuid.UUID) -> uuid.UUID:
        search = await self._repo.get_by_id(search_id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        orchestrator = PipelineOrchestrator(self._session)
        run_id = await orchestrator.run(str(search_id))
        return run_id
