"""Read-time personalized match between a resume and a set of jobs.

Computes, per job, how well it fits a specific resume — reusing the job embeddings
and skills already stored by the hourly pipeline. Nothing here writes to the DB or
touches the pipeline; it runs on demand when the user picks a resume to match against.
"""
import logging

from models.job import Job
from schemas.job import JobMatchDetail
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

_embedding_service = EmbeddingService()


def _norm(skill: str) -> str:
    return skill.strip().lower()


def match_jobs(
    resume_text: str,
    resume_skills: list[str],
    jobs: list[Job],
) -> dict[str, JobMatchDetail]:
    """Return {job_id (str): JobMatchDetail} for each job.

    match_score = cosine similarity between the resume embedding and the job's stored
    embedding (0 when a job has no embedding). matched/missing skills compare the job's
    skill list against the resume's parsed skills, case-insensitively.
    """
    if not jobs:
        return {}

    resume_embedding = _embedding_service.embed_single(resume_text) if resume_text.strip() else None
    resume_skill_set = {_norm(s) for s in resume_skills if s and s.strip()}

    out: dict[str, JobMatchDetail] = {}
    for job in jobs:
        # job.embedding is a pgvector/numpy array — compare with `is not None` + length,
        # never a bare truth test (numpy raises on ambiguous truth value).
        job_embedding = job.embedding
        if resume_embedding is not None and job_embedding is not None and len(job_embedding) > 0:
            score = _embedding_service.cosine_similarity(resume_embedding, list(job_embedding))
        else:
            score = 0.0

        job_skills = job.skills or []
        matched = [s for s in job_skills if _norm(s) in resume_skill_set]
        missing = [s for s in job_skills if _norm(s) not in resume_skill_set]

        out[str(job.id)] = JobMatchDetail(
            match_score=max(0.0, min(1.0, score)),
            matched_skills=matched,
            missing_skills=missing,
        )
    return out
