import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.resume_controller import ResumeController
from core.auth import get_current_user
from core.rate_limit import GROQ_ENDPOINT_LIMIT, limiter
from core.response import ok
from models.user import User
from schemas.resume import CoverLetterFromResumeRequest

router = APIRouter(prefix="/resumes")


@router.get("")
async def list_resumes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = ResumeController(db)
    resumes, total = await ctrl.list_resumes(user, page, page_size)
    return ok(data=[r.model_dump() for r in resumes], total=total, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = ResumeController(db)
    resume = await ctrl.upload(user, file)
    return ok(data=resume.model_dump())


@router.post("/extract-text")
async def extract_resume_text(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Stateless extraction used by the New Search page's optional resume attachment — no DB write, no auth needed."""
    ctrl = ResumeController(db)
    result = await ctrl.extract_text_only(file)
    return ok(data=result.model_dump())


@router.get("/{resume_id}")
async def get_resume(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = ResumeController(db)
    resume = await ctrl.get_resume(user, resume_id)
    return ok(data=resume.model_dump())


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = ResumeController(db)
    await ctrl.delete_resume(user, resume_id)


@router.post("/{resume_id}/cover-letter")
@limiter.limit(GROQ_ENDPOINT_LIMIT)
async def generate_cover_letter(
    request: Request,
    resume_id: uuid.UUID,
    data: CoverLetterFromResumeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Streams the cover letter as plain text chunks rather than the usual
    {success, data} envelope — the resume is still validated up front (see
    ResumeController.generate_cover_letter_stream) so a 404 arrives normally;
    only the body of a successful response is a raw token stream."""
    ctrl = ResumeController(db)
    token_stream = await ctrl.generate_cover_letter_stream(user, resume_id, data)
    return StreamingResponse(token_stream, media_type="text/plain")


@router.get("/{resume_id}/tailor/{job_id}")
async def get_resume_tailoring(
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the cached tailoring result, if one was already generated."""
    ctrl = ResumeController(db)
    result = await ctrl.get_tailoring(user, resume_id, job_id)
    return ok(data=result.model_dump())


@router.post("/{resume_id}/tailor/{job_id}")
@limiter.limit(GROQ_ENDPOINT_LIMIT)
async def tailor_resume(
    request: Request,
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates (or regenerates) a tailored resume + suggestions for this job."""
    ctrl = ResumeController(db)
    result = await ctrl.tailor_resume(user, resume_id, job_id)
    return ok(data=result.model_dump())
