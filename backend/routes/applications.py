import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.job_application_controller import JobApplicationController
from core.response import ok
from schemas.job_application import JobApplicationCreate, JobApplicationUpdate

router = APIRouter(prefix="/applications")


@router.get("")
async def list_applications(db: AsyncSession = Depends(get_db)):
    ctrl = JobApplicationController(db)
    apps = await ctrl.list_applications()
    return ok(data=[a.model_dump() for a in apps], total=len(apps))


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
