import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.handlers import NotFoundError
from models.user import User
from repositories.job_application_repository import JobApplicationRepository
from repositories.job_repository import JobRepository
from schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
)


class JobApplicationController:
    def __init__(self, session: AsyncSession):
        self._repo = JobApplicationRepository(session)
        self._job_repo = JobRepository(session)

    async def list_applications(
        self, user: User, page: int = 1, page_size: int = 100, status: str | None = None
    ) -> tuple[list[JobApplicationResponse], int]:
        apps, total = await self._repo.get_all(user.id, page, page_size, status)
        return [JobApplicationResponse.model_validate(a) for a in apps], total

    async def create(self, user: User, data: JobApplicationCreate) -> JobApplicationResponse:
        job = await self._job_repo.get_by_id(data.job_id)
        if not job:
            raise NotFoundError("Job", str(data.job_id))
        app = await self._repo.create(data, user_id=user.id)
        return JobApplicationResponse.model_validate(app)

    async def update(self, user: User, application_id: uuid.UUID, data: JobApplicationUpdate) -> JobApplicationResponse:
        app = await self._repo.update(application_id, data, user_id=user.id)
        if not app:
            raise NotFoundError("JobApplication", str(application_id))
        return JobApplicationResponse.model_validate(app)

    async def delete(self, user: User, application_id: uuid.UUID) -> None:
        deleted = await self._repo.delete(application_id, user_id=user.id)
        if not deleted:
            raise NotFoundError("JobApplication", str(application_id))

    async def download_tailored_docx(self, user: User, application_id: uuid.UUID) -> tuple[bytes, str]:
        from services.resume_storage_service import resolve_storage_path

        app = await self._repo.get_by_id(application_id, user_id=user.id)
        if not app or not app.tailored_docx_path:
            raise NotFoundError("JobApplication", str(application_id))
        path = resolve_storage_path(app.tailored_docx_path)
        if not path.exists():
            raise NotFoundError("JobApplication", str(application_id))
        filename = f"tailored-resume-{app.job.title.replace(' ', '-')}.docx"
        return path.read_bytes(), filename
