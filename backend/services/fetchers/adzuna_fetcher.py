import logging
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from constants.sources import ADZUNA, SOURCE_RESULT_CAPS
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher

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

        search_queries = expansion.get("search_queries", [])
        what = search_queries[0] if search_queries else f"{search.job_title} {search.field_domain}"

        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": min(50, SOURCE_RESULT_CAPS[ADZUNA]),
            "what": what,
            "content-type": "application/json",
        }

        if search.location:
            params["where"] = search.location

        if search.work_mode == "remote":
            params["what"] = f"remote {what}"

        if search.salary_min:
            params["salary_min"] = search.salary_min

        jobs: list[JobRaw] = []
        try:
            data = await self._fetch_page(params, page=1)
            for item in data.get("results", []):
                jobs.append(self._map(item))
        except httpx.HTTPError as e:
            raise SourceFetchError(ADZUNA, str(e))

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
