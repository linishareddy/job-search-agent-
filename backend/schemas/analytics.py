import uuid
from typing import Optional

from pydantic import BaseModel


class Bucket(BaseModel):
    label: str
    count: int


class SalaryStats(BaseModel):
    listed_count: int
    unlisted_count: int
    median: Optional[int]
    average: Optional[int]
    histogram: list[Bucket]  # salary range buckets


class SearchAnalytics(BaseModel):
    total_jobs: int
    salary: SalaryStats
    top_skills: list[Bucket]
    by_source: list[Bucket]
    by_work_mode: list[Bucket]
    postings_over_time: list[Bucket]  # weekly buckets, chronological


class SearchCounts(BaseModel):
    total: int
    active: int
    paused: int


class JobCounts(BaseModel):
    unique: int
    total_matches: int
    new_7d: int
    new_24h: int


class TrackerStats(BaseModel):
    saved: int
    applied: int
    interviewing: int
    offer: int
    rejected: int


class SearchSummary(BaseModel):
    search_id: uuid.UUID
    name: str
    job_count: int
    new_count: int
    median_salary: Optional[int] = None


class GlobalAnalytics(BaseModel):
    searches: SearchCounts
    jobs: JobCounts
    tracker: TrackerStats
    salary: SalaryStats
    top_skills: list[Bucket]
    by_source: list[Bucket]
    by_work_mode: list[Bucket]
    postings_over_time: list[Bucket]
    by_search: list[SearchSummary]
