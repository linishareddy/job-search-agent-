import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from services.embedding_service import EmbeddingService
from utils.fingerprint import compute_fingerprint

logger = logging.getLogger(__name__)

_embedding_service = EmbeddingService()


@dataclass
class DeduplicatedJob:
    """Intermediate representation after dedup — merges data from multiple sources."""
    title: str
    company_name: str
    location: Optional[str]
    work_mode: Optional[str]
    employment_type: Optional[str]
    experience_level: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_text: Optional[str]
    description: Optional[str]
    apply_url: str
    source: str
    source_urls: list[str] = field(default_factory=list)
    posted_at: Optional[object] = None
    fingerprint: str = ""
    embedding: Optional[list[float]] = None


def dedup_in_memory(raw_jobs: list, existing_fingerprints: set[str]) -> list[DeduplicatedJob]:
    """
    Deduplicate raw jobs:
    1. Skip jobs whose fingerprint already exists in the DB.
    2. Within the current batch, merge near-duplicates by fingerprint first, then fuzzy embedding similarity.

    Args:
        raw_jobs: Normalized JobRaw list.
        existing_fingerprints: Set of fingerprints already stored in the DB.

    Returns:
        List of DeduplicatedJob objects — unique, merged records ready for enrichment.
    """
    # Stage 1: fingerprint-based grouping within batch
    seen: dict[str, DeduplicatedJob] = {}
    skipped_existing = 0

    for job in raw_jobs:
        fp = compute_fingerprint(job.company_name, job.title)

        if fp in existing_fingerprints:
            skipped_existing += 1
            continue

        if fp in seen:
            # Merge into the richer record (prefer the one with description)
            existing = seen[fp]
            if job.apply_url and job.apply_url not in existing.source_urls:
                existing.source_urls.append(job.apply_url)
            if not existing.description and job.description:
                existing.description = job.description
            if not existing.salary_min and job.salary_min:
                existing.salary_min = job.salary_min
                existing.salary_max = job.salary_max
        else:
            seen[fp] = DeduplicatedJob(
                title=job.title,
                company_name=job.company_name,
                location=job.location,
                work_mode=job.work_mode,
                employment_type=job.employment_type,
                experience_level=job.experience_level,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                salary_text=job.salary_text,
                description=job.description,
                apply_url=job.apply_url,
                source=job.source,
                source_urls=[job.apply_url] if job.apply_url else [],
                posted_at=job.posted_at,
                fingerprint=fp,
            )

    candidates = list(seen.values())
    logger.info(
        f"Dedup: {len(raw_jobs)} in → "
        f"{skipped_existing} skipped (already in DB) → "
        f"{len(candidates)} new candidates"
    )

    # Stage 2: embed all candidates for vector-based near-dupe detection
    if not candidates:
        return []

    texts = [f"{j.title} at {j.company_name} in {j.location or 'unknown'}" for j in candidates]
    embeddings = _embedding_service.embed_texts(texts)

    for job, emb in zip(candidates, embeddings):
        job.embedding = emb

    # Stage 3: within-batch vector near-dupe merge (O(n²) — acceptable for n < 400)
    merged_indices: set[int] = set()
    result: list[DeduplicatedJob] = []

    for i, job_i in enumerate(candidates):
        if i in merged_indices:
            continue
        for j, job_j in enumerate(candidates):
            if j <= i or j in merged_indices:
                continue
            sim = _embedding_service.cosine_similarity(job_i.embedding, job_j.embedding)
            if sim >= 0.85:
                # Merge j into i
                merged_indices.add(j)
                for url in job_j.source_urls:
                    if url not in job_i.source_urls:
                        job_i.source_urls.append(url)
                if not job_i.description and job_j.description:
                    job_i.description = job_j.description
                if not job_i.salary_min and job_j.salary_min:
                    job_i.salary_min = job_j.salary_min
                    job_i.salary_max = job_j.salary_max

        result.append(job_i)

    logger.info(f"Vector dedup: {len(candidates)} candidates → {len(result)} unique jobs")
    return result
