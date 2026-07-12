from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.analytics_controller import AnalyticsController
from core.auth import get_current_user
from core.response import ok
from models.user import User

router = APIRouter(prefix="/analytics")


@router.get("/overview")
async def get_overview(
    active_only: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = AnalyticsController(db)
    overview = await ctrl.get_overview(user=user, active_only=active_only)
    return ok(data=overview.model_dump())
