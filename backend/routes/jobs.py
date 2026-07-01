import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.job_controller import JobController
from core.response import ok

router = APIRouter(prefix="/jobs")


@router.get("/search/{search_id}/results")
async def get_search_results(
    search_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    only_new: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobController(db)
    results, total = await ctrl.get_results(search_id, page, page_size, only_new)
    return ok(
        data=[r.model_dump() for r in results],
        total=total,
        page=page,
        page_size=page_size,
    )
