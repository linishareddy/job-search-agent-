import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.job_application_controller import JobApplicationController
from core.response import ok
from schemas.job_application import JobApplicationCreate, JobApplicationUpdate

router = APIRouter(prefix="/applications")


@router.get("")
async def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobApplicationController(db)
    apps, total = await ctrl.list_applications(page, page_size)
    return ok(data=[a.model_dump() for a in apps], total=total, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(data: JobApplicationCreate, db: AsyncSession = Depends(get_db)):
    ctrl = JobApplicationController(db)
    app = await ctrl.create(data)
    return ok(data=app.model_dump())


@router.patch("/{application_id}")
async def update_application(
    application_id: uuid.UUID,
    data: JobApplicationUpdate,
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobApplicationController(db)
    app = await ctrl.update(application_id, data)
    return ok(data=app.model_dump())


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ctrl = JobApplicationController(db)
    await ctrl.delete(application_id)
