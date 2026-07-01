import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.search_controller import SearchController
from core.response import ok
from schemas.saved_search import SavedSearchCreate, SavedSearchUpdate

router = APIRouter(prefix="/searches")


@router.get("")
async def list_searches(
    user_id: uuid.UUID = Query(..., description="User UUID"),
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    searches = await ctrl.list_searches(user_id)
    return ok(data=[s.model_dump() for s in searches], total=len(searches))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_search(
    data: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
):
    ctrl = SearchController(db)
    search = await ctrl.create_search(data)
    return ok(data=search.model_dump())


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
    db: AsyncSession = Depends(get_db),
):
    from controllers.job_controller import JobController
    ctrl = JobController(db)
    results, total = await ctrl.get_results(search_id, page, page_size, only_new)
    return ok(
        data=[r.model_dump() for r in results],
        total=total,
        page=page,
        page_size=page_size,
    )
