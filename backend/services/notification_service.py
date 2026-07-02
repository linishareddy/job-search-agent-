import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession):
        self._repo = NotificationRepository(session)

    async def notify_new_jobs(
        self,
        search_name: str,
        search_id: uuid.UUID,
        run_id: uuid.UUID,
        new_count: int,
        high_score_count: int,
    ) -> None:
        if new_count <= 0:
            return

        message = (
            f"'{search_name}': {new_count} new job(s) found"
            + (f", {high_score_count} highly relevant" if high_score_count > 0 else "")
        )

        await self._repo.create(
            search_id=search_id,
            run_id=run_id,
            message=message,
            new_job_count=new_count,
        )
        logger.info(f"Notification created: {message}")
