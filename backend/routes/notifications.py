import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.notification_controller import NotificationController
from core.response import ok

router = APIRouter(prefix="/notifications")


@router.get("")
async def list_notifications(
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    ctrl = NotificationController(db)
    notifications, total = await ctrl.list_notifications(unread_only, page, page_size)
    return ok(data=[n.model_dump() for n in notifications], total=total, page=page, page_size=page_size)


@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ctrl = NotificationController(db)
    await ctrl.mark_read(notification_id)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ctrl = NotificationController(db)
    await ctrl.delete_notification(notification_id)
