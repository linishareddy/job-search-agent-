"""Aggregate a search's stored jobs into chart-ready analytics.

Pure in-Python aggregation over the job rows already produced by the pipeline —
fine at this scale (single-tenant, dozens of results per search).
"""
from collections import Counter
from datetime import datetime, timezone
from statistics import median

from models.job import Job
from schemas.analytics import Bucket, SalaryStats, SearchAnalytics

# Annual-USD histogram edges (in thousands): <60k, 60-90, 90-120, 120-150, 150-200, 200k+
_SALARY_EDGES = [60_000, 90_000, 120_000, 150_000, 200_000]
_SALARY_LABELS = ["<60k", "60–90k", "90–120k", "120–150k", "150–200k", "200k+"]

_TOP_SKILLS_LIMIT = 12


def _job_salary(job: Job) -> int | None:
    """A single representative salary per job: midpoint if both bounds, else whichever exists."""
    if job.salary_min and job.salary_max:
        return (job.salary_min + job.salary_max) // 2
    return job.salary_min or job.salary_max


def _salary_bucket_index(value: int) -> int:
    for i, edge in enumerate(_SALARY_EDGES):
        if value < edge:
            return i
    return len(_SALARY_EDGES)


def _salary_stats(jobs: list[Job]) -> SalaryStats:
    salaries = [s for s in (_job_salary(j) for j in jobs) if s is not None]
    listed = len(salaries)
    unlisted = len(jobs) - listed

    hist_counts = [0] * len(_SALARY_LABELS)
    for s in salaries:
        hist_counts[_salary_bucket_index(s)] += 1
    histogram = [Bucket(label=lbl, count=c) for lbl, c in zip(_SALARY_LABELS, hist_counts)]

    return SalaryStats(
        listed_count=listed,
        unlisted_count=unlisted,
        median=int(median(salaries)) if salaries else None,
        average=int(sum(salaries) / len(salaries)) if salaries else None,
        histogram=histogram,
    )


def _counter_buckets(items: list[str], limit: int | None = None) -> list[Bucket]:
    counts = Counter(i for i in items if i)
    ordered = counts.most_common(limit)
    return [Bucket(label=label, count=count) for label, count in ordered]


def _postings_over_time(jobs: list[Job]) -> list[Bucket]:
    """Group posted_at into ISO year-week buckets, chronological. Skips unknown dates."""
    week_counts: Counter[str] = Counter()
    for j in jobs:
        if not j.posted_at:
            continue
        dt = j.posted_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        iso = dt.isocalendar()
        week_counts[f"{iso.year}-W{iso.week:02d}"] += 1
    return [Bucket(label=k, count=week_counts[k]) for k in sorted(week_counts)]


def compute_analytics(jobs: list[Job]) -> SearchAnalytics:
    all_skills: list[str] = []
    for j in jobs:
        all_skills.extend(j.skills or [])

    return SearchAnalytics(
        total_jobs=len(jobs),
        salary=_salary_stats(jobs),
        top_skills=_counter_buckets(all_skills, _TOP_SKILLS_LIMIT),
        by_source=_counter_buckets([j.source for j in jobs]),
        by_work_mode=_counter_buckets([j.work_mode or "unknown" for j in jobs]),
        postings_over_time=_postings_over_time(jobs),
    )
