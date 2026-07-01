import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from repositories.notification_repository import NotificationRepository
from schemas.notification import NotificationResponse


class NotificationController:
    def __init__(self, session: AsyncSession):
        self._repo = NotificationRepository(session)

    async def list_notifications(self, user_id: uuid.UUID, unread_only: bool = False) -> list[NotificationResponse]:
        notifications = await self._repo.get_for_user(user_id, unread_only)
        return [NotificationResponse.model_validate(n) for n in notifications]

    async def mark_read(self, notification_id: uuid.UUID) -> None:
        success = await self._repo.mark_read(notification_id)
        if not success:
            raise NotFoundError("Notification", str(notification_id))

    async def delete_notification(self, notification_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(notification_id)
        if not deleted:
            raise NotFoundError("Notification", str(notification_id))
