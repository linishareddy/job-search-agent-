import uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from constants.sources import PIPELINE_STAGE_LABELS
from exceptions.handlers import NotFoundError
from models.user import User
from repositories.saved_search_repository import SavedSearchRepository
from repositories.search_run_repository import SearchRunRepository
from schemas.saved_search import (
    BulkDeleteSearchesRequest,
    BulkDeleteSearchesResponse,
    SavedSearchBase,
    SavedSearchCreate,
    SavedSearchResponse,
    SavedSearchUpdate,
)
from schemas.search_intent import ParsedSearchIntent
from schemas.search_run import RunStatusResponse
from services.pipeline.orchestrator import PipelineOrchestrator, run_in_background
from services.search_intent_service import SearchIntentService


class SearchController:
    def __init__(self, session: AsyncSession):
        self._repo = SavedSearchRepository(session)
        self._run_repo = SearchRunRepository(session)
        self._session = session
        self._intent_service = SearchIntentService()

    async def list_searches(self, user: User, page: int = 1, page_size: int = 100) -> tuple[list[SavedSearchResponse], int]:
        searches, total = await self._repo.get_all(user.id, page, page_size)
        return [SavedSearchResponse.model_validate(s) for s in searches], total

    async def create_search(self, user: User, data: SavedSearchCreate) -> SavedSearchResponse:
        search = await self._repo.create(data, user_id=user.id)
        return SavedSearchResponse.model_validate(search)

    async def get_search(self, user: User, search_id: uuid.UUID) -> SavedSearchResponse:
        search = await self._repo.get_by_id(search_id, user_id=user.id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        return SavedSearchResponse.model_validate(search)

    async def update_search(self, user: User, search_id: uuid.UUID, data: SavedSearchUpdate) -> SavedSearchResponse:
        search = await self._repo.update(search_id, data, user_id=user.id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        return SavedSearchResponse.model_validate(search)

    async def delete_search(self, user: User, search_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(search_id, user_id=user.id)
        if not deleted:
            raise NotFoundError("SavedSearch", str(search_id))

    async def bulk_delete_searches(self, user: User, data: BulkDeleteSearchesRequest) -> BulkDeleteSearchesResponse:
        if data.only_paused:
            search_ids = await self._repo.get_ids_by_active(False, user_id=user.id)
        else:
            search_ids = data.ids

        if not search_ids:
            return BulkDeleteSearchesResponse(deleted=0)

        deleted = await self._repo.delete_many(search_ids, user_id=user.id)
        return BulkDeleteSearchesResponse(deleted=deleted)

    async def trigger_run(self, user: User, search_id: uuid.UUID, background_tasks: BackgroundTasks) -> uuid.UUID:
        search = await self._repo.get_by_id(search_id, user_id=user.id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        orchestrator = PipelineOrchestrator(self._session)
        search, run = await orchestrator.create_run(str(search_id))
        if not run:
            raise NotFoundError("SavedSearch", str(search_id))
        # The run row is already committed (create_run does this) — hand the actual
        # pipeline work to a background task so this request returns immediately
        # and the frontend's progress polling isn't blocked behind it.
        background_tasks.add_task(run_in_background, str(search_id), run.id)
        return run.id

    async def get_run_status(self, user: User, search_id: uuid.UUID) -> RunStatusResponse:
        search = await self._repo.get_by_id(search_id, user_id=user.id)
        if not search:
            raise NotFoundError("SavedSearch", str(search_id))
        run = await self._run_repo.get_latest_any(search_id)
        if not run:
            raise NotFoundError("SearchRun", str(search_id))
        return RunStatusResponse(
            run_id=run.id,
            status=run.status,
            current_stage_index=run.current_stage_index,
            current_stage_label=PIPELINE_STAGE_LABELS[run.current_stage_index],
            total_stages=len(PIPELINE_STAGE_LABELS),
            jobs_fetched=run.jobs_fetched,
            jobs_matched=run.jobs_matched,
            new_jobs=run.new_jobs,
            error_detail=run.error_detail,
        )

    async def parse_text(self, text: str) -> ParsedSearchIntent:
        return await self._intent_service.parse(text)

    async def create_from_text(
        self,
        user: User,
        text: str,
        overrides: SavedSearchUpdate | None,
        run_immediately: bool,
        background_tasks: BackgroundTasks,
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

        search = await self.create_search(user, SavedSearchCreate(**fields))

        run_id = await self.trigger_run(user, search.id, background_tasks) if run_immediately else None
        return search, run_id
