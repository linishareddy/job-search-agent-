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
