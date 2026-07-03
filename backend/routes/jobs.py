import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.job_controller import JobController
from core.response import ok
from schemas.job import CoverLetterRequest

router = APIRouter(prefix="/jobs")


@router.post("/{job_id}/cover-letter")
async def generate_cover_letter(
    job_id: uuid.UUID,
    data: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
):
    ctrl = JobController(db)
    result = await ctrl.generate_cover_letter(job_id, data.resume_id)
    return ok(data=result.model_dump())
