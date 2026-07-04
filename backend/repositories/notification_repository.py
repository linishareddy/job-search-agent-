import uuid

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        message: str,
        new_job_count: int,
        search_id: uuid.UUID | None = None,
        run_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            search_id=search_id,
            run_id=run_id,
            message=message,
            new_job_count=new_job_count,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def get_all(
        self, unread_only: bool = False, page: int = 1, page_size: int = 50
    ) -> tuple[list[Notification], int]:
        def _filtered(stmt):
            return stmt.where(Notification.is_read.is_(False)) if unread_only else stmt

        total = (await self._session.execute(_filtered(select(func.count(Notification.id))))).scalar_one()

        query = _filtered(select(Notification)).order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(query)
        return result.scalars().all(), total

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

    async def delete_for_search(self, search_id: uuid.UUID, run_ids: list[uuid.UUID]) -> int:
        """Remove notifications tied to a search or its pipeline runs."""
        conditions = [Notification.search_id == search_id]
        if run_ids:
            conditions.append(Notification.run_id.in_(run_ids))
        result = await self._session.execute(delete(Notification).where(or_(*conditions)))
        await self._session.flush()
        return result.rowcount or 0
