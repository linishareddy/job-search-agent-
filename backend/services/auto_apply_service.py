"""Assisted auto-apply: on a schedule, find each opted-in user's best new job
matches, prepare a tailored resume + cover letter for each, and queue them as
'ready_to_apply' tracker cards. This does NOT submit anything to the employer —
the user still reviews and clicks apply themselves; see the plan's decision to
avoid browser-form automation (fragile, ToS-gray, requires storing credentials).
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.job_application_repository import JobApplicationRepository
from repositories.job_repository import JobRepository
from repositories.resume_repository import ResumeRepository
from services import email_service, email_templates
from services.groq_service import GroqService
from services.resume_tailor_service import ResumeTailorService

logger = logging.getLogger(__name__)


class AutoApplyService:
    def __init__(self, session: AsyncSession):
        self._job_repo = JobRepository(session)
        self._resume_repo = ResumeRepository(session)
        self._app_repo = JobApplicationRepository(session)
        self._tailor_service = ResumeTailorService(session)
        self._groq = GroqService()

    async def run_for_user(self, user: User) -> list[dict]:
        """Returns the list of {title, company_name, apply_url, match_score} prepared
        this run, for the caller to email a summary of."""
        if not user.auto_apply_resume_id:
            logger.debug(f"User {user.id} has auto-apply on but no resume selected — skipping")
            return []

        resume = await self._resume_repo.get_by_id(user.auto_apply_resume_id, user_id=user.id)
        if not resume:
            logger.warning(f"User {user.id}'s auto_apply_resume_id no longer exists — skipping")
            return []

        tracked_job_ids = await self._app_repo.get_tracked_job_ids(user.id)
        candidates = await self._job_repo.get_auto_apply_candidates(
            user_id=user.id,
            min_score=user.auto_apply_min_score,
            exclude_job_ids=tracked_job_ids,
            limit=user.auto_apply_max_per_run,
        )

        prepared: list[dict] = []
        for job in candidates:
            try:
                tailoring = await self._tailor_service.tailor(user, resume.id, job.id)
                job_dict = {
                    "title": job.title,
                    "company_name": job.company_name,
                    "description_summary": job.description_summary,
                    "skills": job.skills,
                }
                cover_letter = await self._groq.generate_cover_letter(job_dict, resume.raw_text)

                tailored_docx_path = None
                if tailoring.docx_available:
                    try:
                        tailored_docx_path = await self._tailor_service.get_docx_path(user, resume.id, job.id)
                    except Exception:
                        tailored_docx_path = None

                await self._app_repo.create_auto_prepared(
                    user_id=user.id,
                    job_id=job.id,
                    match_score=tailoring.match_score / 100.0,
                    cover_letter=cover_letter,
                    tailored_resume=tailoring.tailored_resume,
                    tailored_docx_path=tailored_docx_path,
                )
                prepared.append({
                    "title": job.title,
                    "company_name": job.company_name,
                    "apply_url": job.apply_url,
                    "match_score": tailoring.match_score / 100.0,
                })
            except Exception as e:
                logger.error(f"Auto-apply prep failed for user {user.id}, job {job.id}: {e}")

        if prepared and user.email_enabled:
            html = email_templates.auto_apply_summary(prepared)
            await email_service.send_email(
                to=user.email,
                subject=f"{len(prepared)} job(s) ready to apply",
                html=html,
            )

        return prepared
