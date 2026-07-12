from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.auto_apply_controller import AutoApplyController
from core.auth import get_current_user
from core.rate_limit import GROQ_ENDPOINT_LIMIT, limiter
from core.response import ok
from models.user import User

router = APIRouter(prefix="/auto-apply")


@router.post("/run")
@limiter.limit(GROQ_ENDPOINT_LIMIT)
async def trigger_auto_apply(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manual trigger for the same logic the 15-minute scheduler runs — mainly
    for testing/UX ('run now') rather than routine use."""
    ctrl = AutoApplyController(db)
    prepared = await ctrl.run(user)
    return ok(data=prepared, message=f"Prepared {len(prepared)} application(s)")
