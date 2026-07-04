"""Unit tests for analytics aggregation."""
from unittest.mock import MagicMock

from services.analytics_service import compute_analytics


def _job(skills: list[str]) -> MagicMock:
    job = MagicMock()
    job.skills = skills
    job.salary_min = None
    job.salary_max = None
    job.salary_listed = False
    job.source = "test"
    job.work_mode = "remote"
    job.posted_at = None
    return job


def test_skills_deduped_case_insensitive():
    jobs = [
        _job(["Software Development", "Python"]),
        _job(["Software development", "JavaScript"]),
        _job(["SOFTWARE DEVELOPMENT"]),
    ]
    result = compute_analytics(jobs)
    software = [b for b in result.top_skills if _skill_label_match(b.label, "software development")]
    assert len(software) == 1
    assert software[0].count == 3


def test_skills_deduped_within_same_job():
    jobs = [_job(["Python", "python", "PYTHON"])]
    result = compute_analytics(jobs)
    python = [b for b in result.top_skills if b.label.lower() == "python"]
    assert len(python) == 1
    assert python[0].count == 1


def _skill_label_match(label: str, key: str) -> bool:
    return " ".join(label.strip().split()).lower() == key
