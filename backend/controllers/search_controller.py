import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from repositories.saved_search_repository import SavedSearchRepository
from schemas.saved_search import SavedSearchBase, SavedSearchCreate, SavedSearchResponse, SavedSearchUpdate
from schemas.search_intent import ParsedSearchIntent
from services.pipeline.orchestrator import PipelineOrchestrator
from services.search_intent_service import SearchIntentService


class SearchController:
    def __init__(self, session: AsyncSession):
        self._repo = SavedSearchRepository(session)
        self._session = session
        self._intent_service = SearchIntentService()

    async def list_searches(self) -> list[SavedSearchResponse]:
        searches = await self._repo.get_all()
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

    async def parse_text(self, text: str) -> ParsedSearchIntent:
        return await self._intent_service.parse(text)

    async def create_from_text(
        self,
        text: str,
        overrides: SavedSearchUpdate | None,
        run_immediately: bool,
    ) -> tuple[SavedSearchResponse, uuid.UUID | None]:
        parsed = await self.parse_text(text)

        fields = {
            "name": parsed.name,
            "job_title": parsed.job_title,
            "field_domain": parsed.field_domain,
            "location": parsed.location,
            "work_mode": parsed.work_mode,
            "experience_level": parsed.experience_level,
            "employment_type": parsed.employment_type,
            "salary_min": parsed.salary_min,
            "salary_max": parsed.salary_max,
            "company_slugs": parsed.company_slugs,
        }
        if overrides:
            override_dict = overrides.model_dump(exclude_none=True)
            fields.update({k: v for k, v in override_dict.items() if k in SavedSearchBase.model_fields})

        search = await self.create_search(SavedSearchCreate(**fields))

        run_id = await self.trigger_run(search.id) if run_immediately else None
        return search, run_id
