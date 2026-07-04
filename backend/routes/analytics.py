from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.analytics_controller import AnalyticsController
from core.response import ok

router = APIRouter(prefix="/analytics")


@router.get("/overview")
async def get_overview(
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    ctrl = AnalyticsController(db)
    overview = await ctrl.get_overview(active_only=active_only)
    return ok(data=overview.model_dump())
