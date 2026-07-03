import logging
from datetime import datetime

import httpx
from rapidfuzz import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential

from constants.sources import ASHBY
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher
from utils.salary_extractor import extract_salary
from utils.text_normalizer import normalize_work_mode

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


class AshbyFetcher(BaseJobFetcher):
    source_name = ASHBY

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def _fetch_company(self, slug: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                _BASE_URL.format(slug=slug),
                json={"includeCompensation": True},
            )
            if response.status_code in (404, 422):
                logger.warning(f"Ashby slug not found: {slug}")
                return []
            response.raise_for_status()
            return response.json().get("jobPostings", [])

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        slugs = [
            c.slug for c in (search.company_slugs or [])
            if c.source == ASHBY
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
                logger.error(f"Ashby fetch failed for {slug}: {e}")
                continue

            for item in raw_jobs:
                title = item.get("title", "")
                if not self._is_relevant(title, keywords, negative_keywords):
                    continue
                jobs.append(self._map(item, slug))

        logger.info(f"Ashby: fetched {len(jobs)} relevant jobs across {len(slugs)} companies")
        return jobs

    def _is_relevant(self, title: str, keywords: list[str], negative_keywords: list[str]) -> bool:
        title_lower = title.lower()
        if any(neg.lower() in title_lower for neg in negative_keywords):
            return False
        return any(fuzz.partial_ratio(kw.lower(), title_lower) >= 65 for kw in keywords)

    def _map(self, item: dict, company_slug: str) -> JobRaw:
        posted_at = None
        if item.get("publishedDate"):
            try:
                posted_at = datetime.fromisoformat(item["publishedDate"].replace("Z", "+00:00"))
            except ValueError:
                pass

        location = item.get("locationName") or item.get("location", {}).get("name")

        # Ashby provides salary as compensationTierSummary (freetext) or structured
        comp = item.get("compensation") or {}
        salary_text = item.get("compensationTierSummary") or ""
        salary_min = comp.get("minValue")
        salary_max = comp.get("maxValue")
        if not salary_min:
            salary_min, salary_max = extract_salary(salary_text)

        work_mode_raw = item.get("isRemote", False)
        if work_mode_raw:
            work_mode = "remote"
        else:
            work_mode = normalize_work_mode(f"{item.get('title', '')} {location or ''}")

        return JobRaw(
            external_id=item.get("id"),
            source=ASHBY,
            title=item.get("title", ""),
            company_name=item.get("organizationName") or company_slug,
            location=location,
            work_mode=work_mode,
            salary_text=salary_text or None,
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            description=item.get("descriptionHtml") or item.get("description"),
            apply_url=item.get("jobUrl", ""),
            posted_at=posted_at,
        )
