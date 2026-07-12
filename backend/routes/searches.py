import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.search_controller import SearchController
from core.auth import get_current_user
from core.rate_limit import GROQ_ENDPOINT_LIMIT, limiter
from core.response import ok
from models.user import User
from schemas.saved_search import BulkDeleteSearchesRequest, SavedSearchCreate, SavedSearchUpdate
from schemas.search_intent import CreateSearchFromTextRequest, ParseSearchTextRequest

router = APIRouter(prefix="/searches")


@router.get("")
async def list_searches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    searches, total = await ctrl.list_searches(user, page, page_size)
    return ok(data=[s.model_dump() for s in searches], total=total, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_search(
    data: SavedSearchCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.create_search(user, data)
    return ok(data=search.model_dump())


@router.post("/parse-text")
@limiter.limit(GROQ_ENDPOINT_LIMIT)
async def parse_search_text(
    request: Request,
    data: ParseSearchTextRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    parsed = await ctrl.parse_text(data.text)
    return ok(data=parsed.model_dump())


@router.post("/from-text", status_code=status.HTTP_201_CREATED)
@limiter.limit(GROQ_ENDPOINT_LIMIT)
async def create_search_from_text(
    request: Request,
    data: CreateSearchFromTextRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search, run_id = await ctrl.create_from_text(
        user, data.text, data.overrides, data.run_immediately, background_tasks
    )
    result = search.model_dump()
    if run_id:
        result["run_id"] = str(run_id)
    return ok(data=result, message="Pipeline started" if run_id else None)


@router.post("/bulk-delete")
async def bulk_delete_searches(
    data: BulkDeleteSearchesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.only_paused and not data.ids:
        raise HTTPException(status_code=400, detail="Provide ids or set only_paused=true")
    ctrl = SearchController(db)
    result = await ctrl.bulk_delete_searches(user, data)
    return ok(data=result.model_dump())


@router.get("/{search_id}")
async def get_search(
    search_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.get_search(user, search_id)
    return ok(data=search.model_dump())


@router.patch("/{search_id}")
async def update_search(
    search_id: uuid.UUID,
    data: SavedSearchUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.update_search(user, search_id, data)
    return ok(data=search.model_dump())


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search(
    search_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    await ctrl.delete_search(user, search_id)


@router.post("/{search_id}/run", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(GROQ_ENDPOINT_LIMIT)
async def trigger_run(
    request: Request,
    search_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    run_id = await ctrl.trigger_run(user, search_id, background_tasks)
    return ok(data={"run_id": str(run_id)}, message="Pipeline started")


@router.get("/{search_id}/run-status")
async def get_run_status(
    search_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    run_status = await ctrl.get_run_status(user, search_id)
    return ok(data=run_status.model_dump())


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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from controllers.job_controller import JobController
    ctrl = JobController(db)
    results, total = await ctrl.get_results(
        user, search_id, page, page_size, only_new, posted_within_days, resume_id
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
    posted_within_days: int | None = Query(default=None, ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from controllers.job_controller import JobController
    ctrl = JobController(db)
    analytics = await ctrl.get_analytics(user, search_id, posted_within_days=posted_within_days)
    return ok(data=analytics.model_dump())
