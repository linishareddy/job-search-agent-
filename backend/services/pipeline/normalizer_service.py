import logging
import re

from schemas.job_raw import JobRaw
from utils.salary_extractor import extract_salary
from utils.text_normalizer import normalize_work_mode

logger = logging.getLogger(__name__)

_HTML_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str | None:
    if not text:
        return None
    return _HTML_RE.sub(" ", text).strip() or None


def normalize(jobs: list[JobRaw]) -> list[JobRaw]:
    """Normalize a batch of raw jobs: clean HTML, fill missing work_mode, parse salary."""
    normalized = []
    for job in jobs:
        description = _strip_html(job.description)

        # Infer work_mode from title + description if missing
        work_mode = job.work_mode
        if not work_mode and description:
            work_mode = normalize_work_mode(f"{job.title} {description[:300]}")

        # Parse salary from text if structured values are missing
        salary_min = job.salary_min
        salary_max = job.salary_max
        if not salary_min and job.salary_text:
            salary_min, salary_max = extract_salary(job.salary_text)

        # Skip jobs with no apply URL
        if not job.apply_url:
            continue

        normalized.append(
            job.model_copy(
                update={
                    "description": description,
                    "work_mode": work_mode,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                }
            )
        )

    logger.info(f"Normalizer: {len(jobs)} in → {len(normalized)} out")
    return normalized


def apply_negative_filter(jobs: list[JobRaw], negative_keywords: list[str]) -> list[JobRaw]:
    """Discard jobs whose title or description contains any negative keyword."""
    if not negative_keywords:
        return jobs

    filtered = []
    for job in jobs:
        haystack = f"{job.title} {job.description or ''}".lower()
        if any(neg.lower() in haystack for neg in negative_keywords):
            continue
        filtered.append(job)

    logger.info(f"Negative filter: {len(jobs)} in → {len(filtered)} out")
    return filtered
