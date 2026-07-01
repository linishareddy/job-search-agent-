import logging
from dataclasses import dataclass
from typing import Optional

from constants.sources import GROQ_ENRICHMENT_BATCH_SIZE
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService
from services.pipeline.dedup_service import DeduplicatedJob
from utils.salary_extractor import extract_salary

logger = logging.getLogger(__name__)

_groq = GroqService()
_embedding_svc = EmbeddingService()


@dataclass
class EnrichedJob:
    """Final job record after Groq enrichment — ready to upsert into the DB."""
    title: str
    company_name: str
    location: Optional[str]
    work_mode: Optional[str]
    employment_type: Optional[str]
    experience_level: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_listed: bool
    description_raw: Optional[str]
    description_summary: Optional[str]
    skills: list[str]
    apply_url: str
    source: str
    source_urls: list[str]
    posted_at: Optional[object]
    fingerprint: str
    embedding: Optional[list[float]]
    relevance_score: float    # Groq 1-10, normalized to 0-1
    bm25_score: Optional[float]
    cosine_score: Optional[float]


async def enrich_batch(
    jobs: list[DeduplicatedJob],
    job_title: str,
    field_domain: str,
    experience_level: str,
) -> list[EnrichedJob]:
    """Send top-K jobs to Groq for enrichment and return fully populated EnrichedJob objects."""

    batch = jobs[:GROQ_ENRICHMENT_BATCH_SIZE]

    # Build dicts for Groq prompt
    job_dicts = [
        {
            "title": j.title,
            "company_name": j.company_name,
            "description": (j.description or "")[:800],
        }
        for j in batch
    ]

    groq_results = await _groq.enrich_jobs(
        jobs=job_dicts,
        job_title=job_title,
        field_domain=field_domain,
        experience_level=experience_level,
    )

    # Index Groq results by idx
    groq_by_idx: dict[int, dict] = {r["idx"]: r for r in groq_results if "idx" in r}

    enriched: list[EnrichedJob] = []
    for i, job in enumerate(batch):
        groq = groq_by_idx.get(i, {})

        # Salary: prefer Groq-parsed over pre-existing
        salary_min = groq.get("salary_min") or job.salary_min
        salary_max = groq.get("salary_max") or job.salary_max
        if not salary_min and job.salary_text:
            salary_min, salary_max = extract_salary(job.salary_text)

        # work_mode: prefer Groq
        work_mode = groq.get("work_mode") if groq.get("work_mode") not in (None, "unknown") else job.work_mode

        raw_score = groq.get("relevance_score", 5)
        relevance_score = max(0.0, min(1.0, raw_score / 10.0))

        enriched.append(EnrichedJob(
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            work_mode=work_mode,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_listed=salary_min is not None,
            description_raw=job.description,
            description_summary=groq.get("summary"),
            skills=groq.get("skills", []),
            apply_url=job.apply_url,
            source=job.source,
            source_urls=job.source_urls,
            posted_at=job.posted_at,
            fingerprint=job.fingerprint,
            embedding=job.embedding,
            relevance_score=relevance_score,
            bm25_score=getattr(job, "_bm25_score", None),
            cosine_score=getattr(job, "_cosine_score", None),
        ))

    logger.info(f"Enrichment: {len(batch)} jobs enriched by Groq")
    return enriched
