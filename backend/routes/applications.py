import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.job_application_controller import JobApplicationController
from core.auth import get_current_user
from core.response import ok
from models.user import User
from schemas.job_application import JobApplicationCreate, JobApplicationUpdate

router = APIRouter(prefix="/applications")


@router.get("")
async def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    app_status: str | None = Query(default=None, alias="status", description="Filter by application status, e.g. ready_to_apply"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobApplicationController(db)
    apps, total = await ctrl.list_applications(user, page, page_size, app_status)
    return ok(data=[a.model_dump() for a in apps], total=total, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(
    data: JobApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobApplicationController(db)
    app = await ctrl.create(user, data)
    return ok(data=app.model_dump())


@router.patch("/{application_id}")
async def update_application(
    application_id: uuid.UUID,
    data: JobApplicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobApplicationController(db)
    app = await ctrl.update(user, application_id, data)
    return ok(data=app.model_dump())


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobApplicationController(db)
    await ctrl.delete(user, application_id)


@router.get("/{application_id}/tailored-resume/download")
async def download_tailored_resume(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from io import BytesIO

    ctrl = JobApplicationController(db)
    content, filename = await ctrl.download_tailored_docx(user, application_id)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
