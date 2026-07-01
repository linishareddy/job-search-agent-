import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        message: str,
        new_job_count: int,
        search_id: uuid.UUID | None = None,
        run_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            search_id=search_id,
            run_id=run_id,
            message=message,
            new_job_count=new_job_count,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def get_for_user(self, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc())
        result = await self._session.execute(query)
        return result.scalars().all()

    async def mark_read(self, notification_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
            .returning(Notification.id)
        )
        await self._session.flush()
        return result.scalar_one_or_none() is not None

    async def delete(self, notification_id: uuid.UUID) -> bool:
        n = await self._session.get(Notification, notification_id)
        if not n:
            return False
        await self._session.delete(n)
        await self._session.flush()
        return True
