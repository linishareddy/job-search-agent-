import logging
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from constants.sources import REMOTIVE, SOURCE_RESULT_CAPS
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher, build_search_queries
from utils.salary_extractor import extract_salary

logger = logging.getLogger(__name__)

_BASE_URL = "https://remotive.com/api/remote-jobs"


class RemotiveFetcher(BaseJobFetcher):
    source_name = REMOTIVE

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get(self, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(_BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        # Remotive is remote-only — skip for onsite searches
        if search.work_mode == "onsite":
            return []

        cap = SOURCE_RESULT_CAPS[REMOTIVE]
        jobs: list[JobRaw] = []
        seen_ids: set[str] = set()
        last_error: str | None = None

        for query in build_search_queries(search, expansion):
            params = {"search": query, "limit": min(100, cap)}

            try:
                data = await self._get(params)
            except httpx.HTTPError as e:
                last_error = str(e)
                logger.warning(f"Remotive query '{query}' failed: {e}")
                continue

            for item in data.get("jobs", []):
                job = self._map(item)
                if job.external_id and job.external_id in seen_ids:
                    continue
                seen_ids.add(job.external_id)
                jobs.append(job)

            if len(jobs) >= cap:
                break

        if not jobs and last_error:
            raise SourceFetchError(REMOTIVE, last_error)

        del jobs[cap:]
        logger.info(f"Remotive: fetched {len(jobs)} jobs")
        return jobs

    def _map(self, item: dict) -> JobRaw:
        posted_at = None
        if item.get("publication_date"):
            try:
                posted_at = datetime.fromisoformat(item["publication_date"].replace("Z", "+00:00"))
            except ValueError:
                pass

        salary_text = item.get("salary", "")
        salary_min, salary_max = extract_salary(salary_text)

        # Remotive is always remote
        location = item.get("candidate_required_location") or "Remote"

        return JobRaw(
            external_id=str(item.get("id", "")),
            source=REMOTIVE,
            title=item.get("title", ""),
            company_name=item.get("company_name", ""),
            location=location,
            work_mode="remote",
            salary_text=salary_text or None,
            salary_min=salary_min,
            salary_max=salary_max,
            description=item.get("description"),
            apply_url=item.get("url", ""),
            posted_at=posted_at,
        )
