import logging
from datetime import datetime, timezone

import httpx
from rapidfuzz import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential

from constants.sources import LEVER
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher
from utils.text_normalizer import normalize_work_mode

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.lever.co/v0/postings/{slug}"


class LeverFetcher(BaseJobFetcher):
    source_name = LEVER

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def _fetch_company(self, slug: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                _BASE_URL.format(slug=slug),
                params={"mode": "json", "state": "published"},
            )
            if response.status_code == 404:
                logger.warning(f"Lever slug not found: {slug}")
                return []
            response.raise_for_status()
            return response.json()

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        slugs = [
            c["slug"] for c in (search.company_slugs or [])
            if c.get("source") == LEVER
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
                logger.error(f"Lever fetch failed for {slug}: {e}")
                continue

            for item in raw_jobs:
                title = item.get("text", "")
                if not self._is_relevant(title, keywords, negative_keywords):
                    continue
                jobs.append(self._map(item))

        logger.info(f"Lever: fetched {len(jobs)} relevant jobs across {len(slugs)} companies")
        return jobs

    def _is_relevant(self, title: str, keywords: list[str], negative_keywords: list[str]) -> bool:
        title_lower = title.lower()
        if any(neg.lower() in title_lower for neg in negative_keywords):
            return False
        return any(fuzz.partial_ratio(kw.lower(), title_lower) >= 65 for kw in keywords)

    def _map(self, item: dict) -> JobRaw:
        posted_at = None
        if item.get("createdAt"):
            try:
                posted_at = datetime.fromtimestamp(item["createdAt"] / 1000, tz=timezone.utc)
            except (ValueError, OSError):
                pass

        location = item.get("categories", {}).get("location")
        commitment = item.get("categories", {}).get("commitment", "")
        team = item.get("categories", {}).get("team", "")

        text_obj = item.get("text", {}) if isinstance(item.get("text"), dict) else {}
        title = text_obj.get("title") or item.get("text", "")

        # Build description from Lever's structured content
        description_parts = []
        for block in item.get("description", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "paragraph":
                for child in block.get("children", []):
                    if isinstance(child, dict):
                        description_parts.append(child.get("text", ""))
        description = " ".join(description_parts) or item.get("descriptionPlain", "")

        work_mode = normalize_work_mode(f"{title} {location or ''} {commitment}")

        return JobRaw(
            external_id=item.get("id"),
            source=LEVER,
            title=title if isinstance(title, str) else item.get("text", ""),
            company_name=item.get("hostedUrl", "").split("/")[4] if item.get("hostedUrl") else "",
            location=location,
            work_mode=work_mode,
            description=description or None,
            apply_url=item.get("hostedUrl", ""),
            posted_at=posted_at,
        )
