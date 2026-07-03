import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.search_controller import SearchController
from core.response import ok
from schemas.saved_search import SavedSearchCreate, SavedSearchUpdate
from schemas.search_intent import CreateSearchFromTextRequest, ParseSearchTextRequest

router = APIRouter(prefix="/searches")


@router.get("")
async def list_searches(
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    searches = await ctrl.list_searches()
    return ok(data=[s.model_dump() for s in searches], total=len(searches))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_search(
    data: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.create_search(data)
    return ok(data=search.model_dump())


@router.post("/parse-text")
async def parse_search_text(
    data: ParseSearchTextRequest,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    parsed = await ctrl.parse_text(data.text)
    return ok(data=parsed.model_dump())


@router.post("/from-text", status_code=status.HTTP_201_CREATED)
async def create_search_from_text(
    data: CreateSearchFromTextRequest,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search, run_id = await ctrl.create_from_text(data.text, data.overrides, data.run_immediately)
    result = search.model_dump()
    if run_id:
        result["run_id"] = str(run_id)
    return ok(data=result, message="Pipeline started" if run_id else None)


@router.get("/{search_id}")
async def get_search(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.get_search(search_id)
    return ok(data=search.model_dump())


@router.put("/{search_id}")
async def update_search(
    search_id: uuid.UUID,
    data: SavedSearchUpdate,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.update_search(search_id, data)
    return ok(data=search.model_dump())


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    await ctrl.delete_search(search_id)


@router.post("/{search_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    run_id = await ctrl.trigger_run(search_id)
    return ok(data={"run_id": str(run_id)}, message="Pipeline started")


@router.get("/{search_id}/results")
async def get_results(
    search_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    only_new: bool = Query(default=False),
    posted_within_days: int | None = Query(
        default=None,
        ge=1,
        le=365,
        description=(
            "Only return jobs posted within the last N days. Overrides the search's "
            "saved posted_within_days default for this request only. Jobs with an "
            "unknown posted date are always included."
        ),
    ),
    resume_id: uuid.UUID | None = Query(
        default=None,
        description=(
            "If given, score each returned job against this resume and include a "
            "'match' object (cosine similarity + matched/missing skills) per result."
        ),
    ),
    db: AsyncSession = Depends(get_db),
):
    from controllers.job_controller import JobController
    ctrl = JobController(db)
    results, total = await ctrl.get_results(
        search_id, page, page_size, only_new, posted_within_days, resume_id
    )
    return ok(
        data=[r.model_dump() for r in results],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{search_id}/analytics")
async def get_analytics(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from controllers.job_controller import JobController
    ctrl = JobController(db)
    analytics = await ctrl.get_analytics(search_id)
    return ok(data=analytics.model_dump())
