import logging
from datetime import datetime

import httpx
from rapidfuzz import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential

from constants.sources import GREENHOUSE
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher
from utils.text_normalizer import normalize_work_mode

logger = logging.getLogger(__name__)

_BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


class GreenhouseFetcher(BaseJobFetcher):
    source_name = GREENHOUSE

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def _fetch_company(self, slug: str) -> list[dict]:
        url = _BASE_URL.format(slug=slug)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params={"content": "true"})
            if response.status_code == 404:
                logger.warning(f"Greenhouse slug not found: {slug}")
                return []
            response.raise_for_status()
            return response.json().get("jobs", [])

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        # Get company slugs configured for Greenhouse in this search
        slugs = [
            c["slug"] for c in (search.company_slugs or [])
            if c.get("source") == GREENHOUSE
        ]

        if not slugs:
            return []

        jobs: list[JobRaw] = []
        keywords = (
            [search.job_title]
            + expansion.get("search_queries", [])
            + expansion.get("primary_keywords", [])
            + expansion.get("related_titles", [])
        )
        negative_keywords = expansion.get("negative_keywords", [])

        for slug in slugs:
            try:
                raw_jobs = await self._fetch_company(slug)
            except httpx.HTTPError as e:
                logger.error(f"Greenhouse fetch failed for {slug}: {e}")
                continue

            for item in raw_jobs:
                title = item.get("title", "")
                if not self._is_relevant(title, keywords, negative_keywords):
                    continue
                jobs.append(self._map(item, slug))

        logger.info(f"Greenhouse: fetched {len(jobs)} relevant jobs across {len(slugs)} companies")
        return jobs

    def _is_relevant(self, title: str, keywords: list[str], negative_keywords: list[str]) -> bool:
        title_lower = title.lower()
        if any(neg.lower() in title_lower for neg in negative_keywords):
            return False
        return any(fuzz.partial_ratio(kw.lower(), title_lower) >= 65 for kw in keywords)

    def _map(self, item: dict, company_slug: str) -> JobRaw:
        posted_at = None
        if item.get("updated_at"):
            try:
                posted_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        location = item.get("location", {}).get("name")
        work_mode = normalize_work_mode(f"{item.get('title', '')} {location or ''}")

        return JobRaw(
            external_id=str(item.get("id", "")),
            source=GREENHOUSE,
            title=item.get("title", ""),
            company_name=item.get("departments", [{}])[0].get("name") if item.get("departments") else company_slug,
            location=location,
            work_mode=work_mode,
            description=item.get("content"),
            apply_url=item.get("absolute_url", ""),
            posted_at=posted_at,
        )
