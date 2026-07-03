import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from controllers.resume_controller import ResumeController
from core.response import ok

router = APIRouter(prefix="/resumes")


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    ctrl = ResumeController(db)
    resumes = await ctrl.list_resumes()
    return ok(data=[r.model_dump() for r in resumes], total=len(resumes))


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    ctrl = ResumeController(db)
    resume = await ctrl.upload(file)
    return ok(data=resume.model_dump())


@router.post("/extract-text")
async def extract_resume_text(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Stateless extraction used by the New Search page's optional resume attachment — no DB write."""
    ctrl = ResumeController(db)
    result = await ctrl.extract_text_only(file)
    return ok(data=result.model_dump())


@router.get("/{resume_id}")
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ctrl = ResumeController(db)
    resume = await ctrl.get_resume(resume_id)
    return ok(data=resume.model_dump())


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ctrl = ResumeController(db)
    await ctrl.delete_resume(resume_id)
