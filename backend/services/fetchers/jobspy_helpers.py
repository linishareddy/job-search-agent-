"""Shared helpers for JobSpy-based fetchers (LinkedIn, Naukri)."""
import logging
from datetime import datetime
from typing import Any

import pandas as pd

from schemas.job_raw import JobRaw
from utils.salary_extractor import extract_salary

logger = logging.getLogger(__name__)


def _parse_posted_at(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _row_str(row: pd.Series, key: str, default: str = "") -> str:
    val = row.get(key)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return str(val).strip()


def jobspy_row_to_job_raw(row: pd.Series, source: str) -> JobRaw | None:
    title = _row_str(row, "title")
    company = _row_str(row, "company")
    apply_url = _row_str(row, "job_url_direct") or _row_str(row, "job_url")
    if not title or not company or not apply_url:
        return None

    external_id = _row_str(row, "id") or apply_url
    location = _row_str(row, "location") or None

    is_remote = row.get("is_remote")
    work_mode = None
    if is_remote is True or str(is_remote).lower() in ("true", "1"):
        work_mode = "remote"

    salary_min = row.get("min_amount")
    salary_max = row.get("max_amount")
    if pd.isna(salary_min):
        salary_min = None
    if pd.isna(salary_max):
        salary_max = None
    salary_text = None
    if salary_min is not None or salary_max is not None:
        salary_text = f"{salary_min or ''}-{salary_max or ''}".strip("-")
    else:
        parsed_min, parsed_max = extract_salary(_row_str(row, "description"))
        salary_min, salary_max = parsed_min, parsed_max

    description = _row_str(row, "description") or None

    return JobRaw(
        external_id=external_id,
        source=source,
        title=title,
        company_name=company,
        location=location,
        work_mode=work_mode,
        employment_type=_row_str(row, "job_type") or None,
        salary_text=salary_text,
        salary_min=int(salary_min) if salary_min is not None else None,
        salary_max=int(salary_max) if salary_max is not None else None,
        description=description,
        apply_url=apply_url,
        posted_at=_parse_posted_at(row.get("date_posted")),
    )


def dataframe_to_jobs(df: pd.DataFrame, source: str) -> list[JobRaw]:
    jobs: list[JobRaw] = []
    for _, row in df.iterrows():
        job = jobspy_row_to_job_raw(row, source)
        if job:
            jobs.append(job)
    return jobs
