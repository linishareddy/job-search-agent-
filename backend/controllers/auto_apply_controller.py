from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.auto_apply_service import AutoApplyService


class AutoApplyController:
    def __init__(self, session: AsyncSession):
        self._service = AutoApplyService(session)

    async def run(self, user: User) -> list[dict]:
        return await self._service.run_for_user(user)
