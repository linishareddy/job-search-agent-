import logging
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from constants.sources import ARBEITNOW, SOURCE_RESULT_CAPS
from exceptions.handlers import SourceFetchError
from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse
from services.fetchers.base_fetcher import BaseJobFetcher
from services.fetchers.feed_filter import matches_keywords, search_query_list

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowFetcher(BaseJobFetcher):
    source_name = ARBEITNOW

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get_all(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(_BASE_URL)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload.get("data") or []
            return payload if isinstance(payload, list) else []

    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        cap = SOURCE_RESULT_CAPS[ARBEITNOW]
        queries = search_query_list(search, expansion)
        remote_only = search.work_mode in ("remote", None, "any")

        try:
            raw_items = await self._get_all()
        except httpx.HTTPError as e:
            raise SourceFetchError(ARBEITNOW, str(e)) from e

        jobs: list[JobRaw] = []
        seen_ids: set[str] = set()

        for item in raw_items:
            if remote_only and not item.get("remote"):
                continue
            job = self._map(item)
            if not job.external_id or job.external_id in seen_ids:
                continue
            if not matches_keywords(
                " ".join(
                    [
                        job.title,
                        job.company_name,
                        job.description or "",
                        " ".join(item.get("tags") or []),
                    ]
                ),
                queries,
            ):
                continue
            seen_ids.add(job.external_id)
            jobs.append(job)
            if len(jobs) >= cap:
                break

        logger.info(f"Arbeitnow: fetched {len(jobs)} jobs")
        return jobs

    def _map(self, item: dict) -> JobRaw:
        posted_at = None
        if item.get("created_at"):
            try:
                posted_at = datetime.fromtimestamp(int(item["created_at"]), tz=timezone.utc)
            except (TypeError, ValueError):
                pass

        slug = item.get("slug") or ""
        apply_url = item.get("url") or (f"https://www.arbeitnow.com/jobs/{slug}" if slug else "")

        work_mode = "remote" if item.get("remote") else None

        return JobRaw(
            external_id=slug or apply_url,
            source=ARBEITNOW,
            title=item.get("title") or "",
            company_name=item.get("company_name") or "",
            location=item.get("location") or None,
            work_mode=work_mode,
            employment_type=(item.get("job_types") or [None])[0],
            description=item.get("description"),
            apply_url=apply_url,
            posted_at=posted_at,
        )
