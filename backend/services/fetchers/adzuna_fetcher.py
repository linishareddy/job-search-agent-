import logging
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from constants.sources import ADZUNA, SOURCE_RESULT_CAPS
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher, build_search_queries

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"


class AdzunaFetcher(BaseJobFetcher):
    source_name = ADZUNA

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_page(self, params: dict, page: int) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(_BASE_URL.format(page=page), params=params)
            response.raise_for_status()
            return response.json()

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            logger.warning("Adzuna credentials not configured — skipping")
            return []

        # salary_min is deliberately NOT sent: Adzuna would then exclude every posting
        # without structured salary data, but missing-salary jobs must be included
        # (PRD §3) — salary still comes back in the response for downstream use.
        # Likewise no "remote" keyword is injected into `what`; work mode is inferred
        # downstream and relevance is handled by scoring.
        cap = SOURCE_RESULT_CAPS[ADZUNA]
        jobs: list[JobRaw] = []
        seen_ids: set[str] = set()
        last_error: str | None = None

        for what in build_search_queries(search, expansion):
            params = {
                "app_id": settings.adzuna_app_id,
                "app_key": settings.adzuna_app_key,
                "results_per_page": min(50, cap),
                "what": what,
                "content-type": "application/json",
            }
            if search.location:
                params["where"] = search.location

            try:
                data = await self._fetch_page(params, page=1)
            except httpx.HTTPError as e:
                last_error = str(e)
                logger.warning(f"Adzuna query '{what}' failed: {e}")
                continue

            for item in data.get("results", []):
                job = self._map(item)
                if job.external_id and job.external_id in seen_ids:
                    continue
                seen_ids.add(job.external_id)
                jobs.append(job)

            if len(jobs) >= cap:
                break

        if not jobs and last_error:
            raise SourceFetchError(ADZUNA, last_error)

        del jobs[cap:]
        logger.info(f"Adzuna: fetched {len(jobs)} jobs")
        return jobs

    def _map(self, item: dict) -> JobRaw:
        posted_at = None
        if item.get("created"):
            try:
                posted_at = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return JobRaw(
            external_id=str(item.get("id", "")),
            source=ADZUNA,
            title=item.get("title", ""),
            company_name=item.get("company", {}).get("display_name", ""),
            location=item.get("location", {}).get("display_name"),
            salary_min=int(item["salary_min"]) if item.get("salary_min") else None,
            salary_max=int(item["salary_max"]) if item.get("salary_max") else None,
            description=item.get("description"),
            apply_url=item.get("redirect_url", ""),
            posted_at=posted_at,
        )
