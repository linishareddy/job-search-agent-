import logging
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from constants.sources import JOOBLE
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher
from utils.salary_extractor import extract_salary

logger = logging.getLogger(__name__)

_BASE_URL = "https://jooble.org/api/{api_key}"


class JoobleFetcher(BaseJobFetcher):
    source_name = JOOBLE

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _post(self, api_key: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                _BASE_URL.format(api_key=api_key),
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        if not settings.jooble_api_key:
            logger.warning("Jooble API key not configured — skipping")
            return []

        search_queries = expansion.get("search_queries", [])
        keywords = search_queries[0] if search_queries else f"{search.job_title} {search.field_domain}"
        location = search.location or "United States"

        payload = {
            "keywords": keywords,
            "location": location,
            "page": 1,
        }

        if search.work_mode == "remote":
            payload["remotetype"] = "remote"

        try:
            data = await self._post(settings.jooble_api_key, payload)
        except httpx.HTTPError as e:
            raise SourceFetchError(JOOBLE, str(e))

        jobs = [self._map(item) for item in data.get("jobs", [])]
        logger.info(f"Jooble: fetched {len(jobs)} jobs")
        return jobs

    def _map(self, item: dict) -> JobRaw:
        posted_at = None
        if item.get("updated"):
            try:
                posted_at = datetime.fromisoformat(item["updated"].replace("Z", "+00:00"))
            except ValueError:
                pass

        salary_text = item.get("salary", "")
        salary_min, salary_max = extract_salary(salary_text)

        return JobRaw(
            source=JOOBLE,
            title=item.get("title", ""),
            company_name=item.get("company", ""),
            location=item.get("location"),
            salary_text=salary_text or None,
            salary_min=salary_min,
            salary_max=salary_max,
            description=item.get("snippet"),
            apply_url=item.get("link", ""),
            posted_at=posted_at,
        )
